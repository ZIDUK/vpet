# Estándar de técnicas

Fecha: 2026-10-14. Referencia de diseño. No autoriza técnicas nuevas,
cambios de combate, persistencia ni firmware.

Las tres técnicas que sí existen están en `src/core/techniques.py`:
Golpe, Llama y Guardia. El daño de práctica usa poder, ataque, dominio
y defensa (`src/core/practice.py`). La Noche de exploración avanza
Llama o el dominio, y esa regla sigue en
[Exploración y recompensas](2026-10-11-exploration-design.md).

## La lista de Digimon World

Grindosaur publica la lista de Digimon World 1 en una tabla: nombre,
tipo, categoría, poder, MP, efecto y si se puede aprender. Revisada el
2026-10-14: 110 filas.

| Capa | Cantidad | Qué es |
|---|---:|---|
| Técnica aprendible | 56 | Ocho por cada tipo: Fire, Battle, Air, Earth, Ice, Mech, Filth |
| Firma | 53 | La categoría Finisher. Casi todas cuestan 120 MP y no traen efecto de estado |
| Innata que no se aprende | 1 | Bubble: poder variable, 0 MP, aprendible No |

El poder va de un dígito a 777. Cinco técnicas aprendibles tienen poder
0: son buffs, no golpes. Una fila, Glacial Blast, está en 0 de poder y
0 de MP; es un hueco de la tabla, no un patrón.

La página describe cinco formas de aprender, y cuatro dependen del azar
o de un maestro que ignora la especie:

1. Ver el golpe en un combate y tener una probabilidad de copiarlo, solo
   si esa especie puede usarlo.
2. Subir Brains en el gimnasio y tener una probabilidad pequeña de
   aprender una técnica que ya le correspondía.
3. Al digievolucionar, si la forma nueva no puede usar lo anterior,
   recibe la técnica más débil de su propia lista.
4. Seadramon enseña un hielo débil aunque la especie no aprenda hielo.
5. Kabuterimon enseña Bug si defensa y velocidad pasan de 500, aunque
   la especie no pueda aprenderlo.

## La ficha

Cada técnica nueva, cuando se apruebe, llena estos campos. Los números
de Digimon World no se copian.

| Campo | En Digimon World | En el vPet hoy |
|---|---|---|
| ID estable | El nombre del golpe | Sí: `punch`, `flame`, `guard` |
| Nombre ES/EN | Una columna | Parcial: `GOLPE`, `LLAMA`, `GUARDIA` |
| Tipo | Fire, Battle, Air, Earth, Ice, Mech, Filth | Cerrado como elemento de Cyber Sleuth. Golpe `neutral`, Llama `fire`, Guardia sin elemento. Firemon es `fire` |
| Categoría | Technique o Finisher | No está. Las tres son del mismo catálogo |
| Poder | Entero, a veces un rango | Sí: 12, 24 y 0 |
| MP | Coste. Las firmas, 120 | Sí: 0, 8 y 0 |
| Efecto | None, Stun, Confusion, Poison o Flat | No está. El combate no tiene estados |
| Quién la aprende | La especie, salvo los dos maestros que rompen la lista | Implícito: el catálogo es de Firemon rookie |
| Cómo se aprende | Azar, gimnasio, evolución o maestro | Contador: Golpe y Guardia desde el inicio; Llama con `training >= 2`. La Noche suma a ese contador o al dominio |
| Alcance | No está en la tabla | Sí: 1 o 2 |
| Enfriamiento | No está | Sí: Llama tiene 1 |
| Dominio | No está | Sí: 0–100. Entrenar una ya aprendida suma 5. La Noche suma dominio con tope semanal |
| Equipadas | La tabla no dice el cupo | Dos |

El daño de hoy es poder, más ataque, más dominio, menos defensa. El
dominio y el enfriamiento son del vPet. Digimon World limita el golpe
con el MP.

## Qué se toma

La técnica pertenece a la ficha de la especie, no a la mochila. La
comida sigue siendo de todos. Otra especie no muestra las técnicas de
Firemon.

Hay dos categorías. La técnica compartida se aprende. La firma es el
golpe propio del pet: no sale de entrenar ni de la Noche, y no lleva
efecto de estado. Si más adelante una firma existe, el coste de MP es
el mismo entre especies y el poder cambia en la ficha. El 120 y el 777
de esa lista no son cifras del vPet.

Aprender es un contador, como ya hace Llama. El gimnasio de Brains es
el mismo concepto que entrenar o pasar la Noche, sin la probabilidad.
Ver un golpe el sábado y copiarlo al azar no entra. Un maestro que
enseñe un elemento ajeno a la especie tampoco: se vería la técnica de
otro pet.

Al evolucionar, la ficha de la etapa nueva dice qué se conserva. Si no
puede usar lo anterior, se queda con la técnica más débil de esa etapa.
Eso todavía no está en el catálogo: campeón y definitivo no tienen
lista propia.

Un manual, si algún día es un objeto, solo avanza el contador de
aprendizaje. El golpe no se guarda en la bolsa.

## Qué no se toma

- Las 56 técnicas y las 53 firmas. Firemon se queda con tres. Un pet
  nuevo trae su lista corta y, si se aprueba, una firma.
