# Estándar de catálogo de objetos

Fecha: 2026-10-14. Referencia de diseño. No autoriza objetos nuevos,
cambios de economía, persistencia ni firmware.

Los objetos que sí existen siguen en
[Catálogo de objetos](../../items-and-rewards.md). La exploración que
los va a soltar está en
[Exploración y recompensas](2026-10-11-exploration-design.md). El
sábado y la tienda, que reutilizan el mismo recibo, están en
[el plan del negocio](../plans/2026-10-13-mall-business-plan.md).

## De dónde sale el esquema

Digimon World publica cada objeto con las mismas columnas. La tabla
inglesa (efecto, precio, cómo se consigue, quién lo suelta) y la
japonesa (`アイテム名 | 使用可 | 買値 | 功績 | 効果 | 主な入手先`)
dicen lo mismo: nombre, cuándo se puede usar, precio, mérito, efecto
y origen.

Eso es un estándar de ficha, no una lista para copiar. Los nombres,
los bits, los puntos de mérito y los lugares de ese juego no entran
al vPet. Precio y mérito se anotan aquí para no convertirlos en
moneda: el vPet no tiene tienda de bits. Un premio de marca es un
recibo, no un precio.

La lista pública completa está en Grindosaur
(`digimon-world/items`): una sola tabla, 128 objetos, con nombre,
efecto corto y precio. El recuento por efecto, revisado el 2026-10-14:

| Grupo | Cantidad | Ejemplos del grupo |
|---|---:|---|
| Ficha de evolución, una por especie | 47 | Grey Claws, Metal part, Giga Hand |
| Comida y cuidado | 30 | Meat, Blue apple, Power fruit, Pricklypear |
| Curación de vida o magia, en varios tamaños | 8 | sm.recovery, MP Floppy, Double flop |
| Chip permanente | 9 | HP Chip, DV Chip A |
| Herramienta de mapa | 9 | Auto Pilot, fishing rod, Health shoe |
| Disco de un combate | 7 | Off. Disk, Omni Disk |
| Llave o prueba de misión | 6 | Mansion key, Blue Flute, AS Decoder |
| Estado, coma o protección | 5 | Various, Restore, Protection |
| Mejora de entrenamiento | 4 | Supercarrot, Training Manual |
| Herida o enfermedad | 2 | Bandage, Medicine |
| Objeto para vender | 1 | Gold Acorn |

Casi la mitad de la lista son fichas de evolución. El resto repite el
mismo efecto en tamaños: cuatro carnes, cuatro curaciones de vida,
cuatro de magia, disco y superdisco. En una pantalla de 240×135 eso es
un campo de magnitud, no un objeto nuevo por tamaño.

La lista completa también mezcla familias. Power fruit, Muscle Yam,
Deluxe mushroom y Black trout son comida en el nombre y chip en el
efecto. Chain melon dice que sirve para muchas cosas. La ficha del
vPet es más estricta que Digimon World: un objeto nuevo declara una
familia. Los seis objetos ya guardados se quedan con la mezcla que
tienen.

De esa lista, lo que el vPet puede usar más adelante sin un mapa es
poco y ya cabe en las familias de abajo: comida, recuperación, ánimo,
mejora de entrenamiento y disco de pelea. Bajar de peso, como
Pricklypear, es una magnitud negativa de la comida; el peso ya existe
en la partida. La almohada de descanso sería recuperación al dormir.
El coma, el piloto automático, la caña, la campana de enemigos, las
llaves y el objeto para vender necesitan una ciudad que aquí no hay.

Digimon World 3, en la guía de objetos soltados de GameFAQs (FAQ 24593,
Med Jai, 2007), es otro juego: un RPG de equipo, niveles y equipo
puesto. La propia guía deja fuera lo de tienda y lo de cofres, así que
no es un catálogo completo. Lo que sí lista son accesorios elementales
en tres fuerzas, crestas de combate, curaciones por tamaño, objetos de
daño, reducciones de daño y de magia, chips con rango aleatorio,
armas, subastas con reloj de historia, un set de cuatro piezas por
especie y armas legendarias forjadas en cuatro pasos.

