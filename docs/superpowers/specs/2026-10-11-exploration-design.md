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
| Implementación | No empieza hasta aprobar alcance y balance. |

## Ritmo de la semana

- Antes de irse, elige un camino y manda al pet. Tarda lo que tarda mirar el menú.
- Al volver, reclama una vez: un objeto de esa ruta y, si la ruta lo da, un paso permanente hacia el combate. Lo cuida si hace falta y puede mandarlo otra vez.
- El viernes revisa Status, equipa la técnica y deja al pet listo.
- El sábado pelea.
- La exploración pone el piso de la semana. El entrenamiento corto y la práctica ponen la ventaja de quien sí tuvo esos minutos.

## Caminos propuestos

Tres relojes, una familia de botín por camino. La calidad cae dentro de esa
familia. Un viaje no cambia de familia ni entrega objeto raro, EV y técnica
a la vez. Las duraciones y las cantidades de la tabla son la forma del
reloj, no números aprobados.

| Camino | Cuándo se manda | Botín | Qué deja para el sábado |
|---|---|---|---|
| Patio | Un hueco corto, menos de una hora | Comida o energía | El pet sigue usable. Casi no falla. |
| Jornada | La mañana, hasta la noche | Material o cuidado | Un paso de EV con tope semanal, en la stat de esa ruta. |
| Noche | Al dormir | Más raro: chispa de técnica, o vuelve hambriento si salió mal cuidado | Progreso de una técnica. |

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

1. Qué garantiza una semana de expediciones para el sábado.
   - **A.** Un pet que ya puede pelear: EV con tope y una técnica avanzada. Los objetos son extra.
   - **B.** La bolsa llena. Los stats siguen saliendo de los minutos de entrenamiento activo.
   - **C.** Un piso de las dos cosas, bajo un tope semanal. Quien además entrenó llega más fuerte.
   - Recomendación de este brainstorm: **C.** Sin elegir todavía.
2. Duraciones reales, coste de energía, requisitos para salir y qué pasa si se cancela a mitad.
3. Orden del icono nuevo entre las ocho entradas actuales.
4. Catálogo: ID estable, categoría, rareza, icono, ES/EN, stack máximo, efecto tipado, objetivo, magnitud, duración, límites y origen.
5. Familias a confirmar: alimento, recuperación, material, manual de técnica. El cosmético queda con el álbum, fuera de este corte.
6. Inventario lleno más allá de «espera en la puerta», recompensa duplicada, topes, probabilidades y tablas por destino.
7. Guardado atómico de salida, regreso y reclamación única, compatible con el esquema NVS actual. No se diseña la serialización hasta cerrar el alcance.

## Fuera de este corte

- Cerrar la aceptación física de la placa.
- Igualar el combate entre simulador y firmware.
- Cambiar IV o permitir EV sin tope.
- Álbum, sellos y cosméticos de colección.
- Habilitar WiFi o depender de un servidor para que el tiempo siga corriendo.
