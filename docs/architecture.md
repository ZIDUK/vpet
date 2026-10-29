# Arquitectura de software

## Decision Aprobada: Persistencia Invisible

El 2026-10-29 el usuario aprobo registro pequeno recuperable y respaldo completo
al dormir/en reposo, sin interrumpir el juego ni presentar GUARDANDO. El alcance
incluye entrenamiento, combate, CLAIM, cuidado y ajustes; no basta ocultar un
texto ni cambiar una pausa por un spinner. La consolidacion tambien debe ceder
ante entradas y evitar contencion con el renderer.

El documento tecnico fue aprobado el 2026-10-29. La implementacion nueva usa
`VPCJ2` sobre la clave existente `colCare`: snapshot, inventario y hasta 64
experiencias consecutivas compactas se confirman juntos. `LearningRuntime`
reproduce esas experiencias sobre la politica base al reiniciar. El checkpoint
escribe primero la politica completa y despues una generacion `VPCL v2` con la
revision incorporada. Conservar el recibo antiguo es seguro: esa revision evita
reaplicarlo. No se retiran experiencias sin una referencia de politica nueva.
Se mantienen lectores `VPCJ1` / `VPCL v1`, NVS schema 3 y VPL1.

`App` tiene un solo escritor de capacidad uno, compartido por recibos y
checkpoint. La cola de ocho eventos conserva su orden; solo la presentacion se
anticipa, las mutaciones dependientes esperan la confirmacion. Un recibo
aceptado pero no confirmado se resuelve sin volver a concederlo. Un rechazo
real restaura el estado anterior y muestra un error recuperable. La tabla de
entrenamiento representa el resultado en RAM, no un acuse de durabilidad.

El mantenimiento se solicita al dormir o tras cinco segundos sin entradas. Los
adaptadores consultan cancelacion entre bloques de 256 bytes y antes de
publicar. La copia anterior se prepara y valida en `previous.bin.pending`
antes de reemplazarla atomicamente; cancelar no destruye generaciones validas.
Durante E/S completa se conserva el framebuffer presentado para evitar lecturas
de assets competidoras. La latencia de esa cancelacion y la continuidad visual
requieren medicion fisica, no se deducen de mover el trabajo a FreeRTOS.

La entrega se cargo firmware-only, conservando LittleFS. La observacion fisica
inicial mide p95 entrada-a-presentacion de 610 ms, fuera del objetivo de 100 ms;
no se declara fluidez ni aceptacion fisica. Las consultas completas de espacio
tardan unos 2.3 s y el mantenimiento aun retiene la imagen. Ver el informe
[de verificacion](superpowers/reviews/2026-10-29-invisible-progress-verification.md).
El baseline 64addc8 solo tenia cuidado compacto y una vista de guardado
en entrenamiento. Ver
[SPEC-GAME-FLUID-001](superpowers/specs/2026-10-29-invisible-progress-journal-design.md)
y su [plan](superpowers/plans/2026-10-29-invisible-progress-journal.md).

## Supervivencia Y Muerte Gradual: Piloto 2026-10-28

El core conserva la muerte por 15 lesiones acumuladas o seis horas herido.
Como piloto nuevo, hambre=0 o energia=0 inicia un reloj independiente de gracia
de 12 horas de cuidado activo; alimentar o recuperar energia por encima de cero
reinicia el reloj correspondiente. Sueño, pausa/frio, exploracion, huevos y
tiempo offline no cuentan para hambre/energia. El contador de lesion conserva
su regla anterior, incluso durante sueño. Las claves NVS `hunCritMs` y
`eneCritMs` usan cero por defecto para saves anteriores y se persisten en los
snapshots existentes, sin cambiar enums ni schema principal. Ver
[`SPEC-GAME-SURVIVAL-001`](superpowers/specs/2026-10-28-game-survival-death.md).

La compilacion y pruebas host no sustituyen la prueba fisica. La revision aun
no se ha flasheado; la validacion de las cuatro paginas Status exigida por
`AGENTS.md` sigue pendiente.

## Recuperacion Y Ciclo De Vida De Huevos: 2026-10-28

`App` conserva la propiedad del estado vivo y del TFT. Si un checkpoint no
puede confirmarse, la pantalla de reintento permite volver visualmente a Home
con BACK mientras los reintentos continúan. La persistencia sigue pendiente y
las acciones que mutan estado permanecen bloqueadas hasta que el almacenamiento
confirma el resultado; volver a Home no descarta, duplica ni da por guardada la
accion. Esto también cubre la recuperación tras una batalla. La implementación
no convierte el guardado en un servicio de dominio ni reejecuta la batalla.

`CollectionStore::discardEgg` elimina mediante el mismo commit atomico de la
coleccion solo huevos reservados: requiere confirmacion explicita, no admite el
slot activo y no muta memoria durable cuando falla la transaccion. La vista de
coleccion expone la confirmacion/cancelacion y muestra sexo desconocido (`?`)
para huevos. Los individuos conservan DNA0..3 y un locus DNA4 para sexo. En
datos antiguos el locus se migra desde el perfil sin modificar los cuatro bytes
previos; la coleccion y el snapshot versionado lo persisten. El cruce elige el
sexo parental con probabilidad proporcional a la suma de sus seis IV (empate
sin IV: 50/50), y lo fija en el huevo. La UI mantiene `?` hasta la eclosion. Ver
[`SPEC-GAME-GENETICS-BLE-001`](superpowers/specs/2026-10-28-sex-locus-ble-egg-transfer.md).

El cruce local ya crea una cria en forma de huevo cuando ambos padres son
elegibles y hay plaza: cuerpo con ADN heredado, referencias a ambos padres,
incubacion de 30 minutos y cooldown parental se confirman en la transaccion de
coleccion. Los tests verifican el ciclo y evitan duplicar la cria ante reintento;
esto no equivale a recepcion de huevos externos ni a un sistema de intercambio.
El huevo de fundador es una accion separada de prueba/creacion, no representa
un huevo recibido de otro usuario. Requisitos, criterios y limites estan en
[`SPEC-GAME-REC-001`](superpowers/specs/2026-10-28-battle-recovery-egg-lifecycle.md).

La persistencia de coleccion incluye un recibo atomico para importacion de
huevo, idempotente aunque el huevo recibido se descarte luego. El ledger admite
27 tokens por coleccion para mantener `CollectionState` bajo 2 KiB; al agotarse
rechaza de forma segura. El codec portable esta separado del adaptador, pero la
sala GATT, la UI de aceptar/enviar y el borrado del emisor tras ACK aun no estan
integrados; por tanto no hay intercambio BLE operativo todavia.

## Especificaciones Y Verificacion Local

El piloto SDD mantiene `docs/requirements.json` como registro de specs,
requisitos y entregas; `docs/superpowers/specs/` expresa comportamiento y
aceptacion, y `docs/superpowers/plans/` registra pasos y evidencia. `scripts/`
provee chequeo estructural y ejecucion local, no una puerta remota: no hay
GitHub Actions ni hooks, y los estados de aprobacion no se elevan solos. Las
pruebas automatizadas no son aprobacion humana ni validacion fisica. El piloto
abarca Creator y el proceso nuevo; la historia previa migra gradualmente, sin
fabricar aprobaciones retrospectivas. Detalle operativo en
[`docs/spec-driven-development.md`](spec-driven-development.md).

## Creator Hub: Frontera De Datos

El Hub corre como servidor local loopback. El catalogo/importador y el asistente
Creator usan `PetDefinition` para validar contenido sin duplicar reglas del
dominio. Creator mantiene borrador y recursos en estado de autor, con preview
y exportacion ZIP; no publica, instala ni concede huevos/items. Web Serial no
abre el puerto ni instala contenido. Se conserva la frontera entre autoría,
validacion, exportacion y eventual instalacion de firmware/paquetes. Ver
[`vpet-creator.md`](vpet-creator.md) y [`vpet-hub.md`](vpet-hub.md).

## Journal Compacto De Cuidado: 2026-10-27

El usuario aprobo separar comida, items y luz del checkpoint completo. Con
Coleccion habilitada, el worker de capacidad uno llama `saveCare`, que reemplaza
atomicamente una sola clave NVS `vpet_state/colCare`. Guarda el snapshot absoluto
de la mascota activa y los ajustes, incluida la mochila compartida; no reaplica
incrementos de comida ni descuentos de items al recuperar. El limite es 3950
bytes por registro y 3800 por snapshot, dentro de la particion NVS existente de
20 KiB. Falta de espacio, lectura fallida o escritura rechazada no acreditan una
accion nueva. `Pending` conserva el efecto pero bloquea acciones dependientes
hasta `sync` y readback; la recuperacion no emite un segundo consumo.

