# Combate de practica: plan de implementacion

## Revision vigente: 2026-10-11

- [x] Entrenamiento por atributo y Tecnicas integrados en C++ y desplegados,
  con recursos generados y arranque confirmado. Ya no son pendientes de port.
- [x] Entrenamiento automatico de 10 segundos; contrato en
  [training-session.md](../../training-session.md).
- [x] Paridad de Training/Tecnicas comprobada por comparacion de imagen ES/EN.
- [ ] Paridad de la pantalla Arena: `Panels.cpp::drawPractice` conserva el
  renderer anterior y 1500 ms de animacion, frente al feedback de impacto del
  simulador. Portar el feedback y verificarlo sin modificar el balance.
- [ ] Aceptacion fisica: botones, persistencia y combate con BLE activo.

La carga y la telemetria de arranque NO sustituyen esta aceptacion.
El resto del documento conserva el registro original; sus frases "no se ha
desplegado" y "portar entrenamiento" no describen el estado actual.
Pendientes priorizados: [plan de cierre](2026-10-11-delivery-roadmap.md).

## Plan y seguimiento historicos

**Objetivo:** Firemon contra un rival de practica, con golpe, llama y guardia,
HP/MP separados de crianza, orden del jugador y decision explicable del pet.
**Arquitectura:** motor determinista portable Python/C++, progreso independiente
del encuentro, UI de dos botones en el simulador. Se conserva combate legado
para las demas especies. No hay cargas a la board en este trabajo.
**Stack:** Python/Pillow/pygame; C++ portable/PlatformIO. Sin TinyML inicialmente.

## Contrato v1

- IV/EV existentes alimentan HP/MP/OFF/DEF/SPD/BRN (1..99).
- HP max = 40 + HP*2; MP max = 10 + MP. Distancia fija corta (1).
- Golpe: potencia 12, coste 0, alcance 1, enfriamiento 0.
- Llama: potencia 24, coste 8, alcance 2, enfriamiento 1 ronda completa.
- Guardia: coste 0, reduce dano a la mitad esa ronda y recupera 4 MP.
- Dano = max(1, potencia + OFF/3 + dominio/20 - DEF/4), enteros.
- Velocidad define orden; empate alterna por ronda. Guardia se prepara antes
  de los ataques. Si cae un actor, no ejecuta su ataque.
- 30 rondas como limite: empate. Sin heridas, consumo de DP ni victorias
  oficiales en practica; no acelera requisitos de evolucion.
- Orden invalida se rechaza; una orden conocida sin MP o en enfriamiento puede
  sustituirse por otra valida con motivo visible.
- Personalidad deriva de DNA[3] modulo 3. Vinculo 0..100 pesa en obediencia.
- Progreso: golpe y guardia conocidos; llama tras 2 entrenamientos de tecnica.
  Dos tecnicas equipadas, nunca cero. Dominio 0..100, +1 por uso al completar
  encuentro; entrenar cuesta 4 energia y suma 5 dominio. Abandonar no premia.
- Guardado antiguo sin progreso recibe defaults; progreso persiste al evolucionar
  y se borra al iniciar nueva vida. Los previews usan un JSON separado; el
  adaptador firmware guarda progreso en claves NVS opcionales.

## Fases y archivos

1. Contrato y motor: `src/core/practice.py`,
   `firmware/t-display/lib/vpet_core/src/vpet/PracticeBattle.h`.
   Probar damage, cooldown, MP, muerte, empate y determinismo en
   `tests/test_practice.py`; comparar trazas Python/C++ con compilador nativo.
2. Tecnicas/progreso: `src/core/techniques.py`, `src/core/pet.py`.
   Serializar progreso versionado y sanitizar saves; preservar IV/EV.
3. Encuentro: integrar ronda y resultado unico en `scripts/practice_session.py`.
   No invocar `finish_battle` ni contabilizar resultados de practica como oficiales.
4. UI: `scripts/practice_renderer.py`, `scripts/sim.py`. Espadas abre la batalla
   directamente; Pesa abre entrenamiento/tecnicas. NEXT selecciona, ACTION
   confirma; resultado requiere
   confirmacion. Pausar crianza/evolucion durante sesion. Capturas a 240x135.
