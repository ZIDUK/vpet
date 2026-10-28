# Paquetes De Mascotas, Items Y Themes

## Objetivo

Revision 2026-10-23. Requisito aclarado por el usuario: otro vPet es una
mascota distinta recibida como huevo de premio, con vida propia y futura
participacion en breeding interno. No es una skin de la mascota activa.
El contrato publico, capacidades y maximos siguen por aprobar; no existe
un instalador disponible. La [arquitectura](architecture.md) separa clases
actuales de composicion/paquetes propuestos.
F1 implementa localmente [definiciones y resolver](content-definitions.md),
no descarga/activacion en placa. Objetivo solicitado: cuatro mascotas sujeto
a medicion; inventario compartido confirmado. Huevos/crianza inactiva siguen
por aprobar. [Decisiones actuales](product-decisions-2026-10-23.md).

Permitir que autores publiquen mascotas y themes en un catalogo web, que los
usuarios puedan previsualizarlos e instalarlos sin recompilar el firmware.
Requisito adicional del usuario (2026-10-23): recibir tambien items de otras
personas o proveedores. El Hub por USB propuesto debe separar instalacion
de contenido y acreditacion de unidades al inventario. No esta implementado.

LittleFS tiene 12451840 bytes de particion; no es espacio libre para instalar.
La ultima carga registrada dejo 659456 bytes libres tras overhead. No esta
demostrado que quepa otra linea completa. La viabilidad necesita presupuesto
real de arte compartido, individuos, huevos, journals, staging y recuperacion.

## Paquete, Mascota Y Huevo Son Cosas Diferentes

- **Paquete:** definicion y assets de una linea; se instala una vez por version.
- **Mascota:** individuo con ID propio, ADN, sexo futuro, progreso y referencia
  al contenido. Varias mascotas de la misma linea comparten arte, no progreso.
- **Huevo:** un individuo en fase de incubacion, con ID de premio o breeding,
  definicion de destino y padres cuando corresponda. Eclosionar no duplica
  el registro, la recompensa ni los archivos instalados.
- **Roster/incubadora:** administracion de individuos, distintos del catalogo
  de paquetes instalados. La reserva actual no implementa este sistema.

Los maximos de paquetes, mascotas y huevos se determinaran por separado.
El futuro limite de juego debe coexistir con comprobacion de bytes disponibles;
no prometer una cantidad sin medir dos paquetes completos y peores casos de
datos/journals. Un huevo puede ser pequeno en datos, pero su linea necesita
arte disponible para que nazca sin un fallo de recursos.

La decision de producto tambien debe cerrar crianza/incubacion de mascotas
inactivas. Inventario compartido: no copiar stock al cambiar individuo.
Se propone cargar en RAM solo el
individuo activo, sin simular ilimitados pets a la vez ni inventar progreso
durante un apagado sin reloj fiable.

## Contrato De Funcionamiento Comun Propuesto

El motor usa composicion: PetState/instancia para progreso, definiciones
inmutables para etapas, reglas comunes y AssetResolver para presentacion.
No se agrega una subclase C++ por cada criatura ni se compilan plugins externos.
Agregar un paquete compatible no cambia App, reglas o codigo de cada panel.

Primera version propuesta: nueva linea visual con los cinco roles de etapa
del juego actual. Definiciones versionadas identifican roles y nombres sin
usar nombres de especies como permisos. Las acciones se resuelven por clave:
idle, locomocion, comer, dormir, cansancio, enojo, entrenamiento, ataque,
guardia, dano, victoria/derrota y evolucion, segun capacidades del rol.

Cada clip declara recurso, dimensiones/canvas, frames, duracion, anclaje,
direccion y rango de loop si procede. El loop acostado no se presupone en
los frames 12..14 de todos los autores. Una variante opcional ausente puede
tener fallback explicito al mismo rol/accion compatible; una accion requerida
ausente bloquea instalacion, no modifica silenciosamente el juego.