Eso no mejora la ficha del vPet. El elemento ya vive en las técnicas.
El chip aleatorio choca con el resultado fijo del cuidado. El set de
cuatro piezas por especie y la forja de cuatro niveles son el catálogo
que esta pantalla no puede cargar. Training Book y Power Brace repiten
la mejora de entrenamiento, esta vez como equipo que se lleva puesto;
en la placa basta con gastar el objeto antes de la sesión. Revisado el
2026-10-14 y no adoptado.

## Los 12 campos

El roadmap pide estos campos antes de crear botín. Estado contra el
código de hoy (`INVENTORY_ITEMS` en `src/core/inventory.py`): una
tupla de nombre, id, un objetivo y una magnitud. El resto de los
efectos está escrito aparte.

| Campo | En Digimon World | En el vPet hoy |
|---|---|---|
| ID estable | Nombre interno del objeto | Sí: `meat`, `energy`, `exp`, `ring`, `protein`, `medkit` |
| Categoría | La sección de la lista, no una columna | No está en la ficha |
| Rareza | Común, raro, semi, super, según el lugar | No está |
| Icono | Sprite del objeto | Sí, en `scripts/item_icons.py`. Es presentación, no el id |
| ES/EN | Dos columnas de nombre | Parcial: etiquetas cortas (`CARNE` / `MEAT`). No hay descripción traducible. En código el anillo sigue como `ANILLO` / `FIRE RING`; el nombre visible Amuleto está solo en el catálogo escrito |
| Stack máximo | No lo publica | No está. El guardado cuenta unidades sin tope declarado |
| Efecto tipado | Un texto compuesto (`hambre +12, peso +1`) | Parcial: la tupla cubre un efecto. El EV de la carne, la proteína cada cuatro usos, la lesión del botiquín y el sobrealimentar están en código aparte |
| Objetivo | El stat que menciona el efecto | Solo el efecto principal |
| Magnitud | El número dentro de ese texto | Solo el efecto principal |
| Duración | Dentro del efecto (`6 horas`, `×1.2`, `hasta comer otra cosa`) | No está |
| Límites | `使用可`: libre, en combate, en desplazamiento | No está. El botiquín exige lesión y el huevo no usa objetos, pero no es un campo |
| Origen | `主な入手先`: lugar o personaje | No está. Hoy la única fuente es el kit inicial |

Faltan como datos: categoría, rareza, stack, duración, cuándo se puede
usar y origen. El efecto tipado, el objetivo y la magnitud cubren un
solo número. Precio y mérito de Digimon World no se agregan a los 12.

`使用可` es el campo que más falta. Dice en qué pantalla el objeto
hace algo. Un tónico de combate no se bebe desde la mochila de casa,
y un objeto de casa no se usa mientras el pet está de viaje. Eso cabe
en la ficha sin un sistema nuevo.

Valores de límite para el vPet, cuando un objeto nuevo los necesite:

| Límite | Cuándo |
|---|---|
| `casa` | El pet está en casa y no está en combate ni de viaje |
| `combate` | Solo dentro de una pelea |
| `viaje` | No se usa: el pet no está |
| `condición` | Hace falta lesión, hambre, etapa u otra regla ya existente |

## Familias que tomamos

Digimon World separa el efecto en familias. El vPet se queda con
estas. Un objeto nuevo declara una.

| Familia | Qué hace | Qué no hace |
|---|---|---|
| Comida | Hambre y peso | No sube EV |
| Recuperación | Energía, vida o lesión. Se gasta | No sube EV |
| Ánimo | Ánimo, con tope | No sube EV |
| Mejora de entrenamiento | La próxima sesión rinde más, o dura hasta la próxima comida | No suma EV por sí misma |
| Disco de pelea | Un combate, y se acaba | No escribe el stat al terminar |
| Ficha de especie | Solo la usa una especie. Es el objeto exclusivo de un pet futuro | No reemplaza a la comida genérica |

