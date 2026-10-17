# Estado y alcance del proyecto

## Estado vigente: 2026-10-16

Roadmap actualizado: [prioridades vigentes](superpowers/plans/2026-10-11-delivery-roadmap.md).
Flamemon y Dragfiremon tienen Guardia, dano y emociones propias desplegadas.
La entrega de sprites paso 1077 pruebas Python; firmware/LittleFS coinciden
por digest con placa. Heap libre 72504, minimo 72436; filesystem
9404416/12451840; manifest 1. El ultimo arranque registro PAIRED/CONNECTED y
VPET_READY, no una prueba completa de reconexion movil.

El usuario reporta Training lento en placa: NO esta aceptado como fluido.
La nueva cache de diez iconos estaticos y lecturas agrupadas del retrato
reducen E/S en host, pero son posteriores al flash de sprites. Falta cargar
esta optimizacion y medir latencia/heap reales. Ver
[rendimiento de Training](training-board-performance.md).
Validacion local de la cache: 1078 pruebas Python aprobadas; compilacion
T-Display correcta, RAM estatica 56028/327680, flash 1007657/4194304 bytes.
Codigo, sprites, pruebas y roadmap publicados en origin/master: `bdcf027`.
La optimizacion de E/S sigue sin desplegarse; el flash anterior contiene
los sprites nuevos pero no esta cache.

Los numeros de exploracion siguientes son su corte previo, no los de la
ultima carga de sprites.

Exploracion portada y cargada a T-Display: nueve iconos, Patio/Jornada/Noche,
tablas ES/EN, retorno anticipado, cobro unico, recibo y Guia en entrenamiento.
El registro expState v1 usa snapshots atomicos v2 compatibles con v1, sin
cambiar schema principal 3 ni enums persistidos. Sin reloj respaldado, perder
el calendario exige ajustar Fecha/Hora antes de enviar o reclamar un viaje.

Evidencia final: 1067 pruebas Python, 172 nativas, 162 vectores numericos
sim/C++, 127 casos de UI y regresiones de App/persistencia. Firmware y LittleFS
verificados por digest en placa; heap libre 72644, minimo 72568, manifest 1.
La aceptacion visual fisica y del viaje en uso real continua abierta. Ese
arranque registro PAIR_FAILED; el arranque de sprites citado arriba lo
supera, sin cerrar la validacion prolongada de conectividad.
Contrato: [Exploracion](exploration.md). Evidencia y hashes:
[port de placa](superpowers/plans/2026-10-16-exploration-board.md).

El roadmap vigente sigue en
[Plan de cierre](superpowers/plans/2026-10-11-delivery-roadmap.md).
Los cortes inferiores son historia, no la lista actual de pendientes.

## Corte historico: 2026-10-11

Este bloque sustituye las afirmaciones de entrega del registro historico inferior.
El indice de pendientes vigente es
[Plan de cierre y siguientes entregas](superpowers/plans/2026-10-11-delivery-roadmap.md).

- Status, entrenamiento temporizado y tecnicas estan implementados en el
  simulador y firmware. La ultima carga de firmware y LittleFS termino con
  `Deploy OK`, `heap_free=109620`, `heap_min=55836`,
  `fs=5722112/12451840`, `manifest=1`.
- START inicia una sesion automatica de 10 segundos; al terminar aplica y guarda
  una vez. El contrato vigente es [Timed Training Contract](training-session.md),
  no el antiguo flujo de repeticiones manuales TRAIN/FINISH.
- El regreso a Home tras 10 segundos de inactividad esta implementado; no
  interrumpe entrenamiento ni combate activos. BACK tiene prioridad sobre NEXT
  en la cola de entrada. Ambos comportamientos requieren aceptacion fisica.
- Evidencia de la ultima ejecucion: 511 pruebas Python aprobadas, compilacion
  T-Display aprobada y prueba ampliada de 466 comparaciones de imagen ES/EN
  entre Python y el renderer C++ de Training/Tecnicas. No son fotografias de
  la placa ni certifican la paridad de todas las pantallas del juego.
