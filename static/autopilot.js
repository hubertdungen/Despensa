/* Work routine, best shopping windows, automatic recommendation, plates and refuels. */
const autoCopy = {
  'pt-PT': {
    workHours:'Horário de trabalho',workStart:'Entrada',workEnd:'Saída',shopFrom:'Nos dias livres, a partir das',shopUntil:'até às',
    workHoursHint:'Com o horário, a Despensa compara ir antes de entrar, à saída ou mais tarde a partir de casa, com o trânsito típico de cada hora e o horário das lojas.',
    autopilot:'Recomendar automaticamente o melhor dia e hora',
    whenTitle:'Quando compensa ir?',whenSubtitle:'Compara os próximos 7 dias: lojas, hora de saída, trânsito típico e horários de abertura.',
    findWhen:'Encontrar o melhor momento',findingWhen:'A comparar dias e horas…',
    kind_before_work:'Antes de entrar no trabalho',kind_after_work:'À saída do trabalho',kind_evening_home:'Mais tarde, a partir de casa',kind_day_off:'Dia livre, a partir de casa',
    leave:'Saída',arrive:'Chegada',extraKm:'km a mais',extraMin:'min a mais',traffic:'trânsito',trafficLight:'leve',trafficModerate:'moderado',trafficHeavy:'intenso',
    tripExtra:'Viagem a mais',basket:'Compras',decision:'Custo para decidir',versusBest:'mais do que a melhor opção',bestOverall:'Melhor opção',
    perDay:'Melhor por dia',useWindow:'Usar este momento',hoursUnknown:'horário da loja por confirmar',projected:'preços de hoje; podem mudar até lá',
    autoTitle:'Próxima ida recomendada',autoUpdating:'A atualizar a recomendação…',autoNone:'Ainda sem recomendação. Indique casa, trabalho e horário no perfil.',
    autoSeeAll:'Ver alternativas',autoUpdated:'Atualizado',
    status_missing_home:'Indique a morada de casa no perfil para comparar momentos.',status_car_only:'A comparação de horas usa o carro. Nos transportes, use o plano por hora de partida.',
    status_no_prices:'Ainda não há preços para os produtos da lista.',status_empty_list:'A lista não tem produtos por comprar.',status_no_window:'Nenhuma loja aberta nos momentos possíveis. Reveja o horário no perfil.',
    status_service_unavailable:'O serviço de percursos não respondeu. Tente daqui a pouco.',status_no_branch:'Sem lojas localizadas perto de casa ou do trabalho.',
    trafficModel:'Trânsito típico por hora (perfil de Lisboa, TomTom Traffic Index 2025) sobre tempos OSRM. Não é trânsito em direto.',trafficTomTom:'Os 3 melhores momentos foram confirmados com o TomTom.',
    plate:'Matrícula (opcional)',plateHint:'Estima o ano do carro a partir da sequência da matrícula. Não consulta dados do proprietário.',plateButton:'Estimar ano',
    plateRange:'Matrícula de',plateApprox:'aprox.',trafficScale:'Sensibilidade ao trânsito (0–2)',trafficScaleHint:'1 = trânsito típico de Lisboa/Porto. Use 0,5 numa zona calma ou 1,5 se o seu percurso costuma estar pior.',
    refuels:'Abastecimentos e gastos do carro',refuelsHint:'Registe cada abastecimento com a quilometragem. Com dois depósitos cheios, a Despensa calcula o consumo real do seu carro.',
    refuelDay:'Data do abastecimento',litres:'Litros (ou kWh)',paid:'Total pago (€)',odometer:'Quilómetros no conta-quilómetros',fullTank:'Depósito cheio',addRefuel:'Registar abastecimento',
    measuredConsumption:'Consumo real medido',useMeasured:'Usar este consumo nas contas',usingMeasured:'As contas usam o consumo medido',measuredMissing:'Precisa de dois abastecimentos de depósito cheio com quilometragem.',
    fuelThisMonth:'Combustível este mês',shoppingTrips:'Idas às compras registadas',costPerKm:'Custo real por km',refuelSaved:'Abastecimento registado',remove:'Remover',noRefuels:'Sem abastecimentos registados.'
  },
  'es-ES': {
    workHours:'Horario de trabajo',workStart:'Entrada',workEnd:'Salida',shopFrom:'Los días libres, desde las',shopUntil:'hasta las',
    workHoursHint:'Con el horario, Despensa compara ir antes de entrar, a la salida o más tarde desde casa, con el tráfico típico de cada hora y el horario de las tiendas.',
    autopilot:'Recomendar automáticamente el mejor día y hora',
    whenTitle:'¿Cuándo compensa ir?',whenSubtitle:'Compara los próximos 7 días: tiendas, hora de salida, tráfico típico y horarios de apertura.',
    findWhen:'Buscar el mejor momento',findingWhen:'Comparando días y horas…',
    kind_before_work:'Antes de entrar a trabajar',kind_after_work:'A la salida del trabajo',kind_evening_home:'Más tarde, desde casa',kind_day_off:'Día libre, desde casa',
    leave:'Salida',arrive:'Llegada',extraKm:'km de más',extraMin:'min de más',traffic:'tráfico',trafficLight:'ligero',trafficModerate:'moderado',trafficHeavy:'intenso',
    tripExtra:'Viaje adicional',basket:'Compra',decision:'Coste para decidir',versusBest:'más que la mejor opción',bestOverall:'Mejor opción',
    perDay:'Mejor por día',useWindow:'Usar este momento',hoursUnknown:'horario de la tienda por confirmar',projected:'precios de hoy; pueden cambiar',
    autoTitle:'Próxima compra recomendada',autoUpdating:'Actualizando la recomendación…',autoNone:'Aún sin recomendación. Indique casa, trabajo y horario en el perfil.',
    autoSeeAll:'Ver alternativas',autoUpdated:'Actualizado',
    status_missing_home:'Indique la dirección de casa en el perfil para comparar momentos.',status_car_only:'La comparación de horas usa el coche. En transporte público, use el plan por hora de salida.',
    status_no_prices:'Aún no hay precios para los productos de la lista.',status_empty_list:'La lista no tiene productos pendientes.',status_no_window:'Ninguna tienda abierta en los momentos posibles. Revise el horario en el perfil.',
    status_service_unavailable:'El servicio de rutas no respondió. Inténtelo en un rato.',status_no_branch:'Sin tiendas localizadas cerca de casa o del trabajo.',
    trafficModel:'Tráfico típico por hora (perfil de Lisboa, TomTom Traffic Index 2025) sobre tiempos OSRM. No es tráfico en directo.',trafficTomTom:'Los 3 mejores momentos se confirmaron con TomTom.',
    plate:'Matrícula (opcional)',plateHint:'Estima el año del coche a partir de la secuencia de la matrícula. No consulta datos del propietario.',plateButton:'Estimar año',
    plateRange:'Matrícula de',plateApprox:'aprox.',trafficScale:'Sensibilidad al tráfico (0–2)',trafficScaleHint:'1 = tráfico típico de Lisboa/Oporto. Use 0,5 en una zona tranquila o 1,5 si su recorrido suele estar peor.',
    refuels:'Repostajes y gastos del coche',refuelsHint:'Registre cada repostaje con los kilómetros. Con dos depósitos llenos, Despensa calcula el consumo real de su coche.',
    refuelDay:'Fecha del repostaje',litres:'Litros (o kWh)',paid:'Total pagado (€)',odometer:'Kilómetros del cuentakilómetros',fullTank:'Depósito lleno',addRefuel:'Registrar repostaje',
    measuredConsumption:'Consumo real medido',useMeasured:'Usar este consumo en las cuentas',usingMeasured:'Las cuentas usan el consumo medido',measuredMissing:'Necesita dos repostajes de depósito lleno con kilómetros.',
    fuelThisMonth:'Combustible este mes',shoppingTrips:'Compras registradas',costPerKm:'Coste real por km',refuelSaved:'Repostaje registrado',remove:'Quitar',noRefuels:'Sin repostajes registrados.'
  }
};
const at = key => autoCopy[locale]?.[key] || autoCopy['pt-PT'][key] || mt(key);
const clockOf = iso => iso ? iso.slice(11, 16) : '—';
const trafficWord = f => f >= 1.45 ? at('trafficHeavy') : f >= 1.2 ? at('trafficModerate') : at('trafficLight');