5. Autonomia: puntuar acciones con personalidad, vinculo, HP, MP, cooldown;
   mostrar motivo de sustitucion. Casos repetibles con distinta personalidad.
6. Balance/firmware: compilar motor en firmware y ejecutar encuentros por lotes.
   Adaptar UI y persistencia NVS despues de revisar el prototipo; medir BLE/heap
   en hardware solo cuando el usuario solicite despliegue.

## Verificacion

```sh
.venv-platformio/bin/python -m pytest tests/test_practice.py -q
.venv-platformio/bin/python -m pytest -q
.venv-platformio/bin/pio run -d firmware/t-display
SDL_VIDEODRIVER=dummy .venv-platformio/bin/python scripts/sim.py --profile tdisplay --build-dir build-tdisplay --practice --max-frames 60
```

## Seguimiento

- [x] Fases 1-3: contrato, progreso y motor local.
- [x] Fases 4-5: UI y autonomia local.
- [x] Fase 6: 24 encuentros deterministas comparados Python/C++ y compilacion.
- [x] Fase 6: extension de cobertura a 56 escenarios (punch + flame + guard,
  personalidades 0/1/2, dominio 0..100, equipo variable). El harness nativo
  C++ ahora produce ambas ventanas; la prueba `test_python_cpp_round_traces_*`
  las compara fila por fila.
- [x] Fase 6: ajuste de balance cubierto por pruebas deterministas
  (daño minimo y maximo, MP no negativo, victoria/derrota/empate, desobediencia
  segun vinculo y personalidad, compatibilidad con guardados sin `techniques`).
- [x] Fase 6: revision UX del simulador con `hit`/`hurt` durante el impacto,
  banner visible de victoria/derrota/empate, label "PRACTICA" en lugar de
  "RIVAL" y aviso explicito cuando el pet sustituye la orden del jugador.
- [x] Fase 6: UI/persistencia firmware conectada y compilada; 119 pruebas nativas.
- [x] Fase 6: revision UX del simulador cierra el primer bloque (impacto,
  banner, label, sustitucion). `_draw_combatant` deriva el sprite del
  resultado real: `hit` solo en el atacante, `hurt` solo en el defensor que
  perdio HP, con el orden por velocidad para romper la simetria del
  intercambio simultaneo.
- [x] Fase 6: revision UX del simulador cierra el segundo bloque
  (items 3 y 4). El feedback band ya no muestra el mensaje generico
  "PET SUSTITUYO ORDEN"; en su lugar pinta dos lineas explicitas:
  `PEDISTE <orden> -> HIZO <accion>` (verde si obedecio, rojo si
  sustituyo) con R#X a la derecha, y `MOTIVO: <razon real>` con dano
  de ronda `PRACT -X | FIRE -Y` a la derecha, donde `damage[i]` es
  el dano que fighter `i` inflige al oponente: `PRACT` recibe
  `damage[0]` (lo que Firemon le hizo) y `FIRE` recibe `damage[1]`
  (lo que Practica le hizo). La razon se pinta en
  verde para `SIGUE ORDEN` y `RECUPERA`, rojo para `SIN MP` y
  `EN RECARGA`, amarillo para `PREFIERE DEFENDER` / `PREFIERE ATACAR`,
  blanco para `A SU CRITERIO` y gris para `ESPERANDO ORDEN`. El header
  de 240x135 muestra HP/MP en doble columna con barras de 46 px de
  ancho y 6 px de alto, icono + label + barra + numeros
  right-aligned. El action selector expone `PET DECIDE` para AUTO,
  `COSTE N MP` en cian para tecnica disponible, `RECUPERA 4 MP` en
  verde para guardia, `RECARGA N` y `SIN MP` en rojo para tecnica
  bloqueada, y `FIN BATALLA` en amarillo para RETIRARSE. El banner
  terminal usa outline verde/rojo/amarillo segun el resultado. 24
  pruebas nuevas validan el color, texto y limites de cada banda en
  el render nativo.
- [ ] Fase 6: el panel firmware del combate sigue usando la vista anterior;
  todavia no pinta los frames `hit`/`hurt` ni el banner de resultado. Pendiente
  de portar la nueva UX a la T-Display. Duracion del impacto: 1500 ms en el
  firmware (`Panels.cpp`), 1200 ms (`PRACTICE_IMPACT_MS`) en el simulador.