- El usuario confirmo una mejora importante de Status. Aun falta confirmar
  en la ultima carga la salida por pulsacion larga, respuesta de NEXT,
  animaciones, ausencia de solapamientos y retorno por inactividad.
- Combate conserva diferencias de presentacion Python/C++: el panel Arena del
  firmware sigue usando una ventana de 1500 ms y la vista anterior. No marcar
  la paridad visual global como terminada.
- `vpet-ui-assets` y `vpet-pixel-art` son propuestas; no estan creadas ni
  instaladas para MiniMax. Exploracion y catalogo de recompensas no estan
  implementados.
- HEAD comprobado: `de63fd0`. Existen cambios locales y archivos nuevos sin
  seguimiento; estas entregas no constituyen un commit ni un push confirmado.

## Registro historico: corte 2026-10-07

Se conserva a continuacion como trazabilidad, NO como lista de pendientes vigente.
Las referencias a ausencia de despliegue, Training solo en simulador o FINALIZAR
manual describen ese corte y quedaron superadas por el estado del 2026-10-11.

Actualizado originalmente el 2026-10-07. El hash del HEAD era
`de63fd0 feat: add practice battles and targeted training` (con cambios
locales posteriores sobre `master`); no se asume un `commit` por omision.

## Confirmado

- El telefono detecta el vPet por BLE cuando el modo `ADVERTISING` esta activo.
- WiFi esta deshabilitado y no aparece en el menu del dispositivo.
- La navegacion de dos botones y las animaciones tienen una respuesta mas
  fluida que las versiones anteriores.
- El simulador y el firmware comparten recursos y reglas principales.
- La intro de arranque existe en ambos entornos, pero aun no se ha cargado a la
  placa despues del ultimo commit.
- `make sim-practice` y el icono de espadas abren directamente el combate
  determinista. `make sim-training` abre entrenamiento y tecnicas en la pesa.
  Ambos comandos comparten un guardado de preview separado de la partida normal.
- En el simulador Firemon tiene seis entrenamientos por atributo con iconos,
  coste de 8 ENE, ganancia de 6 EV y vista antes/despues. No cambia sus IV.
  Aprendizaje y dominio de tecnicas se abren desde la pesa; Guardia usa `block`.
- El motor de practica Python/C++ tiene trazas comparadas y pruebas nativas;
  la vista y persistencia NVS estan integradas en codigo y compiladas, sin
  despliegue ni validacion fisica del flujo nuevo.
- **Balance de entrenamiento v1 (simulador + tests deterministas)**:
  - Menu training: **3 ENE por sesion** (antes 0), **+1 EV en una stat
    elegida (off o spd)**, **cap 8 sesiones por ciclo de cuidado**
    (resetea con `reset_after_evolution`).
  - Dumbbell: sin cambio (8 ENE, +6 EV en cualquiera de 6 stats).
  - Wake-from-sleep / battle / feed: sin cambio (sus caps naturales —
    motion, dp+injury, ciclo overfeed — ya acotan los loops).
  - EV/ENE ratio v1: menu 0.33 EV/ENE, dumbbell 0.75 EV/ENE. El
    dumbbell sigue siendo el camino fuerte para maxar una stat; el
    menu es la sesion diaria barata. 31 pruebas en
    `tests/test_balance_sim.py` validan los 6 stats, energia
    insuficiente, caps, y comparan estrategias rest+dumbbell+menu.
  la vista y persistencia NVS estan integradas en codigo y compiladas, sin
  despliegue ni validacion fisica del flujo nuevo.
