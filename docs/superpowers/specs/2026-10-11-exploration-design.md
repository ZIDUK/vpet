# Exploración y recompensas

Requerimientos vivos del brainstorm del 2026-10-11. Índice de fase:
`docs/superpowers/plans/2026-10-11-delivery-roadmap.md`, sección
«P2: exploracion y recompensas».

No hay funcionalidad implementada. Este documento no autoriza cambios de
economía, persistencia, menú ni firmware. Los valores numéricos siguen
pendientes de aprobación. La exploración no adelanta el cierre físico de la
placa ni la paridad de combate.

## Jugador

Tiene poco tiempo entre semana. Le gusta tener el vPet, lo prepara para
combatir y el sábado se enfrenta a otros jugadores por hobby. Esos combates
son el momento social. Entre semana el pet tiene que avanzar casi solo: lo
manda a explorar y cierra el aparato. Los minutos que sí tiene se usan para
cuidarlo, equipar una técnica y pelear.

Éxito de la fase: una semana de mandarlo a explorar deja al pet presentable
para el sábado. Quien además usó el entrenamiento corto y la práctica llega
un poco más fuerte. Dejar el aparato en un cajón no maxea al pet.

## Decisiones cerradas

| Tema | Decisión |
|---|---|
| Entrada | Icono nuevo de exploración en la barra superior. |
| Tipo de salida | Larga. El pet se va, el tiempo corre con el aparato apagado y el botín se reclama una sola vez. |
| Sesión corta en pantalla | Fuera. El entrenamiento de 10 segundos sigue siendo la sesión activa. |
| Manía que expira al dormir | Fuera. El progreso que cuenta para el sábado tiene que seguir ahí. |
| Álbum de estampas y cosmético de colección | Después. No entra en este corte. |
| IV | No cambian. |
| Stats permanentes | Con tope. La exploración no regala crecimiento ilimitado. |
| Recuperación temporal y EV permanente | Efectos distintos. No se mezclan en un mismo premio. |
| Expediciones atrasadas | Si el jugador no abre el aparato, se resuelve un solo viaje. No se simulan varias salidas perdidas. |
| Piso del sábado | **C**, cerrado el 2026-10-12. Una semana deja un piso de las dos cosas: EV con tope semanal y progreso de técnica, más el objeto de la ruta. Quien además usó la pesa o el entrenamiento del menú llega más fuerte. |
| Ritmo frente al entrenamiento | La pesa sigue siendo el camino fuerte para subir una stat. Una semana completa de mandarlo solo queda por debajo de unas pocas pesas. La exploración no paga igual ni mejor que la sesión activa. |
| Coste de energía | **A**, cerrado el 2026-10-12. La salida no gasta energía. El coste es el tiempo y que, hasta que vuelva, el pet no está para entrenar ni pelear. La energía sigue disponible para cuidar, usar la pesa y combatir cuando está en casa. |
| Retorno anticipado | **B**, cerrado el 2026-10-12. Vuelve en el acto y cobra solo la parte proporcional al tiempo ya transcurrido, dentro de la misma ruta. Esa cobranza es la única. No queda un segundo premio al cumplirse el reloj original. |
| Quién puede salir | Cerrado el 2026-10-12. El huevo y el bebé se quedan en casa. Explorar empieza en rookie, la misma etapa en la que ya puede entrenar y pelear. Desde ahí, la única traba es que no esté ya entrenando, peleando o de viaje. No hay candado de hambre ni de energía. Si salió mal cuidado, el botín cae en la parte peor de la misma ruta. |
| Relojes | Cerrados el 2026-10-12. Patio: 30 minutos. Jornada: 8 horas. Noche: 8 horas. |
| Puesto del icono | Cerrado el 2026-10-12. Después de entrenamiento y antes de batalla: Status, comida, entrenamiento, exploración, batalla, descanso, objetos, pedia, opciones. |
| Cantidades | Cerradas el 2026-10-12. Jornada completa: +2 EV en la stat elegida al salir, tope 8 EV por semana entre todas las stats. Noche completa con técnica aprendida: +2 de dominio, tope 4 por semana. Noche completa sin Llama aprendida: +1 al contador de aprendizaje; dos noches completas la aprenden. Patio: sin EV ni técnica. Por debajo de 4 horas el premio permanente de Jornada o Noche es 0; a las 4 horas, la mitad (+1 EV o +1 de dominio). El contador de Llama solo sube con la noche completa. El tope se reinicia el lunes a las 00:00. El resultado bueno o pobre dentro de la misma ruta lo decide el cuidado, sin azar. |
| Implementación | No empieza hasta aprobar alcance y balance. |