- [ ] Fase 6: BLE/heap y aceptacion fisica tras autorizacion.

Las etapas nuevas, rival definitivo, aprendizaje por observacion y TinyML quedan
fuera de v1. El rival usa el sprite Firemon espejado y se identifica PRACTICA.

## Diferencias Python / C++ documentadas (Fase 6)

El motor portable de combate (`firmware/t-display/lib/vpet_core/src/vpet/PracticeBattle.{h,cpp}`)
y su envoltura de sesion (`PracticeSession.h`) coinciden con la implementacion
Python (`src/core/practice.py` y `scripts/practice_session.py`) en la formula
de dano, el orden por velocidad, los enfriamientos y los resultados. El
round-trip de 56 escenarios en `tests/test_practice.py` lo confirma con trazas
byte a byte. Quedan estas diferencias intencionales, sin impacto en la partida:

- **Default personality**: el `Fighter` de C++ arranca con `personality = 1`
  para que el rival generico (el que crea `PracticeBattle` sin rival explicito)
  tienda a defender; el de Python arranca con `personality = 0` y se sobreescribe
  en cada llamada con un `personality` explicito.
- **Etiquetas de desobediencia**: `PracticeSession::input` calcula la razon en
  sitio y solo emite `"SIN MP"` cuando la orden es flame (`order == 1`) y el
  MP es insuficiente. Python distingue MP y cooldown para cualquier tecnica.
  La traza numerica coincide; la etiqueta humana es menos detallada en C++.
- **Razon fallback "RECUPERA"**: Python devuelve esa cadena cuando el pet no
  tiene ninguna accion valida. En C++ `choose()` siempre retorna 2 (guard)
  porque guardia no consume MP ni cooldown, por lo que la cadena no se usa.
- **Frames de impacto (`hit`/`hurt`)**: solo se dibujan en el simulador. El
  panel firmware sigue mostrando el sprite de accion durante los 1500 ms de
  animacion; la nueva vista de banner esta pendiente de portar. El
  simulador los pinta durante 1200 ms (`PRACTICE_IMPACT_MS`) y los elige
  con `_draw_combatant` segun las acciones/resultado de la ronda.
- **Banner victoria/derrota/empate**: solo presente en el simulador. El
  `EMPATE`) sobre la franja inferior.

Ninguna de estas diferencias altera el motor, las estadisticas, el
enfriamiento o el resultado; son solo cuestiones de presentacion y de los
valores por defecto del rival.

## Estado de la entrega local

El motor C++ esta conectado a App/Panels y NVS mediante PracticeSession y
PracticeProgress. La practica pausa el tick de cria durante la sesion.
No se ha desplegado firmware. Las cifras de RAM del compilador no validan el
heap con BLE activo. El alcance es metadata: la arena v1 mantiene distancia 1.
Los encuentros son por rondas a demanda, sin movimiento tactico ni TinyML.
En el simulador se muestran las animaciones existentes de golpe/llama y `block`
para guardia. El renderer firmware conserva la vista anterior.

El aprendizaje por etapas posteriores a Firemon y los efectos de estado quedan
pendientes de diseno. El progreso se persiste en JSON y en claves NVS tech*;
los IV/EV existentes se conservan, no se vuelven a sortear durante combate.

Para revisar cuatro pantallas reproducibles sin tocar partidas:
`.venv-platformio/bin/python scripts/preview_practice.py`.

## Revision UX del 2026-10-06 (simulador)

- [x] Iconos junto a vida, MP, atributos, vinculo y datos de tecnicas.
- [x] La pesa abre seis atributos y una entrada a aprendizaje/dominio de tecnicas.
- [x] Espadas abre directamente la batalla con las tecnicas equipadas. No hay
  menu de preparacion. Consultar/equipar queda en Pesa > Tecnicas; retirarse o
  confirmar el resultado devuelve a Home con las espadas seleccionadas.
- [x] Entrenamiento por atributo: 8 ENE, 6 EV, tope 252; IV intactos. HP maximo
  sube 2 y los otros valores 1 por sesion completa. Si se alcanza el tope, la
  ganancia se limita. No cura HP ni aumenta ENE de crianza.
- [x] Cada sesion suma al contador, aumenta esfuerzo 8 y animo 3 (maximo 100),
  y reduce peso 1 (minimo 0). Estas sesiones no desbloquean Llama: sus lecciones
  separadas cuestan 4 ENE cada una y se abren en Pesa > Tecnicas.