El registro VPCJ1 enlaza generacion base VPCL v1, revision monotona, slot,
identidad, tiempo acumulado encendido y CRC. El arranque valida el archivo base
antes de superponer el journal. Identidad, perfil y forma deben coincidir; un
registro futuro, corrupto, sin base o de otra mascota bloquea, sin migracion
silenciosa desde legacy. Los lectores y escritores estructurales comparan la
huella del journal esperado: una vista antigua no puede sustituir cuidado ya
aceptado aunque no cambien stock ni metadatos de Coleccion.

El cuidado normal comprueba solo el encabezado base de 24 bytes y el journal;
no escribe el archivo completo. Cambiar mascota, crear/cruzar huevos, guardar
experiencias, guardar manualmente o evolucionar siguen siendo checkpoints
completos. Estos fusionan snapshot, mochila y temporizadores antes de publicar
la siguiente generacion; el journal anterior queda obsoleto, sin requerir una
segunda escritura para borrarlo. Incubacion y cooldown acumulan solo tiempo
encendido confirmado, sin duplicarlo al reiniciar ni tras una recuperacion.
Los fallos transitorios del journal se distinguen del bloqueo del archivo base.

Al rechazar un guardado de combate antes de publicar su generacion, App revierte
el candidato y conserva el resultado terminal con `pendingAward`. Antes de
permitir otro intento, `recoverRejectedSave` valida la misma secuencia/activo,
cuerpo, metadatos, recibo compacto y politica de aprendizaje. Si la lectura
falla, conserva el bloqueo y vuelve a comprobarla; nunca borra el diario para
desbloquear. La adquisicion se reintenta con ACTION sin repetir el combate ni
duplicar premios. Los logs `VPET_EXPERIENCE_SAVE_REJECTED` y
`VPET_BATTLE_SAVE_REJECTED` identifican fase y recuperacion. Ver
[contrato de jugabilidad](superpowers/specs/2026-10-28-battle-retry-inventory-status.md).

Entrenamiento aplica la misma validacion despues de su rollback: conserva la
pantalla de error, permite ACTION para reintentar el resultado retenido o BACK
para descartarlo. Un rechazo no concede EV ni aprendizaje ni consume recursos;
un resultado confirmado solo se publica una vez. La bandera RAM solo cubre
experiencias rechazadas, no cuidados aceptados pendientes. El registro
`VPET_EXPERIENCE_SAVE_REJECTED context=training` identifica la fase fallida.

El regreso de exploracion usa el mismo controlador de recuperacion despues de
restaurar el viaje al rechazarse Claim. Permite recoger de nuevo tras validar
la misma vista durable, sin cancelar el viaje ni duplicar premio/aprendizaje.
El log compartido incluye context=exploration_claim, stage y recovered. Estos
cambios resuelven el bloqueo posterior al rechazo; no prueban la causa inicial
de un fallo de escritura en placa sin capturar dicho rechazo por USB.

La captura posterior de CLAIM identifica policy_publish. El volumen instalado
tiene name_max=32, aunque el SDK permita 64; los nombres legacy de politicas
superan ese limite. Nuevas publicaciones usan claves de 26 bytes derivadas del
sobre completo (FNV64 y CRC32); no son firmas ni prueba de autenticidad.
El lector valida ID, contenido y checksum, acepta nombres antiguos y compactos,
y nunca sobrescribe bytes distintos ante colision. GC protege ambas generaciones.
No cambia el schema NVS ni se reformatea el volumen. HUB STORAGE valida en modo
solo lectura sin GC cuando App esta lista; STATUS conserva su protocolo.

La validacion del GC de aprendizaje usa un flujo de lectura por generacion,
no uno por bloque: comprueba longitud, CRC completo y cuerpos antes de cerrar
con resultado verificado. Cada operacion reabre y revalida; no conserva bytes
ni certificados de validacion entre generaciones. App mide el guardado final
de entrenamiento con VPET_TRAINING_SAVE. El usuario confirma que reducir esas
aperturas no elimino la pausa. La confirmacion de entrenamiento ahora reutiliza
SaveTask/FreeRtosSaveTask: un snapshot posterior y un evento inmutables en heap,
sin segunda tarea, cola adicional ni framebuffer. App dibuja GUARDANDO/SAVING
antes de iniciar el escritor; despues solo actualiza el indicador animado sobre
ese framebuffer, sin lecturas de assets ni mas memoria grafica. La mascota en
esa vista permanece quieta. Solo el escritor accede a Coleccion/NVS
hasta la barrera acquire de finished(). App no consulta aprendizaje mientras
dibuja y ready es false, bloqueando operaciones del Hub. La tabla solo aparece
tras commit y settlement; rechazos restauran efectos y permiten reintento tras
recuperacion, sin duplicar cargos/experiencias. Un commit aceptado pendiente
no se revierte. La destruccion espera al escritor y begin no reinicia el trabajo.
La telemetria agrega frames, max_frame_gap_ms, stack_free_bytes y heap_min.
Las pruebas host y paridad visual no acreditan fluidez fisica. CLAIM, reloj y
combate conservan su camino sincrono; REQ-GAME-PLAY-007 sigue pendiente.

No cambian enums persistidos, VPCL v1, assets, Status, WiFi ni particiones. El
modo sin Coleccion conserva el guardado legacy existente. Para volver a un
firmware sin soporte del journal debe completarse primero un checkpoint total;
de otro modo ese firmware no veria el ultimo cuidado. NVS tambien escribe flash
y puede hacer garbage collection: eliminar escrituras LittleFS por accion no
certifica fluidez en hardware. Esta revision se cargo el 2026-10-28 con
autorizacion separada y hashes protegidos verificados. La prueba del usuario
acepta la mejora visual; cuatro MEAT y dos cambios de luz guardan en 272-341 ms
frente a los 4175-7016 ms anteriores. No se midio un commit efectivo de Mochila.
El heap minimo observado de 37652 bytes y un pico de loop no atribuido de
7622063 us fuera de esos jobs mantienen abiertos los limites de memoria y
otros flujos sincronos; no se declara resuelta toda la latencia del firmware.
El margen LittleFS real es 5%, igual
que antes de la carga y por debajo del criterio de 10%; no se limpia ni migra
el filesystem automaticamente. Ver [plan](superpowers/plans/2026-10-27-compact-care-journal.md).

## Cuidado Responsivo Y Menos I/O: Revision Cargada 2026-10-27

La ampliacion de la base de alimentacion inferior reutiliza `CareSave` para
comida, items de Mochila y luz. Cada trabajo copia estado anterior, snapshot,
ajustes y panel/cursor de origen. Mochila presenta la cantidad actualizada;
luz presenta Home y el nuevo estado de sueno antes de iniciar el mismo worker.
No se inventa otra animacion ni assets. Se conserva capacidad de un trabajo:
ACTION/Back no ejecutan otra transaccion mientras el commit esta pendiente.
BACK de Mochila si puede cerrar visualmente el panel durante el trabajo; si
este se rechaza, el rollback conserva la salida a Home y restaura el consumo.
Por eso mover el guardado a un hilo no garantizaba comidas seguidas sin espera.

`prepareCare` actualiza el cuidado y sueno hasta el input sin persistir aun,
y acumula tiempo de Coleccion en RAM. Al terminar el worker, el flujo normal
recupera el intervalo transcurrido bajo el estado de sueno resultante. Rechazo
restaura mascota, Motion y panel de origen; un journal aceptado pero pendiente
conserva el efecto y bloquea acciones hasta recuperar. Items legacy usan ahora
el mismo snapshot completo `saveTx`; los journals `itemTx` previos siguen
recuperandose por el adaptador existente, sin cambios de schema.

`LittleFsCollectionRepository` mantiene un descriptor de lectura durante una
vista, invalidado en cada `size()` y antes del cambio de generacion. Dos buffers
fijos de 512 bytes evitan el buffer implicito de libc; cursores explicitos evitan
seek/ftell por bloque contiguo. La transicion lectura -> escritura de staging
siempre posiciona el stream C. Se evita prellenar/sincronizar staging con ceros
antes de sobrescribirlo y se elimina una validacion `current()` duplicada en
`saveActive`: `persist` conserva la comprobacion durable antes de `begin`.
Readback completo, CRC, backup anterior, sync y rename atomico se conservan.

