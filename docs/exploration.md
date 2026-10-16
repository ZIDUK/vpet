# Exploracion en Make Sim y T-Display

Implementada el 2026-10-14 para el simulador y portada al firmware el
2026-10-16. La barra de ambos tiene nueve iconos; Explorar esta entre
entrenamiento y batalla. La placa incluye rutas, atributo, tabla de salida,
viaje, regreso anticipado, reclamacion unica y recibo, en ES/EN.

## Reloj y persistencia de placa

La T-Display usa segundos del calendario civil para viajes y semana, nunca
millis para recompensas. Sin RTC respaldado no puede medir un intervalo sin
alimentacion: cuando pierde la hora pide AJUSTAR RELOJ / SET THE CLOCK.
Las rutas se pueden consultar, pero enviar/reclamar requiere hora fiable.
El ajuste abre Fecha y luego Hora. Retroceder el calendario no repone topes
semanales; el tiempo anterior a la salida da cero progreso.

Se conserva `clockCheckpoint`, el ultimo calendario fiable observado al guardar,
con checkpoint cada minuto durante viaje. Un reinicio con calendario conservado
reanuda el viaje; un calendario perdido o anterior al checkpoint pide ajuste.
No se simulan expediciones adicionales ni se inventa tiempo apagado.

NVS principal sigue en schema 3. La clave opcional `expState` es un String
ASCII, version 1, maximo 320 bytes, 25 enteros decimales separados por coma:

```text
version,week,weekEv,weekMastery,guide,guidePending,clockCheckpoint,
away,route,stat,started,good,learning,hasReceipt,
receiptRoute,receiptStat,receiptGood,receiptFull,receiptElapsed,
receiptEnergy,receiptEv,receiptMastery,receiptLearning,receiptGuide,receiptLearned
```

Rutas 0=Patio, 1=Jornada, 2=Noche; stats siguen CombatStat Hp/Mp/Off/Def/Spd/Brn
0..5. Es una clave nueva: no se renumera ningun enum persistido anterior.
Campos booleanos solo aceptan 0/1; tiempos no negativos hasta 2^53-1, EV semanal
0..8, dominio semanal 0..4. Registros truncados/futuros/incompatibles bloquean la
carga sin borrar la partida. Ausencia de la clave migra a estado vacio.

Salida, cobro y reconocimiento del recibo usan el snapshot completo atomico
`saveTx` version 2, junto con EV, energia, tecnicas y stock. Se leen journals
version 1, que no sobrescriben una exploracion existente. Rechazo restaura el
snapshot en RAM; intent aceptado pendiente bloquea acciones y se recupera antes
de confirmar. Swap/park conservan el estado por mascota. La evolucion normal
conserva la expedicion; una vida nueva limpia viajes, topes y Guia.

Guia ocupa el indice legacy 7 sin reutilizar Volver=6. Se muestra cuando existe
y abre Entrenamiento sin gastarse. Al completar una sesion con hueco de EV se
consume antes que Manual y no se suman ambos bonos. App guarda la sesion completa,
incluida la Guia; cancelar o rechazar el guardado conserva el objeto.

El renderer de placa usa `ExplorationUi.h`, llamado desde Panels.cpp y desde
el harness nativo de imagen. Las tablas mantienen celdas delineadas, divisor,
colores por fila, sprite de la evolucion actual y botones de contorno en salida.
`scripts/preview_exploration_board.py` produce capturas ES/EN reproducibles.
Las pruebas de host no sustituyen la inspeccion visual fisica posterior.

## Visual aprobada 2026-10-15

Rutas y atributos mantienen tres filas visibles a 240x135, con iconos,
franja amarilla y fondo resaltado solo en la seleccion. Las rutas separan
nombre y premio en dos areas de texto medidas; la duracion tiene su propia
columna derecha. Los atributos reutilizan los iconos de Training, incluido
el icono de flecha para Volver.

Preparar salida muestra el vPet evolucionado a la izquierda y una tabla de
atributo/recurso/tecnica, premio, objeto y coste a la derecha. La Guia solo
se anuncia cuando el premio real la incluye. La condicion de cuidado y
los botones ocupan bandas separadas. No cambia balance ni persistencia.

Correccion segun referencia de Training: Preparar salida usa celdas
delineadas con divisor central, etiquetas verdes/amarillas/rosas y valores
blancos alineados a la izquierda. Los botones tienen contorno amarillo o
neutro, sin relleno brillante. El cuidado permanece junto al sprite para
dar mas altura a las filas. Las tablas de regreso comparten los bordes.

`scripts/preview_exploration.py` genera las pantallas ES/EN y `layout.png`;
`tests/test_exploration_layout.py` verifica la contencion de texto y que
no se superponga al recorrer todas las posiciones de ambas listas.

De vuelta, Regreso anticipado y Recompensas guardadas comparten otra tabla:
tiempo transcurrido (no tiempo restante), atributo/recurso/tecnica, premio y
objeto. El estado Por reclamar distingue una prevision del recibo Ya guardado.
El recibo usa sus valores persistidos aunque los atributos del pet cambien.
`returns.png` muestra estas tres pantallas ES/EN; sus pruebas incluyen las
tres rutas y premios parciales, sin modificar el protocolo de reclamacion.

## Flujo

Rutas -> atributo (solo Jornada) -> confirmar -> viaje -> reclamar -> recibo.
NEXT mueve el foco; ACTION activa; BACK cancela la preparacion o cierra el
panel. El regreso anticipado tiene una confirmacion cuyo foco inicial es
Volver. Cerrar un panel o dejarlo inactivo diez segundos no cancela un viaje.
El recibo se guarda con los premios; Continuar lo reconoce y abre las rutas.