- [x] `make sim-training` y previews reproducibles de entrenamiento y bloqueo.

## Balance v1 del entrenamiento (2026-10-07, simulador + tests)

Auditoria pre-v1 (`tests/test_balance_sim.py` evidencia):

- Menu training era gratis y sin cap: 0 ENE por sesion, +2 off +1 spd,
  sin tope. Spam produce 126 sesiones para capear off y 252 para capear
  off+spd, todo por 0 ENE. EV/ENE ratio = infinito.
- Dumbbell mantiene 8 ENE / +6 EV (0.75 EV/ENE). Sin cambios en v1.
- Battle free EV (+1 off, +1 brn) acotado por dp e injury (4 battles
  consecutivos antes de injury).
- Wake-from-sleep (+2 mp, +1 def) acotado por motion state.
- Feed (+2 hp EV si h<100) acotado por ciclo overfeed (1 vez por ciclo
  de hambre).

Tabla de balance v1:

| Path | ENE | EV / sesion | Cap natural | EV/ENE | Cap en 1 ciclo |
|---|---|---|---|---|---|
| Menu training (off o spd) | 3 | +1 en stat elegida | 8 sesiones / ciclo | 0.33 | 8 EV |
| Dumbbell (6 stats) | 8 | +6 en stat elegida | 252 EV / stat | 0.75 | 252 EV |
| Wake (mp, def) | 0 | +2 mp, +1 def | motion state | ∞ | 2/1 EV |
| Battle (off, brn) | 0 | +1 off, +1 brn | dp + injury | ∞ | ~4 EV |
| Feed (hp) | 0 | +2 hp | overfeed cycle | ∞ | 2 EV |

Reglas v1 nuevas (documentadas, no silenciosas):

- `MENU_TRAIN_ENERGY_COST = 3` — menu training ahora cuesta 3 ENE.
- `MENU_TRAIN_EV_GAIN = 1` — gana 1 EV en la stat elegida (off o spd).
- `MENU_TRAIN_SESSION_CAP = 8` — maximo 8 sesiones de menu training por
  ciclo de cuidado; `reset_after_evolution` lo resetea.
- `MENU_TRAIN_STATS = ("off", "spd")` — el menu solo entrena una de
  las dos; el jugador alterna con `menu_train_stat` en
  `activate_menu_item`.
- Nueva clave NVS `menu_train_sessions` (default 0 en saves antiguos).

Trade-off v1: el dumbbell sigue siendo 2.27x mas eficiente en EV/ENE
que el menu, y es el unico camino realista para capear una stat en un
solo ciclo. El menu es la sesion diaria barata para ir sumando 1 EV
sin esperar el dumbbell.

Cumplimiento de criterios PO:

- Trade-off real entre elegir atributo: elegir stat en menu
  (off o spd) es excluyente; dumbbell cubre los 6.
- Coste/gain visible refleja el real: dumbbell renderer sigue
  mostrando `COSTE 8 ENERGIA` y `MEJORA +%d`; menu no tiene UI
  dedicada todavia (es accion instantanea en `activate_menu_item`).
- Sin farming absurdo: cap de 8 sesiones/ciclo en menu; caps
  naturales en battle/wake/feed.
- Esfuerzo/animo/peso: menu training suma +2 effort y +1 p; dumbbell
  suma +8 effort y +3 p. La diferencia escala con la inversion.
- [x] El simulador ahora pinta `firemon_hit_atlas.bmp` en el atacante y
  `firemon_hurt_atlas.bmp` en el defensor durante `PRACTICE_IMPACT_MS` (1.2 s);
  los sprites estaban en assets pero no se enlazaban al combate.
- [x] Banner de resultado visible en el simulador (VICTORIA verde, DERROTA
  rojo, EMPATE amarillo) con resumen, ronda final y mensaje de guardado.
