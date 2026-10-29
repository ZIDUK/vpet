# Plan: Reintento De Combate Y Legibilidad

Spec: [SPEC-GAME-PLAYABILITY-001](../specs/2026-10-28-battle-retry-inventory-status.md).

1. Capturar registro USB del recorrido reportado sin modificar progreso.
2. Reproducir rechazo al guardar el resultado con App, LittleFS, politica y
   CareJournal; agregar rechazo de Coleccion e indisponibilidad de lectura.
3. Validar estado durable antes de desbloquear el reintento de adquisicion;
   conservar premio unico e informar fase de fallo.
4. Probar BACK durante tarea diferida; cerrar solo la navegacion.
5. Reorganizar columnas y aumentar iconos en ambos renderers. Comparar textos,
   valores maximos, no mutacion y vista previa.
6. Ejecutar regresiones/suite, native, build y spec-check. Respaldar NVS,
   cargar solo firmware y pedir prueba de combate con registro abierto.
7. Registrar observaciones fisicas y publicar commit/push autorizado.

## Trazas

- REQ-GAME-PLAY-008: `tests/test_esp32_learning_runtime.py::test_learning_scan_reuses_generation_streams_without_caching_validation` y las regresiones de App; ampliar medicion fisica antes de aceptar fluidez.

- REQ-GAME-PLAY-007 (propuesto): medir fases en placa; `tests/test_exploration_app.py::test_actual_app_exploration_clock_and_transactions` y las regresiones de experiencia son guardas funcionales, no benchmarks de latencia.

- REQ-GAME-PLAY-006: `tests/test_esp32_learning_runtime.py::test_policy_files_atomic_refs_and_runtime_recovery`, `tests/test_esp32_learning_runtime.py::test_actual_esp32_app_learning_hooks_and_review_fixes`, con `tests/posix_littlefs32.h`.

- REQ-GAME-PLAY-005: `tests/test_esp32_learning_runtime.py::test_actual_esp32_app_learning_hooks_and_review_fixes` (explore_policy, explore_collection, explore_unreadable).

- REQ-GAME-PLAY-004: `tests/test_esp32_learning_runtime.py::test_actual_esp32_app_learning_hooks_and_review_fixes` (training_policy, training_collection, training_unreadable).

- REQ-GAME-PLAY-001: `tests/test_esp32_learning_runtime.py::test_actual_esp32_app_learning_hooks_and_review_fixes`.
- REQ-GAME-PLAY-002: `tests/test_collection_app.py::test_collection_app_runtime_and_transactions`,
  `tests/test_status_pages.py::test_inventory_back_has_no_item_detail`.
- REQ-GAME-PLAY-003: `tests/test_status_pages.py::test_dna_icons_and_maximum_values_have_separate_columns`.

## Evidencia Inicial

Se aplican systematic-debugging y test-driven-development, ya consultadas en
esta sesion. Antes de cambiar produccion: falla el escenario de rechazo al
terminar combate por app.ready=false; falla BACK durante tarea diferida porque
no dibuja Home; falla el tamano minimo de iconos ADN (10 px previos).

Registro `out/board-backups/20261028-battle-pending-observation.json`: 300.053 s,
58 eventos de entrada, 29 muestras runtime, sin reinicios ni fallos fatales;
no aparece SAVE PENDING en esa captura. Se observa inicio de exploracion.
No acredita recuperacion del fallo original ni autoriza cancelar el viaje.

## Evidencia Final

### Final De Entrenamiento: 2026-10-29

El usuario reporta congelamiento al terminar entrenamiento antes de la tabla.
App confirma persistExperience de forma sincrona antes de dibujar Result.
ReadOnlyGeneration del colector de politicas hacia stat/open/seek/read/close
por cada bloque. La regresion real con dos mascotas y dos generaciones cuenta
44 aperturas, 44 cierres y 44 seeks antes del cambio y falla el presupuesto.

Se mantiene una lectura abierta por validacion de generacion, con posicion
continua y limites del archivo observado. size invalida la vista; finish cierra
y comprueba antes de aceptar referencias para GC. Destructor libera en errores.
No hay cache de cuerpos/CRC ni otro worker, framebuffer o formato de guardado.
Se agrega VPET_TRAINING_SAVE duration_ms/committed/pending para medir la pausa.
Las pruebas de corrupcion posterior y fallo de cierre preservan el bloqueo.
Verificacion: 2110 Python aprobadas (356.13 s, 13278 advertencias), 185 nativas,
13 focalizadas de aprendizaje/recuperacion; escaneo reforzado de corrupcion al
ultimo byte y cierre fallido repetido despues. Test aislado ejecutado: opens=2,
closes=2, seeks=2, frente a 44/44/44. spec-check: 6 specs, 30 requisitos.
Build final tdisplay correcto: app 1121317 y RAM estatica 53916 bytes.