/* ---------- profile: routine and car ---------- */
function routineSchedule() {
  const p = state.profile, time = (name, label, value) => `<div class="field"><label for="f-${name}">${at(label)}</label><input id="f-${name}" name="${name}" type="time" value="${esc(value || '')}"></div>`;
  return `<div class="field"><label>${at('workHours')}</label><div class="form-grid">${time('work_start', 'workStart', p.work_start)}${time('work_end', 'workEnd', p.work_end)}${time('shop_from', 'shopFrom', p.shop_from || '09:00')}${time('shop_until', 'shopUntil', p.shop_until || '21:00')}</div><small class="muted">${at('workHoursHint')}</small></div>
  <label class="checkbox-field"><input type="checkbox" name="autopilot" ${p.autopilot !== false ? 'checked' : ''}>${at('autopilot')}</label>`;
}
function scheduleFormData(f) {
  return {work_start: f.elements.work_start.value, work_end: f.elements.work_end.value, shop_from: f.elements.shop_from.value,
    shop_until: f.elements.shop_until.value, autopilot: f.elements.autopilot.checked};
}
function plateField() {
  return `<div class="field" data-car-field><label for="vehicle-plate">${at('plate')}</label><div class="toolbar"><input id="vehicle-plate" autocomplete="off" placeholder="AA-00-AA" maxlength="12"><button type="button" class="small" id="plate-lookup">${at('plateButton')}</button></div><small class="muted" id="plate-result" aria-live="polite">${at('plateHint')}</small></div>`;
}
function bindPlate() {
  $('#plate-lookup')?.addEventListener('click', async () => {
    const out = $('#plate-result');
    try {
      const r = (await api('/plate?q=' + encodeURIComponent($('#vehicle-plate').value))).plate;
      if (r.year && $('#vehicle-year')) $('#vehicle-year').value = r.year;
      out.textContent = r.year ? `${r.country} · ${at('plateApprox')} ${r.estimate}${r.hint ? ' · ' + r.hint : ''}` : `${r.country} · ${at('plateRange')} ${r.year_from}–${r.year_to}${r.hint ? ' · ' + r.hint : ''}`;
    } catch (e) { out.textContent = e.message; }
  });
}

