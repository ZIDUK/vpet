# Investigación Digimon Vpet y plan de cría

Investigación de los Digimon Vpet actuales (Digital Monster COLOR y
Pendulum COLOR), estado real del vPet T-Display, huecos frente a Bandai
y plan de continuación **sin implementar caca**. Fecha: 10 septiembre
2026. Hardware objetivo: LILYGO TTGO T-Display clásica,
ESP32-D0WDQ6-V3, 16 MB flash, sin PSRAM, 240×135.

Fuentes principales: [manual Digital Monster COLOR](https://humulos.com/digimon/dmc/manual/),
[guía de evos COLOR](https://humulos.com/digimon/dmc/),
[manual Pendulum COLOR](https://humulos.com/digimon/penc/manual/),
[Wikimon Digital Monster COLOR](https://wikimon.net/Digital_Monster_COLOR),
y el repo local (`README.md`, `docs/architecture.md`, `PetState`, menú y
evolución).

## 1. Qué es un Digimon Vpet de verdad

No es un RPG de barras. Es un **timer de cría + llamadas que no puedes
ignorar + snapshot de cuidado al vencer el reloj**.

Bandai no usa un modelo de lenguaje. El “cerebro” es:

- hearts que se vacían
- un icono de **Call** que pita
- **care mistakes** si no atiendes a tiempo
- **effort** por entrenar
- **win ratio** si quieres Ultimate/Mega
- muerte si fallas demasiado

Eso es lo que hay que copiar. El sprite bonito y el menú de 8 iconos ya
los tenemos.

Los modelos recientes de **cría** son:

| Aparato | Año | Qué es |
|---|---|---|
| **Digital Monster COLOR** Ver.1–5 y crossovers | 2023–2026 | El vpet clásico en color. Referencia principal. |
| **Digimon Pendulum COLOR** | 2024–2025 | Igual de cría, más Jogress y acelerómetro. |
| Digivice 25th COLOR EVOLUTION | 2024 | **No es vpet de cría.** Walk-battler: evo temporal en combate. |
| Vital Bracelet BE | 2023+ | Wearable de pasos. Otra línea. |

Este documento usa COLOR como norte. Pendulum se cita cuando cambia una
regla útil.

## 2. Interfaz COLOR: botones e iconos

### Botones

| Botón | Función |
|---|---|
| **A** | Ciclar iconos |
| **B** | Confirmar. Sin icono: reloj |
| **C** | Cancelar. Hold 2 s: Settings. Hold largo: power |
| **A+C** | Mute / (en reloj) cambiar hora |
| **A+B** | Nuevo huevo sobre la tumba |

La pantalla se apaga a los 16 s. Se enciende con cualquier botón, o sola
al llamar, evacuar o evolucionar.

Nuestro mapeo ya es cercano: GPIO0 corto = NEXT (A), GPIO0 2 s = BACK
(C), GPIO35 = ACTION (B).

### Los 8 iconos

**Status (báscula)** — expediente, no HP/MP:

- Age, Weight (GB), Hunger ♥, Strength ♥
- Effort (cada 4 entrenos = 1 heart; cuenta éxitos y fallos)
- Energy / DP (sin DP no peleas; se llena con 8 h de sueño o 4 proteínas)
- Win Ratio (la única stat que **sobrevive** a cada evo)
- Ocultas: Care Mistakes, Protein Overdose, Power, atributo Vaccine/Data/Virus
- Pendulum añade **Condition**: hearts que pierdes por mistake. A 0
  cambian las ramas III/IV y bloquean V/VI naturales

**Food (carne)**

- Carne → +1 hunger, +1 GB. En COLOR puedes **overfeed** (seguir
  comiendo con hearts llenos: es requisito de algunas evos)
- Proteína → +1 strength, +2 GB; cada 4 = +1 DP y más riesgo de lesión

**Training (pesas)** — única forma de Effort. Minijuego por versión.
4 sesiones = 1 Effort Heart. Baja peso.

**Battle** — Stage III+ y ≥1 DP.

- Quest: áreas + boss. Cada pelea cuenta para evo
- Connect: otro COLOR/Pendulum por pines
- Jogress (Pendulum y VI+ COLOR): fusión instantánea
- Hitrate ≈ `power_tú / (tú + él)` ± atributo. Vaccine > Virus > Data > Vaccine

**Clean (caca)** — **fuera de alcance en este plan.** En COLOR: I cada
3 min, II cada 60, III+ cada 120. 8 pilas = lesión. No es care mistake.

**Sleep (bombilla)**

- Lights: al dormirse hay que apagar. Si no, care mistake (1 h de margen)
- Despertarlo no es mistake; en COLOR es *sleep disturbance* (otra
  condición de evo)
- Cold Mode: pausa total
- Backup: aparcas este Digimon y sacas otro huevo

**Heal (venda)** — lesión por batalla (y en COLOR también por 8 cacas,
que no vamos a tener). 15 lesiones o 6 h herido = muerte. La proteína
extra sube la chance de lesionarte al perder.

**Call (grito)** — el alma del sistema. Beeps + icono:

| Motivo | Margen | ¿Mistake si lo ignoras? |
|---|---|---|
| Hunger a 0 | 10 min | Sí |
| Strength a 0 | 10 min | Sí |
| Quiere luces off | 1 h | Sí |
| Caca / lesión / overfeed / despertarlo | — | **No** |

Hambre y fuerza a 0 a la vez = **dos** mistakes. El contador se
resetea en cada evo. En III/IV decide *qué* forma. En V/VI, demasiados
mistakes bloquean la evo o matan.

## 3. Evolución COLOR

No es “sube de nivel”. Es **timer + snapshot**.

```text
Digitama —8 s—►
  I   Baby I / In-Training I      10 min     (nada cuenta)
  II  Baby II / In-Training II    12 h       (empiezan mistakes)
  III Child / Rookie              24 h       (rama: mistakes + effort)
  IV  Adult / Champion            36 h       (casi garantizado)
  V   Perfect / Ultimate          48 h       (exige 15 batallas + win ratio)
  VI  Ultimate / Mega             —
  VI+ Super Ultimate / Ultra      solo Jogress
```

El reloj corre **también dormido**. Cold/Backup lo paran.

| Destino | Qué se mira |
|---|---|
| I → II | Solo tiempo |
| II → III | Care mistakes (ej. 0–2 Agumon, 3+ Betamon) |
| III → IV | Mistakes + entrenos + a veces overfeeds / sleep disturbances. Si no caes en rama “buena”, vas a basura (Numemon) |
| IV → V y V → VI | ≥15 batallas **en esta forma** + win ratio. 80% = garantizado; 40–80% = chance; <40% = no |
| VI+ | Solo Jogress |

Al evolucionar se resetean mistakes, entrenos, overfeeds, disturbances,
overdosis, lesiones y batallas-para-evo. **Win ratio no.**

Muerte típica COLOR: 15 lesiones, 6 h herido, 12 h con hunger/strength a
0, o 5+ mistakes al fallar evo de IV/V. Tumba → A+B → huevo. Un V+
muerto tiene 30% de Traited Egg (bonus de Power).

Ejemplo Ver.1:

```text
Digitama → Botamon (I) → Koromon (II)
  ├ 0–2 mistakes → Agumon
  └ 3+ mistakes  → Betamon
Agumon → Greymon / Tyranomon / otras / Numemon (según effort + mistakes)
Greymon → Perfect si 15 batallas + ratio
Perfect → Mega si 1 mistake o menos + 80% wins
```

## 4. Qué tenemos hoy en el vPet

Placa: T-Display clásica, firmware C++ PlatformIO, simulador Python
240×135, BLE bajo demanda (`vPet-XXXX`, Device Information de solo
lectura). WiFi aplazado.

### Línea visual

```text
Egg —8 s—► Sparkmon → Firemon → Flamemon → Dragfiremon
 I/Baby              Rookie      Champion     Ultimate
```

- Sparkmon: idle, caminar, comer, dormir. **Sin** entreno ni batalla.
- Firemon en adelante: idle, movimiento, comida, entreno, descanso,
  ataque, evo.
- Criterios Sparkmon→Firemon y Flamemon→Dragfiremon: **pendientes**.
- Firemon→Flamemon: 60 s de edad + H/E/P ≥55 y HP ≥75 (reglas Python;
  el firmware C++ evoluciona por comando, no por timer de cría).
- La guía muestra 3 nodos, siluetas `???` hasta descubrir, detalle sin
  inventar umbrales.

### Menú actual (8 iconos)

| # | Icono | Qué hace |
|---|---|---|
| 0 | Status | Barras HUN / ENR / MOO / HP (0–100) |
| 1 | Feed | +hambre, animación comer |
| 2 | Training | +esfuerzo, −energía, animación punch |
| 3 | Battle | −energía, +esfuerzo, animación cast. No hay rival ni win/loss |
| 4 | Rest | Sueño persistente + fondo noche. ACTION otra vez = wake |
| 5 | Items | Mochila (carne, tónico, medkit) |
| 6 | Pedia | Árbol de evo compacto |
| 7 | Options | BLE, idioma, sonido, save/load, fecha/hora |

### Estado persistido (`PetState` C++)

Ya existen y se pueden reutilizar: `hunger`, `energy`, `happiness`,
`effort`, `health`, `meals`, `trainingSessions`, `battles`,
`ageSeconds`, descubrimientos por especie.

Decay: −1 hunger/energy/happiness cada 30 s (firmware). El simulador
Python decae más rápido (cada 3 s). Huevo no decae. Baby no puede
entrenar ni pelear.

**No existen:** Call, care mistakes, hearts discretos, carne vs
proteína, overfeed, DP, win ratio, lesión, muerte, Cold/Backup, peso,
atributo, Quest, connect battle, Jogress, ramas.

### AI / SML

Un Small Language Model **no cabe** en este ESP32 sin PSRAM. El primer
“cerebro” es on-device: Call + mistakes + ramas. Un SLM iría después en
el iPhone por BLE, narrando el estado, no decidiendo evos.

## 5. Hueco COLOR vs vPet (sin caca)

| Pieza COLOR | vPet hoy | ¿Hace falta para “sentirse Digimon”? |
|---|---|---|
| Hunger / Strength hearts | Barras 0–100 H/E | Sí. Se pueden mapear a 4 hearts sin redibujar todo |
| **Call + care mistakes** | No | **Sí. Es el loop.** |
| Lights como cuidado | Rest toggle | Sí. Hay que convertir el sueño en evento con margen |
| Effort | Contador interno, poco visible | Sí. Mostrarlo y usarlo en evos |
| Carne / proteína | Un solo Feed | Sí. Encaja en Items o submenú de Feed |
| DP + win ratio + 15 batallas | `battles` sin resultado | Sí para Champion→Ultimate |
| Heal / lesión | medkit en mochila, sin lesión | Sí, solo por batalla (no por caca) |
| Timers de etapa (10 min / 12 h / 24 h) | 8 s huevo; resto umbral de stats | Sí, se pueden acortar para desarrollo |
| Ramas II→III→IV | Línea única | Sí, aunque la 2ª rama sea un Digimon “basura” |
| Status tipo expediente | 4 barras | Sí |
| Pedia / Album | Ya hay guía | Mantener |
| Clean / caca | No | **No. Aplazado.** |
| Muerte / tumba | No | Fase posterior |
| Cold / Backup | No | Fase posterior |
| Connect / Jogress | BLE solo info | Fase posterior |
| SLM en el chip | — | No. Imposible en esta placa |

## 6. Plan para que el vPet se parezca a un Digimon

Principio: **no añadir iconos**. Los 8 actuales se quedan. Call no es un
octavo menú nuevo: es un **estado visual** (icono que parpadea / badge
en Status). Heal vive en Items (ya hay medkit). Caca no se toca.

Mapeo estable:

| Icono que ya tenemos | Rol Digimon |
|---|---|
| Status | Expediente: hearts, age, effort, DP, win ratio, mistakes |
| Feed | Carne. Proteína como segunda fila o ítem |
| Training | Effort + strength. Sigue el punch actual |
| Battle | Gasta DP, registra win/loss, chance de lesión |
| Rest | Luces / dormir. Ignorar la hora de dormir = mistake |
| Items | Medicina (cura lesión) + proteína + consumibles |
| Pedia | Árbol. Cuando haya rama, el layout ya la soporta |
| Options | BLE, sonido, reloj (el reloj **sí** importa para dormir) |

### Fase 0 — Cerrar la línea actual

Sin esto, cualquier sistema de cría queda colgando.

- Definir Sparkmon → Firemon (tiempo + mistakes bajos o effort mínimo;
  Baby no entrena, así que aquí mandan tiempo + no dejarlo a 0 de
  hambre)
- Definir Flamemon → Dragfiremon (15 “batallas” + win ratio cuando
  exista; hasta entonces: effort + age)
- Unificar Python y C++: misma función de chequeo, mismos umbrales
- Acelerar timers en simulador (`e` ya fuerza evo; añadir factor de
  tiempo de debug)

Entregable: una partida nueva eclosiona, llega a Firemon sola y a
Flamemon/Dragfiremon con reglas publicadas en Pedia (ya no
`REQUIREMENTS NOT DEFINED`).

### Fase 1 — Loop de cuidado: Call + mistakes + luces

Esta es la fase que más se parece a COLOR. **Sin caca.**

Nuevo estado mínimo en `PetState` / `Pet`:

- `hungerHearts` / `strengthHearts` (0–4), o umbrales sobre H/E
  (0, 25, 50, 75, 100)
- `careMistakes` (reset al evolucionar)
- `callReason` (`None`, `Hunger`, `Strength`, `Lights`)
- `callStartedMs`, márgenes 10 min / 10 min / 1 h (constantes
  acortables en sim)
- `asleep`, `wantsLightsOff`

Reglas:

1. Si hunger o strength llegan a 0 → Call. 10 min sin
   Feed/Train/Proteína → +1 mistake y el call se apaga.
2. Al entrar en Rest por horario o por icono, si no confirmas “luces
   off” en 1 h → +1 mistake. (Con 2 botones: abrir Rest **es** apagar
   luces. Ignorar el call de sueño es el mistake.)
3. Hambre y fuerza a 0 a la vez = dos mistakes si ambos vencen.
4. Caca no existe, así que no genera call ni lesión.
5. El menú no añade icono. El selector o Status muestra un badge cuando
   hay call. Beep si el sonido está on (hoy el flag ya existe).

UI: Status deja de ser solo 4 barras. Primera versión usable:

- AGE
- HUN ♥♥♥♥
- STR ♥♥♥♥
- EFF (hearts o número de sesiones / 4)
- CM (care mistakes de **esta** forma)

Entregable: dejar a Sparkmon/Firemon sin comer produce un call visible;
ignorarlo suma mistakes y se ve en Status; evolucionar resetea CM.

### Fase 2 — Comida dual + Effort visible

- Feed = carne (llena hunger hearts, puede overfeed 1 vez por ciclo;
  overfeed **no** es mistake)
- Items → Proteína (llena strength; cada 4 sesiones de proteína
  incrementa un contador `proteinOverdose`, tope 7)
- Training sigue sumando `trainingSessions`; cada 4 = 1 Effort Heart,
  éxito o fallo
- Strength también sube con Training, como en COLOR

Entregable: dos formas de “cuidar fuerza”; Pedia puede exigir “0–7
entrenos” vs “8+”.

### Fase 3 — Batalla con consecuencia (aún vs CPU)

Hoy Battle es una animación. Convertirlo en un duelo mínimo de 3 hits,
como COLOR Quest de 1 ronda.

- `dp` (0–N). 0 DP = Battle no arranca (igual que Baby no entrena)
- Dormir 8 h (o el factor de debug) restaura DP; 4 proteínas = +1 DP
- `battlesWon` / `battlesLost` → win ratio persistente **entre evos**
- Al perder (y a veces al ganar): `injured = true`. Items/medkit cura.
  15 lesiones en **esta** forma o 6 h herido → muerte (Fase 5 si aún no
  queremos tumba; hasta entonces: cap de batalla + aviso)
- Protein overdose sube la chance de lesión al perder

Entregable: no puedes spamear Battle; el ratio existe; Heal tiene
sentido sin caca.

### Fase 4 — Ramas de evolución

El panel de evo ya es grafo. Falta **una** rama hermana real, no
inventar un roster de 20.

Propuesta mínima (nombres de trabajo):

```text
Egg → Sparkmon
        ├ 0–1 CM, tiempo cumplido     → Firemon
        └ 2+ CM                      → (Rookie “descuidado”, silueta ???)
Firemon
        ├ effort alto + CM bajos     → Flamemon
        └ effort bajo o CM altos     → (Champion basura)
Flamemon
        ├ 15 batallas + ratio ≥ 60%  → Dragfiremon
        └ falla el timer             → se queda Flamemon (COLOR: no evo más)
```

Hasta tener el segundo sprite, la rama oscura puede ser silueta `???`
jugable (mismo atlas tintado / recorte) para no bloquear reglas.

Al evo: reset de CM, effort, entrenos, overfeeds, lesiones,
batallas-para-evo. Win ratio permanece.

Entregable: dos caminos Sparkmon→Rookie visibles en Pedia; Dragfiremon
exige combate, no solo barras.

### Fase 5 — Later (no ahora)

- Muerte + tumba + A+B huevo nuevo + Traited Egg
- Cold Mode y Backup (el icono Rest ya tiene sitio para un submenú de
  3 filas, como COLOR)
- Quest de varias áreas
- Connect battle por BLE (hoy el radio existe; el protocolo no)
- SLM en iPhone narrando el snapshot
  (`species, hearts, cm, effort, ratio`)
- **Caca / Clean** — aplazado a propósito. Cuando se haga: icono nuevo
  o submenú de Rest, lesión a las 8 pilas, **nunca** care mistake
- LLM on-device: descartado en esta placa

## 7. Orden de implementación recomendado

```text
Fase 0  reglas de evo de la línea actual     → partida completa
Fase 1  Call + mistakes + luces              → se siente Digimon
Fase 2  carne/proteína + Effort visible      → hay knobs de rama
Fase 3  DP + win/loss + lesión/cura          → Battle deja de ser fake
Fase 4  1 rama hermana + umbrales en Pedia   → el árbol cobra sentido
Fase 5  muerte / backup / BLE battle / SLM   → después
        caca                                 → explícitamente no
```

Por qué este orden: sin Call, Effort y batallas son números muertos.
Sin Fase 0, las ramas no tienen a quién aplicar. Sin Fase 3, Dragfiremon
no puede usar la regla COLOR de verdad. La caca solo añade un timer
visual; no decide ramas. Por eso se puede (y se debe) saltar.

### Constraints de esta placa

- Nada de SLM/LLM en el ESP32. Heap ya está comprometido por 2
  framebuffers TFT + BLE.
- Misma regla en `src/core/` (sim) y
  `firmware/t-display/lib/vpet_core/` (C++).
- NVS versionado: al añadir `careMistakes` / `dp` / `injured`, bump de
  schema y default 0.
- Timers reales de COLOR (12 h / 24 h) solo con un `CARE_TIME_SCALE`
  (1 en device, 60–600 en sim).
- Pedia no inventa umbrales: si la regla no está en el catálogo, sigue
  diciendo `REQUIREMENTS NOT DEFINED`.
- Dos botones: ningún flujo nuevo de más de 3 filas sin wrap + BACK.

## 8. Criterio de éxito (“ya se parece”)

Una sesión de 15 minutos en el simulador debe permitir esto:

1. El huevo eclosiona en Sparkmon.
2. Sparkmon pita cuando tiene hambre. Si lo ignoras, Status muestra
   CM > 0.
3. Llega a Firemon o a la rama oscura según mistakes.
4. En Firemon entrenas, ves Effort, das carne o proteína.
5. Peleas, gastas DP, puedes lesionarte y curarte con medkit. **No hay
   caca.**
6. Flamemon no se vuelve Dragfiremon solo por barras: hace falta
   combate + ratio.
7. Pedia revela el nombre solo al llegar. La otra rama sigue `???`.

Si eso funciona, el aparato ya se juega como un COLOR reducido. El resto
es roster, muerte y conectividad.

## 9. Próximo paso concreto

Empezar **Fase 0 + esqueleto de Fase 1** en el mismo corte:

1. Catálogo de evos con umbrales reales para Sparkmon y Flamemon.
2. Campos `careMistakes` + `callReason` persistidos.
3. Badge de Call en el menú / Status.
4. Tests nativos C++ y pytest del sim, misma tabla de casos.

No abrir caca, SLM, Quest de 5 áreas ni rama con sprite nuevo hasta que
Call resetee bien al evolucionar.
