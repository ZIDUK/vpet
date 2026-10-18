# Arena: celebracion, escala y seleccion

Correccion del reporte fisico del 2026-10-18 (IMG_4002 y IMG_4003).

## Causas y comportamiento

- Victoria/derrota: el renderer C++ enviaba retratos de 88x88 al escalador
  con fuente por defecto 20x20. Ahora explicita 88, muestra una reaccion
  de 64x64 completa y anima desde el momento del resultado. Happy/sad
  corresponden a Firemon, Flamemon o Dragfiremon; empate usa idle.
- Arena elimina las lineas ORDER/DID/WHY y PEDISTE/HIZO/MOTIVO sobre los
  iconos. Conserva HP/MP, resultado, recompensa y etiqueta del selector.
- Assets de Arena propios en `/battle/`: celda 96x76, altura de referencia
  del cuerpo 60, suelo y=74. Se calibra una sola escala por clip usando
  su primera pose y la union de todos sus frames, conservando movimiento
  interno y efectos. No se recentra o reescala cada frame por separado.
- Python y el empaquetador C++ usan `scripts/battle_assets.py`. Las
  animaciones originales de Home/Status/Training permanecen disponibles.
- Llama usa cast cuando el resultado real indica que el pet la ejecuto;
  Guardia y hurt siguen el resultado de dano y el orden real de ataque.
- El cursor de Arena permanece en la opcion elegida tras cada ronda
  automatica o manual. Solo el resultado terminal cambia al menu de salida.
  El combate sigue avanzando mientras se navega, incluso en Mochila.
- Los iconos de tecnica se escalan desde sus 16px reales (los de UI usan
  20px). Reglas de obediencia, dano, elementos, EV y formato NVS conservados.

## Evidencia reproducible

- Regresion roja/verde Python: elegir Golpe, Guardia, Mochila o Retirarse
  no salta a AUTO al vencer el temporizador.
- Caso nativo de rondas automaticas registrado en el runner Unity, con
  comprobacion del cursor y la orden despues de dos rondas y ACTION.
- `tests/test_arena_panel.py` compila **Panels.cpp y AssetStore.cpp reales**
  con adaptadores host. 24 escenarios: ES/EN, tres especies, combate y tres
  resultados. Comprueba celebracion visible/animada y ausencia de feedback.
  El adaptador captura etiquetas, no rasteriza las fuentes TFT; esto no
  cierra la comparacion exacta de imagen sim/placa del roadmap.
- `tests/test_battle_assets.py`: misma altura entre idle/ataques, suelo
  estable, movimiento interno y efectos anchos dentro de la celda.
- Pruebas UI sustituyen los casos de texto retirado por ausencia de ese
  texto; conservan selector, costes, impacto, Guardia, KO y resultados.
- `scripts/preview_arena.py`: capturas ES/EN y GIF de las tres especies en
  `out/arena-review/`. No abre ni cambia la partida del usuario.

La aceptacion visual fisica de esta correccion sigue pendiente.

## Seguimiento IMG_4004: color y latencia

El usuario acepta la distribucion de la pelea, pero reporta sprites lentos,
colores alterados en el resultado y navegacion lenta en Exploracion.

- Causa del color: TFT_eSprite inicia `swapBytes=false`. El escalador recibia
  RGB565 nativo en ese lienzo temporal, mientras destino y paletas usan
  `swapBytes=true`. Se iguala el temporal; no se invierte la paleta global.
  La prueba host ahora reproduce el intercambio de bytes de `pushImage`:
  fallo antes del cambio, paso despues. Incluye rojo conocido y todos los
  pixeles de un retrato escalado de 88px con fondo y pies.
- Arena reutiliza el framebuffer estatico existente de Home para fondo y
  selector. Los iconos se reconstruyen solo al cambiar cursor, equipamiento
  o resultado. Tras calentar, solo los dos luchadores abren assets por frame.
  Se conserva el intervalo de animacion de 80ms y el impacto de 1200ms.