Carga firmware-only completada, sin reemplazar LittleFS. SHA256 firmware
a36aad5a189aba86f37e47315b1a6d0098aacaccbca410f49c6ca7f64f6f1edc.
Respaldo NVS fresco out/board-backups/20261029-training-stream-critical.bin,
24576 bytes, SHA256 604b7714f85e0cca3bed958187fd3dda870320465af07242219538638388a80d.
Registro 20261029-training-stream-deploy.log: READY, heap libre 78340/minimo
58584, FS 11862016/12451840, manifest=1. El arranque posterior y HUB STORAGE
valid=1 constan en 20261029-training-stream-live.log. Se pide un entrenamiento
real al usuario; aun no se capturo VPET_TRAINING_SAVE ni aceptacion de fluidez.
Menos aperturas no prueba menor pausa de commit: queda por medir en placa.

### Ampliacion Exploracion

Nuevo reporte: SAVE PENDING al regresar de exploracion. Regresion explore_policy
falla antes del cambio: App queda bloqueada tras restaurar el viaje rechazado.
Los tres consumidores de experiencia comparten ahora recoverRejectedExperience
despues de su rollback; solo libera el bloqueo tras validar la vista durable.
El log VPET_EXPERIENCE_SAVE_REJECTED incluye context, stage y recovered.
No se cambian reglas de premios ni se cancela el viaje del usuario.

Captura anterior al cambio: out/board-backups/20261028-exploration-live.log,
120 s de observacion sin comandos, sin entradas ni regreso capturado.
No identifica el fallo inicial de escritura. Verificacion local y despliegue
de esta ampliacion pendientes.

### Causa Fisica Capturada Y Correccion De Nombres

En out/board-backups/20261028-exploration-fixed-live.log, el usuario pulsa CLAIM:
VPET_EXPERIENCE_SAVE_REJECTED context=exploration_claim stage=policy_publish
recovered=1, repetido tres veces. Confirma NOT SAVE RETRY; la recuperacion evita
el bloqueo global pero el primer rechazo sigue presente.

Lectura de 8192 bytes en 0x410000, sin escrituras, conservada en
out/board-backups/20261028-learning-superblocks.bin. El superbloque littlefs
declara version 0x20000, bloque 4096, 3040 bloques y name_max=32 (0x20 en offset
0x20 del primer bloque). El SDK permite 64 pero el volumen formateado conserva
32. Los nombres anteriores L+owner+secuencia+CRC tienen al menos 44 bytes.
Referencia de formato: https://github.com/littlefs-project/littlefs/blob/master/SPEC.md.

La regresion con rename limitado a 32 bytes falla al primer commit con la
implementacion anterior; no es una deduccion basada solo en el simulador.
Se publican claves de 26 bytes P+FNV64(sobre)+punto+CRC32(sobre). El sobre sigue
ligado al propietario y secuencia; hashes no autentican ni permiten sobreescribir
un contenido distinto. Se comprueban bytes antes de reutilizar un archivo.
Lectura legacy, GC de referencias de ambas generaciones y checksums preservados.

HUB STORAGE agrega diagnostico de solo lectura; inspect no borra huerfanos ni
sincroniza directorios. Los errores compartidos incluyen errno ademas de fase.
Verificacion final: 2109 Python aprobadas (359.93 s, 13278 advertencias), 185
nativas, 20 focalizadas de aprendizaje/Hub, build tdisplay correcto, app 1121077
y RAM estatica 53916 bytes. La regresion real de App tambien ejecuta rename con
limite de 32, no solo la prueba aislada del repositorio.

Carga firmware-only completada. SHA256
f8ace78761aac07f6501b9f68566740e1fc724aecb2b921a642686fb3daac73b.
Registro out/board-backups/20261028-learning-namefix-deploy.log: heap libre
78836/minimo 67892, FS 11845632/12451840, manifest=1. Respaldo fresco NVS
20261028-learning-namefix-critical.bin (24576 bytes, SHA256
df4ace1fc8a0b19d2078ad4951921b745bf8eb5824f9e37b11899e9ba8bb0a37).

