# COLOR Protein, Effort, Battle, Grave

Cierra Fase 2–3 y la tumba de Fase 5. Sin 9º icono. Sin caca. Sin BLE mando.

## OF y CM (recordatorio)

| Sigla | Significa | Es error? |
|---|---|---|
| **CM** | Care mistakes: call ignorado o despertar de noche | Sí |
| **OF** | Overfeeds: 1 comida extra con HAM 100 | No |

## Items

Índices estables. Carne/Energía/EXP/Anillo no se renumeran.

| Índice | Item | Default | Efecto |
|---|---|---|---|
| 0–3 | igual | 3/2/1/1 | igual |
| 4 | Proteína | 2 | ENE +20. Cada 4 usos: overdose +1 (tope 7) y DP +1 (tope 3) |
| 5 | Medkit | 1 | Solo si `injured`. Cura lesión, PV +20 |
| 6 | ATRÁS | — | Home |

Medkit sin lesión → `Blocked`, no gasta. Huevo → `Blocked`.

## Effort hearts

`effortHearts = min(4, trainingSessions / 4)`. Status muestra `EFF n/4`. El stat `effort` 0–100 sigue interno.

## Batalla (3 hits, 1 roll)

- Baby / huevo / muerto / herido / DP 0 → no arranca.
- Cuesta 1 DP. Rest +1 DP (tope 3). Hatch arranca con DP 1.
- `roll` 0–99. Gana si `roll < chance`. Chance 50 + hearts×8 + ENE/20 − overdose×4, clamp 15–90.
- Win: `wins++`. Lose: `losses++`, `injured=true`, `injuries++`.
- Win con overdose ≥ 4: también lesiona.
- Win ratio ≥ 60% ya es candado de Flamemon → Dragfiremon.

## Muerte / tumba

15 lesiones en esta forma, o 6 h herido (`21600000` ms) → `dead`. Home pinta tumba. ACTION en Home → huevo nuevo.

## Sprites nuevos

`Protein.png`, `Medkit.png` (iconos). `bag.png` (saco en Training). `grave.png` (tumba).
