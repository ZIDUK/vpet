# Inventory Spend And Status Pages

Diseño del corte **Items (gasto) + Status (barras y 2 páginas)** en la
T-Display. El árbol de evolución **no entra**. El simulador Python se alinea
**después** de que la placa funcione; esta spec manda sobre el sim.

## Goal

En Inventario, ACTION gasta un item, baja el stock y aplica un stat. El menú
no se cierra. Status muestra HP / HAM / ENE como barras; NEXT pasa a una
segunda página con el resto del expediente.

## Decisiones cerradas

| Tema | Decisión |
|---|---|
| Orden | Placa primero. El sim copia este comportamiento después. |
| Catálogo | 4 items + ATRÁS. Carne, Energía, EXP, Anillo. |
| Carne | +20 HAM (igual que Feed). Stock inicial 3. |
| Energía | +25 ENE (igual que Rest). Stock inicial 2. |
| EXP | +8 ESF (igual que Training, sin gastar energía). Stock inicial 1. |
| Anillo | +15 mood (`happiness`). Stock inicial 1. |
| Vacío | ACTION no cambia stats ni stock. Se queda en Inventario. |
| Huevo | No puede usar items. |
| Feed del header | No gasta Carne. Sigue siendo acción suelta. |
| Tras gastar | Sigue en Inventario. Se redibuja `xN`. Sin animación de Home. |
| Persistencia | NVS schema 1, claves nuevas. Save viejo → 3/2/1/1. Autosave al gastar. |
| Status p.1 | Barras 0–100 a ancho completo: HP, HAM, ENE. |
| Status p.2 | AGE, ESF, BAT, mood, reloj. |
| Status NEXT | Cicla página 1 ↔ 2. |
| Status ACTION / BACK | Vuelve a Home. |
| Árbol / Call / CM / DP | Fuera. Siguiente corte. |

## User Flow — Inventario

1. Icono Items → lista Carne / Energía / EXP / Anillo / ATRÁS.
2. NEXT mueve el cursor (wrap de 5, igual que ahora).
3. ACTION en un item con stock > 0: resta 1, aplica el stat (tope 100),
   guarda NVS, redibuja la fila (`CARNE x2`, etc.).
4. ACTION con stock 0: no-op, sigue en el menú.
5. ACTION en ATRÁS, o GPIO0 2 s: Home.

## User Flow — Status

1. Icono Status → página 1: tres barras HP / HAM / ENE.
2. NEXT → página 2: AGE, ESF, BAT, mood y reloj de placa.
3. NEXT otra vez → página 1.
4. ACTION o BACK largo → Home.

## Architecture

`PetState` posee `meat_`, `energyItem_`, `expItem_`, `ring_` (uint8, 0–99) y
`useItem(uint8_t index)`:

| Retorno | Cuándo |
|---|---|
| `Used` | Stock > 0, stat aplicado, stock −1 |
| `Empty` | Índice de item con stock 0, o índice inválido |
| `Blocked` | Huevo |
| `Back` | Índice ATRÁS (`kInventoryCount - 1`) |

`App::handlePanelInput` intercepta ACTION en Inventario como Options:
`Used`/`Empty`/`Blocked` se quedan; `Back` → Home. `Navigation` deja de
cerrar Inventario en cualquier ACTION; solo ATRÁS cierra.

`SettingsStore` lee/escribe `invMeat`, `invEner`, `invExp`, `invRing` en
schema 1. `LOAD` restaura esas claves. Si faltan, defaults 3/2/1/1.

`Panels::drawInventory` pinta `pet.itemCount(i)`, no literales `x3`.
`Panels::drawStatus` usa `navigation.panelIndex() % 2` para la página.
Barras: track de 200×8 px, relleno `value` de 100, etiqueta + número a la
izquierda del track.

## Constraints

- No nuevo icono de menú.
- No EXP/Anillo como equipo permanente: son consumibles de un uso.
- Mood no se muestra en página 1 (cabe en página 2).
- Reloj de Status sigue siendo el de `time()`; se pierde al apagar (sin RTC).
- Tests nativos cubren `useItem` (gasto, vacío, huevo, tope 100) y Status
  NEXT que cicla 0↔1 sin ir a Home.
- Deploy: `pio test` native + upload firmware. No `uploadfs` (sin assets
  nuevos).

## Fuera de este corte

Pedia con requisitos, Call, care mistakes, proteína/DP, win ratio, animación
al usar item, y paridad del sim (se hace cuando la placa esté verde).