/* ---------- profile: refuel log ---------- */
function refuelPanel() {
  const r = state.refuels, m = r?.measured, mob = state.profile.mobility || {};
  const rows = (r?.refuels || []).slice(0, 12);
  return `<section class="panel wide" id="refuel-panel"><div class="panel-body"><h2>${at('refuels')}</h2><p class="muted">${at('refuelsHint')}</p>
  ${r ? `<div class="savings-summary"><div><span>${at('fuelThisMonth')}</span><strong>${money(r.month.fuel_cents)}</strong></div><div><span>${at('shoppingTrips')}</span><strong>${money(r.month.shopping_trips_cents)}</strong></div><div><span>${at('measuredConsumption')}</span><strong>${m.consumption != null ? distanceNumber(m.consumption) + ' /100 km' : '—'}</strong></div><div><span>${at('costPerKm')}</span><strong>${m.cost_per_km_cents != null ? money(Math.round(m.cost_per_km_cents)) : '—'}</strong></div></div>
  ${m.consumption != null ? (mob.consumption_source === 'refuels' ? `<p class="notice">${icon('check')}${at('usingMeasured')}</p>` : `<button type="button" class="small" id="use-measured">${at('useMeasured')} (${distanceNumber(m.consumption)})</button>`) : `<p class="muted">${at('measuredMissing')}</p>`}` : ''}
  <div class="form-grid refuel-form"><div class="field"><label for="r-day">${at('refuelDay')}</label><input id="r-day" type="date" value="${today()}" max="${today()}"></div>
  <div class="field"><label for="r-litres">${at('litres')}</label><input id="r-litres" type="number" min="0.5" max="300" step="0.01"></div>
  <div class="field"><label for="r-total">${at('paid')}</label><input id="r-total" type="number" min="0" max="2000" step="0.01"></div>
  <div class="field"><label for="r-odometer">${at('odometer')}</label><input id="r-odometer" type="number" min="0" max="2000000" step="1"></div>
  <label class="checkbox-field"><input id="r-full" type="checkbox" checked>${at('fullTank')}</label>
  <button type="button" class="primary small" id="add-refuel">${icon('plus')}${at('addRefuel')}</button><p class="auth-error" id="refuel-error" role="alert"></p></div>
  ${rows.length ? `<div class="plan-products refuel-list">${rows.map(x => `<div><span>${dateText(x.day)} · ${distanceNumber(x.litres)} · ${money(x.total_cents)}${x.odometer != null ? ` · ${x.odometer} km` : ''}${x.full ? ' · ⛽' : ''}</span><button type="button" class="quiet small" data-remove-refuel="${x.id}" aria-label="${at('remove')}">${icon('close')}</button></div>`).join('')}</div>` : `<p class="muted">${at('noRefuels')}</p>`}
  </div></section>`;
}
async function loadRefuels() {
  try { state.refuels = await api('/refuels?month=' + state.month); } catch { state.refuels = null; }
  if ($('#refuel-panel')) { $('#refuel-panel').outerHTML = refuelPanel(); bindRefuels(); }
}
function bindRefuels() {
  $('#add-refuel')?.addEventListener('click', async () => {
    const button = $('#add-refuel'); button.disabled = true;
    try {
      await api('/refuels', 'POST', {id: newId(), day: $('#r-day').value, litres: $('#r-litres').value, total: $('#r-total').value,
        odometer: $('#r-odometer').value, full: $('#r-full').checked});
      toast(at('refuelSaved'));
      state.profile = (await api('/me')).profile;
      await loadRefuels();
    } catch (e) { $('#refuel-error').textContent = e.message; button.disabled = false; }
  });
  $('#app').querySelectorAll('[data-remove-refuel]').forEach(b => b.onclick = async () => {
    await api('/refuels/' + b.dataset.removeRefuel, 'DELETE', {});
    state.profile = (await api('/me')).profile; await loadRefuels();
  });
  $('#use-measured')?.addEventListener('click', async () => {
    try {
      const r = await api('/profile', 'PUT', {mobility: {consumption_source: 'refuels', consumption: state.refuels.measured.consumption}});
      state.profile = r.profile; if ($('#m-consumption')) $('#m-consumption').value = state.refuels.measured.consumption;
      if ($('#m-consumption_source')) $('#m-consumption_source').value = 'refuels';
      await loadRefuels();
    } catch (e) { toast(e.message); }
  });
}

