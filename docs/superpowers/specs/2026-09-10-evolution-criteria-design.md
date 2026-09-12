# Evolution Criteria And Care Trace (Corte 1)

Diseño de implementación para **Fase 0 + esqueleto de Fase 1** del
[research COLOR](2026-09-10-digimon-vpet-research.md). GPS y caca siguen
fuera. **Sí entran en el producto** (cortes siguientes, persistidos desde
schema 2+): Jogress, ramas, proteína / DP / peso y win ratio como candado
de Ultimate. No hay SLM en el ESP32.

Fuente de cría: Digital Monster COLOR. La placa es la T-Display clásica
(ESP32 sin PSRAM). El simulador y `vpet_core` deben usar la **misma**
función de chequeo y la **misma** tabla.

## Goal

Una partida nueva eclosiona, llega a Firemon sola y a Flamemon / Dragfiremon
con reglas publicadas en Pedia. Dejar a Sparkmon sin comer produce un Call
visible; ignorarlo suma care mistakes; evolucionar los resetea. El firmware
deja de evolucionar solo el huevo.

## Decisiones ya cerradas

| Tema | Decisión |
|---|---|
| Timers | COLOR reales en catálogo. Placa `CARE_TIME_SCALE = 1`. Sim `600`. |
| GPS | Fuera. No hay chip ni IMU. |
| Tiny model | Más adelante en el iPhone. Narra y/o clasifica rasgo. **No decide evos.** |
| Trazabilidad | Schema B: contadores COLOR + `CareSnapshot` + anillo de 32 eventos. |
| Iconos | Siguen siendo 8. Call es badge, no menú. |
| Battle | Corte 1: cada Battle cuenta 1. Desde Fase 3, win/loss real. **Win ratio ≥ 60% es candado** de Flamemon → Dragfiremon. |
| Placa debug | Options `EVOLVE` fuerza la siguiente forma y reproduce la animación (igual que `e` en el sim). |
| Options UI | Letra grande (4 filas). Cada `NEXT` corto baja una fila al instante, sin auto-avance. `BACK` largo no cierra Options. Se sale por la fila `BACK`. |

## User Flow

1. Huevo eclosiona a Sparkmon a los 8 s (sin scale). Ya existe.
2. Sparkmon acumula `stageAge`. Si hambre o energía llegan a 0, hay Call.
   10 min COLOR (`600 s / CARE_TIME_SCALE`) sin Feed / Rest → `+1` CM.
3. Al cumplir **12 h 10 min** COLOR y `careMistakes <= 1`, evoluciona a
   Firemon, anima `Motion::startEvolution` y resetea el snapshot de forma.
4. Firemon: **24 h** COLOR + barras actuales (H/E/P ≥ 55, HP ≥ 75) → Flamemon.
5. Flamemon: **36 h** COLOR + **15** `battlesThisForm` + **win ratio ≥ 60%**
   → Dragfiremon. En Corte 1 el ratio vale 0/0 (no bloquea) hasta que
   Battle registre win/loss. En Fase 3 el candado se enciende.
6. Pedia muestra esos umbrales. Ya no dice `REQUIREMENTS NOT DEFINED` en
   Sparkmon ni Flamemon.
7. Sim `e` y Options `EVOLVE` fuerzan la siguiente forma y cierran el
   panel para ver la animación.

Si `careMistakes >= 2` al vencer el timer de Sparkmon, **no evoluciona
por timer**. La rama oscura (Rookie descuidado) entra en el corte de
ramas: silueta `???` jugable hasta tener sprite. `EVOLVE` de debug sigue
la línea “buena” (Firemon → Flamemon → Dragfiremon).

## Línea y timers

Sparkmon colapsa COLOR I + II. El reloj de etapa corre también dormido.

| De | A | `minStageAgeSeconds` (scale 1) | Extra | Sim @ 600 |
|---|---|---|---|---|
| Egg | Sparkmon | 8 (hatch, no usa `Evolution`) | — | 8 s |
| Sparkmon | Firemon | `43800` (10 min + 12 h) | `careMistakes <= 1` | ~73 s |
| Firemon | Flamemon | `86400` (24 h) | hunger/energy/happiness ≥ 55, health ≥ 75 | ~144 s |
| Flamemon | Dragfiremon | `129600` (36 h) | 15 batallas + win ratio ≥ 60% (Fase 3) | ~216 s + 15 peleas |
| Dragfiremon | — | — | forma final | — |