El validador exige que el mismo contenido funcione en Home, Status,
Training/Tecnicas, Arena, Exploracion, arbol y detalle de Evolucion, incluyendo
retratos/siluetas y posicion de globos sobre bounds visibles. Animacion no
puede duplicar consumos/recompensas ni cambiar la duracion de una sesion.
No se altera el layout de Status como parte de esta propuesta documental.

El ruleset comun es del motor, no una autorizacion para que un paquete de
assets cambie EV, dano, recompensas o genetica. Lineas con otra topologia,
capacidades o tecnicas requieren otra version/entrega con balance aprobado.

## Recepcion De Premio Y Breeding Interno

Flujo objetivo: validar contenido -> instalar/confirmar paquete -> confirmar
premio -> crear huevo unico -> incubar -> eclosionar con el mismo ID.
Una transferencia no concede por si sola un premio: su recibo es independiente
y debe impedir cobrar dos veces. Emisor y verificacion de premios remotos
todavia no estan definidos; un archivo descargado no prueba una recompensa.

Con un dispositivo y dos individuos propios compatibles se puede planear
breeding interno sin radio. Hijo, padres, herencia y cooldown se confirman
en una transaccion local. Breeding entre boards mantiene el protocolo bilateral
propuesto por separado; no exige tener dos boards para la modalidad interna.

Capacidad llena o contenido no disponible no puede borrar mascotas ni cobrar
recursos sin entregar: conservar premio pendiente o rechazar antes de aceptar
segun politica aprobada. No asumir que el hijo de dos lineas tiene arte;
cerrar primero la regla de compatibilidad y seleccion de linea del descendiente.

## Enfoque recomendado

La plataforma se divide en tres piezas:

1. Catalogo web con previews, autor, licencia, versiones y archivos firmados.
2. Paquete declarativo `.vpetpack`, sin codigo ejecutable.
3. Instalador por USB/Web Serial inicialmente y descarga HTTPS posteriormente.

USB es el primer transporte propuesto; BLE actual no instala contenido.
No habilitar WiFi ni prometer aprovisionamiento por radio ya existente.

## Regalos E Items De Personas Y Proveedores

Requisito confirmado: poder recibir items de terceros. El transporte, modelo
de confianza y reglas de intercambio siguientes son propuestas por aprobar.

- **Definicion de item:** ID/version, nombre localizado, icono y efectos
  declarativos compatibles con el motor. No concede unidades al instalarse.
- **Entrega:** ID unico, emisor, destinatario, item/version y cantidad.
  Registra la acreditacion independientemente del paquete de recursos.
- **Proveedor:** entrega autorizada por un emisor reconocido. Una firma
  verifica procedencia/integridad, no concede permiso para efectos arbitrarios.
- **Persona:** distinguir regalar unidades propias (descontarlas al emisor)
  de crear/publicar una definicion. Ser autor de un item no autoriza emitir
  cantidades ilimitadas ni duplicar unidades ya existentes.

Primera ruta propuesta: el usuario abre el Hub, conecta por USB y revisa
emisor, item y cantidad antes de aceptar. Un enlace o QR puede localizar la
entrega, pero no sustituye la autorizacion ni la validacion en la board.
Primero soportar entregas verificadas de proveedores; transferencia entre
usuarios requiere despues un protocolo que coordine ambos inventarios.
BLE directo queda separado: la conectividad actual no transfiere items.

Flujo objetivo: validar autorizacion y destinatario -> comprobar compatibilidad,
stock y bytes -> preparar recursos -> acreditar entrega una sola vez ->
confirmar. Un reintento tras desconexion/reinicio no suma otra vez. Si falta
espacio o excede el stack, rechazar antes de consumir/canjear; no truncar ni
perder unidades silenciosamente. El stock compartido requiere migracion
unica desde una fuente autoritativa; no sumar snapshots de la misma bolsa.

El receptor mantiene un journal durable de entregas y recuperacion, con
presupuesto y politica de retencion; no prometer deduplicacion ilimitada con
un historial finito. Para impedir doble gasto entre dispositivos o despues de
restaurar una copia antigua hace falta un registro de canje coordinado o un
protocolo de propiedad equivalente. Firma y journal local solos no resuelven
ese caso. El Hub podria usar Internet desde el computador sin activar WiFi
en la placa; servidor, cuentas, claves y privacidad aun no estan definidos.

