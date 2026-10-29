/* Car profiles, explicit shopping trips, progress and saved branch selection. */
const mobilityCopy = {
  'pt-PT': {
    savingSettings:'A guardar definições…',shop:'loja',connectionTimes:'Ligações e horários',manualConsumption:'Consumo indicado por si',travelTotal:'Deslocação estimada',otherPlans:'Ver outras alternativas',fewerPlans:'Mostrar só a melhor por número de lojas',advancedTrip:'Custos e tempo nas lojas',bestWithTime:'Melhor equilíbrio entre custo e tempo',journeyTitle:'Onde compensa comprar?',journeySubtitle:'Compare as compras com o custo da viagem e o tempo em cada loja.',
    vehicleSettings:'Como se desloca',car:'Carro',transit:'Transportes públicos',mode:'Meio de transporte',
    vehicleQuery:'Pesquisar marca, modelo e motorização',vehicleYear:'Ano exato (opcional)',vehicleYearHint:'Com ano, a pesquisa alternativa usa o catálogo EPA dos EUA. Sem ano, usa o catálogo europeu ADEME; confirme a geração.',
    vehicleSearch:'Procurar carro',vehicleLabel:'O meu carro',consumption:'Consumo médio por 100 km',consumptionHint:'Pode substituir o valor de homologação pelo consumo real do seu carro.',
    vehicleEmpty:'Sem uma motorização verificada para esta pesquisa. Pode indicar o carro e o consumo real manualmente.',
    vehicleSourceHint:'Escolha a motorização correta. A ADEME publica um intervalo: usamos o limite superior do consumo misto. O ano não é indicado nessa fonte.',
    fuel:'Combustível / energia',petrol95:'Gasolina 95',petrol98:'Gasolina 98',diesel:'Gasóleo',lpg:'GPL',electric:'Eletricidade',
    priceMode:'Preço da energia',automaticPrice:'Média pública atualizada',manualPrice:'Preço que pago',unitPrice:'Preço por litro / kWh (€)',fuelCountry:'País do abastecimento',
    fuelCurrent:'Consultar preços atuais',electricPriceHint:'Na eletricidade, indique a sua tarifa por kWh.',fuelUnavailable:'A fonte de combustível não respondeu. A estimativa por km ficará identificada.',
    parking:'Estacionamento por loja (€)',tolls:'Portagens previstas nesta ida (€)',stopMinutes:'Minutos em cada loja',timeValue:'Valor do meu tempo (€/hora, opcional)',
    timeValueHint:'Serve apenas para ordenar as opções. Não é dinheiro gasto nem poupança registada.',
    transitPass:'Tenho passe que cobre estes percursos',transitTicket:'Preço por embarque (€)',transitHint:'Os horários são consultados quando calcula o plano. Os bilhetes são estimados com o preço que indicar; confirme a cobertura do passe e das ligações.',
    savedBranches:'As minhas lojas guardadas',savedBranch:'Loja guardada',branchPending:'Morada guardada; falta confirmar o ponto no mapa.',saveBranch:'Guardar esta loja',savingBranch:'A guardar loja…',
    noSavedBranches:'Escolha uma filial nas lojas próximas ou localize a morada da sua loja habitual.',openSettings:'Configurar deslocação',
    departureTime:'Hora de saída (vazio = agora)',maximumStops:'Comparar até',shops:'lojas',calculateTrip:'Comparar custos',calculatingTrip:'A comparar…',
    phase_queued:'O seu cálculo está na fila',phase_products:'A preparar os produtos da lista',phase_fuel:'A atualizar o preço do combustível',phase_locations:'A localizar as lojas',phase_roads:'A calcular os percursos',phase_optimizing:'A comparar compras e viagem',phase_traffic:'A verificar o trânsito',phase_transit:'A consultar horários de transportes',phase_ready:'Comparação concluída',
    useThisPlan:'Usar este plano',usingThisPlan:'A guardar plano…',chosenPlan:'Plano escolhido',planSaved:'Plano guardado. As compras estão organizadas por loja.',planStale:'A lista ou as preferências mudaram. Recalcule antes de usar este plano.',
    tripTotal:'Compras + viagem',fuelCost:'Combustível estimado',energyCost:'Energia estimada',manualTrip:'Deslocação estimada por km',ticketCost:'Bilhetes estimados',passCost:'Passe indicado: sem custo adicional',
    drive:'a conduzir',inShops:'nas lojas',allTime:'tempo total',distance:'de percurso',extraDetail:'Como foi calculada a deslocação',
    routeFromHome:'Casa → lojas → casa',routeFromWork:'Trabalho → lojas → casa',trafficUnknown:'Sem trânsito ao vivo; tempo estimado',trafficLive:'Com trânsito atual',trafficHistoric:'Com previsão de trânsito',trafficDelay:'de atraso de trânsito',
    savingsAfterTrip:'Poupança estimada depois da viagem',comparedStops:'face à alternativa de',extraCosts:'Estacionamento e portagens',timeCost:'Valor atribuído ao tempo',
    noComparable:'Ainda não existe uma alternativa completa com viagem calculada para comparar a poupança.',fuelSetup:'Sem consumo e preço utilizáveis, aplica-se o custo por km definido no perfil.',
    journeyUnavailable:'Percurso por confirmar',transitUnavailable:'Não foi possível confirmar uma ligação neste horário.',transitVerified:'Horários consultados',transitSource:'Dados de transportes',
    storesWithoutLocation:'Falta localizar estas cadeias',selectBranch:'Escolher filial',navigate:'Navegar até aqui',beginTrip:'Começar pela primeira loja',returnHome:'Regressar a casa',mapPoint:'Ver no mapa',
    cheaperTrip:'Melhor total estimado',incompleteTrip:'Faltam produtos',onlyProducts:'Só produtos; viagem por confirmar',noOption:'Sem opção encontrada',
    sourceDate:'Preço de',estimatedOnly:'Estimativa desta ida. A poupança mensal só conta depois de registar o valor pago.',
    fuelDisclaimer:'Consumo médio × distância. O consumo real pode variar com trânsito, carga e condução. Estacionamento e portagens usam os valores que indicou.',
    showSelected:'Ver plano escolhido',clearPlan:'Deixar de usar este plano',recalculate:'Recalcular',lookupBusy:'A consultar catálogo…',lookupError:'Não foi possível consultar o catálogo agora.',
    perBoarding:'por embarque',boardings:'embarques',walking:'A pé',min:'min',selectedAt:'Escolhido às',checking:'A confirmar…'
  },
  'es-ES': {
    savingSettings:'Guardando preferencias…',shop:'tienda',connectionTimes:'Conexiones y horarios',manualConsumption:'Consumo indicado por ti',travelTotal:'Desplazamiento estimado',otherPlans:'Ver otras alternativas',fewerPlans:'Mostrar solo la mejor por número de tiendas',advancedTrip:'Costes y tiempo en las tiendas',bestWithTime:'Mejor equilibrio entre coste y tiempo',journeyTitle:'¿Dónde compensa comprar?',journeySubtitle:'Compara la compra con el coste del viaje y el tiempo en cada tienda.',
    vehicleSettings:'Cómo te desplazas',car:'Coche',transit:'Transporte público',mode:'Medio de transporte',
    vehicleQuery:'Buscar marca, modelo y motorización',vehicleYear:'Año exacto (opcional)',vehicleYearHint:'Con año, la alternativa usa el catálogo EPA de EE. UU. Sin año, usa ADEME; confirma la generación.',
    vehicleSearch:'Buscar coche',vehicleLabel:'Mi coche',consumption:'Consumo medio por 100 km',consumptionHint:'Puedes sustituir la homologación por el consumo real de tu coche.',
    vehicleEmpty:'Sin motorización verificada para esta búsqueda. Puedes indicar el coche y su consumo real manualmente.',vehicleSourceHint:'Elige la motorización correcta. ADEME publica un intervalo: usamos el límite superior del consumo mixto. Esa fuente no indica el año.',
    fuel:'Combustible / energía',petrol95:'Gasolina 95',petrol98:'Gasolina 98',diesel:'Gasóleo',lpg:'GLP',electric:'Electricidad',priceMode:'Precio de la energía',automaticPrice:'Media pública actualizada',manualPrice:'Precio que pago',unitPrice:'Precio por litro / kWh (€)',fuelCountry:'País del repostaje',
    fuelCurrent:'Consultar precios actuales',electricPriceHint:'Para electricidad, indica tu tarifa por kWh.',fuelUnavailable:'La fuente no respondió. La estimación por km quedará identificada.',
    parking:'Aparcamiento por tienda (€)',tolls:'Peajes previstos para este viaje (€)',stopMinutes:'Minutos en cada tienda',timeValue:'Valor de mi tiempo (€/hora, opcional)',timeValueHint:'Solo ordena las opciones. No representa dinero gastado ni ahorro registrado.',
    transitPass:'Tengo abono que cubre estos trayectos',transitTicket:'Precio por embarque (€)',transitHint:'Los horarios se consultan al calcular. Los billetes usan el precio que indiques; confirma el abono y las conexiones.',
    savedBranches:'Mis tiendas guardadas',savedBranch:'Tienda guardada',branchPending:'Dirección guardada; falta confirmar el punto en el mapa.',saveBranch:'Guardar esta tienda',savingBranch:'Guardando tienda…',noSavedBranches:'Elige una sucursal cercana o localiza la dirección de tu tienda habitual.',openSettings:'Configurar desplazamiento',
    departureTime:'Hora de salida (vacío = ahora)',maximumStops:'Comparar hasta',shops:'tiendas',calculateTrip:'Comparar costes',calculatingTrip:'Comparando…',
    phase_queued:'El cálculo está en la cola',phase_products:'Preparando los productos',phase_fuel:'Actualizando el precio del combustible',phase_locations:'Localizando tiendas',phase_roads:'Calculando recorridos',phase_optimizing:'Comparando compra y viaje',phase_traffic:'Comprobando el tráfico',phase_transit:'Consultando horarios de transporte',phase_ready:'Comparación terminada',
    useThisPlan:'Usar este plan',usingThisPlan:'Guardando plan…',chosenPlan:'Plan elegido',planSaved:'Plan guardado. Las compras están organizadas por tienda.',planStale:'La lista o las preferencias cambiaron. Recalcula antes de usarlo.',
    tripTotal:'Compra + viaje',fuelCost:'Combustible estimado',energyCost:'Energía estimada',manualTrip:'Desplazamiento estimado por km',ticketCost:'Billetes estimados',passCost:'Abono indicado: sin coste adicional',
    drive:'conduciendo',inShops:'en tiendas',allTime:'tiempo total',distance:'de recorrido',extraDetail:'Cómo se calculó el desplazamiento',routeFromHome:'Casa → tiendas → casa',routeFromWork:'Trabajo → tiendas → casa',trafficUnknown:'Sin tráfico en directo; tiempo estimado',trafficLive:'Con tráfico actual',trafficHistoric:'Con previsión de tráfico',trafficDelay:'de retraso por tráfico',
    savingsAfterTrip:'Ahorro estimado después del viaje',comparedStops:'frente a la alternativa de',extraCosts:'Aparcamiento y peajes',timeCost:'Valor asignado al tiempo',noComparable:'Todavía no hay una alternativa completa con viaje calculado para comparar el ahorro.',fuelSetup:'Sin consumo y precio utilizables, se aplica el coste por km indicado en el perfil.',
    journeyUnavailable:'Recorrido por confirmar',transitUnavailable:'No se pudo confirmar una conexión a esta hora.',transitVerified:'Horarios consultados',transitSource:'Datos de transporte',storesWithoutLocation:'Falta localizar estas cadenas',selectBranch:'Elegir sucursal',navigate:'Ir hasta aquí',beginTrip:'Empezar por la primera tienda',returnHome:'Volver a casa',mapPoint:'Ver en el mapa',
    cheaperTrip:'Mejor total estimado',incompleteTrip:'Faltan productos',onlyProducts:'Solo productos; viaje por confirmar',noOption:'Sin opción encontrada',sourceDate:'Precio del',estimatedOnly:'Estimación para este viaje. El ahorro mensual cuenta al registrar lo pagado.',fuelDisclaimer:'Consumo medio × distancia. El consumo real varía con tráfico, carga y conducción. Aparcamiento y peajes usan tus valores.',
    showSelected:'Ver plan elegido',clearPlan:'Dejar de usar este plan',recalculate:'Recalcular',lookupBusy:'Consultando catálogo…',lookupError:'No se pudo consultar el catálogo ahora.',perBoarding:'por embarque',boardings:'embarques',walking:'A pie',min:'min',selectedAt:'Elegido a las',checking:'Confirmando…'
  }
};
const mt=key=>mobilityCopy[locale]?.[key]||mobilityCopy['pt-PT'][key]||autoCopy[locale]?.[key]||autoCopy['pt-PT'][key]||ft(key);
function mobilitySettings() {
  const m=state.profile.mobility||{},choices=(name,values,value)=>`<div class="field" ${name!=="m-mode"?"data-car-field":""}><label for="${name}">${mt(name.replace('m-',''))}</label><select id="${name}" name="${name}">${values.map(([key,label])=>`<option value="${key}" ${value===key?'selected':''}>${esc(label)}</option>`).join('')}</select></div>`;
  return `<section class="panel wide mobility-settings"><div class="panel-body"><h2>${mt('vehicleSettings')}</h2><div class="form-grid">${choices('m-mode',[['car',mt('car')],['transit',mt('transit')]],m.mode||'car')}
  <div class="field" data-car-field><label for="vehicle-query">${mt('vehicleQuery')}</label><div class="toolbar"><input id="vehicle-query" autocomplete="off" placeholder="Renault Clio"><button type="button" id="vehicle-search">${mt('vehicleSearch')}</button></div></div>
  <div class="field" data-car-field><label for="vehicle-year">${mt('vehicleYear')}</label><input id="vehicle-year" type="number" min="1984" max="${new Date().getFullYear()+1}"><small>${mt('vehicleYearHint')}</small></div>${plateField()}
  <div class="field full" data-car-field id="vehicle-results" aria-live="polite"></div>
  <input type="hidden" id="m-vehicle_id" value="${esc(m.vehicle_id||'')}"><input type="hidden" id="m-consumption_source" value="${esc(m.consumption_source||'manual')}">
  <div class="field" data-car-field><label for="m-vehicle_label">${mt('vehicleLabel')}</label><input id="m-vehicle_label" value="${esc(m.vehicle_label||'')}"></div>
  <div class="field" data-car-field><label for="m-consumption">${mt('consumption')}</label><input id="m-consumption" type="number" min="0.1" max="100" step="0.001" value="${m.consumption??''}"><small>${mt('consumptionHint')}</small><small id="vehicle-source">${esc(m.consumption_source==='catalogue'?m.vehicle?.source||'':m.consumption!=null?mt('manualConsumption'):'')}</small></div>
  ${choices('m-fuel',['petrol95','petrol98','diesel','lpg','electric'].map(k=>[k,mt(k)]),m.fuel||'petrol95')}
  ${choices('m-priceMode',[['auto',mt('automaticPrice')],['manual',mt('manualPrice')]],m.price_mode||'auto')}
  ${choices('m-fuelCountry',[['PT','Portugal'],['ES','España']],m.fuel_country||'PT')}
  <div class="field" data-car-field><label for="m-unit_price">${mt('unitPrice')}</label><input id="m-unit_price" type="number" min="0.01" max="10" step="0.001" value="${m.unit_price??''}"><button type="button" class="quiet small" id="fuel-current">${mt('fuelCurrent')}</button><small id="fuel-preview" aria-live="polite"></small></div>
  <details class="field full"><summary>${mt('advancedTrip')}</summary><div class="form-grid">${[['parking_per_stop','parking',0,100],['tolls','tolls',0,500],['stop_minutes','stopMinutes',15,180],['time_value','timeValue',0,200],['traffic_scale','trafficScale',1,2]].map(([key,label,fallback,max])=>`<div class="field" ${['parking_per_stop','tolls'].includes(key)?'data-car-field':''}><label for="m-${key}">${mt(label)}</label><input id="m-${key}" type="number" min="0" max="${max}" step="${key==='stop_minutes'?'1':'.01'}" value="${m[key]??fallback}"></div>`).join('')}
  <div class="field full"><small>${mt('timeValueHint')}</small></div></div></details>
  <div class="field" data-transit-field><label for="m-transit_ticket">${mt('transitTicket')}</label><input id="m-transit_ticket" type="number" min="0" max="100" step="0.01" value="${m.transit_ticket??''}"></div>
  <label class="checkbox-field" data-transit-field><input id="m-transit_pass" type="checkbox" ${m.transit_pass?'checked':''}>${mt('transitPass')}</label><p class="field full muted" data-transit-field>${mt('transitHint')}</p>
  </div></div></section>`;
}
function mobilityFormData() {
  const m={...(state.profile.mobility||{})};
  for(const key of ['mode','fuel','vehicle_id','vehicle_label','consumption_source','consumption','unit_price','parking_per_stop','tolls','stop_minutes','time_value','transit_ticket']) {
    const field=$('#m-'+key);if(field)m[key]=field.value;
  }
  m.traffic_scale=$('#m-traffic_scale')?.value??m.traffic_scale;m.price_mode=$('#m-priceMode').value;m.fuel_country=$('#m-fuelCountry').value;m.transit_pass=$('#m-transit_pass').checked;
  return m;
}
function bindMobilitySettings() {
  if(!$('#m-mode'))return;
  const price=()=>{$('#m-unit_price').disabled=$('#m-priceMode').value==='auto';};
  $('#m-priceMode').onchange=price;price();
  const unit=()=>{$('label[for="m-consumption"]').textContent=mt('consumption')+($('#m-fuel').value==='electric'?' (kWh)':' (L)');};unit();
  const mode=()=>{
    const car=$('#m-mode').value==='car';
    document.querySelectorAll('[data-car-field]').forEach(el=>el.hidden=!car);
    document.querySelectorAll('[data-transit-field]').forEach(el=>el.hidden=car);
  };mode();$('#m-mode').onchange=mode;
  $('#m-vehicle_label').oninput=()=>{$('#m-vehicle_id').value='';$('#m-consumption_source').value='manual';$('#vehicle-source').textContent='';};
  const manual=()=>{$('#m-consumption_source').value='manual';$('#vehicle-source').textContent=mt('manualConsumption');};
  $('#m-consumption').oninput=manual;
  let previousFuel=$('#m-fuel').value;
  $('#m-fuel').onchange=()=>{if(($('#m-fuel').value==='electric')!==(previousFuel==='electric')){$('#m-consumption').value='';$('#m-unit_price').value='';}previousFuel=$('#m-fuel').value;manual();if($('#m-fuel').value==='electric'){$('#m-priceMode').value='manual';$('#fuel-preview').textContent=mt('electricPriceHint');}price();unit();};
  $('#vehicle-search').onclick=async()=>{
    const button=$('#vehicle-search'),target=$('#vehicle-results'),form=$('#profile-form');button.disabled=true;target.textContent=mt('lookupBusy');
    try {
      const result=await api('/vehicles?q='+encodeURIComponent($('#vehicle-query').value)+'&year='+encodeURIComponent($('#vehicle-year').value));
      if($('#profile-form')!==form)return;
      const rows=result.vehicles||[];
      target.innerHTML=`<p class="muted">${mt(rows.length?'vehicleSourceHint':'vehicleEmpty')}</p><div class="vehicle-options">${rows.map((v,i)=>`<button type="button" class="suggestion" data-vehicle="${i}"><strong>${esc(v.label)}</strong><small>${esc(v.source)}${v.consumption?` · ${distanceNumber(v.consumption)} ${esc(v.unit)}`:''}${v.engine_cc?` · ${v.engine_cc} cm³`:''}${v.transmission?` · ${esc(v.transmission)}`:''}${v.power_kw?` · ${v.power_kw} kW`:''}${v.fuel?` · ${mt(v.fuel)}`:''}</small></button>`).join('')}</div>`;
      target.querySelectorAll('[data-vehicle]').forEach(b=>b.onclick=async()=>{
        b.disabled=true;
        try {
          const v=(await api('/vehicles/detail?id='+encodeURIComponent(rows[+b.dataset.vehicle].id))).vehicle;
          if($('#profile-form')!==form)return;
          if((v.fuel==='electric')!==(previousFuel==='electric'))$('#m-unit_price').value='';previousFuel=v.fuel;
          $('#m-vehicle_id').value=v.id;$('#m-vehicle_label').value=v.label;$('#m-consumption').value=v.consumption;$('#m-fuel').value=v.fuel;$('#m-consumption_source').value='catalogue';
          if(v.fuel==='electric')$('#m-priceMode').value='manual';price();unit();
          $('#vehicle-source').textContent=`${v.source} · ${v.unit}${v.source_updated_at?' · '+v.source_updated_at.slice(0,10):''}`;
          target.innerHTML=`<p class="notice">${icon('check')}${esc(v.label)} · ${distanceNumber(v.consumption)} ${esc(v.unit)}</p>`;
        } catch(e){toast(e.message);b.disabled=false;}
      });
    }catch(e){if($('#profile-form')===form)target.textContent=e.message||mt('lookupError');}
    finally{if(button.isConnected)button.disabled=false;}
  };
  $('#fuel-current').onclick=async()=>{
    const button=$('#fuel-current'),target=$('#fuel-preview'),country=$('#m-fuelCountry').value,fuel=$('#m-fuel').value;
    if(fuel==='electric'){target.textContent=mt('electricPriceHint');return;}
    button.disabled=true;target.textContent=mt('checking');
    try{const r=await api('/fuel-prices?country='+country),q=r.prices[fuel];if(target.isConnected)target.textContent=q?`${distanceNumber(q.unit_price)} €/L · ${q.observed_on} · ${q.source}`:mt('fuelUnavailable');}
    catch(e){if(target.isConnected)target.textContent=mt('fuelUnavailable');}finally{if(button.isConnected)button.disabled=false;}
  };
}