- Exploracion carga los nueve iconos una vez y restaura esa franja desde
  memoria. Rutas/Atributos refrescan en reposo cada segundo; cualquier boton
  sigue dibujando inmediatamente. Las paginas animadas refrescan cada 70ms.
- App invalida la escena de Home antes de prestar su memoria; al volver,
  Home recompone su fondo. `Panels::invalidate` descarta su cache. No hay
  un tercer framebuffer ni cambios en assets, balance, Training o NVS.
- Harness: igualdad de pixeles cache/sin cache en Arena y Exploracion,
  cambios de cursor y nueve selecciones de barra ES/EN, tres especies,
  invalidacion y retorno tras sobrescribir la memoria compartida. App real
  verifica reposo sin redibujos continuos y respuesta inmediata a NEXT.

Estas pruebas miden E/S y equivalencia host, no FPS ni latencia fisica.
La comprobacion visual de los colores y fluidez en placa sigue abierta.

Validacion del seguimiento: 1096 pruebas Python aprobadas (6460 avisos de
Pillow), 173 nativas, 180 frames pygame headless y compilacion T-Display.
RAM estatica 56036/327680 (+8 bytes), firmware 1007409/4194304.
La bateria completa tambien detecto una expectativa antigua de retrato 48px;
se actualizo a 64px manteniendo igualdad pixel a pixel en los 15 frames.
Assets sin cambios: LittleFS instalado verificado por digest antes de cargar
firmware. Respaldo particiones/NVS nuevo en
`out/board-backups/20261018-color-performance/08f9e0d00788-20261018-083945-critical.bin`.

Validacion local del 2026-10-18: 1096 pruebas Python aprobadas, 173 nativas,
180 frames del simulador pygame en modo headless sin error, compilacion
T-Display y LittleFS correctas. RAM estatica 56028/327680, firmware
1007025/4194304 bytes. Assets: 202 archivos, 10497318 bytes antes del
filesystem. Las cifras de build no sustituyen el espacio usado en placa.

## Despliegue del 2026-10-18

Carga de firmware y LittleFS completada: `Deploy OK`, heap libre 66656,
minimo 66580, filesystem 11292672/12451840 y manifest 1.
`verify_flash` confirma ambos binarios por digest (firmware en 0x10000,
LittleFS en 0x410000). Respaldo nuevo conservado en
`out/board-backups/20261018-arena-fixes/08f9e0d00788-20261018-081340-critical.bin`.
Logs locales: `out/arena-board-deploy/`.
Arranque final observado durante 18 segundos: `ARENA_BOARD_BOOT_OK` y
`VPET_READY`, heap libre 66660, minimo 66584; BLE CONNECTED/PAIRED.
Sin VPET_FATAL, Guru Meditation, brownout ni abort durante esa ventana.
La clave opcional swapTx ausente emitio NOT_FOUND; el arranque continuo.

SHA-256 firmware:
`d950d48b9c6bb954a99f16efc813eafaed9d086c0da55c29b3ea6965680e9831`.
SHA-256 LittleFS:
`e6bccba9af18786d60f8512b4f480dd991c5f943737d2be19704c64147742563`.

## Despliegue del seguimiento IMG_4004

Firmware corregido cargado el 2026-10-18, sin reescribir LittleFS ni borrar
NVS. `verify_flash` confirma firmware y assets por digest en 0x10000 y
0x410000. Arranque observado 18 segundos: `COLOR_PERFORMANCE_BOARD_OK`,
`VPET_READY`, heap libre 66512, minimo 66440, filesystem
11292672/12451840, manifest 1. BLE ADVERTISING/PAIRED/CONNECTED; llamada
HUNGER del pet. Sin fatal, Guru Meditation, brownout ni abort observado.
La clave opcional swapTx ausente sigue registrando NOT_FOUND sin bloquear.

SHA-256 del firmware corregido:
`41cf777a609a1f596c29c52b7b85c267427a3b4c1e24b7fae137e80a2a6d587c`.
LittleFS conserva el digest anterior. Logs y pruebas en
`out/color-performance-board-deploy/`. Pendiente confirmacion visual del
usuario para colores y fluidez; no se ha medido FPS fisico.