Prueba fisica out/board-backups/20261028-learning-namefix-live.log:
HUB STORAGE valid=1 stage=none; una consulta de solo lectura enviada por el
agente, ningun comando de juego. CLAIM del usuario produce VPET_EXPLORE away=0
receipt=1 route=0 sin policy_publish. El usuario confirma que recoge y vuelve a
Home, pero reporta demora en CLAIM y Save del reloj. Pico de loop 7419575 us
alrededor de Claim, no una medicion aislada del handler; otro de 7210016 us sin
fase identificada. Minimo de heap posterior 26264 bytes: no cierra rendimiento.
Las comidas medidas siguen confirmando en 341-453 ms, no equivalen a CLAIM.

REQ-GAME-PLAY-007 queda propuesto: applyDateTime llama saveState sincrono y Claim
confirma experiencia/Coleccion en el hilo principal. Medir fases y disenar una
mejora segura separada; no afirmar que ya se acelero ni ocultar el error.
La aceptacion fisica de CLAIM cierra el fallo de nombres en ese recorrido, no
certifica todos los casos de combate/entrenamiento ni cortes de energia.
Un firmware anterior que solo lee nombres L no puede abrir referencias P;
no hacer downgrade sin un plan compatible. No se borra ni resetea aprendizaje.

### Ampliacion Entrenamiento

Reporte posterior: SAVE PENDING al entrenar. Regresion training_policy falla
antes del cambio: app.ready permanece false despues del rollback. Se amplia la
bandera de recuperacion a resultados rechazados de entrenamiento, sin incluir
guardados de cuidado aceptados. Error de entrenamiento no concede efectos;
permite otra sesion explicita tras validar la vista durable. Regresiones:
training_policy, training_collection y training_unreadable en App real.
- Regresiones nuevas: 3 passed; native 185/185; build tdisplay correcto,
  app 1120317 bytes y RAM estatica 53916. spec-check: 6 specs, 26 requisitos.
- Respaldo fresco `out/board-backups/20261028-training-critical.bin` (24576
  bytes), SHA256 `df4ace1fc8a0b19d2078ad4951921b745bf8eb5824f9e37b11899e9ba8bb0a37`.
- Firmware cargado sin reemplazar LittleFS ni NVS. SHA256
  `e59556c02727304d029b2ebe91c21a7d1832a94d0d847465ae1438ac06a76436`;
  `out/board-backups/20261028-training-deploy.log`: Deploy OK, heap libre
  78836, minimo 67892, FS 11845632/12451840, manifest=1.
- Capturas USB de 120 s antes y despues: `20261028-training-live.log` y
  `20261028-training-fixed-live.log` bajo `out/board-backups/`. Sin entradas ni
  entrenamiento capturado; arranque READY y 11 muestras runtime posteriores,
  sin fallo fatal ni reinicio posterior al arranque. Se solicito reproduccion.
  No acredita causa del primer rechazo fisico ni aceptacion de entrenamiento.
- Suite Python completa: 2106 passed, 13278 warnings, 396.61 s. Advertencias
  de deprecacion existentes; sin fallos. diff --check correcto.

### Entrega Anterior 48c9145

- Suite Python final: 2103 passed, 13278 warnings, 336.96 s. Las advertencias
  son deprecaciones existentes de Pillow/pytest; no hubo fallos.
- PlatformIO native: 185/185; build tdisplay correcto, app 1120173 bytes,
  RAM estatica 53916 bytes. spec-check: 6 specs, 25 requisitos, 59 targets.
- Recuperacion limitada por bandera RAM al rechazo del resultado de combate;
  nunca reutiliza este camino para un cuidado aceptado pendiente de confirmar.
- Vista previa `out/status-preview/status-overview-es.png` inspeccionada;
  columnas separadas e iconos mayores. No equivale a aceptacion visual fisica.
- Respaldo NVS fresco `out/board-backups/20261028-playability-critical.bin`,
  SHA256 `df4ace1fc8a0b19d2078ad4951921b745bf8eb5824f9e37b11899e9ba8bb0a37`.
- Carga solo firmware completada en ESP32 `08f9e0d00788`, sin reemplazar
  LittleFS. Registro `out/board-backups/20261028-playability-deploy.log`:
  VPET_READY, heap libre 78836, minimo 67920, FS 11845632/12451840.
  Firmware SHA256 `70c304dcc483e94126333a12d7a7a18cef61a7647daf9683ef575f6c06580116`.
- Observacion posterior de 120 s, sin comandos: registro
  `out/board-backups/20261028-playability-live.log`, 11 muestras runtime,
  sin entradas, fallos fatales ni reinicios posteriores al arranque.
  Se solicito al usuario probar batalla y BACK. No se capturo un combate ni
  SAVE PENDING; causa inicial fisica y aceptacion del recorrido siguen abiertas.
- Cambios preparados para commit/push autorizado. Implementado no significa
  aceptado en hardware; la entrega no se marca como release verificada.
