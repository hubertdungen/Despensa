# Despensa · compras con sentido

[Português](../README.md) · [Fuentes y metodología](SOURCES.md) · [Authelia y Rumo](../integrations/README.md)

Despensa organiza la compra mensual y **busca precios automáticamente** en supermercados de Portugal y España. Se aloja en un ordenador o NAS, tiene interfaz en portugués europeo y español, diseño para móvil/escritorio, logo propio e instalación como PWA.

## Instalación

```sh
git clone https://github.com/hubertdungen/Despensa.git
cd Despensa
docker compose up -d --build
```

Abra `http://IP-DEL-SERVIDOR:8108` y cree una cuenta local, o configure entrada directa con Authelia. Los datos quedan en un volumen Docker. Para instalar en el teléfono y usar la lista sin conexión, necesita **HTTPS válido**. En Android/PC, use la instalación del navegador; en iPhone, **Compartir → Añadir a pantalla de inicio**. Los instaladores `.exe` y `.apk` todavía están pendientes.

## Funciones actuales (0.5)

- Listas mensuales privadas, cantidades, notas, fechas y repetición del mes anterior. Modo de compra y cambios offline que se sincronizan con una sesión válida.
- Investigación prioritaria al añadir o buscar productos, independiente de la recogida general. Busca también marcas, plurales, prefijos y pequeños errores de escritura; permite elegir Portugal/España y cargar más resultados. El progreso y los precios nuevos aparecen sin recargar la página.
- Investigación automática al añadir o buscar productos. Vocabulario ibérico para palabras como leche/leite y aceite/azeite; sugerencias de familias con alternativas de varias tiendas.
- Varios métodos de lectura: catálogos, JSON-LD, datos de producto embebidos, microdatos y descubrimiento en mapas oficiales del sitio. La cola persiste, reparte consultas entre productos y continúa donde se quedó.
- Reintentos progresivos cuando una fuente falla, conservando observaciones anteriores. El radar muestra el estado de cada cadena, métodos utilizados, páginas descubiertas y siguiente intento.
- Fotografías de productos, comparación inmediata por litro/kg/unidad, mejor precio observado, fuente, fecha e historial.
- Tarjetas, acceso profesional y programas reales en el perfil. EntregaZero es una suscripción de entregas: no presupone descuentos en productos. Tener tarjeta tampoco implica tener un cupón personalizado.
- Detección de tiendas cerca de **casa y trabajo**, por separado. Los kilómetros, desvíos y orden de hasta tres paradas se calculan automáticamente; contempla trabajo→tiendas→casa según la fecha y los días de trabajo.
- Presupuesto mensual desde Rumo, si se configura la integración de lectura. Sigue el mes seleccionado, con una exportación limitada a supermercado y cuentas explícitamente autorizadas.
- Gastos y ahorro mensual a partir de compras registradas y una referencia guardada en la fecha de compra. Los costes adicionales de desplazamiento y los datos que faltan se muestran por separado.
- Exportación de datos en JSON; todavía no hay importación/restauración desde la interfaz.

La versión 0.4 corrige los precios por kg de fruta y carne fresca, busca marcas y formatos aunque no aparezcan en el URL, consulta la búsqueda pública de Auchan y separa los precios Lidl Plus. Los totales al peso son estimados y respetan los mínimos y pesos nominales publicados. El catálogo público de Makro ES aporta precios con IVA del centro Barajas; se muestran con su ubicación y no entran en el plan sin confirmar el centro.

## Cobertura y límites reales

El motor tiene fuentes de investigación para Continente, Auchan, Pingo Doce, Lidl PT/ES, Aldi PT/ES, Intermarché, Mercadona PT/ES, Makro PT/ES, Recheio, Carrefour, DIA, Eroski y Alcampo. **No se exige registrar precios manualmente para utilizar España u otras cadenas.** El registro manual sigue disponible como opción para una observación física.

Una fuente configurada no garantiza un catálogo completo. En la validación 0.2 se extrajeron precios reales de Continente, Auchan, Pingo Doce, Lidl Portugal, Aldi Portugal/España, DIA y Lidl España. Algunas otras fuentes devolvieron restricciones de acceso, páginas sin precios o solo mapas del catálogo. El radar conserva ese estado y programa nuevos intentos; no se inventan resultados. El catálogo público alternativo de Makro PT permite descubrir productos, pero sigue exigiendo sesión de la tienda para mostrar precios. El folleto oficial de Recheio aporta precios Cash **sin IVA**, con fechas explícitas: se muestran identificados y se excluyen del plan personal. Authelia no sustituye esa cuenta. No se eluden autenticaciones ni CAPTCHAs.

Los precios online pueden variar por región o tienda física. Las observaciones de más de 72 h quedan fuera del plan; para fechas futuras se exige vigencia explícita. Se compran envases enteros. Las familias no garantizan equivalencia de marcas, nutrición o calidad; leche desnatada, semidesnatada, sin lactosa, fresca y ecológica se separan cuando hay información suficiente. Las condiciones desconocidas se excluyen y el saldo futuro no reduce lo pagado hoy.

Para medir ahorro, confirme el precio pagado y elija una tienda habitual o referencia confirmada. Las compras sin referencia cuentan para gastos pero no para ahorro. Las compras offline/pasadas no reciben retroactivamente precios automáticos actuales. Los costes de viaje solo se descuentan cuando se registran; las estimaciones y los totales parciales se identifican.

Elegir una ubicación con Localizar guarda inmediatamente la dirección y las coordenadas. El plan explica si falta casa, trabajo, una sucursal cercana o la respuesta del servicio. Si falla el servicio de rutas, la distancia queda por confirmar y el total es solo de productos. La búsqueda cercana usa localizadores oficiales de Continente/Auchan y Overpass para ampliar cobertura; las limitaciones se muestran. No hay tráfico en tiempo real.

## Privacidad y desarrollo

Listas, perfiles, compras y precios manuales pertenecen a cada cuenta. El catálogo público se comparte entre las cuentas de la instalación. Las fotos se sirven por un proxy limitado a dominios identificados; no se comparten cookies con supermercados. Los textos/coordenadas necesarios se envían a Nominatim, Overpass y OSRM para localizar zonas, tiendas y rutas. Puede configurar servicios propios. Datos geográficos [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright).

No cierre sesión con cambios pendientes: cerrar sesión elimina la copia local del dispositivo. Para desactivar nuevos registros, establezca `DESPENSA_REGISTRATION: "false"`. El modo Authelia exige un secreto entre proxy y aplicación y permite gestionar passkeys de Bitwarden y llaves FIDO2 en el portal de identidad.

Python 3.12+, Flask/Waitress, SQLite y HTML/CSS/JavaScript sin compilación. Consulte el [README principal](../README.md) para pruebas, backups y hoja de ruta. Licencia **AGPL-3.0-or-later**, gratuita para uso personal y utilizable comercialmente según sus condiciones. El código no concede derechos sobre los datos, fotografías o marcas de las tiendas.

En la versión 0.5 las sugerencias incluyen referencias específicas como Café Delta y cereales Fitness. Al elegirlas se rellenan categoría, unidad y cantidad publicada sin sobrescribir cantidades ya editadas. La búsqueda tiene en cuenta “Línea y fibra” como categoría comercial cuando está publicada y marca los resultados relacionados cuando la categoría no está disponible. Se conservan la marca y restricciones como “sin azúcar”.