/* ---------- plan view: when is it worth going ---------- */
function windowCard(w, result, best) {
  const plan = result.plans[w.plan_id] || {}, index = result.windows.indexOf(w);
  return `<article class="plan-card journey-card window-card ${best ? 'best' : ''}"><header><div>${best ? `<span class="tag">${at('bestOverall')}</span>` : ''}${!w.complete ? `<span class="tag amber">${mt('incompleteTrip')}</span>` : ''}
  <h3>${dateText(w.day)} · ${at('kind_' + w.kind)}</h3><p class="muted">${w.stores.map(s => esc(storeName(s))).join(' + ')} · ${w.coverage}/${w.total_items}</p></div><strong class="price">${money(w.basket_cents + w.trip_cents)}</strong></header><div class="journey-card-body">
  <div class="journey-facts"><div>${icon('clock')}<strong>${clockOf(w.departure)} → ${clockOf(w.arrival)}</strong><span>${at('leave')} / ${at('arrive')}</span></div>
  <div>${icon('route')}<strong>+${distanceNumber(w.extra_km)} km · +${w.extra_minutes} min</strong><span>${at('traffic')} ${trafficWord(w.traffic_factor)} (×${distanceNumber(w.traffic_factor)})</span></div></div>
  <div class="cost-breakdown"><span>${at('basket')}<b>${money(w.basket_cents)}</b></span><span>${at('tripExtra')}<b>${money(w.trip_cents)}</b></span>${w.time_cost_cents ? `<span>${at('decision')}<b>${money(w.decision_cents)}</b></span>` : ''}</div>
  ${w.versus_best_cents > 0 ? `<p class="muted">+${money(w.versus_best_cents)} ${at('versusBest')}</p>` : ''}
  <ol class="trip-stops">${w.stops.map((s, i) => `<li><div class="stop-number">${i + 1}</div><div class="stop-body"><h3>${esc(s.name || storeName(s.store))}</h3><p>${clockOf(s.arrive)}–${clockOf(s.leave)}${s.address ? ' · ' + esc(s.address) : ''}${s.hours_known ? '' : ` · <span class="amber-text">${at('hoursUnknown')}</span>`}</p>
  <p class="muted">${(plan.selections || []).filter(v => v.offer.store === s.store).map(v => esc(v.item_name)).join(', ')}</p></div></li>`).join('')}</ol>
  ${w.projected ? `<p class="privacy-note">${at('projected')}</p>` : ''}
  <button type="button" class="primary use-plan" data-select-window="${index}">${icon("check")}${at("useWindow")}</button></div></article>`;
}
function renderWindows() {
  const run = state.windowsRun, result = run?.status === 'ready' ? run.result : null, busy = run && ['queued', 'running'].includes(run.status);
  const perDay = result?.day_best?.map(d => result.windows[d.index]).filter(w => w !== result.best) || [];
  return `<section class="journey-heading when-heading"><h2>${at('whenTitle')}</h2><p>${at('whenSubtitle')}</p><div class="toolbar"><button type="button" class="primary" data-action-windows ${busy ? 'disabled' : ''}>${icon(busy ? 'refresh' : 'calendar', busy ? 'spinner' : '')}${at(busy ? 'findingWhen' : 'findWhen')}</button>${!state.profile.work_start ? `<button type="button" class="quiet" data-view="profile">${at('workHours')}</button>` : ''}</div></section>
  ${busy ? `<section class="plan-progress" role="status"><div>${icon('refresh', 'spinner')}<strong>${mt('phase_' + (run.phase || 'queued'))}</strong></div></section>` : ''}
  ${run?.status === 'error' ? `<div class="notice amber" role="alert">${esc(run.error)}</div>` : ''}
  ${result && result.status !== 'ok' ? `<div class="notice amber">${at('status_' + result.status)}</div>` : ''}
  ${result?.best ? `${windowCard(result.best, result, true)}${result.missing?.length ? `<p class="notice amber missing-products">${ft('missingInPlan')}: ${result.missing.map(esc).join(', ')}</p>` : ''}
  ${perDay.length ? `<details class="when-days"><summary>${at('perDay')}</summary>${perDay.map(w => windowCard(w, result, false)).join('')}</details>` : ''}
  <p class="privacy-note">${at('trafficModel')}${result.assumptions?.traffic === 'tomtom_top3' ? ' ' + at('trafficTomTom') : ''}</p>` : ''}`;
}
async function pollWindows(run) {
  const seq = state.windowsSeq = (state.windowsSeq || 0) + 1;
  while (run && ['queued', 'running'].includes(run.status)) {
    state.windowsRun = run; if (state.view === 'plan') render();
    await new Promise(r => setTimeout(r, 900));
    if (seq !== state.windowsSeq) return;
    run = (await api('/plans/' + run.id)).run;
  }
  state.windowsRun = run;
  if (run?.status === 'ready') state.autopilot = run;
  render();
}
async function findWindows() {
  try {
    const r = await api('/plans', 'POST', {kind: 'windows', month: state.month, day: today(), max_stops: state.planMaxStops || state.profile.max_stops || 4,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone});
    await pollWindows(r.run);
  } catch (e) { state.windowsRun = {status: 'error', error: e.message}; render(); }
}
async function selectWindow(button) {
  const run = state.windowsRun?.status === 'ready' ? state.windowsRun : state.autopilot;
  if (!run) return;
  button.disabled = true;
  try {
    const r = await api('/plans/select', 'POST', {run_id: run.id, plan_id: button.dataset.selectWindow});
    state.selectedPlan = r.selected; state.view = 'list'; saveSnapshot(); render(); toast(mt('planSaved')); window.scrollTo({top: 0, behavior: 'smooth'});
  } catch (e) { toast(e.message); button.disabled = false; }
}