## Ritmo de la semana

- Antes de irse, elige un camino y manda al pet. Tarda lo que tarda mirar el menú.
- Al volver, reclama una vez: un objeto de esa ruta y, si la ruta lo da, un paso permanente hacia el combate. Lo cuida si hace falta y puede mandarlo otra vez.
- El viernes revisa Status, equipa la técnica y deja al pet listo.
- El sábado pelea.
- La exploración pone el piso de la semana. El entrenamiento corto y la práctica ponen la ventaja de quien sí tuvo esos minutos.

## Caminos

Tres relojes cerrados, una familia de botín por camino. La calidad cae dentro
de esa familia. Un viaje no cambia de familia ni entrega objeto raro, EV y
técnica a la vez. Los números de EV y de técnica están cerrados. Los objetos
concretos de cada ruta siguen sin definirse.

| Camino | Reloj | Premio permanente | Tope |
|---|---|---|---|
| Patio | 30 minutos | Ninguno. Solo comida o energía. | Sin EV ni técnica. |
| Jornada | 8 horas | +2 EV en la stat elegida al salir. A las 4 horas, +1 EV. Antes, 0. | 8 EV por semana, entre todas las stats. |
| Noche | 8 horas | Si Llama no está aprendida, +1 al contador y solo con la noche completa. Si ya hay técnica aprendida, +2 de dominio; a las 4 horas, +1. | Dos noches completas aprenden Llama. Dominio: 4 por semana. |

El cuidado previo inclina el resultado hacia la parte buena de la misma
familia. Un pet hambriento o agotado no descubre otra categoría de premio:
vuelve peor dentro de la ruta que ya eligió.

Si la bolsa está llena, el objeto espera en la puerta hasta que haya sitio.
Sigue siendo una sola reclamación.

## Referencias usadas

El Digimon de llavero no manda al monstruo de expedición. El patrón sale de
otros juegos de criar monstruos:

- Poké Pelago separa comida, objetos y EV por isla. El EV es lento y tiene tope.
- Pokémon Quest fija la rareza por la etapa y cobra al terminar.
- DigiFarm asigna una sola tarea: buscar, fabricar o entrenar.
- Las errancias de Monster Rancher pueden fallar si el monstruo sale en mal estado.

## Sigue abierto

1. Objetos concretos de cada ruta. El catálogo actual no se repone: ver `docs/items-and-rewards.md`. Falta decidir qué objeto entrega Patio, Jornada y Noche.
2. Catálogo: ID estable, categoría, rareza, icono, ES/EN, stack máximo, efecto tipado, objetivo, magnitud, duración, límites y origen.
3. Familias a confirmar: alimento, recuperación, material, manual de técnica. El cosmético queda con el álbum, fuera de este corte.
4. Inventario lleno más allá de «espera en la puerta», recompensa duplicada y tablas por destino.
5. Guardado atómico de salida, regreso y reclamación única, compatible con el esquema NVS actual. No se diseña la serialización hasta cerrar el alcance.

## Fuera de este corte

- Cerrar la aceptación física de la placa.
- Igualar el combate entre simulador y firmware.
- Cambiar IV o permitir EV sin tope.
- Álbum, sellos y cosméticos de colección.
- Habilitar WiFi o depender de un servidor para que el tiempo siga corriendo.

El inventario que si existe, sus efectos y sus cantidades iniciales estan en
[Catalogo de objetos](../../items-and-rewards.md). Ese catalogo confirma que
todavia no hay una fuente repetible de botin; las familias de esta propuesta no
deben presentarse como mecanicas disponibles.