La mejora de entrenamiento es el uso que le faltaba al material de la
Jornada: no es un recurso suelto, es un objeto que mejora la pesa que
ya existe.

Estos patrones de Digimon World se ven y no se adoptan:

- El chip que sube el stat para siempre y salta el techo. El piso del
  sábado ya cerró topes: 8 EV de exploración por semana, 4 de dominio,
  y la pesa sigue siendo el camino fuerte.
- La llave que abre un lugar del mapa. No hay mapa. El centro
  comercial usa el recibo.
- La rareza como tabla aleatoria. El cuidado elige el resultado bueno
  o el pobre dentro de la misma ruta, sin tirada.
- Guardar 100 objetos y portar 10 tipos. La mochila de la placa muestra
  tres y, si está llena, el botín espera en la puerta. Partir la bolsa
  en banco y equipo queda para más adelante.
- Comida favorita por especie, con rechazo al azar. El objeto sigue
  siendo genérico. Un pet futuro puede nombrar un favorito en su ficha;
  el rechazo, si algún día existe, tiene que ser una regla fija y no un
  porcentaje.

## Patrones que sí entran

**La mejora de entrenamiento es el objeto fuerte, no el chip.** En
Digimon World una zanahoria multiplica el entrenamiento un rato y no
regala el punto. En el vPet la traducción es la próxima sesión de 10
segundos, o hasta la próxima comida. No se copian el ×1.2 ni las 6
horas: son números de ese juego. El número del vPet se aprueba cuando
se elija el objeto.

**El origen es un lugar que ya tiene nombre.** En Digimon World lo
común sale en un campo y lo más raro, de un personaje después de un
jefe. Aquí el lugar es una fuente ya escrita:

| Origen | Estado |
|---|---|
| Kit inicial | Es la única fuente que existe en código |
| Patio | Cerrado el 2026-10-14. No deja objeto. Al reclamar, +25 ENE con buen cuidado o +10 con mal cuidado, tope 100, sin EV |
| Jornada | Cerrado el 2026-10-14. El +2 EV de la ruta no es un objeto. Con buen cuidado deja `guide` (Guía / Guide): la próxima sesión de entrenamiento gana +1 EV en el stat entrenado. Cabe una. Se usa en casa. El mal cuidado no la deja |
| Noche | Cerrado como regla de técnica, no como objeto de la bolsa |
| Recibo de tienda | Del plan de negocio. Más adelante |
| Recibo del sábado | Del plan de negocio. Más adelante |

No se inventa un bosque ni un NPC para rellenar la columna de origen.

**Un objeto fuerte puede cobrar un precio además del tope.** Carne
mohosa que llena y enferma, o un hongo que sube el ánimo y arriesga
la lesión, es el ejemplo. En el vPet el tope semanal se queda. El
precio no lo sustituye. Si un objeto nuevo cobra peso, ánimo o una
condición, esa contraprestación se escribe en la ficha y sigue dentro
de los topes ya cerrados. La lesión al azar no entra: el cuidado ya
decide el resultado.

## Los seis objetos de hoy no se reescriben con esta ficha

La carne, el tónico, la estrella y la proteína mezclan recuperación y
EV. Eso ya está en el guardado. Esta ficha obliga a los objetos
nuevos. Mover el EV fuera de la carne sería otro cambio de economía y
no forma parte de este documento.

## Qué queda por cerrar

1. El formato en bytes del guardado de exploración.
2. Nombre, poder y MP de la técnica de planta.
3. Filete y champiñón, con la misma familia que la Guía y un origen que no sea el Patio ni la Jornada.
4. El disco de pelea, después de la paridad del combate.