Regresion host de dos mascotas: 56 -> 9 aperturas y 81 -> 5 seeks por guardado.
Son conteos de operaciones, no una medida de milisegundos en ESP32. Las trazas
`VPET_CARE` identifican Item/Light; `VPET_FEED` conserva su formato previo.
Firmware 643ca42 cargado con hashes verificados y partida/graficos conservados.
La prueba fisica posterior rechaza la fluidez: primeros dibujos de 84-211 ms,
guardados de 4175-7016 ms y ciclos de loop de hasta 3122339 us. El minimo de
heap bajo carga fue 44364 bytes y la pila libre minima del worker 3648 bytes.
El renderer sigue leyendo clips desde LittleFS durante el guardado de la misma
coleccion; la contencion explica una hipotesis coherente, pero aun no hay
desglose de fases que atribuya todo el tiempo a un unico punto. La propuesta de
un journal compacto separado de checkpoints completos se desarrolla en la
revision documentada arriba, todavia sin aceptacion fisica.
Ver [plan](superpowers/plans/2026-10-26-responsive-care.md).

## Alimentacion Con Guardado De Fondo: 2026-10-26

`App` sigue siendo el unico propietario de la mascota viva, navegacion y TFT.
Al aceptar MEAT/PROTEIN crea mediante RAII un trabajo con estado anterior,
snapshot posterior y ajustes copiados. Dibuja Home/Eat antes de despertar el
escritor, incluso si hay un checkpoint de tiempo vencido. `SaveTask` admite
un trabajo; `FreeRtosSaveTask` lo ejecuta con notificacion en una tarea
persistente de 8192 bytes de pila, creada al primer uso. No hay una cola
creciente ni dependencias FreeRTOS en el dominio portable.

Hasta la barrera acquire/release de finalizacion, solo el escritor accede a
Collection/NVS. App avanza Motion y dibuja Home; NEXT mueve el cursor, mientras
ACTION/Back no abren otras transacciones. Antes de evaluar comida se actualiza
el cuidado a la hora del input y se acumula tiempo sin I/O; el intervalo de
espera se recupera al volver al flujo normal, incluso tras fallos de guardado.
El snapshot del worker es independiente de la mascota mostrada. La primera llamada tras
completar descarta la tecla recibida durante el guardado.

Un commit rechazado restaura la mascota anterior y muestra el error existente;
el adaptador legacy usa el snapshot completo y su journal saveTx existente,
para incluir evolucion y errores de cuidado ocurridos justo al alimentar.
Un journal NVS aceptado pero pendiente de replay conserva el efecto y bloquea
nuevos cambios hasta recuperarlo. Los reintentos se espacian un segundo usando
un reloj independiente del cuidado retenido. Fallos de reserva/creacion de tarea no
ejecutan un guardado sincrono de comida como alternativa; los cambios previos
de cuidado que requieren checkpoint se conservan para su recuperacion.
Destruir App espera al trabajo antes de liberar su contexto. `ready()` es falso mientras hay comida pendiente,
lo que no equivale a afirmar que el almacenamiento esta danado.

`CollectionStore::saveActive` incorpora opcionalmente el tiempo confiable de
`CollectionPanel` al mismo candidato atomico: cooldown/incubacion y cuerpo se
confirman juntos, sin un flush separado. Se conserva el formato VPCL, version,
numeros de enums, CRC, generacion anterior y rename como punto de visibilidad.
Las otras transacciones y el simulador mantienen sus adaptadores existentes.

No es una garantia de duracion cero: assets y partidas usan la misma LittleFS,
y la flash puede bloquear momentaneamente ambas CPU. No se precargan los 25
fotogramas completos (133-162 KiB, incompatibles con el margen de RAM actual).
Las trazas `VPET_FEED_PRESENT` y `VPET_FEED_SAVE` distinguen primer dibujo,
duracion de persistencia, pila libre y minimo de heap. Corte de energia antes
del commit puede perder la comida pendiente; no se acredita como guardada al
encolarla. Pruebas host con ejecucion diferida y shim multihilo no certifican
latencia/TFT/BLE reales. Estado de entrega en [el plan](superpowers/plans/2026-10-26-responsive-feeding.md).

## Coleccion Y Experiencias: Revision 2026-10-25

La entrega agrega composicion `PetProfile`/`LearningState`, reglas de
cruce portables y coleccion de cuatro individuos con mochila compartida.
Adaptadores separados en simulador y ESP32, snapshots por cuerpo y commits
de coleccion en filesystem; NVS legacy se conserva. No son subclases ni
codigo nuevo por cada skin. [Contrato, limites y estado](collection-learning-breeding.md).
La ultima carga fisica es coleccion/aprendizaje del 2026-10-25, con arranque,
digests y BLE comprobados. Status conserva el diseno aceptado de F1/F2;
las nuevas vistas siguen pendientes de aceptacion del usuario.
El despliegue normal de LittleFS queda bloqueado para no borrar individuos;
solo firmware compatible hasta disponer de actualizador preservando datos.

Revision visual 2026-10-26: `CollectionView.cpp` dibuja la presentacion de
coleccion y `CollectionPanel.cpp` conserva seleccion y transacciones. No hay
otro framebuffer ni cambios de persistencia; se reutilizan los clips instalados
de Training y el retrato del huevo. La consulta de preferencias en placa usa
solo la politica activa ya residente; las politicas de reserva no se cargan.
La bienvenida visible no ejecuta la migracion por abrirla.

Correccion de pila 2026-10-26: las transacciones de `CollectionStore` reservan
los metadatos candidatos en heap mediante RAII y comprueban el fallo de reserva.
La migracion tampoco mantiene un individuo temporal en pila. El guardado
anidado agotaba los 8 KiB de loopTask en hardware aunque cada frame individual
pasaba el limite antiguo de host. El limite de regresion ahora es 1024 bytes
por frame; esto no sustituye validar la ruta completa en la placa. Serializado,
schema, journals y momento de commit permanecen iguales.

## Portal Local vPet Hub

`scripts/hub_server.py` sirve `web/hub/` en loopback. El cliente consulta
catalogo y previews PNG derivados de los atlas preparados; el adaptador host
reutiliza `PetDefinition` para validar JSON F1 en memoria. No modifica el core,
guardados ni firmware. GET se limita a rutas explicitas y POST a validacion
de hasta 64 KiB para F1, sin CORS abierto ni escritura de archivos. CSP restringe
recursos al propio origen. Ver [limites y uso](vpet-hub.md).

El [asistente Crear vPet](vpet-creator.md) agrega estado de autor independiente,
previews PNG locales, borradores descargables y exportacion ZIP en memoria.
`scripts/hub_creator.py` valida imagenes/cuadriculas y genera una PetDefinition;
no duplica ni cambia reglas de dominio. Los endpoints /api/creator/check y
/api/creator/export admiten hasta 24 MiB de JSON, con 16 MiB de PNG decodificados
y 4 MiB por recurso. El ZIP es un proyecto de autor, no un paquete instalable.

Web Serial se detecta solo como capacidad del navegador. No hay puerto abierto
ni comandos de instalacion: esa entrega necesita protocolo firmware, contrato
publico, autenticidad, presupuesto y recuperacion transaccional.

## Plataforma vigente

La plataforma principal es la LILYGO TTGO T-Display clasica con ESP32,
pantalla ST7789 de 240x135 y 16 MB de flash. El firmware es C++17 sobre Arduino,
compilado con PlatformIO y renderizado con TFT_eSPI.

La implementacion Pico W/CircuitPython permanece disponible como compatibilidad
legada. No define la arquitectura principal ni el formato de despliegue actual.

## Flujo de datos