- [x] Mensaje "PET SUSTITUYO ORDEN" eliminado. La franja de feedback
  ahora muestra siempre la razon real devuelta por `choose()` con color
  por categoria (verde ok, rojo bad, amarillo warn, blanco neutral, gris
  muted) y dano de ronda `PRACT -X | FIRE -Y` a la derecha, donde
  `damage[i]` es el dano que fighter `i` inflige al oponente (PRACT
  recibe `damage[0]`, FIRE recibe `damage[1]`). AUTO se identifica
  explicitamente con el icono `auto` y label `PET DECIDE` en el action
  selector. El renderer se valida con un helper de captura de texto
  (`_capture_text`) que registra el orden y contenido real de las
  cadenas pintadas, no solo el color de los pixeles.
- [x] Pruebas deterministas de balance: dano minimo y maximo, MP no negativo,
  treinta rondas de empate, desobediencia segun vinculo y personalidad, y
  compatibilidad con guardados sin clave `techniques`.
- [x] Pruebas renderer para los estados del combate: obedece (verde),
  sustituye por SIN MP (rojo), sustituye por EN RECARGA (rojo),
  sustituye por PREFIERE DEFENDER/ATACAR (amarillo), AUTO (icono + PET
  DECIDE), coste/RECUPERA en cian/verde, SIN MP/RECARGA en rojo, dano
  por ronda, banner VICTORIA/DERROTA/EMPATE, y verificacion de que
  todo el texto cae dentro de 240x135 sin solapamientos.
- [ ] Portar reglas de entrenamiento y nuevos layouts/iconos a C++; comparar
  trazas antes de afirmar paridad. No se ha desplegado a hardware.
- [ ] Portar al firmware el banner de resultado y los frames de impacto.
- [ ] Validar visualmente con sprites de victoria/derrota dedicados cuando se
  generen; los `agumon_victory` y la falta de un sprite de derrota siguen
  pendientes.

Los sprites `hit`, `hurt` y `dodge` ya existen en los assets. `dodge` no se
usa todavia: la evasion no forma parte del motor v1 y mostrarla sin reglas
reales confundiria al jugador. El plan solo agrega feedback de impacto real.

## Items UX/UI 3 y 4 de Fase 6 (2026-10-07)

- [x] **Item 3 (orden real del jugador + accion del pet)**: la franja de
  feedback pinta dos lineas explicitas: `PEDISTE <orden> > HIZO <accion>`
  (verde cuando coinciden, rojo cuando no) + `MOTIVO: <razon real>`.
  Sustituye al placeholder generico "PET SUSTITUYO ORDEN". Constantes
  `REASON_LABELS` / `REASON_CATEGORY` / `REASON_COLORS` y helper
  `_order_icon` / `_action_icon` en `scripts/practice_renderer.py`.
  Helper `_capture_text` para que los tests validen contenido, no
  solo pixeles.
- [x] **Item 4 (dano bidireccional)**: el dano de ronda `PRACT -X | FIRE -Y`
  se pinta en la franja de feedback con el dano que cada fighter
  infringe al oponente. `damage[i]` es el dano que fighter `i` infringe;
  por tanto PRACT recibe `damage[0]` y FIRE recibe `damage[1]`.
  Correccion del bug donde PRACT y FIRE estaban invertidos en la
  primera entrega.

## Coordinacion con la sesion de entrenamiento por tandas

El plan `2026-10-07-batched-training-session.md` reescribe el flujo
del menu training (estado A→B→C→confirm) sobre el mismo balance v1
documentado aqui. No hay cambios en este plan de combate; la
coordinacion es:

- El menu training v1 (`3 ENE / +1 EV / cap 8`) sigue vigente y se
  prueba en `tests/test_balance_sim.py`.
- El dumbbell (`8 ENE / +6 EV / 252 stat`) sigue siendo el camino
  fuerte y se prueba en `tests/test_batched_training.py`.
- La UI del dumbbell ahora se sirve desde `scripts/training_renderer.py`
  con 7 vistas (select, prepare, session, confirm, cancel, result,
  error) reusando los helpers de `scripts/practice_renderer.py`.
- 39 tests de dominio + 57 tests de UI cubren contrato transaccional,
  politica EV al tope, bounds 240x135, no overlap, NEXT/ACTION/BACK,
  freeze time y retry idempotente.
- 443/443 tests Python pasan (`pytest -q`, 48.75 s).
- `git diff --check` limpio. `sim.py --training` arranca sin errores
  bajo `SDL_VIDEODRIVER=dummy`. No se toco firmware, NVS, BLE, WiFi
  ni `out/board-backups/`.