- **Sesion de entrenamiento por tandas (simulador, 2026-10-07)**:
  - Reemplaza el ciclo "presionar y el stat cambia" por
    `elegir > entrenar > revisar > confirmar`. Cada ACTION de
    entrenamiento = una repeticion; el costo se reserva y los EV se
    proyectan en paralelo a los valores reales sin mutar el pet.
  - Dominio (`src/core/training.py`): `training_index_for`,
    `batch_block_reason`, `batch_max_reps`, `batch_plan_one_rep`,
    `batch_projected_value`, `batch_apply`, `batch_commit` (snapshot
    pre-apply + rollback), `BatchSaveError`. Politica EV al tope:
    partial last-rep allowed (cabe 1 rep cuando headroom < 6),
    zero-gain reps bloqueadas cuando `pending_ev + real_ev >= 252`.
  - Orquestador (`scripts/training_session.py`): 5 estados
    (A select, B prepare, C session, D result, E error) con foco
    por estado, sub-estados confirm/cancel, save atomico via
    `batch_commit`, retry idempotente. `busy()` durante 1500 ms
    tras una rep bloquea solo ACTION con foco `train`; NEXT nunca
    se bloquea. Un toque = una repeticion.
  - Renderer (`scripts/training_renderer.py`): 7 vistas (select,
    prepare, session, confirm, cancel, result, error) reusando
    `pet_sprite`, `info_icon`, `info_label`, `icon_button`, `text`
    de `practice_renderer.py`. Bandas: header (y=0..19), sprite +
    datos (y=23..110), action buttons (y=115..132). En D muestra
    ANTES/CAMBIO/AHORA solo si el delta no es 0; no inventa `+1
    stat` cuando solo aumento EV.
  - Tests: `test_batched_training.py` (39, contrato transaccional
    y politica EV al tope, frozen pre-renderer) +
    `test_batched_training_ui.py` (57, bounds 240x135, no overlap,
    NEXT/ACTION/BACK, 6 atributos, freeze time, retry idempotente).
  - Previews reproducibles: 12 PNGs en
    `out/practice-preview/training-*.png` (select, select-def,
    prepare, session, session-cap, confirm, result, result-legacy,
    cancel, error, overview 4x2) via `scripts/preview_practice.py`.
  - Suite: 443/443 tests Python pasan en 48.75 s.
    `git diff --check` limpio. `sim.py --training` arranca sin
    errores bajo `SDL_VIDEODRIVER=dummy`.
  - NO firmware/NVS/BLE/WiFi. NO se modifico
    `out/board-backups/`. Plan completo + decisiones en
    `docs/superpowers/plans/2026-10-07-batched-training-session.md`.
- **Localizacion y resultado navegable del entrenamiento (2026-10-07)**:
  - Catalogo i18n (`src/core/i18n.py`): `TRAINING_STRINGS` y
    `STAT_STRINGS` con ES/EN, `tr(pet, key)` con fallback seguro a
    ES para lenguajes no soportados. El renderer no embebe strings
    visibles (verificado por
    `test_renderer_has_no_hardcoded_user_facing_strings` y
    `test_i18n_every_used_key_is_bilingual`).
  - Estado D partido en dos paginas navegables con NEXT:
    `RESULT_PAGE_SUMMARY` (tabla ANTES | +CAMBIO | AHORA con delta
    solo donde hubo cambio) y `RESULT_PAGE_STATS` (6 stats con
    barras compactas, escala documentada `round(ev / 252 * 96)` px,
    stat entrenado resaltado en amarillo). Indicador
    `RESUMEN | STATS` arriba a la derecha. ACTION/BACK vuelven al
    selector; NEXT solo flipea la pagina.
  - Previews bilingues: 16 PNGs nuevos en
    `out/practice-preview/training-{select,select-def,prepare,
    session,session-cap,confirm,result,result-stats}-{es,en}.png`
    mas `training-bilingual-overview.png` (8x2 grid 1920x540).
    Para que las barras del STATS page se vean utiles, el preview
    refleja el EV/ENE/ESF post-apply en el pet antes de capturar;
    el renderer nunca muta.
  - Tests: i18n (ES/EN/fallback/formato/keys faltantes/blacklist),
    dos paginas de D (NEXT toggle, ACTION returns, BACK returns,
    NEXT no avanza el state machine), barras (clamp 0..96,
    monotonia), extremos (EV 0/50/252, zero deltas, freeze time).
  - Suite: pasa completa. `git diff --check` limpio. NO se toco
    firmware, NVS, BLE, WiFi ni `out/board-backups/`. Plan
    actualizado con seccion 11 (catalogo, renderer, dos paginas,
    tests, previews, decisiones).
