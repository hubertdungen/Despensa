# Despensa · compras con sentido

[Português](../README.md) · [Fuentes y metodología](SOURCES.md)

Despensa es una aplicación personal que puede alojar en un ordenador o NAS para organizar la lista mensual, consultar precios observados y preparar un plan de compra. Interfaz en portugués europeo y español, diseño para móvil y escritorio, logo propio e instalación como PWA.

## Instalación

```sh
git clone https://github.com/hubertdungen/Despensa.git
cd Despensa
docker compose up -d --build
```

Abra `http://IP-DEL-SERVIDOR:8108` y cree su cuenta. Los datos quedan en un volumen Docker. Para instalar en el teléfono y usar la lista sin conexión, necesita **HTTPS válido**. En Android/PC, use la opción de instalación del navegador. En iPhone: **Compartir → Añadir a pantalla de inicio**.

## Funciones actuales

- Listas mensuales privadas por cuenta, cantidades, categorías, notas y fechas; repetir el mes anterior.
- Modo de compra con controles grandes y cambios offline que se sincronizan al recuperar conexión y con una sesión válida.
- Recogida diaria en el servidor, intervalo configurable entre 6 y 168 horas y actualización manual, con al menos 15 minutos entre recogidas.
- Precios con fuente, fecha e historial; registro manual de precios físicos de Portugal y España.
- Tiendas, tarjetas, suscripciones, acceso profesional y códigos de cupones en el perfil.
- Comparación de cestas en hasta tres tiendas, comprando envases enteros. Identifica cestas incompletas y saldo futuro, sin descontarlo del importe a pagar hoy.
- Estimación de desvíos por carretera desde casa o de regreso del trabajo según la fecha, con coordenadas elegidas por el usuario. Sin coordenadas, puede indicar kilómetros adicionales estimados.
- Exportación de datos en JSON. Todavía no hay importación/restauración desde la interfaz.

## Cobertura y límites

La recogida automática inicial cubre algunas categorías de **Continente y Auchan en Portugal**, hasta 36 referencias de la primera página de cada categoría. **España admite precios manuales, pero todavía no tiene un conector automático activo.** No se utiliza la API de Mercadona ni la búsqueda restringida de Continente. No se eluden bloqueos ni autenticaciones.

Los precios online pueden diferir de los de tiendas físicas. Las observaciones de más de 72 horas quedan fuera de los planes. Para fechas futuras, solo entran ofertas con vigencia explícita. Las ofertas de condiciones ambiguas no se utilizan en la optimización. Los cupones requieren su código concreto: tener tarjeta no confirma que tenga un cupón personalizado.

Las alternativas genéricas se buscan por palabras; **no se garantiza equivalencia de marcas, calidad o nutrición**. Añadir un producto del catálogo fija esa referencia concreta. Las ofertas de compra mínima o combinaciones complejas no se interpretan automáticamente: registre solo condiciones que pueda cumplir. Los precios sin IVA no entran en los planes.

Con distancias desconocidas, el total incluye solo productos. Los kilómetros manuales se suman como estimaciones. Las rutas por carretera usan OSRM, hasta tres paradas, sin tráfico en tiempo real ni tiempo de estancia. No hay instaladores `.exe` o `.apk` publicados: la versión instalable actual es la PWA.

## Privacidad

Los datos personales quedan en la instalación. Los precios públicos automáticos se comparten entre sus cuentas para reducir peticiones. Use una zona o lugar público cercano, sin datos personales. Al pulsar **Localizar**, el texto se envía a Nominatim, sujeto a su [política de uso](https://operations.osmfoundation.org/policies/nominatim/) (consultas manuales, sin autocompletar, con caché y máximo una por segundo); al abrir el plan con coordenadas guardadas, estas se envían a OSRM. Ambos utilizan datos [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright). No se solicitan contraseñas de supermercados, ubicación GPS ni números de tarjetas de cliente.

No cierre sesión con cambios pendientes de sincronizar: cerrar sesión elimina la copia local del dispositivo. Si la sesión caduca, vuelva a entrar en la misma cuenta. Para desactivar nuevos registros después de crear las cuentas necesarias, establezca `DESPENSA_REGISTRATION: "false"` en Compose y aplique `docker compose up -d`.

## Desarrollo y licencia

Python 3.12+, Flask/Waitress, SQLite, HTML/CSS/JavaScript sin compilación. Consulte el [README principal](../README.md) para pruebas, backups, configuración y hoja de ruta. Los conectores, reglas de comparación y contribuciones se documentan por separado.

Licencia **AGPL-3.0-or-later**, gratuita para uso personal y también utilizable comercialmente conforme a sus condiciones. El código no concede derechos sobre datos, marcas o contenidos de terceros.