/* ---------- list view: automatic recommendation ---------- */
async function loadAutopilot() {
  if (state.offline || state.month !== thisMonth()) return;
  try {
    const r = await api('/autopilot?month=' + state.month);
    state.autopilot = r.run; state.autopilotRunning = !!r.running;
    if (!state.windowsRun || state.windowsRun.status === 'ready') state.windowsRun = r.run;
    // Swap only the card: a full render would close forms the user has open.
    const slot = $('#autopilot-slot');
    if (slot) {
      slot.innerHTML = autopilotCard();
      slot.querySelectorAll('[data-select-window]').forEach(b => b.onclick = () => selectWindow(b));
      slot.querySelectorAll('[data-view]').forEach(b => b.onclick = () => { state.view = b.dataset.view; render(); loadPlan(); window.scrollTo(0, 0); });
    }
    if (r.running) setTimeout(loadAutopilot, 8000);
  } catch { /* the list works without it */ }
}
function renderAutopilot() { return `<div id="autopilot-slot">${autopilotCard()}</div>`; }
function autopilotCard() {
  const chosen = state.selectedPlan && !state.selectedPlan.stale && !state.selectedPlan.expired;
  if (state.shopping || chosen || state.month !== thisMonth() || state.profile?.autopilot === false) return '';
  const result = state.autopilot?.result, w = result?.best;
  if (!w) return state.autopilotRunning ? `<section class="panel autopilot-card"><div class="panel-body"><span class="tag">${at('autoTitle')}</span><p>${icon('refresh', 'spinner')}${at('autoUpdating')}</p></div></section>`
    : result && result.status !== 'ok' ? `<section class="panel autopilot-card"><div class="panel-body"><span class="tag">${at('autoTitle')}</span><p class="muted">${at('status_' + result.status)}</p></div></section>` : '';
  return `<section class="panel autopilot-card"><div class="panel-body"><span class="tag">${icon('spark')}${at('autoTitle')}</span>
  <h2>${dateText(w.day)} · ${clockOf(w.departure)} · ${at('kind_' + w.kind)}</h2>
  <p>${w.stores.map(s => esc(storeName(s))).join(' + ')} · ${w.coverage}/${w.total_items} · <strong>${money(w.basket_cents + w.trip_cents)}</strong> · +${distanceNumber(w.extra_km)} km · +${w.extra_minutes} min · ${at('traffic')} ${trafficWord(w.traffic_factor)}</p>
  ${w.projected ? `<p class="privacy-note">${at('projected')}</p>` : ''}
  <div class="toolbar"><button type="button" class="primary small" data-select-window="${result.windows.indexOf(w)}">${icon('check')}${at('useWindow')}</button><button type="button" class="quiet small" data-view="plan">${at('autoSeeAll')}</button>
  ${state.autopilotRunning ? `<small class="muted">${at('autoUpdating')}</small>` : `<small class="muted">${at('autoUpdated')} ${new Date(state.autopilot.updated * 1000).toLocaleTimeString(locale, {hour: '2-digit', minute: '2-digit'})}</small>`}</div></div></section>`;
}
function bindAutopilot() {
  $('[data-action-windows]')?.addEventListener('click', findWindows);
  $('#app').querySelectorAll('[data-select-window]').forEach(b => b.onclick = () => selectWindow(b));
  bindPlate(); bindRefuels();
}