- **Menu Status T-Display 240x135 (2026-10-07, simulador + tests)**:
  - Direccion visual aprobada: barra superior de 8 iconos, selector
    amarillo, paleta y sprite actuales, mascota a izquierda y datos
    a derecha. Cabecera compacta `STATUS n/4`; filas alineadas con
    iconos, etiquetas y valores legibles.
  - Pagina 1/4 vital: HP de crianza (`stats["hp"]`), alimentacion
    (`stats["h"]`), energia (`stats["e"]`) con barras diferenciadas
    rojo/naranja/cian. El HP de combate (pool derivado de IV+EV)
    vive en la pagina 4/4 junto al codigo DNA para no confundir
    las dos metricas.
  - Pagina 2/4 care: 5 filas claras — EDAD (formato s/m/h/d segun
    magnitud), SOBREAL/OVERFEED, CUIDADO/CARE ERR, ESFUERZO/EFFORT,
    BATALLAS/BATTLES. Sin siglas tipo OF/CM. La primera fila
    acepta texto extra (reloj o llamada) en la segunda linea.
  - Pagina 3/4 battle: PESO/WEIGHT, DP (no renombrado), %VIC/WIN%,
    PROT/PROT, V-D/W-L. `--` cuando no hay encuentros. Layout
    apilado (label arriba, valor abajo) en las 4 fichas estrechas
    para que las etiquetas largas quepan.
  - Pagina 4/4 DNA (obligatoria): codigo completo `DNA: XX-XX-XX-XX`
    visible (fuente 10 px para caber en el strip de 92 px), helice
    rotando suavemente derivada de `now_ms` via `helix_spin`, 6
    stats HP/MP/OFF/DEF/SPD/BRN con barras en escala 0..99
    (`combat_stat`, no EV). El giro no muta ADN, IV, EV ni stats.
    Caso sin ADN con placeholder honesto.
  - Catalogo i18n extendido (`src/core/i18n.py`): claves
    `status.vital.*`, `status.care.*`, `status.battle.*`,
    `status.dna.*`, `status.header` con fallback seguro a ES.
    Helpers `tr_status_dna_label(pet, stat)` y
    `format_age(pet, total_seconds)`.
  - Tests: `tests/test_status_card.py` (10, contrato de filas y
    layout) + `tests/test_status_pages.py` (16, bounds, no-overlap,
    barras diferenciadas, helix rotando, render sin mutar, DNA
    completo, valores estables entre timestamps, i18n bilingue).
  - Previews: 10 PNGs + 1 GIF en `out/status-preview/`:
    `status-{1,2,3,4}-4-{es,en}.png`, `status-overview-{es,en}.png`
    (4x1 grid 1920x270), `status-helix-{es,en}.gif` (24 frames a
    100 ms cubriendo un giro completo de 2400 ms).
  - Suite: 489/489 tests Python pasan. `git diff --check` limpio.
    Smoke test `sim.py --max-frames 3 --training` OK.
  - **Limitacion firmware pendiente**: el layout apilado de las
    paginas 2/4 y 3/4, la fuente 10 px para el codigo DNA y el
    formato de edad adaptativo son features del simulador. El
    port a C++/firmware requiere verificar que la fuente 10 px
    esta disponible en el atlas del T-Display y que el cache de
    glifos cabe en la RAM del sprite. NO se ha desplegado a
    hardware.
