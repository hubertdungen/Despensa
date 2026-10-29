"""Private asynchronous planning runs and explicit, persisted trip selection."""
import hashlib
import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from datetime import datetime,timedelta,timezone
from planner import eligible,make_plan,matching
from routing import road_matrix
from travel import resolve,summarize
from journey import departure,traffic_key,enrich_traffic,enrich_transit,traffic_summary
from schedule import best_windows

SCHEMA='''
CREATE TABLE IF NOT EXISTS plan_runs(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,month TEXT NOT NULL,
 signature TEXT NOT NULL,selection_signature TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL,
 status TEXT NOT NULL,phase TEXT NOT NULL,params TEXT NOT NULL,result TEXT,error TEXT NOT NULL DEFAULT '');
CREATE INDEX IF NOT EXISTS plan_owner ON plan_runs(user_id,created);
CREATE TABLE IF NOT EXISTS selected_plans(user_id TEXT NOT NULL,month TEXT NOT NULL,run_id TEXT NOT NULL,
 plan_id TEXT NOT NULL,signature TEXT NOT NULL,data TEXT NOT NULL,PRIMARY KEY(user_id,month));
'''


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


class PlanService:
    def __init__(self,database,profile,items,offers,folder):
        self.database=database;self.profile=profile;self.items=items;self.offers=offers;self.folder=folder
        self.pool=ThreadPoolExecutor(max_workers=2,thread_name_prefix='shopping-plan')
        self.slots=threading.BoundedSemaphore(8);self.lock=threading.Lock()
        with database() as db:
            db.executescript(SCHEMA)
            db.execute("UPDATE plan_runs SET status='interrupted',phase='interrupted',error='Cálculo interrompido; volte a calcular' WHERE status IN ('queued','running')")

    def user_signature(self,uid,month,params):
        return digest([self.profile(uid),self.items(uid,month),params])

    def selection_signature(self,uid,month,params):
        # Checking off purchases keeps the chosen itinerary usable. Editing or
        # removing products still invalidates its quantities and assignments.
        # A window search spans days, so its start day does not invalidate it.
        items=[{k:v for k,v in item.items() if k!='checked'} for item in self.items(uid,month)]
        if params.get('kind')=='windows':params={k:v for k,v in params.items() if k!='day'}
        return digest([self.profile(uid),items,params])

    def start(self,uid,month,params):
        user_sig=self.user_signature(uid,month,params);selection_sig=self.selection_signature(uid,month,params)
        with self.lock,self.database() as db:
            stamp=db.execute("SELECT MAX(rowid),COUNT(*) FROM offers WHERE user_id='' OR user_id=?",(uid,)).fetchone()
            bucket=int(time.time()//300) if not params.get('departure_time') else 0
            signature=digest([user_sig,list(stamp),bucket])
            old=db.execute("SELECT id FROM plan_runs WHERE user_id=? AND signature=? AND status IN ('queued','running','ready') AND created>? ORDER BY created DESC LIMIT 1",(uid,signature,time.time()-300)).fetchone()
            if old:return old['id']
            if not self.slots.acquire(blocking=False):raise ValueError('Há vários planos em cálculo. Aguarde um momento.')
            identifier=uuid.uuid4().hex;now=time.time()
            db.execute("UPDATE plan_runs SET status='superseded',phase='superseded' WHERE user_id=? AND status='queued'",(uid,))
            db.execute('INSERT INTO plan_runs(id,user_id,month,signature,selection_signature,created,updated,status,phase,params) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (identifier,uid,month,signature,selection_sig,now,now,'queued','queued',json.dumps(params)))
            db.execute("DELETE FROM plan_runs WHERE created<? AND status NOT IN ('queued','running')",(now-2*86400,))
        try:self.pool.submit(self._run,identifier,uid,month,params)
        except RuntimeError:
            self.slots.release();raise ValueError('Serviço de planos a reiniciar; volte a tentar') from None
        return identifier

    def _phase(self,identifier,phase):
        with self.database() as db:
            row=db.execute('SELECT status FROM plan_runs WHERE id=?',(identifier,)).fetchone()
            if not row or row['status']=='superseded':raise ValueError('Pedido substituído por um cálculo mais recente')
            db.execute("UPDATE plan_runs SET status='running',phase=?,updated=? WHERE id=?",(phase,time.time(),identifier))

    def _run(self,identifier,uid,month,params):
        try:
            work=self.calculate_windows if params.get('kind')=='windows' else self.calculate
            result=work(uid,month,params,lambda phase:self._phase(identifier,phase))
            with self.database() as db:
                db.execute("UPDATE plan_runs SET result=?,status='ready',phase='ready',updated=? WHERE id=?",(json.dumps(result),time.time(),identifier))
        except Exception as error:
            message=str(error) if isinstance(error,ValueError) else 'Não foi possível concluir o plano. Volte a tentar.'
            with self.database() as db:
                db.execute("UPDATE plan_runs SET status='error',phase='error',error=?,updated=? WHERE id=?",(message[:200],time.time(),identifier))
        finally:self.slots.release()

    def calculate(self,uid,month,params,report=lambda phase:None):
        report('products');p=self.profile(uid);day=params['day']
        p['max_stops']=params.get('max_stops',p['max_stops'])
        items=[i for i in self.items(uid,month) if not i['needed_on'] or i['needed_on']<=day]
        offers=self.offers(uid);matches=matching(items,offers)
        report('fuel');p['mobility']=resolve(p,self.folder)
        when=departure(day,params.get('departure_time',''),p.get('countries',['PT'])[0],params.get('timezone'))
        report('locations');road=None;route_error=False
        ids=sorted({o['store'] for found in matches.values() for o in found if eligible(o,p,day)})
        if ids and p.get('home_coords'):
            try:
                from nearby import discover
                try:branches=discover(p)['stores']
                except Exception:branches=[]
                report('roads');road=road_matrix(p,ids,day,params.get('route','auto'),branches=branches)
            except Exception:route_error=True
        report('optimizing');result=make_plan(items,offers,p,day,road=road,matches=matches)
        result.update(route_error=route_error,calculated_at=time.time(),month=month,departure=when.isoformat())
        for option in result['plans']:
            option['distance_reason']=None if option['route'] else 'missing_home' if not p.get('home_coords') else 'missing_work' if params.get('route')=='work' and not p.get('work_coords') else 'service_unavailable' if route_error else 'no_branch'
            if p['mobility']['mode']=='transit' and option['route']:
                option['route'].update(total_km=None,total_minutes=None,base_km=None,km=None,extra_minutes=None,verified=False,provider='unverified')
        summarize(result,p)
        candidates=[]
        for n in range(1,min(4,p['max_stops'])+1):
            candidate=next((o for o in result['plans'] if len(o['stores'])==n and o['route']),None)
            if candidate:candidates.append(candidate)
        if p['mobility']['mode']=='transit' or traffic_key():
            # Refine the shortlisted best road candidate for each stop count,
            # then compare those consistently; never let an unrefined static
            # alternative undercut a candidate priced with actual schedules.
            candidate_ids={o['id'] for o in candidates}
            result['plans']=[o for o in result['plans'] if o['id'] in candidate_ids or not o['route']]
            result['candidate_method']='best_road_candidate_per_stop_count'
        if p['mobility']['mode']=='transit':
            report('transit')
            for option in candidates:
                option['route']=enrich_transit(self.folder,option['route'],when,p['mobility']['stop_minutes'])
        elif traffic_key():
            report('traffic')
            for option in candidates:option['route']=enrich_traffic(option['route'],when)
        summarize(result,p)
        result['unresolved_stores']=[sid for sid in ids if not road or sid not in road['ids']]
        result['saved_stores']=[dict(store=sid,name=s.get('branch_name') or sid,address=s.get('address',''),coords=s.get('coords')) for sid,s in p['stores'].items() if s.get('address') or s.get('coords')]
        result['traffic_configured']=bool(traffic_key())
        return result

    def calculate_windows(self,uid,month,params,report=lambda phase:None):
        """Best day, time and shops over the next days, around the work routine."""
        report('products');p=self.profile(uid);start=params['day'];zone=params.get('timezone') or 'Europe/Lisbon'
        p['max_stops']=params.get('max_stops',p['max_stops'])
        items=[i for i in self.items(uid,month) if not i['checked'] and (not i['needed_on'] or i['needed_on']<=start)]
        base=dict(kind='windows',calculated_at=time.time(),month=month,windows=[],plans={},best=None,day_best=[],pending=len(items))
        if not items:return dict(base,status='empty_list')
        report('fuel');p['mobility']=resolve(p,self.folder)
        if p['mobility']['mode']=='transit':return dict(base,status='car_only')
        if not p.get('home_coords'):return dict(base,status='missing_home')
        offers=self.offers(uid);matches=matching(items,offers)
        ids=sorted({o['store'] for found in matches.values() for o in found if eligible(o,p,start,projection=True)})
        if not ids:return dict(base,status='no_prices')
        report('locations')
        try:
            from nearby import discover
            branches=discover(p)['stores']
        except Exception:branches=[]
        report('roads');matrices={};route_error=False
        for name in ('home','work','morning'):
            if name!='home' and not p.get('work_coords'):continue
            try:matrices[name]=road_matrix(p,ids,start,name,branches=branches)
            except Exception:route_error=True
        if not any(matrices.values()):return dict(base,status='service_unavailable' if route_error else 'no_branch')
        report('optimizing')
        def day_plans(day,name):
            result=make_plan(items,offers,p,day,road=matrices[name],matches=matches,projection=True)
            return summarize(result,p)['plans']
        result=best_windows(day_plans,matrices,p,start,datetime.now(timezone.utc),zone,int(params.get('horizon',7)))
        if traffic_key() and result['windows']:
            report('traffic')
            for w in result['windows'][:3]:
                coords=result['plans'][w['plan_id']]['route'].get('coordinates')
                live=traffic_summary(coords,datetime.fromisoformat(w['departure'])) if coords else None
                if live:w.update(drive_minutes=round(live['seconds']/60),traffic_source='TomTom',traffic_delay_minutes=round(live['delay_seconds']/60))
            result['assumptions']['traffic']='tomtom_top3'
        missing=result['plans'][result['best']['plan_id']]['missing'] if result['best'] else []
        return dict(base,**result,status='ok' if result['windows'] else 'no_window',route_error=route_error,
            missing=missing,work_schedule=bool(p.get('work_start') and p.get('work_end')),mobility=p['mobility'],
            unresolved_stores=[sid for sid in ids if not any(m and sid in m['ids'] for m in matrices.values())])

    def latest(self,uid,month,kind='windows'):
        """Most recent run of a kind, preferring a ready one over one still running."""
        with self.database() as db:
            rows=db.execute("SELECT id,status FROM plan_runs WHERE user_id=? AND month=? AND params LIKE ? AND status IN ('queued','running','ready') ORDER BY created DESC LIMIT 5",
                (uid,month,f'%"kind": "{kind}"%')).fetchall()
        ready=next((r['id'] for r in rows if r['status']=='ready'),None)
        running=next((r['id'] for r in rows if r['status'] in ('queued','running')),None)
        return (self.get(uid,ready) if ready else None),running

    def autopilot(self,uid,month,day,zone='Europe/Lisbon',max_age=6*3600):
        """Keep a fresh best-window recommendation without anyone asking for it."""
        params=dict(kind='windows',day=day,route='auto',departure_time='',max_stops=self.profile(uid)['max_stops'],timezone=zone,horizon=7)
        sig=self.selection_signature(uid,month,params)
        with self.database() as db:
            row=db.execute("SELECT created,selection_signature,status FROM plan_runs WHERE user_id=? AND month=? AND params LIKE '%\"kind\": \"windows\"%' ORDER BY created DESC LIMIT 1",(uid,month)).fetchone()
        if row and row['status'] in ('queued','running'):return None
        if row and row['selection_signature']==sig and time.time()-row['created']<max_age and row['status']=='ready':return None
        if row and row['status']=='error' and time.time()-row['created']<1800:return None
        return self.start(uid,month,params)

    def get(self,uid,identifier):
        with self.database() as db:row=db.execute('SELECT * FROM plan_runs WHERE id=? AND user_id=?',(identifier,uid)).fetchone()
        if not row:return None
        value=dict(id=row['id'],status=row['status'],phase=row['phase'],created=row['created'],updated=row['updated'],error=row['error'])
        if row['status']=='ready':value['result']=json.loads(row['result'])
        return value

    def select(self,uid,identifier,plan_id):
        with self.database() as db:row=db.execute("SELECT * FROM plan_runs WHERE id=? AND user_id=? AND status='ready'",(identifier,uid)).fetchone()
        if not row:raise ValueError('Calcule um plano antes de o guardar')
        params=json.loads(row['params']);current=self.selection_signature(uid,row['month'],params)
        if current!=row['selection_signature']:raise ValueError('A lista ou as preferências mudaram. Volte a calcular.')
        windows=params.get('kind')=='windows'
        if time.time()-row['created']>(6*3600 if windows else 1800):raise ValueError('O plano está desatualizado. Atualize os preços e percursos.')
        result=json.loads(row['result'])
        if windows:
            # plan_id is the window's position: the same shops can win at several moments.
            try:window=result['windows'][int(plan_id)]
            except (ValueError,IndexError):raise ValueError('Alternativa não encontrada') from None
            plan=dict(result['plans'][window['plan_id']],window=window,transport_mode='car')
            plan['route']=dict(plan['route'],stops=window['stops'],total_minutes=window['drive_minutes'])
            departure=window['departure'];params=dict(params,day=window['day'])
        else:
            plan=next((p for p in result['plans'] if p['id']==plan_id),None);departure=result['departure']
        if not plan:raise ValueError('Alternativa não encontrada')
        saved=dict(plan=plan,selected_at=time.time(),calculated_at=result['calculated_at'],departure=departure,params=params,month=row['month'])
        with self.database() as db:
            db.execute('INSERT OR REPLACE INTO selected_plans VALUES(?,?,?,?,?,?)',(uid,row['month'],identifier,plan_id,current,json.dumps(saved)))
        return saved

    def selected(self,uid,month):
        with self.database() as db:row=db.execute('SELECT * FROM selected_plans WHERE user_id=? AND month=?',(uid,month)).fetchone()
        if not row:return None
        data=json.loads(row['data']);data['stale']=row['signature']!=self.selection_signature(uid,month,data['params'])
        window=data['plan'].get('window')
        data['expired']=(datetime.now(timezone.utc)>datetime.fromisoformat(window['arrival'])+timedelta(hours=6)) if window else time.time()-data['selected_at']>86400
        return data