Efectos limitados a operaciones conocidas y balanceadas, sin scripts externos.
IDs y enums existentes se conservan; nuevos items necesitan un catalogo
versionado y migracion aprobada, no reinterpretar slots actuales. El plan de
pruebas debe cubrir replay, destinatario equivocado, emisor no autorizado,
stack lleno, corte en cada fase, reinicio y restauracion de respaldos.

## Formato propuesto

Propuesta, no formato publico implementado: `.vpetpack` seria un ZIP de distribucion.
El navegador o herramienta
de escritorio lo valida y envia sus archivos individualmente al dispositivo.

```text
manifest.json
preview.png
animations/idle.vpa
animations/walk.vpa
animations/eat.vpa
animations/punch.vpa
animations/sleep.vpa
animations/cast.vpa
animations/evolution.vpa
portraits/default.vpa
backgrounds/day.vpa
backgrounds/night.vpa
signature.json
```

Un paquete podria ser `pet`, `item`, `theme` o `bundle`. Son tipos propuestos,
no enums implementados. No todos requieren todos los archivos; una entrega
de unidades es un recibo independiente, no otro tipo de paquete ejecutable.

## Manifiesto minimo

Ejemplo historico orientativo, NO esquema final aceptado ni paquete instalable.
Ademas de estos campos hacen falta referencias de linea/rol y metadatos de
animacion descritos arriba, version de contrato de contenido, perfil de juego
requerido, capacidades obligatorias/opcionales y limites medibles. El
manifiesto generado hoy por build_tdisplay.py no implementa ese contrato.

```json
{
  "schema_version": 1,
  "package_id": "author.firemon",
  "package_type": "pet",
  "version": "1.0.0",
  "name": "Firemon",
  "author": "Author name",
  "license": "CC-BY-4.0",
  "min_firmware": "1.0.0",
  "display_profile": "tdisplay-240x135",
  "files": [
    {"path": "animations/idle.vpa", "sha256": "...", "bytes": 12345}
  ]
}
```

La especificacion final debe agregar especies, acciones, numero de frames,
duracion por frame, puntos de anclaje y relaciones de evolucion.

## Reglas de seguridad

- Solo datos: no C++, Python, JavaScript ni bytecode.
- Rutas relativas normalizadas; se rechazan `..` y rutas absolutas.
- Rechazar entradas duplicadas, enlaces y expansion desmedida del ZIP en el host.
- Limites estrictos de archivos, dimensiones, frames y bytes.
- SHA-256 para integridad de cada archivo.
- Firma del catalogo y de paquetes aprobados.
- La firma exige una raiz de confianza y politica de claves/revocacion;
  no esta implementada y un hash no acredita al autor ni el premio.
- Activacion atomica: el paquete incompleto nunca se vuelve activo.
- Rollback al paquete anterior si validacion o carga falla.
- Licencia y atribucion obligatorias.

## Almacenamiento en dispositivo

```text
/packs/<package_id>/<version>/manifest.json
/packs/<package_id>/<version>/...
```

Propuesta: un indice persistente referencia versiones instaladas y el roster
referencia cada individuo mediante ID y definicion/version. No se reservan
sin medir todos esos registros en los 20 KiB de NVS. La estrategia NVS/FS
para datos nuevos necesita diseno de recuperacion y presupuesto propios;
el guardado actual schema 3 permanece intacto.

No copiar sprites por individuo ni usar una ruta como identidad. No borrar
un paquete referenciado por mascota/huevo ni una version necesaria para
recuperar una transaccion. Actualizaciones son inmutables; contenido ausente
no reinicia la partida. Caches de paleta/icono/escena incluyen pack/version y
se invalidan al activar otra definicion.

Staging y rollback necesitan capacidad adicional real. Si no caben candidato,
contenido activo y margen de recuperacion, rechazar antes de escribir; no
reformatear LittleFS ni borrar recursos activos para aparentar una instalacion
atomica. Compartir/deduplicar recursos requiere contabilidad de referencias
y validacion, no se da por implementado.