- Los siete tipos de Digimon World 1 como tabla de ventajas. Esa lista
  no publica un círculo de debilidades. La propuesta de más abajo es
  otra: la debilidad vive en la ficha de la especie.
- Veneno, aturdimiento, confusión y pixelado. El combate de la placa y
  el del simulador todavía no son la misma regla.
- Poder aleatorio dentro de un rango. Bubble es el único caso, y el
  daño del vPet ya es una cuenta fija.
- Equipar más de dos. El cupo actual se queda.

## Firemon, leído con esta ficha

| ID | Categoría | Elemento | Poder | MP | Cómo se obtiene |
|---|---|---|---:|---:|---|
| `punch` | Técnica innata | `neutral` | 12 | 0 | Desde el inicio |
| `guard` | Técnica innata, poder 0 | ninguno | 0 | 0 | Desde el inicio. Ocupa el lugar del buff |
| `flame` | Técnica aprendible | `fire` | 24 | 8 | Dos entrenamientos, o dos Noches completas |

Guardia no es una firma. Es el golpe de poder 0 que ya se conoce. La
firma, si un pet futuro la tiene, es otra fila.

## Atributo en Time Stranger

Revisión del 2026-10-14, con la nota de Bandai Namco y la guía de
campo del juego. No está adoptado en el vPet.

El atributo es uno por monstruo: Vaccine, Data, Virus, y fuera del
círculo Free, Variable, Unknown y No Data. No Data solo aparece en
In-Training I y II. El círculo no tiene excepciones entre los Vaccine,
Data y Virus del juego: Vaccine le gana a Virus, Virus a Data, Data a
Vaccine. Quien pega lleva su atributo. En la ficha del que recibe hay
una casilla para cada uno de los tres, y esa casilla siempre dice lo
mismo: débil al que le gana, resistente al que pierde contra él.

Free, Variable, Unknown y No Data no consultan esas casillas. Su
multiplicador de atributo es 1.

Bandai describe el daño combinado entre un 50 % y un 300 %. Ese techo
es el mismo cruce de Cyber Sleuth: atributo a doble o a la mitad, y el
elemento acertado suma la mitad. Time Stranger parte de ahí y agrega
otra cosa: cada especie tiene además su fila de elementos, con
resistencia a la mitad e inmunidad a cero. Un fuego puede pegar menos
si esa ficha resiste el fuego. En Cyber Sleuth fallar el elemento no
resta.

## Elementos cerrados

Cerrado el 2026-10-14. Se usa el elemento de Cyber Sleuth, no la fila
por especie de Time Stranger y no la lista `weak_to` suelta.

Nueve elementos: `fire`, `plant`, `water`, `electric`, `wind`, `earth`,
`light`, `dark`, `neutral`.

| Círculo | Regla |
|---|---|
| Fuego, planta, agua | Fuego gana a planta, planta a agua, agua a fuego |
| Eléctrico, viento, tierra | Eléctrico gana a viento, viento a tierra, tierra a eléctrico |
| Luz y oscuridad | Se ganan entre sí |
| Neutral | No gana a nadie y nadie gana por elemento contra él |

La especie tiene un elemento. La técnica tiene otro. Si el elemento de
la técnica le gana al elemento de quien recibe, el daño se multiplica
por 3 y se divide por 2. Si no le gana, el multiplicador queda en 1.
Guardia se aplica después y parte el daño a la mitad, con mínimo 1.

El cálculo de hoy no cambia hasta cerrar la paridad de combate del
roadmap. Después, el mismo cambio entra en el simulador y en la placa.
El pendiente está en
[el roadmap](../plans/2026-10-11-delivery-roadmap.md), sección
«Despues de P1: elemento de la tecnica».

Firemon es `fire`. Golpe es `neutral`. Guardia no tiene elemento, porque
no hace daño. Llama es `fire`. Una técnica de agua contra Firemon suma
la mitad. Llama contra una especie planta suma la mitad. Llama contra
una especie agua se queda en el daño normal.

La especie siguiente, cerrada el 2026-10-14, es planta. Lleva un golpe
neutral, una guardia y una técnica de planta que se aprende con el mismo
contador de dos. No lleva firma. Su nombre, su poder y su MP siguen
sin elegir. Al cambiar de etapa se conservan las técnicas que esa etapa
liste; si no tiene lista propia, se quedan las aprendidas.

## Técnicas de Digimon World 1, pasadas a esos elementos

La tabla de 110 no entra al juego con esos nombres ni con ese poder.
Esos golpes son de ese juego. Lo que se estandariza es la traducción
del tipo al elemento, para cuando una ficha propia declare el suyo.

| Tipo en Digimon World 1 | Elemento del vPet |
|---|---|
| Fire | `fire` |
| Ice, incluidos los golpes de agua de esa fila | `water` |
| Air, si el golpe es eléctrico | `electric` |
| Air, si el golpe es viento | `wind` |
| Earth, insecto o planta | `plant` |
| Battle | `neutral` |
| Mech | `neutral` |
| Filth | `neutral` |

Air se parte en dos porque en esa tabla el rayo y el viento comparten
fila, y aquí son elementos distintos. Mech y Filth se quedan en
neutral: Cyber Sleuth no tiene acero ni suciedad. El acero y el hielo
como elementos propios son de Time Stranger, y este corte no los usa.