Revision: 2026-10-25. F1 implementa `PetDefinition`, resolucion
por rol/accion/contexto y tablas generadas Python/C++; integra Motion,
Renderer y Panels sin cambiar guardado o balance. Ver
[definiciones de contenido](content-definitions.md). F1/F2 estan cargados desde
el 2026-10-24; no hay instalador externo. Coleccion se cargo el 2026-10-25.
Consulta [estado y diferencias conocidas](project-status.md),
[guia del producto](product-guide.md) y [paquetes](content-packages.md).
F2b integra [crecimiento por ADN](growth-integration.md): `core.growth`
y `vpet/Growth.h` alimentan Pet/PetState, Training, ganancias, penalizaciones,
combate y vistas. Stats derivados uint16, EV persistido compatible y schema sin
cambios. El [piloto](growth-pilot.md) conserva baseline legacy para comparar.
F2a agrega
[perfil individual](individual-profile.md): identidad/sexo/padres por composicion,
entropia inyectada y migracion de partida/reserva. La coleccion, aprendizaje y
breeding se describen en el [contrato local](collection-learning-breeding.md).
La [vista grafica actual de Archify](../.archify/architecture-vpet-20261028-132049/vpet-architecture.html)
resume persistencia, locus sexual, supervivencia, breeding local y los limites
de la transferencia BLE aun no integrada. La fuente editable es
`.archify/architecture-vpet-20261028-132049/candidate.json`; la revision del
2026-10-05 se conserva como instantanea historica. Archify valido composicion,
entrega y procedencia. El browser-check queda fallido por terminacion del canal
Chrome DevTools antes de recibir datos; no se declara inspeccion visual aprobada.

```text
assets/*.png + src/data
          |
          | scripts/build.py --profile tdisplay
          v
build-tdisplay/ (BMP y catalogo intermedio)
          |
          | scripts/build_tdisplay.py
          v
firmware/t-display/data/*.vpa + manifest.json
firmware/t-display/include/generated/catalog.h
          |
          | PlatformIO
          v
firmware.bin + littlefs.bin
          |
          | scripts/deploy_tdisplay.py --firmware-only
          v
ESP32 app partition (LittleFS instalado se conserva)

CollectionPanel + LearningRuntime
          |
          | generaciones y referencias a politicas confirmadas
          v
LittleFS /collection/ (datos propios, no son assets generados)
```

`make sim` consume el arte generado para T-Display. `make deploy-firmware`
ejecuta pruebas y build antes de cargar solo firmware compatible. Reemplazar
`littlefs.bin` queda bloqueado: borraria los datos nuevos. Se requiere un
actualizador de assets preservando coleccion antes de habilitar esa ruta.

## Capas

| Capa | Ruta | Responsabilidad |
|---|---|---|
| Arte fuente | `assets/` | PNG originales del fondo, iconos y sprites |
| Modelo Python | `src/core/` | Reglas usadas por el simulador y pipeline legado |
| Herramientas | `scripts/` | Conversion VPA, simulador, validacion y despliegue |
| Nucleo C++ | `firmware/t-display/lib/vpet_core/` | Estado, movimiento, navegacion y politica BLE portable |
| Plataforma ESP32 | `firmware/t-display/src/` | TFT, botones, BLE, NVS y LittleFS |
| Recursos generados | `firmware/t-display/data/` | Payload LittleFS; no se versiona |
| Catalogo generado | `firmware/t-display/include/generated/` | Registro C++ derivado; no se versiona |

Las reglas portables no incluyen Arduino, TFT_eSPI, WiFi ni Preferences. Esto
permite ejecutar sus pruebas como binarios nativos en macOS.

## Componentes del firmware

| Componente | Funcion |
|---|---|
| `main.cpp` | Inicializa pantalla, buffers, recursos, entradas y servicios |
| `App` | Coordina el loop, acciones, paneles, Bluetooth y persistencia |
| `Renderer` | Dibuja fondo, menu, selector y animaciones sin parpadeo |
| `Panels` | Dibuja estado, inventario, evolucion, opciones y fecha/hora |
| `AssetStore` | Monta LittleFS, valida VPA1 y dibuja frames indexados |
| `BoardInput` | Traduce GPIO0/GPIO35 a `Next`, `Action` y `Back` |
| `PetState` | Estadisticas, inventario gastable, acciones, descubrimientos y evolucion |
| `PetProfile` | ID individual, sexo expresado y referencias de padres; el sexo heredable se persiste ademas en DNA4 |
| `CollectionStore` | Cuatro cuerpos por separado, inventario compartido y recibos atomicos sin modificar NVS legacy |
| `CollectionPanel` | Confirmaciones, seleccion de individuo/padres y coordinacion con App; no modifica Status |
| `LearningState` / `LearningRuntime` | Politica portable y eventos confirmados por individuo; herencia limitada y AUTO legal |
| Repositorios LittleFS | Generaciones, blobs inmutables y GC conservador; sin formatear ni reemplazar assets |
| `ProfileRandom` | Adaptador ESP32: siembra mbedTLS antes de RF/ADC, genera perfiles sin activar radio |
| `PetDefinition` | Nombres, clips, rutas y contextos; responsabilidad del resolver sin plugins |
| `Motion` | Idle, caminar/volar, acciones y sueno; frames/intervalos/loops declarados con overrides legacy |
| `SleepRoutine` | Cansancio por ADN/energia, habito gradual, sesiones y premio nocturno unico |
| `Navigation` | Menu superior, paneles, paginas de Status e inventario |
| `DateTimeMenu` | Filas +/- de fecha u hora; SAVE escribe el reloj ESP32 |
| `Strings.h` | Copy EN/ES de paneles |
| `SettingsStore` | Serializacion versionada de estado, inventario y preferencias |
| `PracticeBattle` | Motor portable de combate de practica con HP/MP y tecnicas |
| `PracticeSession` | Controlador portable C++ de Tech y batalla, integrado en App |
| `EvolutionProgress` / `EvolutionUi` | Lectura de condiciones salientes y ficha paginada; no aplican evolucion ni escriben la partida |
| `BleAdvertiseSession` | Primera vez configura el ADV; reconnect solo `start()` |
| `BleService` | NimBLE bajo demanda: HID teclado, DIS y bateria |
| `NvsKeyValueStore` | Adaptador de Preferences/NVS |

## Orientacion A Objetos Y Limites Actuales

El firmware YA usa orientacion a objetos: `App` recibe referencias a
Renderer, Panels, SettingsStore y BleService; posee PetState, Motion,
Navigation y sesiones. PetState encapsula campos privados y operaciones
del dominio; SleepRoutine, Exploration y PracticeProgress se componen con
la mascota. No se necesita convertir cada funcion pura en una clase.

Sin embargo, tener clases no hace que un paquete sea plug and play:

| Dependencia actual | Evidencia en fuente | Consecuencia |
| --- | --- | --- |
| Solo cinco especies numericas | `PetState.h`, `Navigation.cpp` | Agregar otra criatura requiere decisiones de identidad/migracion |
| Activacion no persistida | F1 inyecta `PetDefinition` en Motion/Renderer/Panels, builtin por defecto | Vistas desacopladas, sin instalacion/cambio de paquete en board |
| Perfil visual y adaptadores legacy | Cadencias comunes de herramientas y `AnimationId` compatible | Frames/loops por criatura ya son datos; no admite perfiles arbitrarios |
| Disponibilidad por enum de especie | `MenuAccess.h`, `PetState::techniqueStage` | Las capacidades no proceden de una definicion intercambiable |
| Metadata legacy de eclosion | Las tres reglas automaticas ya se generan desde `src/data/digimon/`; persiste metadata 8 s / runtime 2 s del huevo | No cambiar esa diferencia ni balance bajo F1 |
| Lista de hojas y recortes especificos | `scripts/build.py` | Otro autor no puede aportar solo un paquete autocontenido |
| Manifiesto minimo, no instalador | `AssetStore::begin` busca la marca de formato; `drawFrame` valida parte de VPA1 | No existe validacion/activacion segura de paquetes externos |

El motor ya permite sustituir definiciones en pruebas; el firmware normal
sigue usando la builtin. No anunciar intercambio instalado sin recompilar.
Dos lineas del tamano actual no caben; no equivalen a cuatro individuos
con arte compartido.

## Direccion Propuesta: Motor Comun Y Contenido Intercambiable

Requisito del usuario del 2026-10-23: recibir otra mascota como huevo de
premio, criar individuos diferentes con el mismo funcionamiento del motor
y permitir breeding interno. No es un cambio de apariencia de la mascota
actual. La revision 2026-10-25 implementa cuatro plazas incluyendo huevos,
inventario compartido y cruce local para la linea instalada. El contrato de
coleccion al inicio de este documento prevalece sobre los nombres propuestos
en la tabla siguiente; instalacion y huevos de proveedores siguen pendientes.