## Instalacion fase 1: USB

El sitio puede usar Web Serial desde Chrome o Edge. El firmware expone un
protocolo de instalacion que:

1. consulta version y espacio;
2. abre una transaccion;
3. recibe manifiesto y archivos por bloques;
4. valida hashes y limites;
5. confirma o revierte;
6. activa el paquete seleccionado.

No se debe reemplazar toda LittleFS con cada instalacion porque eliminaria otros
paquetes. Tampoco se debe borrar NVS.

## Instalacion fase 2: WiFi

Ampliacion no aprobada ni habilitada; no condiciona la primera entrega USB.

El usuario elige contenido en la web y recibe un codigo corto. En el vPet
introduce ese codigo; el dispositivo consulta el catalogo por HTTPS, descarga el
paquete, verifica su firma y lo activa.

Esta opcion evita navegar un catalogo complejo en 240x135.

## Flujo para autores

1. Descargar una plantilla de paquete.
2. Agregar PNG fuente y metadata.
3. Ejecutar un validador local que produce VPA y previews.
4. Probar el paquete en el simulador.
5. Enviar el paquete al catalogo.
6. Ejecutar validacion automatica, licencia y moderacion.
7. Firmar y publicar una version inmutable.

## Compatibilidad

El contrato debe distinguir campos opcionales ignorables de capacidades
obligatorias. Rechazar requisitos desconocidos y versiones de esquema
mayores a las soportadas. Una nueva version del paquete nunca debe modificar en
sitio una version publicada; se publica con otro numero semantico.

## Estado de implementacion

El proyecto ya tiene VPA1, manifest generado, LittleFS y validacion de capacidad.
Tambien existe [vPet Hub local](vpet-hub.md): catalogo builtin animado e importacion
de definiciones F1 con validacion de metadatos. No es un catalogo publicado ni
valida paquetes distribuibles completos. La consulta USB (`HUB STATUS`) ya responde version y espacio y rechaza
cualquier otra orden; no esta cargada en la placa. Faltan el respaldo con
consentimiento, el esquema publico, el validador de paquetes/arte, firmas y
el gestor de instalaciones.
El [asistente Crear vPet](vpet-creator.md) ya genera una definicion F1 y un ZIP
de autor con PNG y BMP preparados, revisa sus graficos y permite borradores.
No publica ni firma paquetes ni acredita premios; su validacion no afirma
capacidad fisica ni sustituye el instalador.

F1 ya extrae la definicion builtin, resolver comun y metadatos de clips.
Siguen pendientes roster multi-individuo, premio/huevo idempotente y breeding
interno. Esas entregas se implementan por separado; no activar todo mediante
una reescritura general de PetState ni una migracion silenciosa de partidas.

## Orden Propuesto Y Prueba De Plug And Play

1. Reconciliar reglas y extraer definicion builtin sin cambiar comportamiento.
2. Hacer que todos los consumidores resuelvan etapas/acciones desde definicion;
   probar arte/nombres alternativos sin ramas nuevas por criatura.
3. Definir formato/validador y convertir dos paquetes completos; medir
   memoria, espacio real, duraciones, transparencia, escala y caches.
4. Disenar roster, premios/huevos, seleccion activa y migracion de reserva;
   cerrar capacidades e incubacion antes de recibir otro individuo en placa.
5. Implementar instalacion USB reanudable y activacion recuperable. Carga de
   paquetes con el mismo binario de firmware, sin recompilar por especie.
6. Probar breeding interno transaccional y despues el enlace entre boards.

Aceptacion: mismo firmware y dos paquetes distintos, recorriendo las nueve
opciones con iguales reglas y trazas de estado equivalentes; huevos/individuos
separados sin duplicar assets, premios, stock o progreso al reiniciar/cambiar.
Inyectar archivos corruptos, referencias faltantes, esquema incompatible,
datos excesivos, interrupciones y capacidad llena. Validar fisicamente memoria,
latencia, recuperacion y partidas; previews no bastan. La promesa plug and play
solo aplica al contrato probado, no a contenido arbitrario de otros proyectos.
