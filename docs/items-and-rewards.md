# Catalogo de objetos vPet

Catalogo vigente del inventario, contrastado con `src/core/inventory.py`,
`src/core/pet.py` y `firmware/t-display/lib/vpet_core/src/vpet/PetState.cpp`.
Los efectos respetan topes y condiciones del motor; la cantidad inicial no es
una recompensa recurrente.

## Objetos implementados

| ID estable | Objeto | Descripcion | Efecto al usar | Stock inicial | Origen actual |
|---|---|---|---|---:|---|
| `meat` | Carne asada | Racion para recuperar hambre. | +20 HAM, max. 100; suma 1 de peso. Si HAM estaba por debajo de 100, tambien da +2 EV de HP. Con HAM en 100 puede contar como sobrealimentacion si el ciclo aun lo permite; en ese caso no da EV de HP. | 3 | Kit de inicio; sin reposicion implementada. |
| `energy` | Tonico de energia | Frasco de recuperacion para volver a entrenar o combatir. | +25 ENE, max. 100, y +2 EV de MP. | 2 | Kit de inicio; sin reposicion implementada. |
| `exp` | Estrella de experiencia | Insignia de practica que impulsa el esfuerzo general. | +8 ESF, max. 100, y +2 EV de BRN. | 1 | Kit de inicio; sin reposicion implementada. |
| `ring` | Amuleto | Objeto de animo, valido para cualquier especie. El nombre visible dejo de ser «anillo de fuego» el 2026-10-12; el ID de guardado sigue siendo `ring`. | +15 animo, max. 100. | 1 | Kit de inicio; sin reposicion implementada. |
| `protein` | Proteina | Suplemento para recuperar energia y fortalecer el perfil ofensivo. | +20 ENE, max. 100, y +2 EV de OFF. Cada cuarto uso aumenta Proteina en 1 (max. 7) y DP en 1 (max. 3). | 2 | Kit de inicio; sin reposicion implementada. |
| `medkit` | Botiquin | Kit de primeros auxilios para un vPet lesionado. | Solo se puede usar con lesion: la elimina y restaura +20 HP, max. 100. | 1 | Kit de inicio; sin reposicion implementada. |

Los nombres visibles son genericos para cualquier especie. El animo usa el nombre **Amuleto**; el ID de guardado sigue siendo `ring`. No se crean objetos con tema de una sola especie, como un anillo de fuego.
El botiquin y la carne tambien pueden estar bloqueados por sus condiciones de
uso. Los stats temporales se limitan a 100; los EV permanentes, a 252 por stat.
Los objetos no cambian IV. El inventario se guarda en la partida.

## Como se obtienen hoy

Las cantidades de la tabla se entregan al inicializar una partida nueva y se
usan como valores predeterminados cuando faltan claves de inventario en el
guardado. **Hoy no hay una accion de compra, recoleccion, combate o exploracion
que reponga estos objetos.** Usarlos descuenta una unidad. No se debe describir el stock
inicial como botin ni como una fuente repetible.

## Recompensas futuras: brainstorm de exploracion

El brainstorm vivo esta en
[Exploracion y recompensas](superpowers/specs/2026-10-11-exploration-design.md).
Todavia no esta implementado y deja pendientes la aprobacion del alcance,
balance, limites de inventario y persistencia. Por ahora sus caminos son
familias conceptuales, no nuevas definiciones de objetos:

| Camino propuesto | Familia de recompensa | Estado |
|---|---|---|
| Patio | Comida o energía | Propuesta. Podría reponer `meat` o `energy`. Las cantidades de EV y técnica de la exploración ya están cerradas; el objeto concreto de esta ruta no. |
| Jornada | Material o cuidado | Propuesta. No hay un material con uso real en el catálogo actual. |
| Noche | Progreso de técnica | Cerrado como regla, no como objeto: +2 de dominio (tope 4/semana) o +1 al contador de Llama. No es un ítem de la bolsa. |

Antes de implementar botin, cada nuevo objeto debe recibir un ID estable,
categoria, rareza, icono, nombre ES/EN, limite de stack, efecto tipado,
objetivo, magnitud, duracion, topes y origen. Una recompensa de recuperacion
temporal no debe confundirse con EV permanente. No agregar materiales sin uso
real ni tratar esas reglas como codigo ya disponible. El EV y el dominio
de la noche estan aprobados como diseno; no estan programados.

## Iconografia

La mochila y los seis consumibles usan sprites pixel-art propios, definidos en
`scripts/item_icons.py` y rasterizados por `scripts/build.py`. El mismo BMP
generado alimenta el simulador; `scripts/build_tdisplay.py` lo empaqueta como
VPA para LittleFS y firmware. Los IDs visuales (`ItemMeat`, `ItemEnergy`, etc.)
son presentacion, no IDs de guardado.