Alternativas consideradas:

1. **Composicion y datos declarativos (recomendada).** Un motor comun recibe
   definiciones y un paquete visual. No requiere una clase por criatura.
2. Herencia `Firemon : Pet`, `OtraCriatura : Pet`: duplica reglas o exige
   compilar nuevas subclases; no satisface instalar solo datos.
3. Plugins ejecutables/scripts: mas libertad, pero agregan otra superficie
   de ejecucion y coste de memoria; fuera del alcance de estos paquetes.

Separacion propuesta:

| Pieza | Responsabilidad y limites |
| --- | --- |
| `PetState` / identidad individual | Guarda barras, ADN, EV, edad, equipo, rutina e inventario. No guarda rutas de imagen como identidad |
| `PetDefinition` + etapas | Datos inmutables de la linea, IDs estables, nombres y referencias a roles/perfiles. Separados de la instancia y su progreso |
| `PetInstance` + `PetRoster` | Identidad y estado de cada individuo, referencia de definicion y seleccion de mascota activa; un premio crea otro individuo, nunca reemplaza al actual |
| Registro de huevos / `Nursery` | Huevos identificados, procedencia de premio o breeding, padres si existen y transicion a cria sin duplicar el individuo. Limites aun no cerrados |
| `RuleSet` comun | Cuidado, entrenamiento, Arena, sueno y evolucion. Un paquete visual no redefine recompensas, limites, sexo ni aprendizaje |
| `ContentPack` | Manifest, version, compatibilidad, licencia y recursos. No contiene C++, scripts ni claves de la partida |
| `AnimationClip` | Accion semantica, frames, duracion, anclaje, canvas y rango de bucle; no nombres de archivo asumidos por el motor |
| `AssetResolver` | Resuelve pack/etapa/accion/variante a un recurso validado; mismo contrato para Home, Status, Training, Arena, Exploracion y Evolucion |
| `PetViewModel` / presentacion | Combina estado, necesidades y definicion para dibujar. La capa de presentacion no concede efectos |
| `PackRepository` / instalador | Transferencia, validacion, capacidad, staging, activacion y recuperacion; adaptador fuera del core |
| `SettingsStore` / repositorio de partida | Persiste referencia de contenido y progreso mediante migracion compatible, separada de los archivos instalables |

`PetProfile` ya es un miembro por valor de PetState/Pet, no otro contenedor
del estado ni un segundo petId. La coleccion futura referencia ese mismo
perfil. El repositorio inyecta la generacion y lo guarda con el individuo;
una definicion visual no puede asignar IDs, sexo o padres.

Son objetos por responsabilidad y composicion. Definiciones pequenas pueden
ser structs/tablas; interfaces virtuales solo donde permitan sustituir un
adaptador real. No introducir un framework de plugins, arbol de herencia
por especie, heap por frame ni otro framebuffer para lograr esta separacion.

Flujo objetivo, no runtime existente:

```text
Input -> App / sesiones -> reglas comunes -> PetState -> guardado
                              |
                      PetViewModel + PetDefinition
                              |
ContentPack -> AssetResolver -> Renderer / Panels -> AssetStore -> TFT
```

En Python se mantiene el mismo contrato y vectores de prueba; no se finge
que ejecuta el mismo binario C++ ni se mantienen reglas divergentes por pack.

### Alcance Del Primer Paquete Compatible

Primera entrega propuesta: otra definicion de mascota/linea para el perfil
de juego actual, con las cinco etapas logicas y todas las acciones requeridas.
Puede cambiar nombres, sprites, retratos y animaciones; un theme compatible
puede cambiar fondos. Menus, acceso por etapa, reglas, premios y tiempos de
juego siguen siendo comunes. No usa el nombre Firemon para calcular permisos.
Instalar contenido no crea mascotas automaticamente: recibir un premio
confirmado crea un huevo distinto asociado a una definicion ya disponible.

Los frames y bucles son metadatos, pero cambiar su numero no puede dar
comidas, acciones ni premios adicionales: la finalizacion de presentacion
y la confirmacion de una accion conservan contratos distintos. Se validan
las duraciones admitidas por cada rol antes de activar contenido.

Lineas con otra cantidad de etapas, ramificaciones, reglas o tecnicas nuevas
son una ampliacion separada y versionada del contrato; no se promete que
cualquier ZIP o atlas arbitrario funcione. El formato debe definir que
campos opcionales se pueden ignorar y rechazar capacidades requeridas no
soportadas. [Alcance e instalacion](content-packages.md).

El usuario aclara que cada nueva mascota llega como huevo de premio y tiene
su propia vida, no reemplaza ni copia a la actual. Un paquete se instala una
sola vez y puede ser referenciado por varios individuos de esa misma linea.
Un huevo de breeding tambien es un individuo unico; la eclosion cambia su
estado, no ocupa un segundo registro ni vuelve a conceder el premio.

Breeding interno selecciona dos individuos propios compatibles; no necesita
una segunda board. Reutiliza reglas de sexo, parentesco, herencia, cooldown
y recibos de la futura entrega de breeding. La via entre boards sigue
siendo otra operacion con consentimiento bilateral y pruebas de radio.
Cruces entre lineas con hijo visual aun inexistente requieren una politica
aprobada; no fabricar una fusion ni aceptar un huevo sin contenido resoluble.

Objetivo de cuatro mascotas solicitado; capacidad efectiva, huevos y paquetes
pendientes de presupuesto/aprobacion. Inventario compartido, no copiado por
individuo. No confundir registros pequenos con atlas grandes,
ni usar espacio disponible como sustituto de un limite de juego. Medir:

- Arte compartido por paquete/version, no una copia por mascota o huevo.
- Datos por individuo y huevo, IDs, parentesco y estado de incubacion.
- Mascota activa en RAM frente a registros aparcados; no cargar todas a la vez.
- Journals/checkpoints temporales, indices y recuperacion con la bolsa llena.

Recomendacion para evaluar, no regla aprobada: una mascota activa y las
demas aparcadas; definir explicitamente si crianza/incubacion avanzan o se
pausan fuera de foco y sin alimentacion. Capacidad agotada debe dejar el
premio pendiente o rechazarlo antes de cobrar/consumir; no borrar al mas viejo.
La reserva legacy requiere migracion explicita, no se presume un roster listo.

### Migracion, Memoria Y Aceptacion

- Mantener enums NVS existentes. Introducir referencias de contenido
  versionadas mediante un adaptador legacy; no reinterpretar SpeciesId
  como identificador universal de todos los paquetes.
- Instalar contenido o cambiar de mascota activa no debe recalcular ADN/EV,
  rutina, equipo ni contadores de otro individuo. Stock compartido necesita
  migracion unica desde una fuente autoritativa, sin sumar snapshots duplicados.
- Actualizar un paquete no migra una partida silenciosamente. Si falta la
  version necesaria, preservar el guardado y ofrecer recuperacion; no borrar
  o seleccionar automaticamente una especie distinta.
- Caches identificadas por pack/version/recurso y vaciadas al activar o
  volver atras. No reutilizar paletas/escenas de un paquete anterior.
- Ultima observacion disponible: heap minimo 60952 bytes en 45 s y LittleFS
  con 659456 bytes libres, no un perfil de peor caso. No se puede suponer
  que caben dos paquetes completos; medir contenido activo, candidato, staging,
  metadatos, rollback y overhead real antes de autorizar una instalacion.
- Conservar los dos framebuffers, presupuestos actuales y partidas. Un
  despliegue completo de LittleFS no es el instalador de paquetes propuesto.
- La aceptacion exige dos paquetes con arte/nombres distintos, mismo firmware
  y mismas trazas de acciones/estado, ademas de fallos de transferencia,
  reinicio durante activacion, espacio insuficiente y recuperacion fisica.

La migracion se divide en definicion builtin, resolucion comun, empaquetado
validado e instalacion USB. El catalogo web, firmas de distribucion y otros
transportes no se presumen implementados. No habilitar WiFi por esta propuesta.

## Renderizado

La intro dura aproximadamente 2.2 segundos antes de cargar el estado. Las rutas
de arranque de firmware y simulador siguen separadas; la paridad visual completa
de la intro queda como tarea de firmware.

La pantalla trabaja en RGB565. Los lienzos que reciben paletas nativas
por `pushImage`, incluido el temporal del escalador, usan `setSwapBytes(true)`.
Se mantienen dos sprites TFT de 240x135:

1. `staticScene` conserva fondo y menu sin elementos animados.
2. `framebuffer` recibe una copia completa de la escena estatica.
3. El selector y el frame actual de la mascota se dibujan en memoria.
4. `pushSprite()` presenta el frame completo en una sola transaccion SPI.

Arena y Exploracion toman prestado `staticScene`: fondo y selector de pelea,
o cabecera de nueve iconos, respectivamente. App invalida la cache de Home
antes de prestarla; `Panels::invalidate()` descarta la cache del panel cuando
Home vuelve a usarla. No se reserva un tercer framebuffer. El selector de
Arena se recompone al cambiar cursor, equipamiento o estado terminal.
Exploracion refresca listas estaticas cada 1000ms en reposo y paginas animadas
cada 70ms; los eventos de boton siempre fuerzan el dibujo sin esperar ese plazo.

Este doble buffer evita limpiar directamente la pantalla y elimina el parpadeo
visible. Las animaciones normales usan frames de 88x88. Las evoluciones usan
111x111 y ocupan el area bajo el menu.

Los VPA1 contienen cabecera, paleta RGB565, offsets de frame y un byte indexado
por pixel. El indice transparente permite dibujar solamente los segmentos
opacos sobre el fondo.

El arranque comprueba la marca de formato del manifiesto generado mediante
`File::find`, sin cargar todo el JSON como un `String`. La lectura anterior
provocaba un pico de heap por reallocaciones. `VPET_HEAP` mide antes/despues de
assets y App; `VPET_READY` conserva los umbrales de despliegue sin rebajarlos.
La correccion y mediciones de placa estan en
[despliegue del 16 de octubre](superpowers/reviews/2026-10-16-board-deployment.md).

## Ciclo de vida actual

```text
Egg --2 s--> Sparkmon --> Firemon --> Flamemon --> Dragfiremon
```

Una partida nueva comienza en `SpeciesId::Egg`. La eclosion (2 s, sin scale)
cambia y guarda el estado como `Baby/Sparkmon`. Despues, `Evolution` aplica
timers COLOR sobre `stageAge * CARE_TIME_SCALE` (placa 1, sim 600):

```text
Sparkmon --12 h 10 min + CM<=1--> Firemon
Firemon  --24 h + H/E/P>=55 HP>=75 + peso 8..14--> Flamemon
Flamemon --36 h + 15 batallas de forma + victorias>=60%--> Dragfiremon
```

Win ratio 0/0 no bloquea en este corte. `EVOLVE` de debug fuerza la linea
buena y resetea el snapshot de forma. Los valores persistidos originales
`Rookie=0`, `Champion=1` y `Ultimate=2` no se renumeran. El arbol muestra
tres nodos por ventana. El detalle redisenado usa EvolutionProgress como
adaptador de solo lectura de reglas salientes y EvolutionUi para cuatro
filas por pagina, tiempo restante y objetivos. App pagina sin cambiar el nodo;
ACTION/BACK vuelve al arbol. Estado de pagina solo en RAM, sin migracion NVS.
Sim y firmware comparten vectores/raster; carga y aceptacion fisica pendientes.
[Contrato](evolution-progress.md). config.py y C++ ya incluyen peso; catalogos
JSON/generados aun deben reconciliarse como fuente unica para paquetes.

## Entrada

```text
Boton izquierdo / GPIO0
  corto   -> NEXT
  2 s     -> BACK

Boton derecho / GPIO35
  corto   -> ACTION
```

El debounce y la deteccion de pulsacion larga viven en `Input`, dentro del
nucleo portable. Un flanco de GPIO0 emite `NEXT` al instante; a los 2 s emite
`BACK`. En Home, `BACK` se ignora. En Opciones, `BACK` tambien se ignora. En el resto,
`BACK` vuelve a Home (o al arbol desde el detalle de evolucion). `NEXT`
emite en el flanco de pulsacion; mantenerlo repite tras 400 ms cada 90 ms.

Opciones muestra tres filas grandes. El orden real es Bluetooth, idioma,
sonido, guardar, cargar, fecha, hora, evolucionar, pausar crianza y volver. `EVOLVE` fuerza
la siguiente forma, guarda NVS y reproduce la animacion en Home. En
Dragfiremon, `EVOLVE` reinicia la partida en huevo.

El estado `Sleep` se acuesta una vez y luego buclea los indices 11..14
(base cero, acotados al numero de frames del clip).
Rest ofrece apagar/encender luz y volver: entrar no cambia el sueno;
ENCENDER LUZ lo interrumpe y la rutina tambien puede finalizarlo al cumplir
su duracion. Navegar no despierta. PAUSAR CRIANZA vive en Opciones, detiene
el descanso y conserva los datos de reserva. [Contrato](rest-and-board-validation.md).

Status conserva cuatro paginas. Vital muestra HP / HAM / ENE / ANIMO;
Cuidado muestra edad, exceso, errores, esfuerzo, batallas y lesiones /15.
Combate conserva sus cinco filas. ADN muestra valor de combate, barra y EV
acumulado en columnas separadas. HERIDO/MUERTO tienen espacio sobre el
retrato, con prioridad de muerte. Ver [contrato Status](status-vitals-care-ev.md).
Un Call activo pinta `*` en el selector. `ACTION` o `BACK` vuelven a Home.

Las necesidades de Home y caras de animo se calculan sin modificar el pet
en `core/cues.py` / `vpet/UiCue.h`. Comparten prioridad lesion/comida/descanso
y umbrales de animo; no crean Calls ni estado persistido nuevo.
[Contrato y evidencia](mood-cues.md).

Alimentar ofrece carne y proteina ilimitadas; no consulta ni descuenta el
stock legado. La mochila conserva los objetos legacy y agrega el catalogo
adoptado de 40 consumibles y Guia; no todos se usan fuera de combate.
`ACTION` consume un item valido, guarda la partida y permanece en el menu; si
el guardado falla, restaura la instantanea anterior. Stock 0 o una accion
bloqueada no cambia la partida. `ACTION` en ATRAS cierra.

Simulador y firmware separan dos entradas para las etapas de combate despiertas:

- Pesa: `TrainingSession` y `render_training` permiten elegir ataque, defensa,
  velocidad, HP maximo, MP maximo o mente, ademas de abrir las lecciones de
  tecnicas. `src/core/training.py` aplica hasta 6 EV al atributo elegido
  (cap adulto por etapa: 84/168/252),
  cuesta 8 ENE y conserva DNA/IV. Se reutilizan los campos EV persistidos.
- Espadas: `PracticeSession` inicia directamente el encuentro con el rival y
  `render_practice` muestra HP/MP y las ordenes equipadas. No hay preparacion ni
  catalogo intermedio. Consultar/equipar tecnicas queda en Pesa > Tecnicas.
  Retirarse o confirmar un resultado cierra la sesion y devuelve a Home con
  las espadas seleccionadas. Abrir el icono no ejecuta la primera ronda.

El motor de Arena aplica nueve elementos compartidos por Python y C++:
fuego/planta/agua, electrico/viento/tierra, luz/oscuridad y neutral.
`elemental_damage` / `elementalDamage` multiplican por 3/2 (division entera)
solo con ventaja de la tecnica sobre el receptor; los demas cruces usan 1.
Guardia divide despues por 2, con minimo 1. Golpe es neutral, Llama fuego
y Guardia no tiene elemento. Las tres etapas de Firemon y el rival de
practica usan fuego. No se agregan atributos Vaccine/Data/Virus ni campos
elementales persistidos en NVS. La paridad numerica no certifica la paridad
visual de Panels ni el comportamiento fisico sin desplegar.

`scripts/practice_icons.py` define iconos pixel-art compartidos por ambas vistas.
Guardia y el ejercicio de defensa usan el atlas `block`; no se cambia el motor
de combate. Las sesiones pausan el tick de crianza. NEXT selecciona, ACTION
confirma y BACK vuelve; una sesion de atributo muestra su resultado durante
1.5 segundos sin repetir el premio por mantener pulsada una tecla.

`make sim-training` y `make sim-practice` abren estos flujos con un guardado
aislado compartido, `out/sim_practice_save.json`. Al entrar desde `make sim`,
guardan la partida normal. Desde 2026-10-18, los resultados decisivos de Arena
suman al contador de batallas de la forma actual y a W/L acumulados: victoria
suma batalla y victoria; derrota suma batalla y derrota. Empate, retirada y
pelea inconclusa no suman. No se ejecuta la accion legacy de combate aleatorio
ni se cobran DP, energia, lesiones o EV adicionales por registrar el resultado.

