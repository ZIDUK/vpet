# ADN, IV y EV (Corte 1)

Cada vida tiene un genoma de 4 bytes al eclosionar. De ahí salen 6 IVs
estilo Digimon World 1. Los EVs suben con cuidado. Status gana una
página con hélice, código ADN, stat visible, IV y EV. Battle no cambia.

## Goal

Un Firemon no es idéntico a otro. Al nacer se tira ADN. En Status se
ve. Feed/Train/Battle/Rest e items mueven EVs. El roll de batalla
sigue siendo el de ahora (effort hearts + energía − proteína).

## Decisiones

| Tema | Valor |
|---|---|
| Genoma | 4 bytes, fijos toda la vida |
| Cuándo se tira | Hatch huevo → Sparkmon (también `EVOLVE` de debug desde huevo) |
| Huevo | ADN `00 00 00 00`. Sin hélice de color. Texto `ADN ----` |
| IVs | 6 valores 0–15: HP MP OFF DEF SPD BRN |
| EVs | 6 valores 0–252. Empiezan en 0 |
| Stat visible | `clamp(1, 99, 10 + IV×3 + EV/6)` |
| Página Status | 4 páginas. NEXT cicla. Página 3 (índice 3) = ADN |
| Hélice | Procedural 28×40 px, colores del ADN. Sin PNG nuevo |
| Persistencia | Schema 3. Claves abajo |
| Snapshot BLE | No se toca (20 bytes). ADN viaja por NVS / Backup |
| Battle / Call / Cold | Sin cambios de regla |
| Backup | El pet aparcado guarda su ADN+EV. El huevo nuevo no tiene ADN |

## Empaque del ADN

```text
byte0 bits 0–3  IV HP
byte0 bits 4–7  IV MP
byte1 bits 0–3  IV OFF
byte1 bits 4–7  IV DEF
byte2 bits 0–3  IV SPD
byte2 bits 4–7  IV BRN
byte3           traits (ver extensión). También colorea la hélice
```

`ivAt(i)` = nibble `i` de `dna[0..2]`. `i` = 0..5 en el orden HP MP
OFF DEF SPD BRN.

### Extensión (no se implementa en este corte)

`byte3` se tira al hatch igual que los demás, pero **ya está reservado**
para traits. Este corte no los muestra ni los usa en batalla.

```text
byte3 bits 0–1  atributo   0 Vacuna  1 Data  2 Virus  3 —
byte3 bits 2–4  elemento   8 valores (Fuego/Agua/Aire/Tierra/Hielo/Elec/Batalla/—)
byte3 bits 5–7  naturaleza 8 valores (estilo DW1: hígado, rebelde, etc.)
```

La hélice puede seguir pintando con los 4 bytes: el trait **es** parte
del color. Un pet Virus/Fuego no se ve igual que uno Vacuna/Agua.

Si más adelante hace falta otro campo (Traited Egg, rareza, “hidden
power”):

1. **Cabe en 2–3 bits** → se redefine un hueco de `byte3` o se usa el
   `—` del atributo. Schema sigue en 3. Pets viejos ya tienen bits
   aleatorios: se interpretan, no se re-tiran.
2. **No cabe** → schema 4 con `dna4`…`dna7`. `load` de schema 3 deja
   los bytes nuevos en 0 y, si se quiere, deriva un default estable
   del ADN existente (igual que la migración 2→3). Nunca se pisa
   `dna0..3`.

EVs no van en el ADN: son esfuerzo, no nacimiento. Un “tipo de
entrenamiento” nuevo es otra tabla de `gainEv`, no otro byte.

Si el mix de entropía da `00 00 00 00`, forzar `dna[0] = 1` para no
confundir “sin hatch” con “ADN nulo”.

## Entropía

`PetState::rollDna(uint32_t entropy)` escribe los 4 bytes. No usa
reloj de pared (los tests nativos inyectan `entropy`).

En placa, `App` pasa `esp_random() ^ nowMs` al eclosionar. En tests,
enteros fijos. Dos `entropy` distintos → ADN distinto.

`resetToEgg()` (muerte ACTION, Backup a huevo, `force` desde Ultimate)
borra ADN y EVs. El próximo hatch tira otro genoma.

## Cómo suben los EV

Tope 252. No suben con el tiempo ni en Cold (Cold ya bloquea acciones
e items). Overfeed no da EV de Feed (la comida extra no entrena).