Comparación de edad:

```text
stageAgeSeconds * CARE_TIME_SCALE >= minStageAgeSeconds
```

`STABILITY_SECONDS` sigue sin usarse. El chequeo es por tick cuando el
timer de etapa ya venció.

## Catálogo

Una sola tabla, tres sitios que deben coincidir:

- `src/config.py` `EVOLUTION_REGISTRY`
- `src/data/digimon/{baby,rookie,champion,ultimate}.json`
- `scripts/tdisplay_assets.py` → `generated/catalog.h`

Campos por arista:

```text
from, to
automatic                 // true para las tres evos vivas
requirements_pending      // false cuando la regla está arriba
min_stage_age_seconds
max_care_mistakes         // 1 en Sparkmon; omitido = sin tope
battles_required          // 15 en Flamemon; 0 en el resto
requirements              // solo Firemon: h/e/p/hp
                          // C++: h=hunger, e=energy, p=happiness, hp=health
```

Pedia: si `requirements_pending` es false, pinta timer + CM/battles/barras
reales. Si falta un campo, no se inventa texto. Ultimate no tiene
`evolves_to`; su detalle puede decir `FINAL FOR NOW` como hoy.

`EvolutionEdge` en `catalog.h` deja de ser solo `{from, to, pending}`.
Pasa a incluir los umbrales numéricos para que C++ no duplique literales
en `App.cpp`.

## Motor `Evolution`

Nuevo en `firmware/t-display/lib/vpet_core/src/vpet/Evolution.h` y el
mismo contrato en `src/core/evolution.py`.

```text
optional<SpeciesId> check(const PetState&, uint32_t scale) const
bool evolve(PetState&, uint32_t scale)          // check + apply
bool force(PetState&)                           // siguiente forma, sin umbral
```

`check` no mira el huevo. `App::tick` conserva los 8 s de hatch y **después**
llama `evolution.evolve(pet_, scale)` si no hay animación de evo en curso.
Si `evolve` es true: `motion_.startEvolution`, `setSpecies`, `save`.

Python `Evolution.check` deja de exigir `automatic` como único freno: el
registro pone `automatic: true` en las tres evos. `force()` no toca CM
hasta `_apply`.

### Reset al evolucionar (`_apply` / `evolveTo`)

Se resetean: `careMistakes`, `callReason`, `callStartedMs`,
`trainingSessions`, `battlesThisForm`, `meals`, `stageAge`.
Se conservan: especie, descubrimientos, H/E/P/HP (Python puede seguir
sumando +10 como hoy), `battlesWon`, `battlesLost`, preferencias.

`evolveTo` de descubrimiento (Rookie/Champion/Ultimate flags) se queda.
El reset de cría vive en `Evolution::apply`, no en cada `evolveTo` de
restore, para no borrar CM al cargar NVS.

## Call (esqueleto)

Mapeo: hunger 0 = Call Hunger. energy 0 = Call Strength (no hay hearts
discretos todavía). Luces / Rest **no** generan Call en este corte.

| Campo | Tipo | Notas |
|---|---|---|
| `callReason` | `None=0`, `Hunger=1`, `Strength=2` | Uno a la vez; si ambos a 0, Hunger tiene prioridad al **entrar**. Al timeout de Hunger, si energy sigue 0, arranca Strength (segundo mistake posible). |
| `callStartedMs` | u32 | Reloj de `App` / monotonic |
| margen | `600000 / scale` ms | 10 min COLOR |

Reglas:

1. Si no hay call y hunger llega a 0 → Hunger + timestamp.
2. Feed (o ítem carne, si se usa) con hunger > 0 apaga Hunger.
3. Rest que sube energy > 0 apaga Strength.
4. Si el margen vence → `careMistakes += 1` (tope 99) y el call se apaga.
5. Hambre y fuerza a 0 a la vez pueden producir **dos** mistakes si ambos
   vencen en secuencia, no un solo +2 instantáneo.
6. Caca, overfeed y despertar no existen.