El contador, premio, dominio y vinculo se confirman juntos. App usa el journal
completo `saveTx` para el flujo de Arena; `itemTx` antiguo mantiene su formato
y recuperacion para los otros consumidores. Un rechazo restaura el pet y
permite Reintentar; una confirmacion pendiente bloquea entrada hasta recuperar
el snapshot aceptado. Repetir ticks, reintentar o reiniciar no reaplica el premio.

La evolucion permanece automatica al regresar a Home, sin interrumpir el
resultado de Arena. Champion->Ultimate mantiene 36 horas de edad de etapa,
15 batallas en esa forma y 60% de victorias entre W/L acumulados de la vida
actual (no un ratio nuevo por etapa). La edad y contador de etapa se reinician
al evolucionar; W/L, tecnicas, dominio y stock conservan las reglas anteriores.
En Make Sim, `SimulatorServices.evolve_and_save` confirma el JSON atomico
antes de iniciar la animacion; si falla, restaura el pet y no muestra una
evolucion no guardada. Las peleas historicas de Arena no se reconstruyen.

La pesa y Tecnicas se dibujan en C++ mediante TrainingUi. El firmware conecta
`PracticeSession`, `App` y `Panels::drawPractice`. `PetState` posee el progreso y SettingsStore lo
guarda con la mascota, incluido su respaldo; una nueva vida lo reinicia.
Las claves `techVer`, `techTrain`, `techBond`, `techM0..4`, `techEquip` son
opcionales dentro del schema 3. Versiones de progreso desconocidas usan defaults.
La validacion de pantalla fisica y heap con BLE sigue pendiente.

## Persistencia

El esquema actual es 3 e incluye ADN/EV. Admite migracion de 1 y 2.
`vpet_bak` conserva la reserva/intercambio legacy, sin accion en Rest. El inventario tambien
incluye proteina y medicina. Status tiene vistas adicionales de ADN.

La particion NVS mide `0x5000` bytes y utiliza namespaces separados:

- `vpet_state` schema 3: especie, barras, edad total, `stageAge`, `cm`,
  `call`, `meals`, `training`, `battles`, `wins`, `losses`, `weight` (5),
  `dp`, `protein`, idioma, sonido, `bluetooth` e inventario
  (`invMeat`, `invEner`, `invExp`, `invRing`; defaults 3/2/1/1).
- `vpet_wifi`: namespace legado reservado; el firmware actual no lo consulta.

Nutricion conserva el schema general 3 y usa `nutVer`, `nutHunRem`,
`nutTrainRem` y `nutProtein` para sus campos versionados. `foodTx` es un
registro idempotente de la ultima comida confirmada: se escribe antes de
actualizar las claves afectadas y se reproduce al cargar si hubo un corte a
mitad de NVS. El simulador reemplaza el JSON mediante archivo temporal y
`os.replace`, por lo que una comida persiste el snapshot completo o conserva
el anterior.

Schema 1 migra con ceros y `stageAge=0` (no evo instantanea). Schema `>3`
es Unsupported: `App::begin` bloquea con error de almacenamiento, no reemplaza
la partida por un huevo. El anillo de 32 eventos
de cria vive solo en RAM. Autosave ocurre al eclosionar, evolucionar, sumar
un care mistake, gastar un item o guardar a mano. Un despliegue normal no
borra NVS. `App::begin` aplica `bluetoothEnabled` al radio al arrancar.

LittleFS comienza en `0x410000`, mide `0xBE0000` y contiene exclusivamente
recursos reconstruibles. El estado del usuario nunca debe depender de LittleFS.

## Conectividad

Bluetooth se controla desde Opciones (indice 0) y sigue este estado:

```text
Off -> Advertising <-> Connected
        |
        -> Error
```

`BleService` vive solo en la placa. Usa `h2zero/NimBLE-Arduino@2.5.1` como
periferico (central y observer desactivados, una conexion). Al activarse:

1. Inicia NimBLE con nombre `vPet-XXXX`, donde `XXXX` son los 16 bits bajos
   de `ESP.getEfuseMac()` (en esta placa, `vPet-F908`).
2. Activa bonding Just Works (`setSecurityAuth(true, false, true)`).
3. Crea `NimBLEHIDDevice`: HID `0x1812` (teclado, appearance `0x03C1`),
   Device Information `0x180A` y Battery `0x180F`.
4. Publica DIS de solo lectura: modelo `vPet T-Display`, firmware `0.1.0`,
   serial igual al nombre.
5. Anuncia el UUID HID y el nombre. El mapa HID existe para iOS Settings;
   no se envian informes de teclas.
6. `BleAdvertiseSession` configura el payload ADV una sola vez; un
   disconnect solo reanuda el anuncio (`advertiseOnDisconnect`).

El simulador 240x135 refleja el toggle y el texto de estado. No usa la radio
del Mac. WiFi esta deshabilitado. No hay transferencia de paquetes ni
protocolo de juego entre vPets. USB es el primer transporte propuesto para
contenido; HTTPS y otros transportes necesitan alcance y aprobacion separados.

Consulta [connectivity.md](connectivity.md) para el flujo de telefono.

## Paquetes extensibles

El requisito es contenido declarativo intercambiable, sin codigo ejecutable.
La separacion OO y los componentes propuestos arriba aun no hacen instalable
el runtime. El manifiesto generado actual no es el contrato publico vpetpack.
Faltan resolver recursos sin nombres fijos, formato publico, validador,
instalacion y migracion/activacion recuperables. La autenticidad por firma
necesita gestion de claves y no existe por tener hashes de integridad.
Consulta [content-packages.md](content-packages.md).

## Seguridad

El entorno de desarrollo conserva carga serial, logs y capacidad de recuperacion.
Secure Boot, Flash Encryption, bloqueo de interfaces y claves de produccion solo
se habilitaran en dispositivos destinados a usuarios finales. Consulta
[security.md](security.md).

## Catalogo adoptado y compatibilidad

`src/core/adopted_items.py` define los 40 consumibles adoptados el 2026-10-15.
`scripts/export_adopted_items.py` genera JSON de desarrollo, fichas oficiales,
sprites RGBA y `AdoptedItems.generated.h`. No se instala SQLite en ESP32.
`build_tdisplay.py` empaqueta estos iconos a 16x16 en `ui/items/*.vpa`.
`ConsumableEffects.h` y `PracticeBattle.use_item` ejecutan recuperacion
porcentual y bonos temporales sin modificar reglas de dano ni EV.
Mochila y Arena consumen el stock separado de objetos adoptados. El kit
inicial se migra una vez; victorias de practica otorgan un objeto mediante
rotacion determinista persistida. Manual y Guia no acumulan bonos.
Sim persiste `adopted_items` v1 dentro del JSON atomico; ESP32 usa las claves
aditivas `adoptBag`/`itemTx` con journal y recuperacion idempotente. La
operacion distingue rechazo, aceptacion pendiente y commit confirmado.
Solo un rechazo restaura efecto/stock; una confirmacion ambigua bloquea nuevas
acciones y muestra guardado pendiente hasta sincronizar y recuperar el journal.
El schema NVS principal permanece en 3. Registros incompatibles no se
sobrescriben con una mascota nueva. No cambia ningun enum antiguo.
Ver [adquisicion y limites](adopted-items.md). Validacion fisica pendiente.

## Tecnicas por etapa

El catalogo portable mantiene los indices 0 Golpe, 1 Llama y 2 Guardia;
agrega 3 Rafaga (Champion+, 4 lecciones) y 4 Inferno (Ultimate, 6 lecciones).
Firemon/Flamemon/Dragfiremon equipan 2/3/4. Aprender no equipa y evolucionar
no rellena espacios nuevos. Python y C++ usan el mismo poder, MP, recarga,
elemento y umbral. El rival Firemon conserva su catalogo inicial.
[Contrato y tablas](techniques.md).

NVS conserva schema 3 y techVer 1; agrega techM3/4 y extiende los bits de
techEquip. Los snapshots internos leen v1-v6; F2a agrega v5 con perfil y v6
agrega el locus sexual y los timers de supervivencia, conservando la recuperacion
atomica de partidas e intercambios. Dominio, recarga y usos de combate son
bytes acotados; Battle sigue por debajo del presupuesto de 256 bytes.