| Fuente | EV |
|---|---|
| Feed (acción, HAM < 100) | HP +2 |
| Training | OFF +2, SPD +1 |
| Battle (gane o pierda) | OFF +1, BRN +1 |
| Rest (al despertar: `completeAction(Rest)`. No al abrir el panel ni al acostarse) | MP +2, DEF +1 |
| Carne (item 0) | HP +2 |
| Energía (item 1) | MP +2 |
| EXP (item 2) | BRN +2 |
| Proteína (item 4) | OFF +2 |
| Anillo, medkit | 0 |

Al evolucionar **no** se resetean IVs ni EVs ni ADN. Es la misma vida.
Win ratio tampoco se toca (ya era así).

## Status página 3 (cuarta, índice 3)

```
[hélice 28×40]  ADN A1B2C3D4
HP  32   IV 08  EV 016
MP  28   IV 07  EV 012
OFF 40   IV 12  EV 024
DEF 22   IV 04  EV 008
SPD 35   IV 11  EV 018
BRN 18   IV 05  EV 006
```

Texto compacto (font 1). Huevo: sin números, `ADN ----`.

Páginas 0–2 no cambian. `Navigation::kStatusPages = 4`.
`test_status_next_cycles_three_pages` pasa a cuatro.

No hay un “Lv” 1–99 aparte. Los 6 stats **son** el 1–99.

## Hélice

`drawHelix(canvas, x, y, dna[4])` en el firmware (Panels, no core).

- Dos senos verticales, 5 “peldaños” horizontales.
- Strand A color RGB565 de `dna[0]<<8 | dna[1]`.
- Strand B color de `dna[2]<<8 | dna[3]`.
- Peldaños alternan esos dos colores.
- Huevo o ADN cero: dos líneas grises, sin peldaños.

Helper testeable en `Layout.h`:

```text
helixColor(dna, strand) -> uint16_t   // 0 = A, 1 = B
helixX(strand, step, width) -> int    // step 0–4
```

## Persistencia (schema 3)

NVS, namespace `vpet_state` (y `vpet_bak` vía el save de Backup):

| Clave | Default |
|---|---|
| `schema` | 3 |
| `dna0`..`dna3` | 0 |
| `evHp` `evMp` `evOff` `evDef` `evSpd` `evBrn` | 0 |

`load` acepta schema 1, 2 y 3. Tras restaurar:

- Schema 3: usa las claves.
- Schema 1–2, o claves ausentes = 0.
- Si la especie **no** es huevo y los 4 bytes son 0: sintetizar
  `rollDna(ageSeconds * 2654435761u + species + wins * 17)` para no
  re-tirar en cada boot. `App::begin` guarda si migró.

`SettingsStore::save` escribe schema 3 siempre.

## API mínima (`PetState`)

```text
enum class CombatStat : uint8_t { Hp, Mp, Off, Def, Spd, Brn };

void rollDna(uint32_t entropy);
const uint8_t* dna() const;          // 4 bytes
uint8_t ivAt(CombatStat) const;      // 0–15
uint8_t evAt(CombatStat) const;      // 0–252
uint8_t combatStat(CombatStat) const; // 1–99
bool hasDna() const;                 // algún byte ≠ 0
```

`completeAction` y `useItem` llaman un `gainEv` interno según la tabla.
Tests nativos cubren cada fila.

## Fuera de este corte

- Battle no lee IVs/EVs (sigue el roll actual).
- Panel Battle con techs / Your Call (Digimon World 1).
- Tiny model en iPhone. El `CareSnapshot` de 20 bytes no crece.
- Mostrar o usar atributo / elemento / naturaleza (ya viven en `byte3`).
- Traited Egg y ramas según atributo.
- Sim Python puede esperar un PR; la placa es el entregable.
- Ramas `???`, Jogress, caca, 9º icono.

Esos cortes **comen** este ADN: Brains desbloquea comandos, OFF/SPD
pesan el hit, Your Call elige tech. No se implementan aquí.

## Tests (nativos)

- `rollDna(1)` y `rollDna(2)` distintos; ninguno queda `00 00 00 00`.
- IVs de un ADN fijo coinciden con los nibbles.
- `combatStat` usa la fórmula y clampa 1–99.
- Feed/Train/Battle/Rest e items suben el EV de la tabla; tope 252.
- Overfeed no suma EV. Anillo y medkit no suman.
- `resetToEgg` borra ADN y EV.
- Evo (Sparkmon→Firemon) conserva ADN y EV.
- Save schema 3 ida y vuelta.
- Schema 2 + Rookie + edad conocida → mismo ADN sintético siempre.
- Status NEXT: 0→1→2→3→0.

## Verificación en placa

Huevo: página 4 `ADN ----`. Tras eclosionar: hex ≠ `00000000`, hélice
de color, 6 IVs 0–15. Un Feed sube HP EV. Backup y volver: mismo ADN.
