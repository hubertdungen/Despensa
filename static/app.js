"use strict";
const APP_VERSION = "0.6.0";
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
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12ZM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6",
  eyeOff:
    "m3 3 18 18M10 5c7-1 12 7 12 7a20 20 0 0 1-4 4M6 6a20 20 0 0 0-4 6s4 7 10 7c2 0 3-1 4-1M10 10a3 3 0 0 0 4 4",
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
      "O radar investiga automaticamente produtos nas lojas de Portugal e Espanha, cruza vários métodos de recolha e volta a tentar quando uma fonte falha. Consulte o estado de cada loja.",
    noResults: "Ainda não encontrámos esse produto",
    noResultsText:
      "Pesquise outro nome, marca ou formato, ou volte a pesquisar nas lojas.",
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
      "Defina as zonas de casa e trabalho no perfil para calcular automaticamente os percursos rodoviários.",
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
    costKm: "Estimativa alternativa (€ / km)",
    routine: "A sua rotina",
    home: "Zona de casa",
    work: "Zona de trabalho",
    homeHint: "Morada ou zona, guardada apenas no seu perfil.",
    stores: "Os seus supermercados",
    storesHint: "Ative apenas as lojas onde pode e quer comprar.",
    enabled: "Usar esta loja",
    hasCard: "Tenho cartão",
    hasSubscription: "Tenho subscrição",
    deliveryPass: "Tenho EntregaZero (entregas)",
    deliveryOnly:
      "Serviço de entregas; não altera automaticamente o preço dos produtos.",
    budgetAuto: "Usar orçamento mensal do Rumo",
    budgetFromRumo: "Rumo · Supermercado",
    budgetMissing: "Sem orçamento para este mês no Rumo",
    budgetUnavailable: "Ligação ao Rumo por atualizar",
    manualBudget: "Orçamento manual (€ / mês)",
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
    showPassword: "Mostrar palavra-passe",
    hidePassword: "Ocultar palavra-passe",
    ssoLogin: "Entrar com Authelia",
    ssoHint:
      "Use a sua sessão Authelia. Não precisa de criar outra conta na Despensa.",
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
      "El radar investiga automáticamente productos en tiendas de Portugal y España, combina varios métodos de recogida y reintenta cuando una fuente falla. Consulte el estado de cada tienda.",
    noResults: "Todavía no encontramos ese producto",
    noResultsText:
      "Busque otro nombre, marca o formato, o vuelva a buscar en las tiendas.",
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
      "Defina las zonas de casa y trabajo en el perfil para calcular automáticamente las rutas por carretera.",
    profileTitle: "A su medida.",
    profileSubtitle: "Sus tiendas, sus tarjetas y su forma de comprar.",
    preferences: "Preferencias",
    locale: "Idioma",
    countries: "¿Dónde hace la compra?",
    budgetField: "Presupuesto (€ / mes)",
    interval: "Actualizar cada (horas)",
    auto: "Actualizar automáticamente en el servidor",
    stops: "Máximo de tiendas por visita",
    costKm: "Estimación alternativa (€ / km)",
    routine: "Su rutina",
    home: "Zona de casa",
    work: "Zona del trabajo",
    homeHint: "Dirección o zona, guardada solo en su perfil.",
    stores: "Sus supermercados",
    storesHint: "Active solo las tiendas donde puede y quiere comprar.",
    enabled: "Usar esta tienda",
    hasCard: "Tengo tarjeta",
    hasSubscription: "Tengo suscripción",
    deliveryPass: "Tengo EntregaZero (entregas)",
    deliveryOnly:
      "Servicio de entregas; no cambia automáticamente el precio de los productos.",
    budgetAuto: "Usar presupuesto mensual de Rumo",
    budgetFromRumo: "Rumo · Supermercado",
    budgetMissing: "Sin presupuesto para este mes en Rumo",
    budgetUnavailable: "Conexión con Rumo pendiente de actualizar",
    manualBudget: "Presupuesto manual (€ / mes)",
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
    showPassword: "Mostrar contraseña",
    hidePassword: "Ocultar contraseña",
    ssoLogin: "Entrar con Authelia",
    ssoHint:
      "Use su sesión Authelia. No necesita crear otra cuenta en Despensa.",
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
  auth: { mode: "local" },
  profile: null,
  budget: null,
  comparisons: [],
  nearby: null,
  savings: null,
  stores: [],
  items: [],
  offers: [],
  status: {},
  plan: null,
  search: "",
  storeFilter: "",
  countryFilter: "all",
  catalogOffset: 0,
  catalogHasMore: false,
  catalogTotal: 0,
  catalogApproximate: false,
  catalogLoading: false,
  catalogError: false,
  queryResearch: null,
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
        auth: state.auth,
        profile: state.profile,
        budget: state.budget,
        comparisons: state.comparisons,
        savings: state.savings,
        plan: state.plan,
        selectedPlan: state.selectedPlan,
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
    err.auth = result.auth;
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
  const quickInput = $("#quick-add input");
  const quickDraft = quickInput?.value || "";
  const quickFocused = quickInput && document.activeElement === quickInput;
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
    `<div class="shell"><aside class="sidebar"><a class="brand" href="/"><img src="/logo.svg" alt=""><div><strong>despensa<span>.</span></strong><span>${t("tagline")}</span></div></a>${nav()}<div class="side-note">${icon("leaf", "sprout")}<strong>${t("greeting")}</strong><p>${t("intro")}</p></div><div class="side-foot"><span class="dot"></span> Portugal & España <span>·</span> v${APP_VERSION}</div></aside><div class="workspace"><header class="topbar"><div class="breadcrumb">Despensa ${icon("chevron")}<b>${t(state.view)}</b></div><a class="mobile-brand" href="/"><img src="/logo.svg" alt="">despensa.</a><div class="top-actions"><span class="top-date">${new Date().toLocaleDateString(locale, { day: "numeric", month: "long" })}</span><button class="quiet small" data-action="refresh" title="${t("refresh")}" aria-label="${t("refresh")}" ${active ? "disabled" : ""}>${icon("refresh", active ? "spinner" : "")}<span class="refresh-label">${t(active ? "updating" : "refresh")}</span></button><button class="avatar" data-view="profile" title="${esc(state.user.username)}" aria-label="${t("profile")}">${esc(state.user.username.slice(0, 2).toUpperCase())}</button></div></header>${state.offline || readQueue().length ? `<div class="offline-banner" role="status">${state.offline ? t("offline") : `${readQueue().length} ${t("pending")}`}</div>` : ""}<main class="content" id="main">${{ list: renderList, explore: renderExplore, plan: renderPlan, profile: renderProfile }[state.view]()}</main></div></div>${nav(true)}`;
  bind();
  if (quickDraft && $("#quick-add input")) {
    $("#quick-add input").value = quickDraft;
    if (quickFocused) $("#quick-add input").focus({preventScroll:true});
  }
}
function renderAuth() {
  if (state.auth?.mode === "proxy") {
    $("#app").innerHTML =
      `<main class="auth-page" id="main"><section class="auth-story"><a class="brand" href="/"><img src="/logo.svg" alt=""><div><strong>despensa.</strong><span>${t("tagline")}</span></div></a><h1>${t("authStory").replace("\n", "<br>")}</h1><p>${t("authText")}</p>${heroArt()}</section><section class="auth-form"><div class="auth-box"><h2>${t("loginTitle")}</h2><p>${t("ssoHint")}</p>${state.auth.login_url ? `<a class="button-link primary" href="${esc(state.auth.login_url)}">${icon("shield")}${t("ssoLogin")}</a>` : ""}</div></section></main>`;
    return;
  }
  $("#app").innerHTML =
    `<main class="auth-page" id="main"><section class="auth-story"><a class="brand" href="/"><img src="/logo.svg" alt=""><div><strong>despensa.</strong><span>${t("tagline")}</span></div></a><div class="eyebrow">PORTUGAL & ESPAÑA</div><h1>${t("authStory").replace("\n", "<br>")}</h1><p>${t("authText")}</p>${heroArt()}</section><section class="auth-form"><div class="auth-box"><div class="auth-locale"><select id="auth-locale" aria-label="${t("locale")}"><option value="pt-PT" ${locale === "pt-PT" ? "selected" : ""}>Português</option><option value="es-ES" ${locale === "es-ES" ? "selected" : ""}>Español</option></select></div><h2>${t(state.registering ? "registerTitle" : "loginTitle")}</h2><p>${t(state.registering ? "registerHint" : "loginHint")}</p><form id="auth-form"><div class="field"><label for="username">${t("username")}</label><input id="username" name="username" autocomplete="username" required minlength="3" maxlength="80"></div><div class="field"><label for="password">${t("password")}</label><div class="password-input"><input id="password" type="password" name="password" autocomplete="${state.registering ? "new-password" : "current-password"}" required minlength="10" maxlength="256" placeholder="${t("passwordHint")}"><button type="button" id="toggle-password" class="quiet" aria-controls="password" aria-pressed="false" aria-label="${t("showPassword")}">${icon("eye")}</button></div></div><div class="auth-error" role="alert" id="auth-error"></div><button class="primary" type="submit">${t(state.registering ? "register" : "login")} ${icon("arrow")}</button></form><div class="auth-toggle">${t(state.registering ? "hasAccount" : "noAccount")} <button class="quiet" id="auth-toggle">${t(state.registering ? "login" : "register")}</button></div><div class="privacy-note">${icon("shield")}<span>${t("privacy")}</span></div></div></section></main>`;
  $("#toggle-password").onclick = () => {
    const visible = $("#password").type === "password";
    $("#password").type = visible ? "text" : "password";
    $("#toggle-password").setAttribute("aria-pressed", String(visible));
    $("#toggle-password").setAttribute(
      "aria-label",
      t(visible ? "hidePassword" : "showPassword"),
    );
    $("#toggle-password").innerHTML = icon(visible ? "eyeOff" : "eye");
  };
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
  const selected=state.selectedPlan;
  const p=selected&&!selected.stale&&!selected.expired?selected.plan:state.plan?.plans?.[0];
  return p?.selections?.find((s) => s.item_id === item.id);
}
function budgetSource() {
  const b = state.budget;
  if (!b || b.source !== "rumo") return t("budgetDetail");
  if (b.status === "month_missing") return t("budgetMissing");
  if (b.status !== "ok") return t("budgetUnavailable");
  return b.url
    ? `<a href="${esc(b.url)}" target="_blank" rel="noopener">${t("budgetFromRumo")} ↗</a>`
    : t("budgetFromRumo");
}
async function loadBudget() {
  const month = state.month;
  const r = await api("/budget?month=" + month);
  if (state.month === month) state.budget = r.budget;
}
function renderList() {
  const checked = state.items.filter((i) => i.checked).length;
  const groups = [
    ...new Set(state.items.map((i) => i.category || "Mercearia")),
  ];
  return `${title("monthList", "subtitle", monthPicker())}${renderSelectedJourney()}${state.shopping ? `<button class="quiet small" data-action="shopping">${icon("close")}${t("exitShopping")}</button>` : ""}<section class="hero"><div class="hero-text"><div class="eyebrow">${t("heroLabel")}</div><h2>${t("heroTitle").replace("\n", "<br>")}</h2><p>${t("heroText")}</p></div>${heroArt()}</section><div class="stats"><div class="stat"><div class="stat-icon">${icon("bag")}</div><div><div class="label">${t("items")}</div><div class="number">${state.items.length}</div><div class="detail">${checked} ${t("done")}</div></div></div><div class="stat"><div class="stat-icon">${icon("wallet")}</div><div><div class="label">${t("budget")}</div><div class="number">${state.budget?.amount_cents == null ? "—" : money(state.budget.amount_cents)}</div><div class="detail" id="budget-source">${budgetSource()}</div></div></div><div class="stat"><div class="stat-icon">${icon("search")}</div><div><div class="label">${t("prices")}</div><div class="number">${state.status.offer_count || 0}</div><div class="detail">${t("pricesDetail")}</div></div></div>${renderSavingsStat()}</div><div class="dashboard-grid"><section class="panel"><div class="panel-head"><div><h2>${t("yourList")}</h2><p>${t("listHint")}</p></div><button class="primary small" data-action="add">${icon("plus")}${t("add")}</button></div>${
    state.items.length
      ? groups
          .map(
            (group) =>
              `<div class="section-title">${esc(categoryName(group))}</div>${state.items
                .filter((i) => (i.category || "Mercearia") === group)
                .map((item) => {
                  const receipt = state.savings?.purchases?.find(
                    (p) => p.item_id === item.id,
                  );
                  const choice = receipt
                    ? {
                        cost_cents: receipt.paid_cents,
                        offer: { store: receipt.store, name: item.name },
                      }
                    : bestForItem(item);
                  return `<div class="item ${item.checked ? "checked" : ""}"><button class="check ${item.checked ? "done" : ""}" data-check="${item.id}" aria-label="${esc(item.name)}" aria-pressed="${!!item.checked}">${item.checked ? icon("check") : ""}</button>${offerVisual(choice?.offer, item.name)}<div class="item-info"><div class="item-name">${esc(item.name)}</div><div class="item-meta"><span>${item.quantity} ${esc(choice?.quantity_basis === "packages" ? ft(item.quantity === 1 ? "package" : "packages") : item.unit)}</span>${item.needed_on ? `<span>${dateText(item.needed_on)}</span>` : ""}${item.offer_id ? `<span>${icon("pin")}</span>` : ""}</div></div><div class="item-price">${choice ? money(choice.cost_cents) : "—"}<small>${choice ? `${receipt ? ft("paidShort") + " · " : ""}${esc(storeName(choice.offer.store))}` : t("noPrice")}</small></div><button class="quiet more" data-edit="${item.id}" aria-label="${t("edit")}: ${esc(item.name)}">${icon("more")}</button></div>`;
                })
                .join("")}`,
          )
          .join("")
      : empty(
          "emptyTitle",
          "emptyText",
          `<button class="quiet small" data-view="explore">${t("browse")}${icon("arrow")}</button>`,
        )
  }<form class="add-row" id="quick-add"><input name="name" required maxlength="160" placeholder="${t("quickAdd")}" aria-label="${t("product")}"><button class="primary" type="submit" aria-label="${t("add")}">${icon("plus")}</button></form><div class="list-foot"><span>${checked} / ${state.items.length} ${t("done")}</span><button class="quiet small" data-action="shopping">${icon("bag")}${t(state.shopping ? "exitShopping" : "shopping")}</button></div></section><aside class="right-stack"><section class="insight">${icon("spark")}<h3>${t("smartTitle")}</h3><p>${t("smartText")}</p><button data-view="plan">${t("seePlan")}${icon("arrow")}</button></section><section class="panel"><div class="panel-head"><div><h3>${t("sources")}</h3><p>${t("sourceHint")}</p></div></div><div class="panel-body">${renderRadar()}<div class="source-row"><div class="store-mark">${icon("plus")}</div><div><div class="store-name">${t("manualPrice")}</div><small>Portugal · España</small></div><button class="quiet small" data-action="manual" aria-label="${t("manualPrice")}">${icon("arrow")}</button></div></div></section><div class="privacy-note">${icon("shield")}<span>${t("privacy")}</span></div></aside></div><div class="toolbar mt16"><button class="quiet small" data-action="copy">${icon("calendar")}${t("copyMonth")}</button><button class="quiet small" data-action="install">${icon("download")}${t("install")}</button></div>`;
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
  return `${title("catalogTitle", "catalogSubtitle")}<div class="toolbar"><div class="search-wrap">${icon("search")}<input id="catalog-search" value="${esc(state.search)}" placeholder="${t("searchPlaceholder")}" aria-label="${t("filter")}"></div><select id="catalog-country" aria-label="${ft("searchCountries")}"><option value="all" ${state.countryFilter === "all" ? "selected" : ""}>Portugal + España</option><option value="PT" ${state.countryFilter === "PT" ? "selected" : ""}>Portugal</option><option value="ES" ${state.countryFilter === "ES" ? "selected" : ""}>España</option></select><select id="catalog-store" aria-label="${t("allStores")}"><option value="">${t("allStores")}</option>${state.stores
    .filter(
      (s) => state.countryFilter === "all" || s.country === state.countryFilter,
    )
    .map(
      (s) =>
        `<option value="${s.id}" ${s.id === state.storeFilter ? "selected" : ""}>${esc(s.name)} · ${s.country}</option>`,
    )
    .join(
      "",
    )}</select><button class="primary" type="button" data-research-now>${icon("search")}${ft("searchShops")}</button></div><div class="notice">${icon("shield")}<span>${t("coverage")}</span></div><details class="research-details"><summary>${t("sources")}</summary>${renderRadar(true)}</details><div id="search-status" role="status" aria-live="polite">${renderSearchStatus()}</div><div id="catalog-results">${renderProducts()}</div>`;
}
function renderProducts() {
  return renderComparisonProducts();
}
function renderPlan() { return renderJourneyPlan(); }
function field(name, label, value, type = "text", extra = "", hint = "") {
  return `<div class="field"><label for="f-${name}">${t(label)}</label><input id="f-${name}" name="${name}" type="${type}" value="${esc(value)}" ${extra}>${hint ? `<span class="hint">${t(hint)}</span>` : ""}</div>`;
}
function checkbox(name, label, checked) {
  return `<label class="checkbox-field"><input type="checkbox" name="${name}" ${checked ? "checked" : ""}>${t(label)}</label>`;
}
function renderProfile() {
  const p = state.profile;
  return `${title("profileTitle", "profileSubtitle")}<form id="profile-form"><div class="settings-grid"><section class="panel"><div class="panel-body"><h2 class="settings-title">${t("preferences")}</h2>${authSettings()}<div class="form-grid"><div class="field"><label for="f-locale">${t("locale")}</label><select name="locale" id="f-locale"><option value="pt-PT" ${locale === "pt-PT" ? "selected" : ""}>Português</option><option value="es-ES" ${locale === "es-ES" ? "selected" : ""}>Español</option></select></div>${field("budget", "manualBudget", p.budget, "number", 'min="0" max="100000" step="1"')}${field("interval_hours", "interval", p.interval_hours, "number", 'min="6" max="168" step="1"')}${field("max_stops", "stops", p.max_stops, "number", 'min="1" max="4" step="1"')}${field("cost_per_km", "costKm", p.cost_per_km, "number", 'min="0" max="10" step="0.01"')}${referenceStoreField()}<div class="field"><label>${t("countries")}</label>${checkbox("country-PT", "Portugal", p.countries.includes("PT"))}${checkbox("country-ES", "España", p.countries.includes("ES"))}</div></div>${state.budget?.rumo_available ? checkbox("budget_source_auto", "budgetAuto", p.budget_source !== "manual") : ""}<p class="muted">${budgetSource()}</p>${checkbox("automatic", "auto", p.automatic)}</div></section><section class="panel"><div class="panel-body"><h2 class="settings-title">${t("routine")}</h2><div class="field"><label for="f-home">${t("home")}</label><div class="toolbar"><input id="f-home" name="home" value="${esc(p.home)}" placeholder="Lisboa, Portugal"><button type="button" class="small" data-locate="home">${icon("pin")}${t("locate")}</button></div><small class="muted" id="coords-home">${p.home_coords ? esc(p.home_coords.join(", ")) : ""}</small></div><div class="field"><label for="f-work">${t("work")}</label><div class="toolbar"><input id="f-work" name="work" value="${esc(p.work)}" placeholder=""><button type="button" class="small" data-locate="work">${icon("pin")}${t("locate")}</button></div><small class="muted" id="coords-work">${p.work_coords ? esc(p.work_coords.join(", ")) : ""}</small></div><p class="privacy-note">${t("geocodeHint")}</p><p class="privacy-note"><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors</a> · <a href="https://operations.osmfoundation.org/policies/nominatim/" target="_blank" rel="noopener">Nominatim</a></p><div class="field"><label>${t("workdays")}</label><div class="toolbar">${Array.from({ length: 7 }, (_, i) => `<label class="checkbox-field"><input type="checkbox" name="workday-${i}" ${p.workdays.includes(i) ? "checked" : ""}>${new Intl.DateTimeFormat(locale, { weekday: "short" }).format(new Date(2026, 0, 5 + i))}</label>`).join("")}</div></div></div></section>${mobilitySettings()}<div class="wide" id="saved-branches-panel">${savedStoresPanel()}</div><section class="wide panel"><div class="panel-body" id="nearby-content">${renderNearby()}</div></section><section class="wide"><div class="page-title"><div><h2>${t("stores")}</h2><p>${t("storesHint")}</p></div></div><div class="store-settings">${state.stores
    .map((s) => {
      const v = p.stores[s.id];
      return `<section class="store-setting" data-store="${s.id}"><header><div><strong>${esc(s.name)}</strong> <span class="tag gray">${s.country}</span></div><span class="tag ${s.automatic ? "" : "gray"}">${researchLabel(s.id)}</span></header>${checkbox(`${s.id}-enabled`, "enabled", v.enabled)}<div class="checks">${s.loyalty ? checkbox(`${s.id}-card`, s.loyalty, v.card) : ""}${s.subscription?.kind === "delivery" ? checkbox(`${s.id}-delivery_subscription`, "deliveryPass", v.delivery_subscription) : ""}${s.professional ? checkbox(`${s.id}-access`, "hasAccess", v.access) : ""}</div>${s.subscription?.kind === "delivery" ? `<p class="privacy-note">${t("deliveryOnly")}</p>` : ""}<div class="field"><label for="f-${s.id}-address">${t("storeAddress")}</label><div class="toolbar"><input name="${s.id}-address" id="f-${s.id}-address" value="${esc(v.address)}"><button type="button" class="small" data-locate="${s.id}">${icon("pin")}${t("locate")}</button></div><small class="muted" id="coords-${s.id}">${v.coords ? esc(v.coords.join(", ")) : ""}</small></div>${field(`${s.id}-coupons`, "coupons", v.coupons.join(", "))}</section>`;
    })
    .join(
      "",
    )}</div></section></div><div class="form-actions"><button class="primary" type="submit">${icon("check")}${t("saveProfile")}</button></div></form><section class="panel mt24"><div class="panel-body"><h2 class="settings-title">${t("data")}</h2><div class="toolbar"><a href="/api/export" class="tag">${icon("download")}${t("export")}</a><button class="quiet small" data-action="install">${icon("download")}${t("install")}</button><button class="quiet small danger" data-action="logout">${icon("logout")}${t("logout")}</button></div></div></section>`;
}
function openModal(head, html) {
  $("#modal-content").innerHTML =
    `<div class="modal-header"><h2>${t(head)}</h2><button class="quiet" data-close aria-label="${t("close")}">${icon("close")}</button></div>${html}`;
  if (!$("#modal").open) $("#modal").showModal();
  $("#modal [data-close]").onclick = () => $("#modal").close();
  $("#modal")
    .querySelectorAll("[data-cancel]")
    .forEach((b) => (b.onclick = () => $("#modal").close()));
}
function itemModal(item = null, offer = null, quickName = "", group = null) {
  const d = item ? structuredClone(item) : {
    name: group?.label || offer?.name || quickName,
    query: group?.query || offer?.name || quickName,
    quantity: offer?.size || 1,
    unit:
      group?.unit ||
      offer?.unit ||
      (/leite|leche|azeite|aceite/i.test(quickName)
        ? "l"
        : /arroz|massa|pasta/i.test(quickName)
          ? "kg"
          : "un"),
    category: "Mercearia",
    needed_on: "",
    note: "",
    offer_id: group ? "" : offer?.id || "",
    family: group?.key || "",
    ...(group?.details || offer?.details || {}),
  };
  openModal(
    item ? "edit" : "add",
    `<form id="item-form"><div class="form-grid">${field("name", "product", d.name, "text", 'required maxlength="160"')}${field("query", "query", d.query, "text", 'required minlength="2" maxlength="120"', "queryHint")}<div class="field full"><div id="item-suggestions" class="item-suggestions" aria-live="polite"></div></div>${field("quantity", "quantity", d.quantity, "number", 'required min="0.001" max="10000" step="0.001"')}<div class="field"><label for="f-unit">${t("unit")}</label><select id="f-unit" name="unit">${["un", "kg", "l"].map((u) => `<option ${d.unit === u ? "selected" : ""}>${u}</option>`).join("")}</select></div><div class="field"><label for="f-category">${t("category")}</label><select id="f-category" name="category">${["Mercearia", "Laticínios", "Frescos", "Casa e limpeza", "Outros"].map((c) => `<option value="${esc(c)}" ${d.category === c ? "selected" : ""}>${esc(categoryName(c))}</option>`).join("")}</select></div>${field("needed_on", "needed", d.needed_on, "date")}<p class="field full muted">${ft("packageHint")}</p><div class="field full"><label for="f-note">${t("note")}</label><textarea id="f-note" name="note" maxlength="300">${esc(d.note)}</textarea></div></div><div class="notice">${icon("search")}<span id="item-kind">${t(d.offer_id ? "lockedItem" : "genericItem")}</span></div><div class="form-actions">${item ? `<button type="button" class="quiet" id="record-item-purchase">${icon("wallet")}${ft("addPurchase")}</button><button type="button" class="quiet danger" id="delete-item">${icon("trash")}${t("delete")}</button>` : ""}<button type="button" data-cancel>${t("cancel")}</button><button class="primary" type="submit">${t("save")}</button></div></form>`,
  );
  setupItemSuggestions(d, !item);
  $("#item-form").onsubmit = async (e) => {
    e.preventDefault();
    const v = Object.fromEntries(new FormData(e.target));
    v.quantity = +v.quantity;
    v.offer_id = d.offer_id || "";
    v.family = d.family || "";
    v.checked = !!d.checked;
    const id = item?.id || newId();
    const payload = { ...v, month: state.month, client_id: id };
    if (item) {
      state.items = state.items.map((i) => (i.id === id ? { ...i, ...v } : i));
    } else state.items.push({ ...v, id });
    $("#modal").close();
    $("#quick-add")?.reset();
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
    $("#record-item-purchase").onclick = () =>
      purchaseModal(item, bestForItem(item));
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
      )}</select></div>${field("price", "price", "", "number", 'required min="0.01" max="100000" step="0.01"')}${field("size", "size", 1, "number", 'required min="0.001" max="10000" step="0.001"')}<div class="field"><label for="f-unit">${t("unit")}</label><select id="f-unit" name="unit"><option>un</option><option>kg</option><option>l</option></select></div><div class="field"><label for="f-condition">${t("condition")}</label><select id="f-condition" name="condition">${["public", "card", "coupon", "professional"].map((c) => `<option value="${c}">${conditionLabel(c)}</option>`).join("")}</select></div>${field("coupon", "couponCode", "")}${field("balance", "balance", 0, "number", 'min="0" max="100000" step="0.01"')}${field("location", "location", "", "text", "required")}${field("valid_from", "from", today(), "date")}${field("valid_to", "until", "", "date")}${field("source_url", "sourceUrl", "", "url")}</div>${checkbox("vat_included", "vat", true)}<div class="notice">${icon("wallet")}<span>${t("manualNote")}</span></div><div class="auth-error" id="manual-error" role="alert"></div><div class="form-actions"><button type="button" data-cancel>${t("cancel")}</button><button class="primary" type="submit">${t("save")}</button></div></form>`,
  );
  setupManualConditions();
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
  queue.push({ id: newId(), method, path, data });
  localStorage.setItem(uidKey() + "-queue", JSON.stringify(queue));
  await flushQueue();
}
let syncing = null;
function flushQueue() {
  if (syncing) return syncing;
  if (!state.user) return Promise.resolve();
  syncing = drainQueue().finally(() => {
    syncing = null;
    saveSnapshot();
  });
  return syncing;
}
async function drainQueue() {
  const owner = uidKey();
  while (state.user && uidKey() === owner) {
    const job = readQueue()[0];
    if (!job) return;
    try {
      await api(job.path, job.method, job.data);
      state.offline = false;
    } catch (err) {
      if (err.network || err.status === 401) {
        state.offline = true;
        if (err.status === 401) toast(t("loginHint"));
        return;
      }
      toast(err.message);
    }
    if (uidKey() !== owner) return;
    // A new mutation may have been appended while this request was in flight.
    // Acknowledge this job against the current queue, never its old snapshot.
    const current = readQueue();
    const index = current.findIndex(entry => job.id ? entry.id === job.id : JSON.stringify(entry) === JSON.stringify(job));
    if (index >= 0) current.splice(index, 1);
    localStorage.setItem(owner + "-queue", JSON.stringify(current));
  }
}

async function loadOffers() {
  return fetchCatalog();
}
function catalogSignature() {
  return JSON.stringify([
    state.search,
    state.storeFilter,
    state.view === "explore" ? state.countryFilter : "profile",
  ]);
}
async function fetchCatalog({
  append = false,
  preserve = false,
  investigate = true,
} = {}) {
  const signature = catalogSignature();
  const offset = append ? state.catalogOffset : 0;
  const r = await api(
    "/offers?q=" +
      encodeURIComponent(state.search) +
      "&store=" +
      encodeURIComponent(state.storeFilter) +
      "&country=" +
      (state.view === "explore" ? state.countryFilter : "profile") +
      "&offset=" +
      offset +
      "&investigate=" +
      investigate,
  );
  if (signature !== catalogSignature()) return;
  state.catalogLoading = false;
  state.catalogError = false;
  const merge = (old, rows, key) =>
    Array.from(
      new Map([...old, ...rows].map((row) => [row[key], row])).values(),
    );
  const keep = (append || preserve) && state.catalogSignature === signature;
  state.offers = keep ? merge(state.offers, r.offers, "id") : r.offers;
  state.comparisons = keep
    ? merge(state.comparisons, r.comparisons || [], "key")
    : r.comparisons || [];
  state.catalogOffset = preserve && keep ? state.catalogOffset : r.next_offset;
  state.catalogHasMore = state.catalogOffset < r.group_total;
  state.catalogTotal = r.total;
  state.catalogApproximate = r.approximate;
  state.queryResearch = r.research;
  state.catalogSignature = signature;
  saveSnapshot();
}
let planSequence = 0;
function updatePlanProgress() {
  if(state.view!=="plan")return;
  const status=$("#plan-loading");
  if(status){
    status.hidden=!state.planLoading;
    const label=status.querySelector('strong');if(label)label.textContent=mt('phase_'+(state.planRun?.phase||'queued'));
    const phases=['queued','products','fuel','locations','roads','optimizing','traffic','transit','ready'];
    const bar=status.querySelector('progress');if(bar)bar.value=Math.min(95,10+Math.max(0,phases.indexOf(state.planRun?.phase||'queued'))*12);
  }
  const button=$('[data-action="plan"]');
  if(button){button.disabled=state.planLoading;button.innerHTML=icon('route',state.planLoading?'spinner':'')+mt(state.planLoading?'calculatingTrip':'calculateTrip');}
  document.querySelectorAll('[data-select-plan]').forEach(b=>b.disabled=!!state.planLoading);
}
async function loadPlan() {
  if (state.offline) return;
  const seq=++planSequence,roads=state.view==='plan',month=state.month;
  state.planLoading=roads;state.planError=null;
  if(roads)state.planRun={phase:'queued'};
  if(roads)render();
  updatePlanProgress();
  try {
    await flushQueue();
    if(state.offline||seq!==planSequence)return;
    if(!roads&&state.selectedPlan)await loadSelectedJourney();
    if(!roads){
      const result=await api(`/plan?month=${month}&day=${state.day}&route=${state.route}&roads=false`);
      if(seq!==planSequence||state.view==='plan'||month!==state.month)return;
      state.plan=result;state.planLoading=false;
      if(state.view==='list')render();return;
    }
    const response=await api('/plans','POST',{month,day:state.day,route:state.route,departure_time:state.departureTime||'',max_stops:state.planMaxStops||4,timezone:Intl.DateTimeFormat().resolvedOptions().timeZone});
    let run=response.run;
    while(seq===planSequence&&state.view==='plan'&&month===state.month){
      state.planRun=run;updatePlanProgress();
      if(run.status==='ready'){
        state.plan=run.result;state.planLoading=false;saveSnapshot();render();return;
      }
      if(['error','interrupted','superseded'].includes(run.status))throw new Error(run.error||t('error'));
      await new Promise(resolve=>setTimeout(resolve,700));
      if(seq!==planSequence||state.view!=='plan')return;
      run=(await api('/plans/'+run.id)).run;
    }
  }catch(err){
    if(seq!==planSequence)return;
    state.planLoading=false;state.planError=err.message;
    if(err.network)state.offline=true;
    if(state.view==='plan')render();else toast(err.message);
  }
}

async function load() {
  try {
    const me = await api("/me");
    state.user = me.user;
    state.auth = me.auth || { mode: "local" };
    state.profile = me.profile;
    state.stores = me.stores;
    locale = state.profile.locale;
    localStorage.setItem("despensa-locale", locale);
    localStorage.setItem("despensa-last-user", JSON.stringify(me.user));
    await flushQueue();
    const [items, status, offers, budget, savings] = await Promise.all([
      api("/items?month=" + state.month),
      api("/status"),
      api("/offers?q=" + encodeURIComponent(state.search)),
      api("/budget?month=" + state.month),
      api("/savings?month=" + state.month),
      loadSelectedJourney(),
    ]);
    state.items = items.items;
    state.status = status;
    state.offers = offers.offers;
    state.budget = budget.budget;
    state.savings = savings.savings;
    state.comparisons = offers.comparisons || [];
    state.offline = false;
    saveSnapshot();
    render();
    loadPlan();
  } catch (err) {
    if (err.status === 401) {
      if (err.auth) state.auth = err.auth;
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
          if (state.view === "profile") loadNearby();
          if (state.view === "explore") searchOffers();
          window.scrollTo(0, 0);
        }),
    );
  $("#app")
    .querySelectorAll("[data-action]")
    .forEach((b) => (b.onclick = () => action(b.dataset.action)));
  $("#month")?.addEventListener("change", async (e) => {
    state.month = e.target.value;
    state.budget = null;
    state.savings = null;
    state.plan = null;
    state.selectedPlan = null;
    try {
      const [r] = await Promise.all([
        api("/items?month=" + state.month),
        loadBudget(),
        loadSavings(),
        loadSelectedJourney(),
      ]);
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
          if (!i.checked && bestForItem(i))
            return purchaseModal(i, bestForItem(i));
          if (
            i.checked &&
            state.savings?.purchases?.some((p) => p.item_id === i.id)
          )
            return savingsModal();
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
  bindFeatureActions();
  bindJourneyActions();
  $("#catalog-search")?.addEventListener("input", (e) => {
    state.search = e.target.value;
    beginCatalogSearch();
    clearTimeout(searchOffers.timer);
    searchOffers.timer = setTimeout(searchOffers, 450);
  });
  $("#catalog-store")?.addEventListener("change", (e) => {
    state.storeFilter = e.target.value;
    searchOffers();
  });
  $("#catalog-country")?.addEventListener("change", (e) => {
    state.countryFilter = e.target.value;
    state.storeFilter = "";
    render();
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
  beginCatalogSearch();
  try {
    await loadOffers();
    if (seq === searchSeq && $("#catalog-results")) {
      $("#catalog-results").innerHTML = renderProducts();
      if ($("#search-status"))
        $("#search-status").innerHTML = renderSearchStatus();
      bindProducts();
      bindFeatureActions();
      $("#catalog-results")
        .querySelectorAll("[data-action]")
        .forEach((b) => (b.onclick = () => action(b.dataset.action)));
    }
  } catch (err) {
    if (seq === searchSeq) {
      state.catalogLoading = false;
      state.catalogError = true;
      if ($("#catalog-results")) $("#catalog-results").innerHTML = renderProducts();
      if ($("#search-status")) $("#search-status").innerHTML = "";
    }
    toast(state.offline ? t("offline") : err.message);
  }
}
function beginCatalogSearch() {
  state.catalogLoading = true;
  state.catalogError = false;
  if ($("#catalog-results")) $("#catalog-results").innerHTML = renderProducts();
  if ($("#search-status")) $("#search-status").innerHTML = renderSearchStatus();
}
async function saveProfile(e) {
  e.preventDefault();
  if(state.profileSaving)return;
  state.profileSaving=true;
  const saveButton=e.target.querySelector('[type="submit"]');
  saveButton.disabled=true;saveButton.textContent=mt("savingSettings");
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
  p.mobility = mobilityFormData();
  p.reference_store = d.reference_store || "";
  for (const key of ["home", "work"])
    if (d[key] !== state.profile[key] && located[key] !== d[key])
      p[key + "_coords"] = null;
  p.countries = ["PT", "ES"].filter((c) => f.elements["country-" + c].checked);
  p.automatic = f.automatic.checked;
  if (f.elements.budget_source_auto)
    p.budget_source = f.elements.budget_source_auto.checked ? "auto" : "manual";
  p.workdays = Array.from({ length: 7 }, (_, i) => i).filter(
    (i) => f.elements["workday-" + i].checked,
  );
  for (const s of state.stores) {
    const v = p.stores[s.id];
    for (const k of [
      "enabled",
      "card",
      "subscription",
      "delivery_subscription",
      "access",
    ])
      v[k] = !!f.elements[`${s.id}-${k}`]?.checked;
    if (
      v.address !== d[s.id + "-address"] &&
      located[s.id] !== d[s.id + "-address"]
    ) {
      v.coords = null;v.branch_id="";v.branch_name="";
    }
    v.address = d[s.id + "-address"];
    v.extra_km = null;
    v.coupons = d[s.id + "-coupons"]
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
  }
  try {
    const unresolved = await resolveRoutine(p);
    const r = await api("/profile", "PUT", p);
    state.profile = r.profile;
    locale = r.profile.locale;
    localStorage.setItem("despensa-locale", locale);
    saveSnapshot();
    toast(unresolved.length ? ft("locationsUnresolved") : t("saved"));
    state.profileSaving=false;
    render();
    await Promise.all([loadOffers(), loadBudget(), loadSavings()]);
    loadPlan();
    loadNearby(true);
  } catch (err) {
    toast(err.message);
  } finally {
    state.profileSaving=false;
    if(saveButton.isConnected){saveButton.disabled=false;saveButton.innerHTML=icon("check")+t("saveProfile");}
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
            else Object.assign(state.profile.stores[key],{coords:place.coords,address:place.label,branch_name:storeName(key),branch_id:""});
            $("#coords-" + key).textContent = place.coords.join(", ");
            const routine=key==='home'||key==='work';
            const payload=routine?{[key]:place.label,[key+'_coords']:place.coords}:{stores:{[key]:state.profile.stores[key]}};
            if(routine)state.profile[key]=place.label;
            api('/profile','PUT',payload).then(r=>{
              state.profile=r.profile;saveSnapshot();toast(t('saved'));
              if($('#saved-branches-panel'))$('#saved-branches-panel').innerHTML=savedStoresPanel();
              loadNearby(true);
            }).catch(err=>toast(err.message));
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
    if (name === "savings") return savingsModal();
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
      const result = await api("/auth/logout", "POST", {});
      localStorage.removeItem(uidKey());
      localStorage.removeItem(uidKey() + "-queue");
      localStorage.removeItem("despensa-last-user");
      state.user = null;
      state.items = [];
      state.offers = [];
      ++planSequence;state.plan = null;state.selectedPlan=null;state.planRun=null;
      if (result.redirect) {
        window.location.assign(result.redirect);
        return;
      }
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
// Native select/number controls can retarget clicks to the dialog. Only a gesture
// that starts and ends outside its bounds is a backdrop dismissal.
let backdropStart = false;
const outsideModal = (e) => {
  const r = $("#modal").getBoundingClientRect();
  return (
    e.clientX < r.left ||
    e.clientX > r.right ||
    e.clientY < r.top ||
    e.clientY > r.bottom
  );
};
$("#modal").addEventListener("pointerdown", (e) => {
  backdropStart = e.target === $("#modal") && outsideModal(e);
});
$("#modal").addEventListener("pointerup", (e) => {
  if (backdropStart && e.target === $("#modal") && outsideModal(e))
    $("#modal").close();
  backdropStart = false;
});
if ("serviceWorker" in navigator && window.isSecureContext)
  navigator.serviceWorker.register("/sw.js").catch(() => {});
setInterval(async () => {
  if (!state.user || state.offline || document.hidden) return;
  try {
    const previous = JSON.stringify(state.status.jobs);
    const oldBudget = JSON.stringify([
      state.budget?.amount_cents,
      state.budget?.status,
      state.budget?.source,
    ]);
    await loadBudget();
    const budgetChanged =
      oldBudget !==
      JSON.stringify([
        state.budget?.amount_cents,
        state.budget?.status,
        state.budget?.source,
      ]);
    const status = await api("/status");
    state.status = status;
    showAppUpdate(status.version);
    if (
      (previous !== JSON.stringify(status.jobs) || budgetChanged) &&
      state.view !== "profile" &&
      state.view !== "explore" &&
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