UI: no hay icono nuevo. Con `callReason != None`, el selector del header
lleva un badge `*` (o recuadro) y Status muestra `CALL HUN` / `CALL STR`
más `CM`. Si `soundEnabled`, el firmware escribe
`VPET_CALL reason=HUNGER|STRENGTH` una vez al **entrar** al call (no cada
frame). No hay buzzer en esta placa.

## Qué se guarda hoy en la placa (schema 1)

NVS namespace `vpet_state` (`0x5000`). **Sí** sobrevive un reset:

`species`, `hunger`, `energy`, `happy`, `effort`, `health`, `age`,
`language`, `sound`, `bluetooth`, `invMeat`, `invEner`, `invExp`, `invRing`.

**No** se guardan todavía (viven solo en RAM y se pierden al apagar):
`meals`, `trainingSessions`, `battles`, descubrimientos, CM,
call, wins/losses, peso, DP, proteína. Schema 2 del Corte 1 los añade.
`EVOLVE` de debug **sí** persiste la nueva especie (usa el save actual).

## Trazabilidad (schema B)

### Contadores en `PetState` (NVS schema 2)

Ya existen en RAM y pasan a persistirse: `meals`, `trainingSessions`,
`battles` (este último es `battlesThisForm`).

Nuevos:

| Clave NVS | Default | Reset al evo |
|---|---|---|
| `schema` | `2` | — |
| `stageAge` | `0` | sí |
| `cm` | `0` | sí |
| `call` | `0` | sí |
| `meals` | `0` | sí |
| `training` | `0` | sí |
| `battles` | `0` | sí |
| `wins` | `0` | no |
| `losses` | `0` | no |
| `weight` | `5` | no (carne +1, proteína +2, train −1) |
| `dp` | `0` | no (4 proteínas o 8 h sueño = +1) |
| `protein` | `0` | sí (overdose 0–7) |

`age` (edad total) se sigue guardando. `stageAge` es independiente.

Migración schema 1 → 2: campos nuevos a 0; `stageAge = 0` (un save viejo
no eclosiona de golpe). Schema `0` = Missing. `> 2` = Unsupported.
`App::begin` debe dejar de ignorar `Unsupported`: carga defaults de huevo
y no mezcla claves viejas.

### `CareSnapshot` (20 bytes, export futuro BLE)

```text
u8  schema = 1
u8  species
u16 stageAgeMin
u8  hunger, energy, happiness, health
u8  careMistakes, effort, meals, training
u8  battlesThisForm, wins, losses
u8  callReason
u8  flags          // bit0 asleep, resto 0
```

`PetState::snapshot()` lo rellena. Corte 1 no añade característica GATT.
El iPhone tiny model (después) come este struct + el anillo.

### Anillo de eventos (RAM, 32 × 4 bytes)

```text
u16 tRelMin     // minutos desde hatch, saturados
u8  type        // FEED=1 TRAIN=2 BATTLE=3 CALL_START=4
                // CALL_MISS=5 SLEEP=6 WAKE=7 EVO=8 DECAY_ZERO=9
u8  value       // payload (CM tras miss, species tras evo, 0 si no)
```

Se pierde al reboot. No va a LittleFS (el estado de usuario no vive ahí).
`record(type, value)` lo usan Feed/Train/Battle/Call/evo. Tests nativos
comprueban wrap del índice.

Peso, DP, proteína y win ratio **sí se persisten** desde schema 2 (defaults
arriba) aunque la UI de carne/proteína y el candado de ratio lleguen en
Fases 2–3. Jogress y la rama hermana son cortes propios; el snapshot ya
reserva sitio (`flags` bit1 = guest/jogress ready).

## Producto que sí vamos a hacer (después de Corte 1)

| Pieza | Cómo | Persistencia |
|---|---|---|
| Peso (GB) | Status. Carne +1, proteína +2, Training −1 | `weight` |
| Proteína | Items: `TONIC` → `PROTEIN`. Strength + DP cada 4 | `protein` |
| DP | Status. 0 DP = Battle no arranca. Sueño 8 h o 4 proteínas | `dp` |
| Win ratio candado | `wins / (wins+losses) >= 60%` + 15 batallas de forma para Dragfiremon | `wins`, `losses` |
| Ramas | Sparkmon 0–1 CM → Firemon; 2+ → Rookie `???`. Firemon effort/CM → Flamemon o Champion basura | catálogo multi-arista |
| Jogress | Battle 3ª fila cuando hay otro vPet (BLE guest). Atlas de fusión + forma destino | Fase connect; no GPS |