function savedStoresPanel() {
  const rows=Object.entries(state.profile.stores).filter(([,s])=>s.address||s.coords);
  return `<section class="panel wide"><div class="panel-body"><h2>${mt('savedBranches')}</h2>${rows.length?`<div class="saved-branches">${rows.map(([sid,s])=>`<article><span class="tag">${mt('savedBranch')}</span><h3>${esc(s.branch_name||storeName(sid))}</h3><p>${esc(s.address||storeName(sid))}</p>${s.coords?`<a href="${nearbyMapLink({coords:s.coords})}" target="_blank" rel="noopener">${mt('mapPoint')} ↗</a>`:`<small>${mt('branchPending')}</small>`}</article>`).join('')}</div>`:`<p class="muted">${mt('noSavedBranches')}</p>`}</div></section>`;
}
function planStops(plan) {
  const actual=plan.route?.stops||[];
  return plan.stores.map(sid=>actual.find(s=>s.store===sid)||{store:sid,name:state.profile.stores[sid]?.branch_name||storeName(sid),address:state.profile.stores[sid]?.address||'',coords:state.profile.stores[sid]?.coords});
}
function directionsTo(coords,mode='car',from=null) {
  const params=new URLSearchParams({api:'1',destination:`${coords[1]},${coords[0]}`,travelmode:mode==='transit'?'transit':'driving'});
  if(from)params.set('origin',`${from[1]},${from[0]}`);
  return 'https://www.google.com/maps/dir/?'+params;
}
function tripStops(plan,products=true) {
  const stops=planStops(plan),ordered=[...new Set([...(plan.route?.order||[]).filter(sid=>plan.stores.includes(sid)),...plan.stores])];
  return `<ol class="trip-stops">${ordered.map((sid,i)=>{
    const s=stops.find(v=>v.store===sid),items=plan.selections.filter(v=>v.offer.store===sid);
    return `<li><div class="stop-number">${i+1}</div><div class="stop-body"><h3>${esc(s.name||storeName(sid))}</h3><p>${esc(s.address||(!s.coords?mt('journeyUnavailable'):storeName(sid)))}</p><div class="stop-links">${s.coords?`<a class="tag" href="${directionsTo(s.coords,plan.transport_mode)}" target="_blank" rel="noopener noreferrer">${icon('route')}${mt('navigate')} ↗</a><a href="${nearbyMapLink(s)}" target="_blank" rel="noopener">${mt('mapPoint')} ↗</a>`:`<button type="button" class="quiet small" data-open-store="${esc(sid)}">${mt('selectBranch')}</button>`}</div>${products?`<div class="stop-products">${items.map(item=>`<div><span>${state.items.find(v=>v.id===item.item_id)?.checked?icon('check'):''}${esc(item.item_name)}<small>${esc(item.offer.name)} · ${item.packs} ${item.quantity_basis==='packages'?ft(item.packs===1?'package':'packages')+' ·':'×'} ${esc(item.offer.pack)}</small></span><b>${money(item.cost_cents)}</b></div>`).join('')}</div>`:''}</div></li>`;
  }).join('')}</ol>`;
}
function journeyTime(value) { return new Date(value).toLocaleTimeString(locale,{hour:'2-digit',minute:'2-digit'}); }
function journeyBreakdown(plan) {
  const route=plan.route,m=state.plan?.mobility||state.profile.mobility||{};
  const traffic=route?.traffic==='live'?'trafficLive':route?.traffic==='historic'?'trafficHistoric':'trafficUnknown';
  const costLabel={fuel:'fuelCost',electric:'energyCost',manual_km:'manualTrip',ticket_estimate:'ticketCost',pass:'passCost'}[plan.travel_method]||'journeyUnavailable';
  return `<div class="journey-facts"><div>${icon('route')}<strong>${route?.total_km!=null?`${distanceNumber(route.total_km)} km`:route?.verified?mt('transitVerified'):mt('journeyUnavailable')}</strong><span>${mt(plan.transport_mode==='transit'&&route?.verified?'transit':'distance')}</span></div><div>${icon('clock')}<strong>${plan.total_minutes!=null?`${plan.total_minutes} ${mt('min')}`:'—'}</strong><span>${mt('allTime')}</span></div><div><strong>${plan.travel_cents!=null?money(plan.travel_cents):'—'}</strong><span>${mt('travelTotal')}</span></div></div>
  <div class="cost-breakdown"><span>${t('basket')}<b>${money(plan.basket_cents)}</b></span><span>${mt(costLabel)}<b>${plan.fuel_cents!=null?money(plan.fuel_cents):plan.travel_cents!=null?money(plan.travel_cents):'—'}</b></span>${(plan.parking_cents||plan.tolls_cents)?`<span>${mt('extraCosts')}<b>${money((plan.parking_cents||0)+(plan.tolls_cents||0))}</b></span>`:''}</div>
  ${plan.balance_cents?`<p class="muted">${t('futureBalance')}: ${money(plan.balance_cents)}</p>`:''}
  ${plan.saving_cents>0?`<div class="trip-saving"><strong>${mt('savingsAfterTrip')}: ${money(plan.saving_cents)}</strong><small>${mt('comparedStops')} ${plan.baseline_stops} ${mt(plan.baseline_stops===1?'shop':'shops')}</small></div>`:''}
  ${plan.transport_mode==='transit'?`<p class="muted">${route?.verified?`${mt('transitVerified')} · ${route.boardings} ${mt('boardings')}`:mt('transitUnavailable')} · <a href="https://transitous.org/sources/" target="_blank" rel="noopener">${mt('transitSource')}</a></p>`:`<p class="muted">${mt(traffic)}${route?.traffic_delay_minutes?` · +${route.traffic_delay_minutes} ${mt('min')} ${mt('trafficDelay')}`:''}</p>`}
  <details class="trip-assumptions"><summary>${mt('extraDetail')}</summary>${plan.transport_mode!=='transit'&&route?.total_minutes!=null?`<p>${route.total_minutes} ${mt('min')} ${mt('drive')} · ${plan.shopping_minutes} ${mt('min')} ${mt('inShops')}</p>`:''}${plan.vehicle_label?`<p>${esc(plan.vehicle_label)} · ${distanceNumber(plan.consumption)} ${plan.energy_unit}/100 km</p>`:''}${plan.fuel_quote?`<p>${distanceNumber(plan.fuel_quote.unit_price)} €/${esc(plan.energy_unit)} · ${mt('sourceDate')} ${esc(plan.fuel_quote.observed_on)} · ${esc(plan.fuel_quote.source)}</p>`:''}${plan.travel_method==='manual_km'?`<p>${mt('fuelSetup')}</p>`:''}${route?.base_km!=null?`<p>${ft('baseline')}: ${distanceNumber(route.base_km)} km · ${ft('additionalKm')}: ${distanceNumber(plan.extra_km)} · ${ft('additionalCost')}: ${plan.extra_travel_cents!=null?money(plan.extra_travel_cents):'—'}</p>`:''}${plan.transport_mode!=='transit'?`<p>${mt('fuelDisclaimer')}</p>`:''}${route?.transit_legs?`<div class="transit-connections"><strong>${mt('connectionTimes')}</strong>${route.transit_legs.map((leg,i)=>`<section><b>${i<plan.stores.length?esc(storeName((route.order||plan.stores)[i])):t('home')}</b>${leg.legs.map(s=>`<p>${esc(journeyTime(s.start))}–${esc(journeyTime(s.end))} · ${s.mode==='WALK'||s.mode==='FOOTPATH'?mt('walking'):esc(s.mode+' '+s.line)}</p>`).join('')}</section>`).join('')}</div>`:''}${plan.time_cost_cents?`<p>${mt('timeCost')}: ${money(plan.time_cost_cents)} · ${mt('timeValueHint')}</p>`:''}</details>`;
}
function renderJourneyPlan() {
  const loading=!!state.planLoading,result=loading?null:state.plan,run=state.planRun;
  const shortlist=new Set((result?.frontier||[]).map(f=>f.plan_id).filter(Boolean));
  const shown=state.showAllPlans?result?.plans:result?.plans?.filter(p=>shortlist.has(p.id));
  const phases=['queued','products','fuel','locations','roads','optimizing','traffic','transit','ready'];
  const progress=Math.min(95,10+Math.max(0,phases.indexOf(run?.phase||'queued'))*12);
  return `${title('planTitle','planSubtitle')}${renderWindows()}<section class="journey-heading"><h2>${mt('journeyTitle')}</h2><p>${mt('journeySubtitle')}</p><div class="toolbar">
    <label>${t('date')}<input type="date" id="plan-day" value="${state.day}"></label><label>${t('routeMode')}<select id="route-mode"><option value="auto" ${state.route==='auto'?'selected':''}>${t('routeMode')}</option><option value="home" ${state.route==='home'?'selected':''}>${t('homeRoute')}</option><option value="work" ${state.route==='work'?'selected':''}>${t('workRoute')}</option></select></label>
    <label>${mt('departureTime')}<input type="time" id="plan-departure" value="${esc(state.departureTime||'')}"></label>
    <label>${mt('maximumStops')}<select id="plan-max-stops">${[1,2,3,4].map(n=>`<option value="${n}" ${n===(state.planMaxStops||4)?'selected':''}>${n} ${mt(n===1?'shop':'shops')}</option>`).join('')}</select></label>
    <label>${mt('mode')}<select id="plan-transport"><option value="car" ${state.profile.mobility?.mode!=='transit'?'selected':''}>${mt('car')}</option><option value="transit" ${state.profile.mobility?.mode==='transit'?'selected':''}>${mt('transit')}</option></select></label>
    <button type="button" class="primary" data-action="plan" ${loading?'disabled':''}>${icon('route',loading?'spinner':'')}${mt(loading?'calculatingTrip':'calculateTrip')}</button><button type="button" class="quiet" data-view="profile">${mt('openSettings')}</button></div></section>
    <section id="plan-loading" class="plan-progress" role="status" ${loading?'':'hidden'}><div>${icon('refresh','spinner')}<strong>${mt('phase_'+(run?.phase||'queued'))}</strong></div><progress max="100" value="${progress}" aria-label="${mt('calculatingTrip')}"></progress></section>
    ${state.planError?`<div class="notice amber" role="alert">${esc(state.planError)}</div>`:''}
    ${result?.frontier?.length?`<div class="stop-comparison">${result.frontier.map(f=>`<button type="button" class="stop-option" ${f.plan_id?`data-focus-plan="${f.plan_id}"`:'disabled'}><strong>${f.stops} ${mt(f.stops===1?'shop':'shops')}</strong><b>${f.total_cents!=null?money(f.total_cents):f.basket_cents!=null?money(f.basket_cents):'—'}</b><small>${!f.plan_id?mt('noOption'):!f.complete?mt('incompleteTrip'):f.total_cents==null?mt('onlyProducts'):mt('tripTotal')}</small></button>`).join('')}</div>`:''}
    ${result?.plans?.length?(shown?.length?shown:result.plans).slice(0,12).map(p=>`<article class="plan-card journey-card ${p.recommended?'best':''}" id="journey-${p.id}"><header><div>${p.recommended?`<span class="tag">${mt(result.mobility?.time_value?'bestWithTime':'cheaperTrip')}</span>`:''}${!p.complete?`<span class="tag amber">${mt('incompleteTrip')}</span>`:''}<h3>${p.stores.map(s=>esc(storeName(s))).join(' + ')}</h3><span class="muted">${p.coverage} / ${p.total_items} ${t('coverageLabel')}</span></div><div class="plan-total">${money(p.total_cents)}<small>${mt(p.travel_cents==null?'onlyProducts':'tripTotal')}</small></div></header>
    ${p.missing?.length?`<p class="notice amber missing-products">${ft('missingInPlan')}: ${p.missing.map(esc).join(', ')}</p>`:''}
    <div class="journey-card-body">${journeyBreakdown(p)}<p class="trip-origin">${p.route?mt(p.route.base==='work'?'routeFromWork':'routeFromHome'):mt('journeyUnavailable')}</p>${tripStops(p)}
    <button type="button" class="primary use-plan" data-select-plan="${p.id}" ${loading||!state.planRun?.id||state.selectingPlan?'disabled':''}>${icon('check')}${mt(state.selectingPlan===p.id?'usingThisPlan':'useThisPlan')}</button></div></article>`).join(''):!loading?empty('planEmpty','planEmptyText',`<button type="button" data-view="profile">${mt('openSettings')}</button>`):''}
    ${result?.plans?.length>shortlist.size?`<button type="button" class="quiet" data-toggle-plans>${mt(state.showAllPlans?'fewerPlans':'otherPlans')}</button>`:''}
    ${result?.unresolved_stores?.length?`<p class="privacy-note">${mt('storesWithoutLocation')}: ${result.unresolved_stores.map(s=>esc(storeName(s))).join(', ')}</p>`:''}<p class="privacy-note">${mt('estimatedOnly')}</p><p class="privacy-note"><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors</a> · OSRM${state.profile.mobility?.mode==='transit'?' · <a href="https://transitous.org/sources/" target="_blank" rel="noopener">Transitous</a>':''}</p>`;
}
function renderSelectedJourney() {
  const selected=state.selectedPlan;if(!selected)return '';
  const p=selected.plan,stops=planStops(p),first=stops.find(s=>s.store===(p.route?.order||p.stores)[0]);
  return `<section class="selected-journey panel"><div class="panel-body"><span class="tag">${mt('chosenPlan')}</span><h2>${p.stores.map(s=>esc(storeName(s))).join(' + ')}</h2><p class="muted">${dateText(selected.params.day)} · ${esc(selected.departure.slice(11,16))} · ${mt(p.transport_mode==='transit'?'transit':'car')}</p><p>${p.coverage}/${p.total_items} ${t('coverageLabel')} · ${money(p.total_cents)} · ${mt('tripTotal')}</p>${selected.stale||selected.expired?`<p class="notice amber">${mt('planStale')}</p><button type="button" class="primary" data-view="plan">${mt('recalculate')}</button>`:first?.coords?`<a class="button-link primary" href="${directionsTo(first.coords,p.transport_mode)}" target="_blank" rel="noopener noreferrer">${icon('route')}${mt('beginTrip')} ↗</a>`:''}<details><summary>${mt('showSelected')}</summary>${tripStops(p)}${state.profile.home_coords?`<a href="${directionsTo(state.profile.home_coords,p.transport_mode)}" target="_blank" rel="noopener">${mt('returnHome')} ↗</a>`:''}</details><button type="button" class="quiet small" data-clear-plan>${mt('clearPlan')}</button></div></section>`;
}
async function loadSelectedJourney() {
  const month=state.month;
  const r=await api('/plans/selected?month='+month);
  if(month===state.month)state.selectedPlan=r.selected;
}
async function selectJourney(button) {
  const id=button.dataset.selectPlan;if(state.selectingPlan||!state.planRun?.id)return;
  state.selectingPlan=id;button.disabled=true;button.innerHTML=icon('refresh','spinner')+mt('usingThisPlan');
  try {
    const r=await api('/plans/select','POST',{run_id:state.planRun.id,plan_id:id});
    state.selectedPlan=r.selected;state.view='list';state.shopping=true;saveSnapshot();render();toast(mt('planSaved'));window.scrollTo({top:0,behavior:'smooth'});
  }catch(e){toast(e.message);if(button.isConnected){button.disabled=false;button.textContent=mt('useThisPlan');}}
  finally{state.selectingPlan=null;}
}
function bindJourneyActions() {
  $('[data-toggle-plans]')?.addEventListener('click',()=>{state.showAllPlans=!state.showAllPlans;render();});
  $('#app').querySelectorAll('[data-select-plan]').forEach(b=>b.onclick=()=>selectJourney(b));
  $('#app').querySelectorAll('[data-focus-plan]').forEach(b=>b.onclick=()=>$('#journey-'+b.dataset.focusPlan)?.scrollIntoView({behavior:'smooth',block:'start'}));
  $('#app').querySelectorAll('[data-open-store]').forEach(b=>b.onclick=()=>{state.view='profile';render();$(`[data-store="${b.dataset.openStore}"]`)?.scrollIntoView({behavior:'smooth'});loadNearby();});
  $('[data-clear-plan]')?.addEventListener('click',async()=>{await api('/plans/selected','DELETE',{month:state.month});state.selectedPlan=null;saveSnapshot();render();});
  $('#plan-departure')?.addEventListener('change',e=>{state.departureTime=e.target.value;loadPlan();});
  $('#plan-max-stops')?.addEventListener('change',e=>{state.planMaxStops=+e.target.value;loadPlan();});
  $('#plan-transport')?.addEventListener('change',async e=>{
    e.target.disabled=true;
    try{const r=await api('/profile','PUT',{mobility:{mode:e.target.value}});state.profile=r.profile;await loadPlan();}
    catch(err){toast(err.message);e.target.disabled=false;}
  });
  $('#app').querySelectorAll('[data-use-branch]').forEach(button=>button.onclick=async()=>{
    const s=state.nearby?.stores?.find(v=>v.id===button.dataset.useBranch);if(!s)return;
    button.disabled=true;button.textContent=mt('savingBranch');
    try {
      const r=await api('/profile','PUT',{stores:{[s.store]:{enabled:true,address:s.address||s.name,coords:s.coords,branch_id:s.id,branch_name:s.name}}});
      state.profile=r.profile;saveSnapshot();
      const address=$(`[name="${s.store}-address"]`),enabled=$(`[name="${s.store}-enabled"]`);
      if(address)address.value=s.address||s.name;if(enabled)enabled.checked=true;
      if($('#coords-'+s.store))$('#coords-'+s.store).textContent=mt('savedBranch')+' · '+s.name;
      if($('#saved-branches-panel'))$('#saved-branches-panel').innerHTML=savedStoresPanel();
      button.textContent=mt('savedBranch');toast(mt('savedBranch'));
    } catch(e){button.disabled=false;button.textContent=mt('saveBranch');toast(e.message);}
  });
  bindMobilitySettings();
}