## Recuperacion de snapshots e intercambio

`sleepState` v1 agrega rutina y sesion de descanso sin cambiar schema NVS 3.
Se guarda junto con energia y premios; restaurar no acredita tiempo apagado.
Home usa calendario para dia/noche, no el estado de Motion. El sprite cansado
no inicia sueno ni interrumpe actividades. [Contrato completo](sleep-routine.md).

El guardado general usa `saveTx`, snapshot interno v6 cuando tiene perfil
individual y v4 para fixtures sin perfil (lector compatible con v1-v5),
rangos y terminador obligatorio. Primero registra el estado absoluto; despues
reproduce las claves legacy del schema 3. Omite escrituras de valores iguales.
`swapLive` y `swapBack` preparan snapshots separados (cada uno menor de 3800
bytes); `swapTx=1` acepta el intercambio de las dos mascotas. El marcador se
limpia solo despues de recuperar ambos lados. La carga recupera estas
operaciones antes de leer campos; registros incompatibles fallan cerrados.

Los snapshots historicos v1-v5 pueden omitir juntos `hunCritMs` y `eneCritMs`;
el lector inicia ambos en cero y conserva el resto del estado. El v4 transitorio
con ambos campos tambien se acepta. Una extension parcial y un v6 sin campos
obligatorios se rechazan. Este contrato aplica tanto a `saveTx` como a cuerpos
de Coleccion y al snapshot del diario compacto `colCare`.

F2a agrega `petProfile` v1 sin cambiar schema NVS 3. El mismo journal captura
identidad y progreso; la carga productiva guarda una migracion sin perfil
antes de permitir juego. La reserva se migra al intercambiarla. Versiones
historicas no borran el campo aditivo, y Pending no vuelve a generar identidad.
Ver [codec, entropia, compatibilidad y limites](individual-profile.md).

`StoreCommit` distingue Rejected/Pending/Committed. El adaptador conserva un
handle si NVS acepta un valor pero falla `nvs_commit`; `sync()` debe confirmar
ese handle antes de reproducir o iniciar otra operacion. No se interpreta un
fallo de confirmacion como rechazo del journal. Tampoco se usan lecturas de
cache como prueba de durabilidad. App conserva el modelo pendiente, bloquea
entrada y tiempo de cuidado, y reintenta una vez por segundo sin repetir el
efecto. Solo muestra exito cuando sync y recuperacion terminan.

`injuredMs` es opcional y acotado a seis horas; saves antiguos parten de cero.
Se guarda al cambiar el estado y cada minuto mientras hay herida. Un corte
puede perder como maximo el progreso desde el ultimo checkpoint; no se cuenta
tiempo apagado. Training/Arena mantienen la pausa de cuidado aprobada.
`VPET_READY` se emite despues de recuperar almacenamiento e iniciar el BLE
configurado. Las callbacks solo cambian estado atomico y usan nombre inmutable;
el desmontaje espera a detener el host antes de liberar sus objetos.

Ver [correcciones y pruebas](superpowers/plans/2026-10-15-board-audit-fixes.md).

`src/core/item_catalog.py` mantiene los siete objetos legacy activos:
IDs, nombres/descripciones ES/EN, familias, rareza, sprites, stock, efectos
tipados, magnitudes, duracion, limites y origen. No admite evolucion.
`scripts/export_item_catalog.py` genera `ItemCatalog.generated.h`, las fichas
de `docs/items-and-rewards.md` y siete PNG RGBA en `assets/ui/items/`.
La compilacion de assets comprueba que esas salidas esten actualizadas.
Inventario y nutricion Python consumen los datos; C++ consume los nombres,
iconos, cantidades y defaults generados. No se renumeran los seis IDs legacy,
Volver=6 ni las claves NVS; Guia=7 esta integrada tambien en T-Display.
El arte editable es pixel-art determinista en `scripts/item_icons.py` y se
exporta sin fondo para uso independiente, con marco neutral en el runtime.

## Exploracion en Make Sim y firmware

Port de placa del 2026-10-16: `Exploration` es un dominio C++ portable,
`ExplorationSession` controla opciones, `ExplorationUi` dibuja tablas en
Panels.cpp y App aplica transacciones completas. Navigation y MenuBar usan
nueve entradas; Exploration se agrega al final de PanelId sin renumerar.
La clave `expState` v1 se captura en snapshots `saveTx` v6 con perfil (v4 en
fixtures sin perfil); el lector conserva compatibilidad con v1/v2/v3/v4.
La hora fiable se valida separadamente del reloj de animacion; sin calendario
tras un corte de alimentacion se requiere ajuste manual. Durante viaje se pausan
cuidado/evolucion y las acciones no disponibles abren la expedicion.
Contrato y formato: [Exploracion](exploration.md).

La exploracion de Make Sim usa `core.exploration` para reglas deterministas,
`scripts/exploration_session.py` para transacciones/navegacion y
`scripts/exploration_renderer.py` para ES/EN a 240x135. El registro versionado
forma parte del snapshot de Pet; salida, premio, recibo y Guia se guardan con
reemplazo atomico JSON. `batch_commit` consume la Guia junto al EV de la sesion.
El reloj de expedicion del simulador avanza y se restaura con la partida.
El firmware usa el registro expState y la validacion de calendario descritos arriba.
Contrato detallado y pruebas: [exploration.md](exploration.md).

## Contrato de despliegue

`make deploy`:

1. Regenera recursos.
2. Ejecuta pruebas Python y C++.
3. Compila firmware y LittleFS.
4. Detecta chip, revision y flash.
5. Valida presupuesto de app, LittleFS, RAM estatica y heap.
6. Crea backup antes de la primera escritura administrada.
7. Carga sin borrar toda la flash ni NVS.
8. Reinicia y exige telemetria `VPET_READY` valida.

La placa no se considera desplegada solo porque `esptool` termino sin error.

## Cache de iconos Training (2026-10-16)

AssetStore conserva diez iconos estaticos Training de hasta 16x16 en RGB565
con mascara de opacidad. Desde 2026-10-25 esos 5840 bytes se reservan bajo
demanda y se liberan al invalidar Panels; no permanecen en la RAM estatica.
Una reserva fallida usa lectura directa sin perder el dibujo. La cache LRU
es independiente de las ocho paletas existentes, no crece con las especies
y se invalida al montar assets. No reserva otra pantalla ni cachea atlas
animados completos. Las lecturas usan el ancho del bitmap para aprovechar
el scratch de 1920 bytes: tres bloques para un cuadro 68x68 en vez de nueve.

Las regresiones ejecutan el adaptador real AssetStore.cpp sobre LittleFS/TFT
de host, contando E/S y comparando pixeles. La carga USB se verifico el
2026-10-17; medicion fisica de latencia/heap durante Training sigue pendiente:
[rendimiento de Training](training-board-performance.md).

Revision 2026-10-22: el selector Tecnicas/Volver dibujaba doce iconos sobre
una cache de diez. El footer reutiliza el buffer existente y evita reabrir
esos iconos por frame; la cadencia de preview Training/Tecnicas queda en
90/120 ms, sin cambiar Home/Arena ni agregar otro framebuffer. Usuario
acepta la mejora de NEXT y velocidad; matriz ampliada sigue pendiente.

## Presentacion De Descanso Y Ultima Entrega

Dia/noche depende del calendario (18:00..06:00), mientras luz apagada
oscurece mundo y pet independientemente del fondo. Home resuelve cansancio
y enojo mediante las reglas de cues existentes. Gotas y carita dormida
no tienen textos, contadores ni barras; sus metas/horarios siguen internos.

Dormido muestra el asset fijo Zzz despues del oscurecimiento. `AssetStore`
devuelve la primera fila opaca durante el dibujo normal, sin otra lectura;
Renderer centra el globo sobre el sprite visible y limita su posicion bajo
el menu. El sim usa bounds de la misma mascara. No agrega datos persistidos
ni otra animacion. [Posicion y evidencia](superpowers/plans/2026-10-23-sleep-bubble-position.md).

Ultima carga registrada ece6506: solo firmware, app/FS verificados, NVS
preservada y VPET_READY; usuario acepta posicion al acostarse. Esto no cierra
noche real, desaparicion al despertar ni cuatro paginas de Status.
La revision arquitectonica actual no compila, instala paquetes ni flashea.
