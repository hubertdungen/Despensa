"use strict";
const $ = (s) => document.querySelector(s);
const esc = (x) =>
  String(x ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const paths = {
  list: "M8 6h12M8 12h12M8 18h12M3 6h.01M3 12h.01M3 18h.01",
  search: "m21 21-5-5M10.5 18a7.5 7.5 0 1 0 0-15 7.5 7.5 0 0 0 0 15",
  route: "M5 5h11a4 4 0 0 1 0 8H8a4 4 0 0 0 0 8h10M5 2v6M18 18l3 3-3 3",
  settings:
    "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M10 2h4l1 3 3 1 3-1 2 4-2 2v3l2 2-2 4-3-1-3 1-1 3h-4l-1-3-3-1-3 1-2-4 2-2v-3L1 9l2-4 3 1 3-1z",
  plus: "M12 5v14M5 12h14",
  check: "m5 12 4 4L19 6",
  close: "m6 6 12 12M6 18 18 6",
  arrow: "M5 12h14m-5-5 5 5-5 5",
  chevron: "m9 5 7 7-7 7",
  refresh: "M20 7v5h-5M4 17v-5h5M6 6a8 8 0 0 1 13 1M18 18a8 8 0 0 1-13-1",
  bag: "M5 8h14l-1 13H6zM8 8V6a4 4 0 0 1 8 0v2",
  wallet: "M3 6h17v14H3zM3 6V4h14v2M15 11h7v5h-7z",
  leaf: "M20 3C8 2 2 7 5 15s13 7 15-12ZM5 21 15 10",
  shield: "m12 2 8 3v6c0 6-8 11-8 11S4 17 4 11V5zM8 12l3 3 5-6",
  clock: "M12 8v5l3 2M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20",
  more: "M12 5h.01M12 12h.01M12 19h.01",
  trash: "M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7",
  download: "M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5",
  logout: "M9 3H4v18h5M9 12h12m-5-5 5 5-5 5",
  calendar: "M3 5h18v16H3zM7 2v6M17 2v6M3 10h18",
  bottle: "M10 2h4v5l3 4v11H7V11l3-4zM7 14h10",
  grain:
    "M12 22V5M12 16C3 16 3 9 3 9s9 0 9 7ZM12 11c9 0 9-7 9-7s-9 0-9 7ZM12 20c9 0 9-7 9-7s-9 0-9 7Z",
  box: "m3 7 9-5 9 5v12l-9 4-9-4zM3 7l9 5 9-5M12 12v11M7 4l10 6",
  spark: "m12 3 3 6 6 3-6 3-3 6-3-6-6-3 6-3z",
  pin: "M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0ZM12 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6",
};
const icon = (name, extra = "") =>
  `<svg class="icon ${extra}" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.bag}"/></svg>`;
const copy = {
  "pt-PT": {
    tagline: "compras com sentido",
    list: "A minha lista",
    explore: "Explorar preços",
    plan: "Plano de compras",
    profile: "O meu perfil",
    greeting: "Menos contas. Mais poupança.",
    intro: "A sua lista do mês, com os preços e as escolhas no sítio certo.",
    monthList: "A lista deste mês",
    subtitle: "Um mês organizado começa aqui.",
    heroLabel: "COMPRAR BEM, VIVER MELHOR",
    heroTitle: "Tudo o que precisa.\nCom mais sentido.",
    heroText:
      "Planeie as compras, compare os preços e leve só as boas escolhas.",
    items: "Produtos na lista",
    itemsDetail: "para este mês",
    budget: "Orçamento mensal",
    budgetDetail: "definido por si",
    prices: "Preços observados",
    pricesDetail: "cobertura parcial do catálogo",
    yourList: "O que vamos levar?",
    listHint: "A sua próxima ida ao supermercado",
    add: "Adicionar",
    quickAdd: "O que falta na despensa?",
    emptyTitle: "A sua lista começa aqui",
    emptyText:
      "Adicione o primeiro produto ou descubra os preços já recolhidos.",
    browse: "Explorar produtos",
    done: "comprados",
    shopping: "Modo de compras",
    exitShopping: "Sair do modo de compras",
    copyMonth: "Repetir mês anterior",
    smartTitle: "Uma lista. Um plano melhor.",
    smartText:
      "Veja onde comprar os produtos com preço disponível, considerando as suas lojas e deslocações.",
    seePlan: "Encontrar o meu plano",
    sources: "O radar de preços",
    sourceHint: "Fontes, datas e condições à vista",
    sourcePartial: "Catálogo parcial",
    manual: "Introduzido por si",
    privacy:
      "As suas listas são privadas. Sem publicidade e sem vender os seus dados.",
    refresh: "Atualizar preços",
    updating: "A atualizar",
    offline:
      "Está sem rede. A lista continua disponível; as alterações serão sincronizadas.",
    pending: "alterações por sincronizar",
    noPrice: "Sem preço",
    edit: "Editar produto",
    product: "Produto",
    query: "Palavras para comparar",
    queryHint:
      "As alternativas devem corresponder a estas palavras. Confirme tipo, marca e formato.",
    quantity: "Quantidade necessária",
    unit: "Unidade",
    category: "Categoria",
    needed: "Comprar até",
    note: "Notas",
    save: "Guardar",
    cancel: "Cancelar",
    delete: "Eliminar",
    saved: "Guardado",
    added: "Adicionado à lista",
    deleted: "Produto eliminado",
    searchPlaceholder: "Procure arroz, leite, azeite…",
    allStores: "Todas as lojas",
    manualPrice: "Registar preço",
    catalogTitle: "Preços, sem adivinhas.",
    catalogSubtitle:
      "Compare o que foi observado. Confira sempre a loja e as condições.",
    coverage:
      "A recolha automática cobre algumas categorias do Continente e Auchan em Portugal. Espanha e outras lojas aceitam preços manuais. Não é um catálogo completo.",
    noResults: "Ainda não encontrámos esse produto",
    noResultsText:
      "Experimente outras palavras, atualize o catálogo ou registe um preço que viu na loja.",
    observed: "Visto",
    source: "Ver na loja",
    history: "Histórico",
    normal: "Preço público",
    card: "Requer cartão",
    subscription: "Requer subscrição",
    coupon: "Requer cupão",
    professional: "Acesso profissional",
    unknown: "Condições por confirmar",
    packUnknown: "Formato por confirmar",
    useProduct: "Adicionar este produto",
    planTitle: "O melhor caminho para a lista.",
    planSubtitle:
      "Compare cabazes com a mesma cobertura e veja o que entra na conta.",
    planNotice:
      "As alternativas são sugeridas por palavras, não por equivalência certificada. Confirme os produtos. O preço online pode diferir na loja física.",
    date: "Data das compras",
    calculate: "Comparar planos",
    best: "Plano sugerido",
    partial: "Cabaz incompleto",
    coverageLabel: "produtos com preço",
    basket: "Produtos",
    travel: "Deslocação",
    unknownKm: "Distância por definir",
    futureBalance: "Saldo futuro",
    missing: "Sem preço elegível",
    planEmpty: "Ainda não há um plano para comparar",
    planEmptyText:
      "Adicione produtos e escolha as suas lojas no perfil. São necessários preços recentes e formatos compatíveis.",
    futureNotice:
      "Para datas futuras, só usamos preços com uma validade publicada que inclua esse dia.",
    distanceNotice:
      "Sem coordenadas, os quilómetros são estimativas que introduz no perfil. A soma de desvios não representa uma rota otimizada.",
    profileTitle: "À sua medida.",
    profileSubtitle:
      "As suas lojas, os seus cartões e a forma como faz compras.",
    preferences: "Preferências",
    locale: "Idioma",
    countries: "Onde faz compras?",
    budgetField: "Orçamento (€ / mês)",
    interval: "Atualizar a cada (horas)",
    auto: "Atualizar automaticamente no servidor",
    stops: "Máximo de lojas por ida",
    costKm: "Custo da deslocação (€ / km)",
    routine: "A sua rotina",
    home: "Zona de casa",
    work: "Zona de trabalho",
    homeHint: "Morada ou zona, guardada apenas no seu perfil.",
    stores: "Os seus supermercados",
    storesHint: "Ative apenas as lojas onde pode e quer comprar.",
    enabled: "Usar esta loja",
    hasCard: "Tenho cartão",
    hasSubscription: "Tenho subscrição",
    hasAccess: "Tenho acesso profissional",
    extraKm: "Quilómetros adicionais estimados",
    storeAddress: "Loja / localização",
    coupons: "Cupões disponíveis (códigos separados por vírgulas)",
    saveProfile: "Guardar preferências",
    data: "Os seus dados",
    export: "Exportar os meus dados",
    logout: "Terminar sessão",
    manualTitle: "Um preço que encontrou",
    size: "Conteúdo da embalagem",
    price: "Preço a pagar (€)",
    condition: "Condição de acesso",
    couponCode: "Código do cupão",
    balance: "Saldo futuro em cartão (€)",
    location: "Loja onde viu o preço",
    from: "Válido desde",
    until: "Válido até",
    sourceUrl: "Ligação à fonte (opcional)",
    vat: "O preço inclui IVA",
    manualNote:
      "O saldo futuro é mostrado à parte. Não é descontado do valor que paga hoje. Preços sem IVA ficam fora dos planos.",
    loginTitle: "Bem-vindo à sua Despensa.",
    loginHint: "Entre para abrir as suas listas e preferências.",
    username: "Nome de utilizador",
    password: "Palavra-passe",
    login: "Entrar",
    register: "Criar conta",
    registerTitle: "Uma despensa só sua.",
    registerHint:
      "Crie a sua conta nesta instalação. As listas ficam privadas.",
    noAccount: "Primeira visita?",
    hasAccount: "Já tem conta?",
    passwordHint: "Pelo menos 10 caracteres",
    authStory: "As boas compras\ncomeçam em casa.",
    authText:
      "A lista organizada. Os preços à vista. Mais espaço para o que importa.",
    loading: "A carregar…",
    error: "Não foi possível concluir. Tente novamente.",
    refreshQueued:
      "Recolha agendada. Os resultados aparecem à medida que chegam.",
    copyDone: "Produtos do mês anterior adicionados",
    noPrevious: "O mês anterior ainda não tem produtos",
    selectMonth: "Escolher mês",
    close: "Fechar",
    install: "Instalar app",
    installHelp:
      "No iPhone: Partilhar → Adicionar ao ecrã principal. No Android/PC: menu do navegador → Instalar app. Requer HTTPS.",
    filter: "Filtrar produtos",
    setup: "Comece pela sua lista",
    total: "Total observado",
    historyEmpty: "O histórico vai crescer com as próximas recolhas.",
    sourceStatus: "Última recolha",
    never: "Ainda sem recolhas",
    merchandise: "Mercearia",
    dairy: "Laticínios",
    fresh: "Frescos",
    cleaning: "Casa e limpeza",
    other: "Outros",
    notValidated: "Verifique condições na fonte",
    lockedItem: "Produto específico: compara apenas esta referência.",
    genericItem: "Pesquisa de alternativas",
    budgetHint: "O total do plano inclui apenas produtos com preço elegível.",
    routeReal: "Percurso rodoviário estimado",
    workdays: "Dias de trabalho",
    locate: "Localizar",
    geocodeHint:
      "Use uma zona ou local público próximo, sem dados pessoais. Ao localizar, o texto é enviado ao OpenStreetMap.",
    chooseLocation: "Escolha uma localização",
    routeMode: "Percurso base",
    homeRoute: "Casa → compras → casa",
    workRoute: "Trabalho → compras → casa",
    routeUnavailable:
      "Não foi possível calcular a rota; a distância fica por confirmar.",
    distanceEstimate: "Estimativa manual",
    subtotal: "Subtotal de produtos",
  },
  "es-ES": {
    tagline: "compras con sentido",
    list: "Mi lista",
    explore: "Explorar precios",
    plan: "Plan de compra",
    profile: "Mi perfil",
    greeting: "Menos cuentas. Más ahorro.",
    intro: "Su lista del mes, con precios y decisiones en su sitio.",
    monthList: "La lista de este mes",
    subtitle: "Un mes organizado empieza aquí.",
    heroLabel: "COMPRAR BIEN, VIVIR MEJOR",
    heroTitle: "Todo lo que necesita.\nCon más sentido.",
    heroText: "Planifique la compra, compare precios y elija mejor.",
    items: "Productos en la lista",
    itemsDetail: "para este mes",
    budget: "Presupuesto mensual",
    budgetDetail: "definido por usted",
    prices: "Precios observados",
    pricesDetail: "cobertura parcial del catálogo",
    yourList: "¿Qué llevamos?",
    listHint: "Su próxima visita al supermercado",
    add: "Añadir",
    quickAdd: "¿Qué falta en la despensa?",
    emptyTitle: "Su lista empieza aquí",
    emptyText: "Añada el primer producto o descubra los precios recogidos.",
    browse: "Explorar productos",
    done: "comprados",
    shopping: "Modo de compra",
    exitShopping: "Salir del modo de compra",
    copyMonth: "Repetir mes anterior",
    smartTitle: "Una lista. Un plan mejor.",
    smartText:
      "Consulte dónde comprar los productos con precio disponible, teniendo en cuenta sus tiendas y desplazamientos.",
    seePlan: "Encontrar mi plan",
    sources: "El radar de precios",
    sourceHint: "Fuentes, fechas y condiciones visibles",
    sourcePartial: "Catálogo parcial",
    manual: "Introducido por usted",
    privacy: "Sus listas son privadas. Sin publicidad ni venta de sus datos.",
    refresh: "Actualizar precios",
    updating: "Actualizando",
    offline:
      "Sin conexión. La lista sigue disponible; los cambios se sincronizarán.",
    pending: "cambios por sincronizar",
    noPrice: "Sin precio",
    edit: "Editar producto",
    product: "Producto",
    query: "Palabras para comparar",
    queryHint:
      "Las alternativas deben incluir estas palabras. Confirme tipo, marca y formato.",
    quantity: "Cantidad necesaria",
    unit: "Unidad",
    category: "Categoría",
    needed: "Comprar antes de",
    note: "Notas",
    save: "Guardar",
    cancel: "Cancelar",
    delete: "Eliminar",
    saved: "Guardado",
    added: "Añadido a la lista",
    deleted: "Producto eliminado",
    searchPlaceholder: "Busque arroz, leche, aceite…",
    allStores: "Todas las tiendas",
    manualPrice: "Registrar precio",
    catalogTitle: "Precios, sin adivinanzas.",
    catalogSubtitle:
      "Compare lo observado. Compruebe la tienda y las condiciones.",
    coverage:
      "La recogida automática cubre algunas categorías de Continente y Auchan en Portugal. España y otras tiendas admiten precios manuales. No es un catálogo completo.",
    noResults: "Todavía no encontramos ese producto",
    noResultsText:
      "Pruebe otras palabras, actualice el catálogo o registre un precio de la tienda.",
    observed: "Visto",
    source: "Ver en la tienda",
    history: "Historial",
    normal: "Precio público",
    card: "Requiere tarjeta",
    subscription: "Requiere suscripción",
    coupon: "Requiere cupón",
    professional: "Acceso profesional",
    unknown: "Condiciones sin confirmar",
    packUnknown: "Formato sin confirmar",
    useProduct: "Añadir este producto",
    planTitle: "El mejor camino para su lista.",
    planSubtitle:
      "Compare cestas con la misma cobertura y vea qué incluye el total.",
    planNotice:
      "Las alternativas se sugieren por palabras, no por equivalencia certificada. Confirme los productos. El precio en línea puede diferir del de la tienda física.",
    date: "Fecha de compra",
    calculate: "Comparar planes",
    best: "Plan sugerido",
    partial: "Cesta incompleta",
    coverageLabel: "productos con precio",
    basket: "Productos",
    travel: "Desplazamiento",
    unknownKm: "Distancia sin definir",
    futureBalance: "Saldo futuro",
    missing: "Sin precio válido",
    planEmpty: "Todavía no hay un plan para comparar",
    planEmptyText:
      "Añada productos y elija sus tiendas en el perfil. Se necesitan precios recientes y formatos compatibles.",
    futureNotice:
      "Para fechas futuras solo usamos precios con una vigencia publicada que incluya ese día.",
    distanceNotice:
      "Sin coordenadas, los kilómetros son estimaciones introducidas en el perfil. La suma de desvíos no representa una ruta optimizada.",
    profileTitle: "A su medida.",
    profileSubtitle: "Sus tiendas, sus tarjetas y su forma de comprar.",
    preferences: "Preferencias",
    locale: "Idioma",
    countries: "¿Dónde hace la compra?",
    budgetField: "Presupuesto (€ / mes)",
    interval: "Actualizar cada (horas)",
    auto: "Actualizar automáticamente en el servidor",
    stops: "Máximo de tiendas por visita",
    costKm: "Coste del desplazamiento (€ / km)",
    routine: "Su rutina",
    home: "Zona de casa",
    work: "Zona del trabajo",
    homeHint: "Dirección o zona, guardada solo en su perfil.",
    stores: "Sus supermercados",
    storesHint: "Active solo las tiendas donde puede y quiere comprar.",
    enabled: "Usar esta tienda",
    hasCard: "Tengo tarjeta",
    hasSubscription: "Tengo suscripción",
    hasAccess: "Tengo acceso profesional",
    extraKm: "Kilómetros adicionales estimados",
    storeAddress: "Tienda / ubicación",
    coupons: "Cupones disponibles (códigos separados por comas)",
    saveProfile: "Guardar preferencias",
    data: "Sus datos",
    export: "Exportar mis datos",
    logout: "Cerrar sesión",
    manualTitle: "Un precio que encontró",
    size: "Contenido del envase",
    price: "Precio a pagar (€)",
    condition: "Condición de acceso",
    couponCode: "Código del cupón",
    balance: "Saldo futuro en tarjeta (€)",
    location: "Tienda donde vio el precio",
    from: "Válido desde",
    until: "Válido hasta",
    sourceUrl: "Enlace a la fuente (opcional)",
    vat: "El precio incluye IVA",
    manualNote:
      "El saldo futuro se muestra aparte. No se descuenta de lo que paga hoy. Los precios sin IVA quedan fuera de los planes.",
    loginTitle: "Bienvenido a su Despensa.",
    loginHint: "Entre para abrir sus listas y preferencias.",
    username: "Nombre de usuario",
    password: "Contraseña",
    login: "Entrar",
    register: "Crear cuenta",
    registerTitle: "Una despensa solo suya.",
    registerHint:
      "Cree su cuenta en esta instalación. Sus listas serán privadas.",
    noAccount: "¿Primera visita?",
    hasAccount: "¿Ya tiene cuenta?",
    passwordHint: "Al menos 10 caracteres",
    authStory: "Las buenas compras\nempiezan en casa.",
    authText:
      "La lista organizada. Los precios a la vista. Más espacio para lo que importa.",
    loading: "Cargando…",
    error: "No se pudo completar. Inténtelo de nuevo.",
    refreshQueued:
      "Recogida programada. Los resultados aparecerán a medida que lleguen.",
    copyDone: "Productos del mes anterior añadidos",
    noPrevious: "El mes anterior todavía no tiene productos",
    selectMonth: "Elegir mes",
    close: "Cerrar",
    install: "Instalar app",
    installHelp:
      "En iPhone: Compartir → Añadir a pantalla de inicio. En Android/PC: menú del navegador → Instalar app. Requiere HTTPS.",
    filter: "Filtrar productos",
    setup: "Empiece por su lista",
    total: "Total observado",
    historyEmpty: "El historial crecerá con las próximas recogidas.",
    sourceStatus: "Última recogida",
    never: "Todavía sin recogidas",
    merchandise: "Despensa",
    dairy: "Lácteos",
    fresh: "Frescos",
    cleaning: "Hogar y limpieza",
    other: "Otros",
    notValidated: "Compruebe las condiciones en la fuente",
    lockedItem: "Producto concreto: solo compara esta referencia.",
    genericItem: "Búsqueda de alternativas",
    budgetHint:
      "El total del plan solo incluye productos con un precio válido.",
    routeReal: "Ruta por carretera estimada",
    workdays: "Días de trabajo",
    locate: "Localizar",
    geocodeHint:
      "Use una zona o lugar público cercano, sin datos personales. Al localizar, el texto se envía a OpenStreetMap.",
    chooseLocation: "Elija una ubicación",
    routeMode: "Trayecto base",
    homeRoute: "Casa → compra → casa",
    workRoute: "Trabajo → compra → casa",
    routeUnavailable:
      "No se pudo calcular la ruta; la distancia queda sin confirmar.",
    distanceEstimate: "Estimación manual",
    subtotal: "Subtotal de productos",
  },
};
let locale = localStorage.getItem("despensa-locale") || "pt-PT";
const t = (key) => copy[locale]?.[key] || copy["pt-PT"][key] || key;
const today = () => new Date().toLocaleDateString("en-CA");
const newId = () =>
  Array.from(crypto.getRandomValues(new Uint8Array(16)), (b) =>
    b.toString(16).padStart(2, "0"),
  ).join("");
const thisMonth = () =>
  `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, "0")}`;
const located = {};
const state = {
  view: "list",
  month: thisMonth(),
  user: null,
  profile: null,
  stores: [],
  items: [],
  offers: [],
  status: {},
  plan: null,
  search: "",
  storeFilter: "",
  shopping: false,
  registering: false,
  offline: false,
  day: today(),
  route: "auto",
};
const money = (cents) =>
  new Intl.NumberFormat(locale, { style: "currency", currency: "EUR" }).format(
    cents / 100,
  );
const dateText = (s) =>
  s
    ? new Date(s).toLocaleDateString(locale, { day: "numeric", month: "short" })
    : t("never");
const storeName = (sid) => state.stores.find((s) => s.id === sid)?.name || sid;
const uidKey = () => (state.user ? `despensa-${state.user.id}` : "");
function readQueue() {
  try {
    return JSON.parse(localStorage.getItem(uidKey() + "-queue") || "[]");
  } catch {
    return [];
  }
}
function saveSnapshot() {
  if (state.user)
    localStorage.setItem(
      uidKey(),
      JSON.stringify({
        user: state.user,
        profile: state.profile,
        stores: state.stores,
        items: state.items,
        offers: state.offers,
        status: state.status,
        month: state.month,
      }),
    );
}
function toast(text) {
  $("#toast").textContent = text;
  $("#toast").classList.add("visible");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => $("#toast").classList.remove("visible"), 4200);
}
async function api(path, method = "GET", data) {
  let response;
  try {
    response = await fetch("/api" + path, {
      method,
      redirect: "manual",
      credentials: "same-origin",
      headers: data ? { "Content-Type": "application/json" } : {},
      body: data ? JSON.stringify(data) : undefined,
    });
  } catch (e) {
    e.network = true;
    throw e;
  }
  if (response.type === "opaqueredirect") {
    window.location.assign("/");
    const e = new Error(t("loginHint"));
    e.status = 401;
    throw e;
  }
  const result = await response.json();
  if (!response.ok) {
    const err = new Error(result.error || t("error"));
    err.status = response.status;
    throw err;
  }
  return result;
}
const heroArt = () =>
  `<svg class="hero-art" viewBox="0 0 250 210" fill="none" aria-hidden="true"><circle cx="150" cy="116" r="87" fill="#E0E9CF"/><path d="m81 90 106 8-15 90-82-6z" fill="#F9F7EB" stroke="#A9BA90" stroke-width="2"/><path d="m100 94 6-32c3-23 48-21 50 3l3 34" stroke="#7C9362" stroke-width="5" stroke-linecap="round"/><path d="m109 120-3 39m24-36-3 39m25-37-3 39" stroke="#E1DCC4" stroke-width="5" stroke-linecap="round"/><path d="m139 91 20-50 17 6-19 52" fill="#D6A773"/><path d="m160 42 9-15 16 8-10 13" fill="#A2B779"/><path d="m102 95-9-38 20-5 13 44" fill="#EAC59C"/><path d="m94 57 8-14 12 9" fill="#7B985C"/><circle cx="173" cy="143" r="33" fill="#D3DFB9" stroke="#FAFBF3" stroke-width="4"/><path d="m159 143 10 9 17-21" stroke="#6A8650" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><path d="m64 56 4 8m-14-1 8 2m138 18 5-5m-3 15 8-1" stroke="#A7BA89" stroke-width="2" stroke-linecap="round"/><path d="M54 142c-3-15-15-16-15-16s-1 15 15 16Zm0 0c0-17 10-22 10-22s6 16-10 22Z" fill="#B9CAA1"/></svg>`;
