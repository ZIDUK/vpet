# Catalogo de objetos vPet

Catalogo vigente del inventario, contrastado con `src/core/inventory.py`,
`src/core/pet.py` y `firmware/t-display/lib/vpet_core/src/vpet/PetState.cpp`.
Los efectos respetan topes y condiciones del motor; la cantidad inicial no es
una recompensa recurrente.

## Objetos implementados

| ID estable | Objeto | Descripcion | Efecto al usar | Stock inicial | Origen actual |
|---|---|---|---|---:|---|
| `meat` | Carne asada | Alimento ilimitado de la pantalla Alimentar; el stock guardado antiguo se conserva y no se descuenta. | +20 HAM (max. 100) y +1 peso. Una sobrealimentacion por ciclo si HAM ya esta lleno; sin EV. | Ilimitado | No requiere obtenerlo; disponible al alimentar. |
| `energy` | Tonico de energia | Frasco de recuperacion para volver a entrenar o combatir. | +25 ENE, max. 100, y +2 EV de MP. | 2 | Kit de inicio; sin reposicion implementada. |
| `exp` | Estrella de experiencia | Insignia de practica que impulsa el esfuerzo general. | +8 ESF, max. 100, y +2 EV de BRN. | 1 | Kit de inicio; sin reposicion implementada. |
| `ring` | Amuleto | Objeto de animo, valido para cualquier especie. El nombre visible dejo de ser «anillo de fuego» el 2026-10-12; el ID de guardado sigue siendo `ring`. | +15 animo, max. 100. | 1 | Kit de inicio; sin reposicion implementada. |
| `protein` | Proteina | Alimento ilimitado de la pantalla Alimentar; el stock guardado antiguo se conserva y no se descuenta. | +20 ENE (se ofrece con ENE <= 80) y +2 peso, una vez por ciclo metabolico; sin EV ni DP. | Ilimitado | No requiere obtenerla; disponible al alimentar. |
| `medkit` | Botiquin | Kit de primeros auxilios para un vPet lesionado. | Solo se puede usar con lesion: la elimina y restaura +20 HP, max. 100. | 1 | Kit de inicio; sin reposicion implementada. |
| `guide` | Guia / Guide | Manual para la proxima sesion, implementado en Make Sim. Icono `ItemGuide`; capacidad una. | +1 EV del stat entrenado al completar y guardar una sesion; se conserva en cancelacion/fallo/EV lleno. Seleccionarla abre entrenamiento. | 0 | Jornada completa con buen cuidado. |

Los nombres visibles son genericos para cualquier especie. El animo usa el nombre **Amuleto**; el ID de guardado sigue siendo `ring`. No se crean objetos con tema de una sola especie, como un anillo de fuego.
El botiquin y la carne tambien pueden estar bloqueados por sus condiciones de
uso. Los stats temporales se limitan a 100; los EV permanentes, a 252 por stat.
Los objetos no cambian IV. El inventario se guarda en la partida.

## Como se obtienen hoy

Los consumibles de mochila se entregan al inicializar una partida nueva y se
usan como valores predeterminados cuando faltan claves de inventario en el
guardado. Usarlos descuenta una unidad. Carne y proteina son excepciones:
Alimentar las ofrece ilimitadamente y no consulta ni descuenta sus claves de
stock antiguas. **Hoy no hay una accion de compra, recoleccion, combate o
exploracion que reponga esos seis consumibles de mochila.** Make Sim obtiene
la Guia mediante Jornada; la placa aun no implementa esa recompensa.

## Recompensas de exploracion en Make Sim

El brainstorm vivo esta en
[Exploracion y recompensas](superpowers/specs/2026-10-11-exploration-design.md).
Patio, Jornada, Noche y Guia estan implementados en el simulador el 2026-10-14.
Flujo, cantidades, limites y guardado: [exploration.md](exploration.md).
El port a placa sigue pendiente:

| Camino | Familia de recompensa | Estado |
|---|---|---|
| Patio | Energía al reclamar, sin objeto y sin EV | Cerrado. Buen cuidado +25 ENE, mal cuidado +10, tope 100. |
| Jornada | Guía, mejora de la próxima sesión | Cerrado. Id `guide`. +1 EV en el stat de esa sesión. Cabe una. El mal cuidado no la deja. El +2 EV de la ruta no es este objeto. |
| Noche | Progreso de técnica | Cerrado como regla, no como objeto: +2 de dominio (tope 4/semana) o +1 al contador de Llama. No es un ítem de la bolsa. |

Antes de implementar botin, cada objeto nuevo llena la ficha de
[estándar de catálogo](superpowers/specs/2026-10-14-item-catalog-standard.md):
ID estable, categoría, rareza, icono, ES/EN, stack máximo, efecto tipado,
objetivo, magnitud, duración, límites de uso y origen. Esa ficha sale de
las columnas de Digimon World y no copia sus nombres, precios ni cifras.
Los seis objetos de esta tabla no se reescriben: la carne, el tónico, la
estrella y la proteína siguen mezclando recuperación y EV porque ya están
en el guardado. Una recuperación temporal nueva no se mezcla con EV
permanente. No agregar materiales sin un uso real ni tratar la ficha como
código ya disponible. El EV y el dominio de la noche están aprobados como
diseño y funcionan en Make Sim; siguen pendientes en firmware.

## Alimentacion y peso implementados

El usuario confirmo que Alimentar contiene **solo carne y proteina, ambas
ilimitadas**, con peso que impacta combate/evolucion. El comportamiento vive
en `core.nutrition` y `vpet_core/Nutrition`; la placa y el simulador comparten
la misma regla de alimentación. El plan de implementacion y su evidencia estan en
[este plan](superpowers/plans/2026-10-14-feeding-weight-combat-evolution.md).
Las comidas no otorgan EV ni descuentan los stocks legacy. El peso afecta OFF,
DEF y SPD dentro de limites y el estado muestra el rango saludable por etapa.
Filete, champinon y otros
objetos se destinan a **mejorar stats desde la mochila**; sus stats objetivo,
magnitudes, duracion y origen requieren su propia definicion de catalogo.
Se descarta la propuesta previa de usarlos como comidas de hambre/peso en
Alimentar, incluido su kit inicial. Todavia no existen como objetos del juego.

La tabla refleja el comportamiento implementado para Alimentar. Filete,
champinon y otros objetos de mejora siguen sin estar implementados y requieren
definir stat, magnitud, limites y origen antes de incorporarse a la mochila.
La recuperación de una escritura NVS incompleta usa la clave `foodTx` con
valores finales absolutos; al reiniciar se completa sin volver a sumar el efecto.

## Iconografia

La mochila y los seis consumibles usan sprites pixel-art propios, definidos en
`scripts/item_icons.py` y rasterizados por `scripts/build.py`. El mismo BMP
generado alimenta el simulador; `scripts/build_tdisplay.py` lo empaqueta como
VPA para LittleFS y firmware. Los IDs visuales (`ItemMeat`, `ItemEnergy`, etc.)
son presentacion, no IDs de guardado.
