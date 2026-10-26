"""Read a narrowly scoped Rumo snapshot for explicitly authorised Despensa accounts."""
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


def monthly_budget(user_id, profile, month):
    path = os.environ.get('DESPENSA_RUMO_SNAPSHOT', '')
    allowed = {x.strip() for x in os.environ.get('DESPENSA_RUMO_USER_IDS', '').split(',') if x.strip()}
    manual = dict(source='manual', status='manual', month=month,
        amount_cents=int(Decimal(str(profile['budget'])) * 100), updated_at=None, lines=[], rumo_available=bool(path and user_id in allowed))
    if not path or user_id not in allowed or profile.get('budget_source') == 'manual':
        return manual
    result = dict(source='rumo', month=month, amount_cents=None, actual_cents=None, updated_at=None, lines=[],
        url=os.environ.get('DESPENSA_RUMO_URL', ''), rumo_available=True)
    try:
        snapshot = Path(path)
        if snapshot.stat().st_size > 2_000_000:
            raise ValueError('Snapshot demasiado grande')
        data = json.loads(snapshot.read_text())
        updated = datetime.fromisoformat(data['updated_at'])
        age = (datetime.now(timezone.utc) - updated).total_seconds()
        result['updated_at'] = data['updated_at']
        if data.get('version') != 1 or not -60 <= age <= 300:
            return dict(result, status='stale')
        record = data['months'].get(month)
        if record is None:
            return dict(result, status='month_missing')
        amount = record['amount_cents']
        if not isinstance(amount, int) or amount < 0:
            raise ValueError('Orçamento inválido')
        return dict(result, status='ok', amount_cents=amount, actual_cents=record.get('actual_cents'), lines=record['lines'])
    except (OSError, ValueError, KeyError, TypeError):
        return dict(result, status='unavailable')