- Fase 6 del combate de practica: balance afinado con pruebas deterministas
  (dano minimo 1, dano maximo ~62 con llama y stats maximas, MP no negativo,
  treinta rondas de empate, desobediencia segun vinculo y personalidad,
  compatibilidad con guardados antiguos sin clave `techniques`,
  `_draw_combatant` mostrando `hit` solo al atacante y `hurt` solo al
  defensor que pierde HP). El layout del simulador 240x135 ahora separa
  cuatro bandas: header con HP/MP de doble columna y barras de 46 px,
  feedback band de dos lineas explicitas (`PEDISTE <orden> -> HIZO
  <accion>` con R#X a la derecha, `MOTIVO: <razon real>` con dano de
  ronda `PRACT -X | FIRE -Y` a la derecha — `damage[i]` es el dano
  que fighter `i` inflige al oponente, por lo que `PRACT` recibe
  `damage[0]` y `FIRE` recibe `damage[1]` — color por categoria
  verde/rojo/amarillo/blanco/muted), action selector de 4 iconos con
  status de coste o disponibilidad (`PET DECIDE` / `COSTE N MP` / `SIN
  MP` / `RECARGA N` / `RECUPERA 4 MP` / `FIN BATALLA`) y banner terminal
  con outline de color por resultado. El mensaje generico "PET SUSTITUYO
  ORDEN" se elimino: cada sustitucion muestra la razon real devuelta por
  `choose()` (`SIN MP`, `EN RECARGA`, `PREFIERE DEFENDER`,
  `PREFIERE ATACAR`, `A SU CRITERIO`). 343 pruebas Python + 119 nativas
  C++ pasan; firmware compila; el simulador pinta frames de `hit`/`hurt`
  durante los 1.2 s del impacto, banner de resultado y label "PRACTICA".

## Pendiente de producto

- Definir el contenido descargable: pets, themes, bundles, metadata, licencias
  y limites de almacenamiento.
- Definir los nuevos pets, sus sprites, acciones, estadisticas y evoluciones.
- Implementar el esquema publico `.vpetpack` y su validador.
- Implementar el catalogo web y sus previews.
- Implementar instalacion inicial por USB/Web Serial.
- Implementar posteriormente aprovisionamiento WiFi y descargas HTTPS.
- Diseñar una app movil para estado, BLE y gestion de contenido.

## Pendiente tecnico

- Trasladar a C++ el entrenamiento por atributo y la nueva interfaz de
  pesa/tecnicas/combate con iconos. El firmware conserva el flujo anterior;
  la paridad del motor de combate no implica paridad de estas nuevas pantallas.
- Portar al firmware los frames de impacto (`hit`/`hurt`) y el banner de
  resultado del combate de practica; el simulador ya los muestra, el panel
  T-Display sigue con la vista anterior. El firmware usa 1500 ms para la
  ventana de animacion (`Panels.cpp: <1500>`), el simulador usa 1200 ms
  (`PRACTICE_IMPACT_MS`).
- Ajustar con pruebas de juego los costes y ganancias de entrenamiento.
- Conectar feedback de impacto con `hit`/`hurt` ya disponibles en el
  simulador (`PRACTICE_IMPACT_MS` = 1.2 s). `dodge` tambien existe en assets,
  pero no se usa para insinuar una evasion que el motor aun no calcula.
  Sprites sugeridos nuevos: victoria, derrota y ejercicios especificos.
- Igualar la intro: firmware usa un sprite Firemon fijo; simulador muestra
  texto FIREMON. Aun no usa la mascota guardada. La intro bloquea el arranque
  durante aproximadamente 2.2 segundos y no tiene pruebas dedicadas.
- Corregir divergencia de eclosion: App.cpp y config.py usan 2 segundos;
  el catalogo generado declara 8 segundos. La documentacion anterior decia 8.
- Revisar paridad de Status/DNA, descanso y guardado entre Python y C++.
  Son implementaciones separadas, aunque comparten recursos generados.

- Probar en la placa la intro posterior al commit.
- Confirmar el ciclo BLE `ADVERTISING -> CONNECTED -> ADVERTISING` desde el
  telefono y dejar evidencia serial.
- Añadir pruebas de regresion para la intro y los nuevos paquetes cuando se
  defina el contrato.
- Validar practica en pantalla y botones reales, restauracion NVS y BLE activo
  cuando se autorice el despliegue.
- Separar una configuracion de firmware de produccion con Secure Boot, Flash
  Encryption, OTA firmada y anti-rollback.

La board actual se mantiene como dispositivo de desarrollo. Ningun cambio se
considera validado fisicamente hasta que se cargue de forma explicita y se
pruebe en pantalla, botones y radio.