Home muestra el viaje, el tiempo restante y la evolucion actual del pet.
La animacion usa milisegundos y el viaje usa segundos de calendario.
Status sigue disponible; las acciones de cuidado, entrenamiento y combate
redirigen a la expedicion hasta reclamar. El cuidado y evolucion automatica
se pausan durante la ausencia. No se cobran viajes adicionales por dias sin
abrir el simulador.

## Reglas

| Ruta | Duracion | Premio |
|---|---:|---|
| Patio | 30 minutos | +25 ENE con buen cuidado; +10 con mal cuidado. Proporcional al regresar antes, redondeado hacia abajo y limitado a 100. Sin EV ni objeto. |
| Jornada | 8 horas | +2 EV en el atributo elegido; +1 desde las 4 horas; 0 antes. Tope compartido 8 EV/semana. Una Guia con buen cuidado y viaje completo. |
| Noche | 8 horas | Llama bloqueada: +1 aprendizaje solo con viaje completo; dos noches la aprenden. Llama aprendida: +2 dominio, +1 desde 4 horas, tope 4/semana y 100 dominio. |

Huevo/bebe no salen. Hambre y energia no bloquean la salida y no se gasta ENE.
El cuidado se captura al salir: hambre, energia y animo >=50 y sin lesion es
buen cuidado; cualquier otro caso es pobre. Este umbral estaba abierto en la
spec y se fija como parametro de balance visible. El cuidado pobre cambia
Patio y la elegibilidad de Guia; conserva las cantidades permanentes cerradas.
Noche toma el modo aprendizaje/dominio al salir y no cambia equipamiento.

Los limites semanales se cobran en la semana de reclamacion. La semana empieza
el lunes a las 00:00 del calendario local del simulador. Retroceder el reloj no
reinicia un limite ya consumido; un reloj anterior a la salida da cero tiempo.
La configuracion del reloj se guarda junto con la partida y sigue avanzando
despues de reiniciar. Como en cualquier partida local, editar el archivo o
adelantar manualmente el calendario permite cambiar el tiempo del juego.

## Guia

ID `guide`, nombre Guia / Guide, categoria mejora de entrenamiento, rareza
comun determinista, icono `ItemGuide`, capacidad una, stock inicial cero.
Origen: Jornada completa con buen cuidado. Efecto: +1 EV del atributo de la
proxima sesion de entrenamiento completada y guardada, sin modificar IV,
peso, energia ni duracion. Su bono no usa el limite semanal de Jornada.
Se conserva si la sesion se cancela, falla el guardado o el entrenamiento base
llena el atributo a 252. Seleccionarla en Mochila abre entrenamiento.

La mochila actual tiene desplazamiento de tres filas y no define capacidad
general. Por eso la Guia puede entrar con los otros objetos presentes; tener
ya una impide obtener otra, sin acumular una segunda en la puerta. El campo
`guide_pending` permite recuperar una entrega pendiente de una futura bolsa
con capacidad, pero esta entrega no inventa ese limite ni genera duplicados.
Los indices legacy 0..5 y Volver=6 se conservan; Guia usa el indice adicional 7.

## Guardado y arquitectura

- `core.exploration.Exploration`: reglas puras, reloj inyectado y preview.
- `ExplorationSession`: navegacion, confirmacion y transacciones completas.
- `exploration_renderer`: pantallas 240x135, ES/EN y recursos existentes.
- `Pet.to_dict/load_from_dict`: campo `exploration` version 1.
- `SimulatorServices`: JSON temporal, fsync y reemplazo atomico; restauracion
  automatica al iniciar Make Sim y persistencia del offset del reloj.
- `batch_commit`: aplica EV, consume Guia y guarda todo en una transaccion.

Contrato JSON del campo `exploration`:

```json
{
  "version": 1,
  "week": 2963,
  "week_ev": 0,
  "week_mastery": 0,
  "guide": false,
  "guide_pending": false,
  "trip": {
    "route": "jornada",
    "stat": "off",
    "started": 1791979200,
    "good": true,
    "learning": true
  },
  "receipt": null
}
```

`started` son segundos civiles locales desde 1970-01-01, del mismo calendario
que muestra el simulador. `trip=null` significa que esta en casa. Reclamacion
reemplaza trip por un recibo con route/stat/good/elapsed/full y cantidades
energy/ev/mastery/learning/guide/learned. Un recibo nunca vuelve a aplicar los
premios. Un fallo al guardar restaura el snapshot anterior y permite reintentar.
Partidas antiguas reciben un registro vacio, sin perder inventario o tecnicas.
Este contrato JSON es el del simulador. El port de placa del 2026-10-16 usa
el registro y transacciones NVS descritos arriba; no guarda JSON ni SQLite.

## Evidencia reproducible

```sh
.venv-platformio/bin/python -m pytest tests/test_exploration.py tests/test_exploration_menu.py tests/test_exploration_ui.py -q
make build-tdisplay
.venv-platformio/bin/python scripts/preview_exploration.py
make sim SIM_ARGS="--max-frames 80"
```

Las pruebas recorren teclas reales de pygame y guardado en disco con reloj
controlado: Jornada, bloqueo de batalla, reclamacion, Guia, entrenamiento y
consumo una sola vez. Tambien cubren 4/8 horas, tope semanal, reloj atrasado,
fallos de guardado, migracion, ES/EN y sprites de las tres evoluciones.

Filete, champinon, disco de pelea, nuevas especies y nuevas tecnicas conservan
su trabajo separado. La paridad de combate y aceptacion fisica siguen abiertas.