const conditionLabel = (c) =>
  t(
    {
      public: "normal",
      card: "card",
      subscription: "subscription",
      coupon: "coupon",
      professional: "professional",
      unknown: "unknown",
    }[c] || "unknown",
  );
const productIcon = (name) =>
  /leite|leche|azeite|aceite|óleo|agua|água|sumo|zumo/i.test(name)
    ? "bottle"
    : /arroz|massa|pasta|aveia|cereal/i.test(name)
      ? "grain"
      : "box";
const visual = (name) =>
  `<div class="product-visual">${icon(productIcon(name))}</div>`;
function empty(title, text, button = "") {
  return `<div class="empty">${icon("bag")}<h3>${t(title)}</h3><p>${t(text)}</p>${button}</div>`;
}
function title(head, sub, side = "") {
  return `<div class="page-title"><div><h1>${t(head)}</h1><p>${t(sub)}</p></div>${side}</div>`;
}
function monthPicker() {
  return `<input type="month" id="month" value="${state.month}" aria-label="${t("selectMonth")}">`;
}
function nav(mobile = false) {
  return `<nav class="${mobile ? "mobile-nav" : "nav"}" aria-label="${t("list")}">${[
    ["list", "list"],
    ["explore", "search"],
    ["plan", "route"],
    ["profile", "settings"],
  ]
    .map(
      ([v, i]) =>
        `<button data-view="${v}" class="${state.view === v ? "active" : ""}" ${state.view === v ? 'aria-current="page"' : ""}>${icon(i)}<span>${t(v)}</span></button>`,
    )
    .join("")}</nav>`;
}
function render() {
  document.documentElement.lang = locale;
  document.body.classList.toggle("shopping-mode", state.shopping);
  if (!state.user) {
    renderAuth();
    return;
  }
  const active = state.status.jobs?.some((j) =>
    ["queued", "running"].includes(j.status),
  );
  $("#app").innerHTML =
    `<div class="shell"><aside class="sidebar"><a class="brand" href="/"><img src="/logo.svg" alt=""><div><strong>despensa<span>.</span></strong><span>${t("tagline")}</span></div></a>${nav()}<div class="side-note">${icon("leaf", "sprout")}<strong>${t("greeting")}</strong><p>${t("intro")}</p></div><div class="side-foot"><span class="dot"></span> Portugal & España <span>·</span> v0.1</div></aside><div class="workspace"><header class="topbar"><div class="breadcrumb">Despensa ${icon("chevron")}<b>${t(state.view)}</b></div><a class="mobile-brand" href="/"><img src="/logo.svg" alt="">despensa.</a><div class="top-actions"><span class="top-date">${new Date().toLocaleDateString(locale, { day: "numeric", month: "long" })}</span><button class="quiet small" data-action="refresh" title="${t("refresh")}" aria-label="${t("refresh")}" ${active ? "disabled" : ""}>${icon("refresh", active ? "spinner" : "")}<span class="refresh-label">${t(active ? "updating" : "refresh")}</span></button><button class="avatar" data-view="profile" title="${esc(state.user.username)}" aria-label="${t("profile")}">${esc(state.user.username.slice(0, 2).toUpperCase())}</button></div></header>${state.offline || readQueue().length ? `<div class="offline-banner" role="status">${state.offline ? t("offline") : `${readQueue().length} ${t("pending")}`}</div>` : ""}<main class="content" id="main">${{ list: renderList, explore: renderExplore, plan: renderPlan, profile: renderProfile }[state.view]()}</main></div></div>${nav(true)}`;
  bind();
}
function renderAuth() {
  $("#app").innerHTML =
    `<main class="auth-page" id="main"><section class="auth-story"><a class="brand" href="/"><img src="/logo.svg" alt=""><div><strong>despensa.</strong><span>${t("tagline")}</span></div></a><div class="eyebrow">PORTUGAL & ESPAÑA</div><h1>${t("authStory").replace("\n", "<br>")}</h1><p>${t("authText")}</p>${heroArt()}</section><section class="auth-form"><div class="auth-box"><div class="auth-locale"><select id="auth-locale" aria-label="${t("locale")}"><option value="pt-PT" ${locale === "pt-PT" ? "selected" : ""}>Português</option><option value="es-ES" ${locale === "es-ES" ? "selected" : ""}>Español</option></select></div><h2>${t(state.registering ? "registerTitle" : "loginTitle")}</h2><p>${t(state.registering ? "registerHint" : "loginHint")}</p><form id="auth-form"><div class="field"><label for="username">${t("username")}</label><input id="username" name="username" autocomplete="username" required minlength="3" maxlength="80"></div><div class="field"><label for="password">${t("password")}</label><input id="password" type="password" name="password" autocomplete="${state.registering ? "new-password" : "current-password"}" required minlength="10" maxlength="256" placeholder="${t("passwordHint")}"></div><div class="auth-error" role="alert" id="auth-error"></div><button class="primary" type="submit">${t(state.registering ? "register" : "login")} ${icon("arrow")}</button></form><div class="auth-toggle">${t(state.registering ? "hasAccount" : "noAccount")} <button class="quiet" id="auth-toggle">${t(state.registering ? "login" : "register")}</button></div><div class="privacy-note">${icon("shield")}<span>${t("privacy")}</span></div></div></section></main>`;
  $("#auth-toggle").onclick = () => {
    state.registering = !state.registering;
    renderAuth();
  };
  $("#auth-locale").onchange = (e) => {
    locale = e.target.value;
    localStorage.setItem("despensa-locale", locale);
    document.documentElement.lang = locale;
    renderAuth();
  };
  $("#auth-form").onsubmit = async (e) => {
    e.preventDefault();
    const button = e.submitter;
    button.disabled = true;
    try {
      const d = Object.fromEntries(new FormData(e.target));
      const r = await api(
        "/auth/" + (state.registering ? "register" : "login"),
        "POST",
        d,
      );
      state.user = r.user;
      localStorage.setItem("despensa-last-user", JSON.stringify(r.user));
      await load();
    } catch (err) {
      $("#auth-error").textContent = err.message;
      button.disabled = false;
    }
  };
}
function bestForItem(item) {
  const p = state.plan?.plans?.[0];
  return p?.selections?.find((s) => s.item_id === item.id);
}
function renderList() {
  const checked = state.items.filter((i) => i.checked).length;
  const groups = [
    ...new Set(state.items.map((i) => i.category || "Mercearia")),
  ];
  return `${title("monthList", "subtitle", monthPicker())}${state.shopping ? `<button class="quiet small" data-action="shopping">${icon("close")}${t("exitShopping")}</button>` : ""}<section class="hero"><div class="hero-text"><div class="eyebrow">${t("heroLabel")}</div><h2>${t("heroTitle").replace("\n", "<br>")}</h2><p>${t("heroText")}</p></div>${heroArt()}</section><div class="stats"><div class="stat"><div class="stat-icon">${icon("bag")}</div><div><div class="label">${t("items")}</div><div class="number">${state.items.length}</div><div class="detail">${checked} ${t("done")}</div></div></div><div class="stat"><div class="stat-icon">${icon("wallet")}</div><div><div class="label">${t("budget")}</div><div class="number">${money(state.profile.budget * 100)}</div><div class="detail">${t("budgetDetail")}</div></div></div><div class="stat"><div class="stat-icon">${icon("search")}</div><div><div class="label">${t("prices")}</div><div class="number">${state.status.offer_count || 0}</div><div class="detail">${t("pricesDetail")}</div></div></div></div><div class="dashboard-grid"><section class="panel"><div class="panel-head"><div><h2>${t("yourList")}</h2><p>${t("listHint")}</p></div><button class="primary small" data-action="add">${icon("plus")}${t("add")}</button></div>${
    state.items.length
      ? groups
          .map(
            (group) =>
              `<div class="section-title">${esc(categoryName(group))}</div>${state.items
                .filter((i) => (i.category || "Mercearia") === group)
                .map((item) => {
                  const choice = bestForItem(item);
                  return `<div class="item ${item.checked ? "checked" : ""}"><button class="check ${item.checked ? "done" : ""}" data-check="${item.id}" aria-label="${esc(item.name)}" aria-pressed="${!!item.checked}">${item.checked ? icon("check") : ""}</button>${visual(item.name)}<div class="item-info"><div class="item-name">${esc(item.name)}</div><div class="item-meta"><span>${item.quantity} ${esc(item.unit)}</span>${item.needed_on ? `<span>${dateText(item.needed_on)}</span>` : ""}${item.offer_id ? `<span>${icon("pin")}</span>` : ""}</div></div><div class="item-price">${choice ? money(choice.cost_cents) : "—"}<small>${choice ? esc(storeName(choice.offer.store)) : t("noPrice")}</small></div><button class="quiet more" data-edit="${item.id}" aria-label="${t("edit")}: ${esc(item.name)}">${icon("more")}</button></div>`;
                })
                .join("")}`,
          )
          .join("")
      : empty(
          "emptyTitle",
          "emptyText",
          `<button class="quiet small" data-view="explore">${t("browse")}${icon("arrow")}</button>`,
        )
  }<form class="add-row" id="quick-add"><input name="name" required maxlength="160" placeholder="${t("quickAdd")}" aria-label="${t("product")}"><button class="primary" type="submit" aria-label="${t("add")}">${icon("plus")}</button></form><div class="list-foot"><span>${checked} / ${state.items.length} ${t("done")}</span><button class="quiet small" data-action="shopping">${icon("bag")}${t(state.shopping ? "exitShopping" : "shopping")}</button></div></section><aside class="right-stack"><section class="insight">${icon("spark")}<h3>${t("smartTitle")}</h3><p>${t("smartText")}</p><button data-view="plan">${t("seePlan")}${icon("arrow")}</button></section><section class="panel"><div class="panel-head"><div><h3>${t("sources")}</h3><p>${t("sourceHint")}</p></div></div><div class="panel-body">${["continente", "auchan"].map((s) => `<div class="source-row"><div class="store-mark">${esc(storeName(s).slice(0, 2).toUpperCase())}</div><div><div class="store-name">${esc(storeName(s))}</div><small>${t("sourcePartial")} · PT</small></div><span class="status">${dateText(state.status.meta?.last_refresh)}</span></div>`).join("")}<div class="source-row"><div class="store-mark">${icon("plus")}</div><div><div class="store-name">${t("manualPrice")}</div><small>Portugal · España</small></div><button class="quiet small" data-action="manual" aria-label="${t("manualPrice")}">${icon("arrow")}</button></div></div></section><div class="privacy-note">${icon("shield")}<span>${t("privacy")}</span></div></aside></div><div class="toolbar mt16"><button class="quiet small" data-action="copy">${icon("calendar")}${t("copyMonth")}</button><button class="quiet small" data-action="install">${icon("download")}${t("install")}</button></div>`;
}
function categoryName(c) {
  return (
    {
      Mercearia: t("merchandise"),
      Laticínios: t("dairy"),
      Frescos: t("fresh"),
      "Casa e limpeza": t("cleaning"),
      Outros: t("other"),
    }[c] || c
  );
}
function renderExplore() {
  return `${title("catalogTitle", "catalogSubtitle")}<div class="toolbar"><div class="search-wrap">${icon("search")}<input id="catalog-search" value="${esc(state.search)}" placeholder="${t("searchPlaceholder")}" aria-label="${t("filter")}"></div><select id="catalog-store" aria-label="${t("allStores")}"><option value="">${t("allStores")}</option>${state.stores
    .filter((s) => state.profile.countries.includes(s.country))
    .map(
      (s) =>
        `<option value="${s.id}" ${s.id === state.storeFilter ? "selected" : ""}>${esc(s.name)} · ${s.country}</option>`,
    )
    .join(
      "",
    )}</select><button class="primary" data-action="manual">${icon("plus")}${t("manualPrice")}</button></div><div class="notice">${icon("shield")}<span>${t("coverage")}</span></div><div id="catalog-results">${renderProducts()}</div>`;
}
function renderProducts() {
  const products = state.offers.filter(
    (o) => !state.storeFilter || o.store === state.storeFilter,
  );
  return products.length
    ? `<div class="product-grid">${products.map((o) => `<article class="product-card"><div class="product-top"><span class="tag gray">${esc(storeName(o.store))} · ${o.country}</span><span class="tag ${o.condition === "public" ? "" : "amber"}">${conditionLabel(o.condition)}</span></div>${visual(o.name)}<div class="card-name"><h3>${esc(o.name)}</h3><span class="unit-price">${esc(o.size ? `${o.size} ${o.unit}` : t("packUnknown"))}</span></div><div><span class="price">${money(o.price_cents)}</span><div class="unit-price">${o.size ? `${money(o.price_cents / o.size)} / ${o.unit}` : esc(o.pack)}</div></div>${o.balance_cents ? `<span class="condition-note">+ ${money(o.balance_cents)} ${t("futureBalance")}</span>` : ""}<div class="evidence">${t("observed")} ${dateText(o.observed_at)} · ${o.source_kind === "manual" ? t("manual") : "online"}<br>${esc(o.location)}</div><div class="card-actions"><button class="quiet small" data-history="${esc(o.id)}">${t("history")}</button><button class="primary small" data-offer="${esc(o.id)}" aria-label="${t("useProduct")}: ${esc(o.name)}">${icon("plus")}${t("add")}</button></div>${o.source_url ? `<a href="${esc(o.source_url)}" target="_blank" rel="noopener noreferrer" class="evidence">${t("source")} ↗</a>` : ""}</article>`).join("")}</div>`
    : empty(
        "noResults",
        "noResultsText",
        `<button class="primary small" data-action="manual">${t("manualPrice")}</button>`,
      );
}
function renderPlan() {
  const result = state.plan;
  return `${title("planTitle", "planSubtitle")}<div class="toolbar"><label for="plan-day" class="muted">${t("date")}</label><input type="date" id="plan-day" value="${state.day}"><select id="route-mode" aria-label="${t("routeMode")}"><option value="auto" ${state.route === "auto" ? "selected" : ""}>${t("routeMode")}</option><option value="home" ${state.route === "home" ? "selected" : ""}>${t("homeRoute")}</option><option value="work" ${state.route === "work" ? "selected" : ""}>${t("workRoute")}</option></select><button class="primary" data-action="plan">${icon("route")}${t("calculate")}</button></div><div class="notice">${icon("shield")}<span>${t("planNotice")}</span></div>${state.day > today() ? `<div class="notice amber">${icon("calendar")}<span>${t("futureNotice")}</span></div>` : ""}${result?.missing?.length ? `<div class="notice amber">${icon("search")}<span><b>${t("missing")}:</b> ${result.missing.map(esc).join(", ")}</span></div>` : ""}${
    result?.plans?.length
      ? result.plans
          .slice(0, 6)
          .map(
            (p, index) =>
              `<article class="plan-card ${index === 0 ? "best" : ""}"><header><div>${index === 0 ? `<span class="tag">${t("best")}</span>` : ""}${!p.complete ? `<span class="tag amber">${t("partial")}</span>` : ""}<h3>${p.stores.map((s) => esc(storeName(s))).join(" + ")}</h3><span class="muted">${p.coverage} / ${p.total_items} ${t("coverageLabel")}</span></div><div class="plan-total">${money(p.total_cents)}<div class="muted total-note">${t(p.travel_cents === null ? "subtotal" : "total")}</div></div></header><div class="plan-metrics"><span>${t("basket")}: <b>${money(p.basket_cents)}</b></span><span>${icon("route")} ${p.extra_km === null ? t("unknownKm") : `${p.extra_km} km · ${money(p.travel_cents)} · ${t(p.distance_method === "road" ? "routeReal" : "distanceEstimate")}`}</span>${p.balance_cents ? `<span>${t("futureBalance")}: ${money(p.balance_cents)}</span>` : ""}</div><div class="plan-products">${p.selections.map((s) => `<div class="plan-product"><div>${esc(s.item_name)}<small>${esc(s.offer.name)} · ${s.packs} × ${esc(s.offer.pack)} · ${esc(storeName(s.offer.store))}</small></div><b>${money(s.cost_cents)}</b></div>`).join("")}</div></article>`,
          )
          .join("")
      : empty(
          "planEmpty",
          "planEmptyText",
          `<button class="primary small" data-view="profile">${t("profile")}${icon("arrow")}</button>`,
        )
  }<p class="privacy-note">${icon("pin")}<span>${t(result?.distance_method === "road" ? "routeReal" : "distanceNotice")}${result?.route_error ? " " + t("routeUnavailable") : ""}</span></p><p class="privacy-note">${t("budgetHint")}</p><p class="privacy-note"><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors</a> · OSRM</p>`;
}
function field(name, label, value, type = "text", extra = "", hint = "") {
  return `<div class="field"><label for="f-${name}">${t(label)}</label><input id="f-${name}" name="${name}" type="${type}" value="${esc(value)}" ${extra}>${hint ? `<span class="hint">${t(hint)}</span>` : ""}</div>`;
}
function checkbox(name, label, checked) {
  return `<label class="checkbox-field"><input type="checkbox" name="${name}" ${checked ? "checked" : ""}>${t(label)}</label>`;
}
function renderProfile() {
  const p = state.profile;
  return `${title("profileTitle", "profileSubtitle")}<form id="profile-form"><div class="settings-grid"><section class="panel"><div class="panel-body"><h2 class="settings-title">${t("preferences")}</h2><div class="form-grid"><div class="field"><label for="f-locale">${t("locale")}</label><select name="locale" id="f-locale"><option value="pt-PT" ${locale === "pt-PT" ? "selected" : ""}>Português</option><option value="es-ES" ${locale === "es-ES" ? "selected" : ""}>Español</option></select></div>${field("budget", "budgetField", p.budget, "number", 'min="0" max="100000" step="1"')}${field("interval_hours", "interval", p.interval_hours, "number", 'min="6" max="168" step="1"')}${field("max_stops", "stops", p.max_stops, "number", 'min="1" max="3" step="1"')}${field("cost_per_km", "costKm", p.cost_per_km, "number", 'min="0" max="10" step="0.01"')}<div class="field"><label>${t("countries")}</label>${checkbox("country-PT", "Portugal", p.countries.includes("PT"))}${checkbox("country-ES", "España", p.countries.includes("ES"))}</div></div>${checkbox("automatic", "auto", p.automatic)}</div></section><section class="panel"><div class="panel-body"><h2 class="settings-title">${t("routine")}</h2><div class="field"><label for="f-home">${t("home")}</label><div class="toolbar"><input id="f-home" name="home" value="${esc(p.home)}" placeholder="Lisboa, Portugal"><button type="button" class="small" data-locate="home">${icon("pin")}${t("locate")}</button></div><small class="muted" id="coords-home">${p.home_coords ? esc(p.home_coords.join(", ")) : ""}</small></div><div class="field"><label for="f-work">${t("work")}</label><div class="toolbar"><input id="f-work" name="work" value="${esc(p.work)}" placeholder=""><button type="button" class="small" data-locate="work">${icon("pin")}${t("locate")}</button></div><small class="muted" id="coords-work">${p.work_coords ? esc(p.work_coords.join(", ")) : ""}</small></div><p class="privacy-note">${t("geocodeHint")}</p><p class="privacy-note"><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors</a> · <a href="https://operations.osmfoundation.org/policies/nominatim/" target="_blank" rel="noopener">Nominatim</a></p><div class="field"><label>${t("workdays")}</label><div class="toolbar">${Array.from({ length: 7 }, (_, i) => `<label class="checkbox-field"><input type="checkbox" name="workday-${i}" ${p.workdays.includes(i) ? "checked" : ""}>${new Intl.DateTimeFormat(locale, { weekday: "short" }).format(new Date(2026, 0, 5 + i))}</label>`).join("")}</div></div></div></section><section class="wide"><div class="page-title"><div><h2>${t("stores")}</h2><p>${t("storesHint")}</p></div></div><div class="store-settings">${state.stores
    .map((s) => {
      const v = p.stores[s.id];
      return `<section class="store-setting" data-store="${s.id}"><header><div><strong>${esc(s.name)}</strong> <span class="tag gray">${s.country}</span></div><span class="tag ${s.automatic ? "" : "gray"}">${t(s.automatic ? "sourcePartial" : "manual")}</span></header>${checkbox(`${s.id}-enabled`, "enabled", v.enabled)}<div class="checks">${checkbox(`${s.id}-card`, "hasCard", v.card)}${checkbox(`${s.id}-subscription`, "hasSubscription", v.subscription)}${s.professional ? checkbox(`${s.id}-access`, "hasAccess", v.access) : ""}</div><div class="field"><label for="f-${s.id}-address">${t("storeAddress")}</label><div class="toolbar"><input name="${s.id}-address" id="f-${s.id}-address" value="${esc(v.address)}"><button type="button" class="small" data-locate="${s.id}">${icon("pin")}${t("locate")}</button></div><small class="muted" id="coords-${s.id}">${v.coords ? esc(v.coords.join(", ")) : ""}</small></div>${field(`${s.id}-extra_km`, "extraKm", v.extra_km ?? "", "number", 'min="0" max="2000" step="0.1"')}${field(`${s.id}-coupons`, "coupons", v.coupons.join(", "))}</section>`;
    })
    .join(
      "",
    )}</div></section></div><div class="form-actions"><button class="primary" type="submit">${icon("check")}${t("saveProfile")}</button></div></form><section class="panel mt24"><div class="panel-body"><h2 class="settings-title">${t("data")}</h2><div class="toolbar"><a href="/api/export" class="tag">${icon("download")}${t("export")}</a><button class="quiet small" data-action="install">${icon("download")}${t("install")}</button><button class="quiet small danger" data-action="logout">${icon("logout")}${t("logout")}</button></div></div></section>`;
}
function openModal(head, html) {
  $("#modal-content").innerHTML =
    `<div class="modal-header"><h2>${t(head)}</h2><button class="quiet" data-close aria-label="${t("close")}">${icon("close")}</button></div>${html}`;
  $("#modal").showModal();
  $("#modal [data-close]").onclick = () => $("#modal").close();
  $("#modal")
    .querySelectorAll("[data-cancel]")
    .forEach((b) => (b.onclick = () => $("#modal").close()));
}
function itemModal(item = null, offer = null, quickName = "") {
  const d = item || {
    name: offer?.name || quickName,
    query: offer?.name || quickName,
    quantity: offer?.size || 1,
    unit: offer?.unit || "un",
    category: "Mercearia",
    needed_on: "",
    note: "",
    offer_id: offer?.id || "",
  };
  openModal(
    item ? "edit" : "add",
    `<form id="item-form"><div class="form-grid">${field("name", "product", d.name, "text", 'required maxlength="160"')}${field("query", "query", d.query, "text", 'required minlength="2" maxlength="120"', "queryHint")}${field("quantity", "quantity", d.quantity, "number", 'required min="0.001" max="10000" step="0.001"')}<div class="field"><label for="f-unit">${t("unit")}</label><select id="f-unit" name="unit">${["un", "kg", "l"].map((u) => `<option ${d.unit === u ? "selected" : ""}>${u}</option>`).join("")}</select></div><div class="field"><label for="f-category">${t("category")}</label><select id="f-category" name="category">${["Mercearia", "Laticínios", "Frescos", "Casa e limpeza", "Outros"].map((c) => `<option value="${esc(c)}" ${d.category === c ? "selected" : ""}>${esc(categoryName(c))}</option>`).join("")}</select></div>${field("needed_on", "needed", d.needed_on, "date")}<div class="field full"><label for="f-note">${t("note")}</label><textarea id="f-note" name="note" maxlength="300">${esc(d.note)}</textarea></div></div><div class="notice">${icon("search")}<span>${t(d.offer_id ? "lockedItem" : "genericItem")}</span></div><div class="form-actions">${item ? `<button type="button" class="quiet danger" id="delete-item">${icon("trash")}${t("delete")}</button>` : ""}<button type="button" data-cancel>${t("cancel")}</button><button class="primary" type="submit">${t("save")}</button></div></form>`,
  );
  $("#item-form").onsubmit = async (e) => {
    e.preventDefault();
    const v = Object.fromEntries(new FormData(e.target));
    v.quantity = +v.quantity;
    v.offer_id = d.offer_id || "";
    v.checked = !!d.checked;
    const id = item?.id || newId();
    const payload = { ...v, month: state.month, client_id: id };
    if (item) {
      state.items = state.items.map((i) => (i.id === id ? { ...i, ...v } : i));
    } else state.items.push({ ...v, id });
    $("#modal").close();
    saveSnapshot();
    render();
    await queueMutation(
      item ? "PATCH" : "POST",
      item ? "/items/" + id : "/items",
      payload,
    );
    toast(t(item ? "saved" : "added"));
    loadPlan();
  };
  if (item)
    $("#delete-item").onclick = async () => {
      state.items = state.items.filter((i) => i.id !== item.id);
      $("#modal").close();
      saveSnapshot();
      render();
      await queueMutation("DELETE", "/items/" + item.id, {});
      toast(t("deleted"));
      loadPlan();
    };
}
function manualModal() {
  openModal(
    "manualTitle",
    `<form id="manual-form"><div class="form-grid">${field("name", "product", "", "text", 'required maxlength="160"')}<div class="field"><label for="f-store">${t("stores")}</label><select id="f-store" name="store">${state.stores
      .filter((s) => state.profile.countries.includes(s.country))
      .map(
        (s) => `<option value="${s.id}">${esc(s.name)} · ${s.country}</option>`,
      )
      .join(
        "",
      )}</select></div>${field("price", "price", "", "number", 'required min="0.01" max="100000" step="0.01"')}${field("size", "size", 1, "number", 'required min="0.001" max="10000" step="0.001"')}<div class="field"><label for="f-unit">${t("unit")}</label><select id="f-unit" name="unit"><option>un</option><option>kg</option><option>l</option></select></div><div class="field"><label for="f-condition">${t("condition")}</label><select id="f-condition" name="condition">${["public", "card", "subscription", "coupon", "professional"].map((c) => `<option value="${c}">${conditionLabel(c)}</option>`).join("")}</select></div>${field("coupon", "couponCode", "")}${field("balance", "balance", 0, "number", 'min="0" max="100000" step="0.01"')}${field("location", "location", "", "text", "required")}${field("valid_from", "from", today(), "date")}${field("valid_to", "until", "", "date")}${field("source_url", "sourceUrl", "", "url")}</div>${checkbox("vat_included", "vat", true)}<div class="notice">${icon("wallet")}<span>${t("manualNote")}</span></div><div class="auth-error" id="manual-error" role="alert"></div><div class="form-actions"><button type="button" data-cancel>${t("cancel")}</button><button class="primary" type="submit">${t("save")}</button></div></form>`,
  );
  $("#manual-form").onsubmit = async (e) => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    d.vat_included = e.target.vat_included.checked;
    try {
      await api("/offers/manual", "POST", d);
      $("#modal").close();
      toast(t("saved"));
      await loadOffers();
      await loadPlan();
      render();
    } catch (err) {
      $("#manual-error").textContent = err.message;
    }
  };
}
async function queueMutation(method, path, data) {
  const queue = readQueue();
  queue.push({ method, path, data });
  localStorage.setItem(uidKey() + "-queue", JSON.stringify(queue));
  await flushQueue();
}
let syncing = false;
async function flushQueue() {
  if (syncing || !state.user) return;
  syncing = true;
  try {
    let queue = readQueue();
    while (queue.length) {
      const job = queue[0];
      try {
        await api(job.path, job.method, job.data);
        queue.shift();
        localStorage.setItem(uidKey() + "-queue", JSON.stringify(queue));
        state.offline = false;
      } catch (err) {
        if (err.network) {
          state.offline = true;
          break;
        }
        if (err.status === 401) {
          state.offline = true;
          toast(t("loginHint"));
          break;
        }
        toast(err.message);
        queue.shift();
        localStorage.setItem(uidKey() + "-queue", JSON.stringify(queue));
      }
    }
  } finally {
    syncing = false;
    saveSnapshot();
  }
}
async function loadOffers() {
  const r = await api(
    "/offers?q=" +
      encodeURIComponent(state.search) +
      "&store=" +
      encodeURIComponent(state.storeFilter),
  );
  state.offers = r.offers;
  saveSnapshot();
}
async function loadPlan() {
  if (state.offline) return;
  try {
    state.plan = await api(
      "/plan?month=" +
        state.month +
        "&day=" +
        state.day +
        "&route=" +
        state.route +
        "&roads=" +
        (state.view === "plan"),
    );
    if (["list", "plan"].includes(state.view)) render();
  } catch (err) {
    if (err.network) state.offline = true;
    else toast(err.message);
  }
}
async function load() {
  try {
    const me = await api("/me");
    state.user = me.user;
    state.profile = me.profile;
    state.stores = me.stores;
    locale = state.profile.locale;
    localStorage.setItem("despensa-locale", locale);
    localStorage.setItem("despensa-last-user", JSON.stringify(me.user));
    await flushQueue();
    const [items, status, offers] = await Promise.all([
      api("/items?month=" + state.month),
      api("/status"),
      api("/offers?q=" + encodeURIComponent(state.search)),
    ]);
    state.items = items.items;
    state.status = status;
    state.offers = offers.offers;
    state.offline = false;
    saveSnapshot();
    render();
    loadPlan();
  } catch (err) {
    if (err.status === 401) {
      state.user = null;
      render();
      return;
    }
    try {
      const last = JSON.parse(
        localStorage.getItem("despensa-last-user") || "null",
      );
      const snap = JSON.parse(
        localStorage.getItem(`despensa-${last?.id}`) || "null",
      );
      if (snap) {
        Object.assign(state, snap);
        state.offline = true;
        render();
        return;
      }
    } catch {}
    state.user = null;
    render();
    toast(err.message || t("error"));
  }
}
function bind() {
  $("#app")
    .querySelectorAll("[data-view]")
    .forEach(
      (b) =>
        (b.onclick = () => {
          state.view = b.dataset.view;
          state.shopping = false;
          render();
          if (state.view === "plan") loadPlan();
          if (state.view === "explore") searchOffers();
          window.scrollTo(0, 0);
        }),
    );
  $("#app")
    .querySelectorAll("[data-action]")
    .forEach((b) => (b.onclick = () => action(b.dataset.action)));
  $("#month")?.addEventListener("change", async (e) => {
    state.month = e.target.value;
    state.plan = null;
    try {
      const r = await api("/items?month=" + state.month);
      state.items = r.items;
      saveSnapshot();
      render();
      loadPlan();
    } catch (err) {
      toast(err.message);
    }
  });
  $("#quick-add")?.addEventListener("submit", (e) => {
    e.preventDefault();
    itemModal(null, null, new FormData(e.target).get("name"));
  });
  $("#app")
    .querySelectorAll("[data-check]")
    .forEach(
      (b) =>
        (b.onclick = async () => {
          const i = state.items.find((i) => i.id === b.dataset.check);
          i.checked = !i.checked;
          saveSnapshot();
          render();
          await queueMutation("PATCH", "/items/" + i.id, {
            checked: i.checked,
          });
          loadPlan();
        }),
    );
  $("#app")
    .querySelectorAll("[data-edit]")
    .forEach(
      (b) =>
        (b.onclick = () =>
          itemModal(state.items.find((i) => i.id === b.dataset.edit))),
    );
  bindProducts();
  $("#catalog-search")?.addEventListener("input", (e) => {
    state.search = e.target.value;
    clearTimeout(searchOffers.timer);
    searchOffers.timer = setTimeout(searchOffers, 300);
  });
  $("#catalog-store")?.addEventListener("change", (e) => {
    state.storeFilter = e.target.value;
    searchOffers();
  });
  $("#plan-day")?.addEventListener("change", (e) => {
    state.day = e.target.value;
    loadPlan();
  });
  $("#route-mode")?.addEventListener("change", (e) => {
    state.route = e.target.value;
    loadPlan();
  });
  $("#profile-form")?.addEventListener("submit", saveProfile);
  $("#app")
    .querySelectorAll("[data-locate]")
    .forEach((b) => (b.onclick = () => locate(b.dataset.locate)));
}
function bindProducts() {
  $("#app")
    .querySelectorAll("[data-offer]")
    .forEach(
      (b) =>
        (b.onclick = () =>
          itemModal(
            null,
            state.offers.find((o) => o.id === b.dataset.offer),
          )),
    );
  $("#app")
    .querySelectorAll("[data-history]")
    .forEach(
      (b) =>
        (b.onclick = async () => {
          try {
            const r = await api(
              "/history?id=" + encodeURIComponent(b.dataset.history),
            );
            openModal(
              "history",
              r.history.length
                ? `<div class="plan-products">${r.history.map((h) => `<div class="plan-product"><span>${new Date(h.observed).toLocaleString(locale)}</span><b>${money(h.price)}</b></div>`).join("")}</div><p class="muted">${t("historyEmpty")}</p>`
                : `<p>${t("historyEmpty")}</p>`,
            );
          } catch (err) {
            toast(err.message);
          }
        }),
    );
}
let searchSeq = 0;
async function searchOffers() {
  const seq = ++searchSeq;
  try {
    await loadOffers();
    if (seq === searchSeq && $("#catalog-results")) {
      $("#catalog-results").innerHTML = renderProducts();
      bindProducts();
      $("#catalog-results")
        .querySelectorAll("[data-action]")
        .forEach((b) => (b.onclick = () => action(b.dataset.action)));
    }
  } catch (err) {
    toast(state.offline ? t("offline") : err.message);
  }
}
async function saveProfile(e) {
  e.preventDefault();
  const f = e.target,
    d = Object.fromEntries(new FormData(f)),
    p = structuredClone(state.profile);
  for (const k of [
    "home",
    "work",
    "locale",
    "budget",
    "interval_hours",
    "max_stops",
    "cost_per_km",
  ])
    p[k] = d[k];
  for (const key of ["home", "work"])
    if (d[key] !== state.profile[key] && located[key] !== d[key])
      p[key + "_coords"] = null;
  p.countries = ["PT", "ES"].filter((c) => f.elements["country-" + c].checked);
  p.automatic = f.automatic.checked;
  p.workdays = Array.from({ length: 7 }, (_, i) => i).filter(
    (i) => f.elements["workday-" + i].checked,
  );
  for (const s of state.stores) {
    const v = p.stores[s.id];
    for (const k of ["enabled", "card", "subscription", "access"])
      v[k] = !!f.elements[`${s.id}-${k}`]?.checked;
    if (
      v.address !== d[s.id + "-address"] &&
      located[s.id] !== d[s.id + "-address"]
    )
      v.coords = null;
    v.address = d[s.id + "-address"];
    v.extra_km = d[s.id + "-extra_km"] === "" ? null : +d[s.id + "-extra_km"];
    v.coupons = d[s.id + "-coupons"]
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
  }
  try {
    const r = await api("/profile", "PUT", p);
    state.profile = r.profile;
    locale = r.profile.locale;
    localStorage.setItem("despensa-locale", locale);
    saveSnapshot();
    toast(t("saved"));
    await loadOffers();
    render();
    loadPlan();
  } catch (err) {
    toast(err.message);
  }
}
async function locate(key) {
  const input =
    key === "home" || key === "work"
      ? $("#f-" + key)
      : $("#f-" + key + "-address");
  if (!input?.value.trim()) return input?.focus();
  try {
    const r = await api("/geocode?q=" + encodeURIComponent(input.value));
    openModal(
      "chooseLocation",
      `<div class="plan-products">${r.results.map((x, i) => `<button class="quiet" data-place="${i}">${icon("pin")}<span>${esc(x.label)}</span></button>`).join("") || t("noResults")}</div>`,
    );
    $("#modal")
      .querySelectorAll("[data-place]")
      .forEach(
        (b) =>
          (b.onclick = () => {
            const place = r.results[+b.dataset.place];
            input.value = place.label;
            located[key] = place.label;
            if (key === "home" || key === "work")
              state.profile[key + "_coords"] = place.coords;
            else state.profile.stores[key].coords = place.coords;
            $("#coords-" + key).textContent = place.coords.join(", ");
            $("#modal").close();
          }),
      );
  } catch (err) {
    toast(err.message);
  }
}
let installPrompt = null;
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  installPrompt = e;
});
async function action(name) {
  try {
    if (name === "add") return itemModal();
    if (name === "manual") return manualModal();
    if (name === "shopping") {
      state.shopping = !state.shopping;
      return render();
    }
    if (name === "plan") return loadPlan();
    if (name === "install") {
      if (installPrompt) {
        await installPrompt.prompt();
        installPrompt = null;
      } else toast(t("installHelp"));
      return;
    }
    if (name === "refresh") {
      await api("/refresh", "POST", {});
      toast(t("refreshQueued"));
      state.status = await api("/status");
      render();
      return;
    }
    if (name === "copy") {
      const [y, m] = state.month.split("-").map(Number);
      const previous = new Date(y, m - 2, 1);
      const source = `${previous.getFullYear()}-${String(previous.getMonth() + 1).padStart(2, "0")}`;
      const r = await api("/items/copy", "POST", {
        source,
        target: state.month,
      });
      toast(t(r.copied ? "copyDone" : "noPrevious"));
      return load();
    }
    if (name === "logout") {
      await api("/auth/logout", "POST", {});
      localStorage.removeItem(uidKey());
      localStorage.removeItem(uidKey() + "-queue");
      localStorage.removeItem("despensa-last-user");
      state.user = null;
      state.items = [];
      state.offers = [];
      state.plan = null;
      render();
      return;
    }
  } catch (err) {
    toast(err.message);
  }
}
window.addEventListener("online", async () => {
  await flushQueue();
  await load();
});
window.addEventListener("offline", () => {
  state.offline = true;
  render();
});
$("#modal").addEventListener("click", (e) => {
  if (e.target === $("#modal")) $("#modal").close();
});
if ("serviceWorker" in navigator && window.isSecureContext)
  navigator.serviceWorker.register("/sw.js").catch(() => {});
setInterval(async () => {
  if (!state.user || state.offline || document.hidden) return;
  try {
    const previous = JSON.stringify(state.status.jobs);
    const status = await api("/status");
    state.status = status;
    if (
      previous !== JSON.stringify(status.jobs) &&
      state.view !== "profile" &&
      !$("#modal").open
    ) {
      await loadOffers();
      saveSnapshot();
      render();
      loadPlan();
    }
  } catch {}
}, 15000);
load();