Corte 1 guarda los enteros y publica Pedia de la línea buena. Los loops
de UI (proteína, DP gate, rama jugable, Jogress) no se implementan en el
mismo PR que Call, pero **no se vuelven a marcar como fuera de producto**.

## Persistencia y `restore`

`PetState::restore` actual amplía firma o se parte en
`restoreStats(...)` + setters. `SettingsStore::save/load` escribe todas
las claves de schema 2. Los tests de `test_settings.cpp` cubren ida y
vuelta de `cm`, `battles`, `wins` y `stageAge`.

Autosave: además de hatch / BLE / SAVE, guardar al evolucionar y al
sumar un care mistake (evita perder CM en reset).

## UI

- Status: AGE (etapa), HUN, ENR, CM, y `CALL …` si aplica. Barras actuales
  se quedan; no redibujar hearts 0–4 todavía.
- Pedia detalle: texto de requisitos del catálogo, no copy inventado.
- Options: 4 filas grandes. Orden: Bluetooth, idioma, sonido, save, load,
  fecha, hora, **EVOLVE**, BACK. Cada `NEXT` corto baja una fila al
  instante. Hold 2 s no cierra. Fila BACK + ACTION sale.
  `EVOLVE` llama `forceNextForm`, guarda NVS, va a Home y reproduce la
  animación de evo.
- Badge de Call en el header, no octavo icono.

## Testing

Misma tabla en pytest y Unity:

| Caso | Esperado |
|---|---|
| Sparkmon age 43799, CM 0 | no evo |
| Sparkmon age 43800, CM 0 | Firemon |
| Sparkmon age 43800, CM 2 | no evo |
| Firemon age 86400, barras bajas | no evo |
| Firemon age 86400, barras ok | Flamemon |
| Flamemon age 129600, 14 battles | no evo |
| Flamemon age 129600, 15 battles | Dragfiremon |
| scale 600, Sparkmon age 73, CM 0 | Firemon |
| Call Hunger 600001/scale ms | CM +1, call None |
| evo aplica | CM 0, battlesThisForm 0, wins intactos |
| schema 1 load | schema 2 defaults, no evo instantánea |

`force` no exige umbrales. Huevo no entra a `check`.

## Constraints

- Nada de SLM/LLM en el ESP32.
- Misma regla en `src/core/` y `vpet_core`.
- NVS `0x5000`: solo enteros/strings cortos, no el anillo.
- Dos botones: Call no añade filas.
- Pedia no inventa umbrales ni ramas.
- `CARE_TIME_SCALE` 1 en device, 600 en sim; tests nativos pasan `scale`
  explícito.
- Sin sprite nuevo. Sparkmon sigue sin punch/cast.

## Fuera de alcance (este corte de código, no del producto)

Call de luces, UI de carne/proteína, gate de DP en Battle, rama `???`
jugable, Jogress BLE, muerte, Cold/Backup, BLE snapshot notify, GPS, caca.

Siguen **dentro del producto** y del schema: peso, DP, proteína, wins/losses,
ramas y Jogress (se implementan en los cortes 2–5 del research).

## Verificación

- `make test` y `make native-test` verdes con la tabla de arriba.
- `make sim`: Sparkmon pita/badge al llegar hambre a 0; `e` sigue
  forzando; a scale 600 se puede llegar a Firemon en ~73 s con CM ≤ 1.
- `make deploy`: eclosión 8 s, no evo de Sparkmon en minutos reales,
  Pedia ya no dice `REQUIREMENTS NOT DEFINED` para Baby/Champion.

## Relación con otros docs

- Norte de producto: [2026-09-10-digimon-vpet-research.md](2026-09-10-digimon-vpet-research.md)
- Árbol visual (sin inventar umbrales; este spec **sí** los publica):
  [2026-09-05-evolution-tree-design.md](2026-09-05-evolution-tree-design.md)
- Tras implementar, actualizar `docs/architecture.md` ciclo de vida y
  persistencia schema 2.
