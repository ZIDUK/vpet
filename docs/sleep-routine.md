# Noche y rutina de descanso

Contrato aprobado el 2026-10-18 para T-Display. La implementacion Pico conserva
su flujo legado; no define el comportamiento actual de la placa.

## Reloj y personalidad

Home cambia al fondo nocturno a las 18:00 y vuelve al diurno a las 06:00,
aunque el vPet siga despierto o dormido. Requiere Fecha/Hora validas; no
activa WiFi. Si el ESP32 pierde el reloj al desconectarse, ajustar Fecha/Hora.
Sin calendario fiable se permite descansar y recuperar energia por tiempo
encendido, pero no se aprende una noche ni se entrega su premio.

La personalidad usa el mismo `dna[3] % 3` del combate:

| Rasgo | Hora inicial de sueno | Energia cansada | Deja de estar cansado |
| --- | --- | --- | --- |
| 0 | 18:30 | <=20 | >=30 |
| 1 | 18:15 | <=25 | >=35 |
| 2 | 18:00 | <=30 | >=40 |

La hora preferida o la energia baja muestran el sprite cansado. Recuperar
energia no cancela el aviso por horario. No se duerme automaticamente ni
interrumpe Training, Arena, viajes, alimentacion o animaciones de evolucion.
El cansancio detiene el paseo autonomo, no las acciones explicitas.

Tres noches completas con horas de acostarse separadas como maximo 30 minutos
establecen un objetivo. La hora preferida se acerca como maximo 15 minutos
por noche; limites 18:00..23:00. Una noche excepcional cambia la muestra,
no el horario adquirido. Noches interrumpidas y siestas no entrenan el habito.
No se repiten lecciones ni premios al atrasar el calendario. El habito se
conserva al evolucionar y cambiar de mascota; una vida nueva lo reinicia.

## Luz y recuperacion

El usuario inicia descanso con la opcion de luz/sueno del menu Rest.
En Home, la misma opcion despierta e interrumpe sin premio de noche.
No se anaden faltas de cuidado por acostarse tarde ni por despertar antes.
Las APIs legadas de Lights/noteWake conservan su contrato para Pico.

Duracion nocturna: el mayor entre ocho horas y el tiempo hasta las proximas
06:00, calculado al apagar la luz. Ejemplos: 18:00->06:00, 23:00->07:00.
Siesta diurna: 30 minutos. El amanecer y el despertar son independientes.
No existe credito de descanso por tiempo apagado; no hay RTC respaldado.

Recupera +1 energia por cinco minutos encendido, hasta 100. Pausa metabolismo
de cuidado, pero edad y lesiones siguen transcurriendo. No permite iniciar
viajes, entrenar, alimentarse o consumir Mochila mientras duerme. Una noche
completa concede +5 salud, +1 DP, +2 EV MP y +1 EV defensa una sola vez.
Siesta, interrupcion y cambio de reloj no permiten repetir ese premio.

## Guardado y assets

Python guarda `sleep` v1 en JSON mediante reemplazo atomico. Firmware guarda
`sleepState` v1 con energia, sesion, fracciones de tiempo, muestras, hora
preferida y ultima noche premiada en el mismo snapshot completo. Checkpoint
cada cinco minutos, al iniciar/interrumpir y al completar. Tras reinicio
retoma el checkpoint, sin sumar el intervalo sin alimentacion.

Se mantiene schema NVS principal 3 y todos los enums existentes. `saveTx`,
`swapLive` y `swapBack` pasan a snapshot interno v4 con lectura v1/v2/v3/v4.
Los journals antiguos no sobrescriben `sleepState`. Registros incompatibles
fallan cerrados; Pending bloquea el loop hasta confirmar el guardado.

Originales suministrados: `sparkmon_tired.png`, `firemon_tired.png`,
`flamemon_tired.png`, `dragfiremon_tired.png`; 25 celdas de 256x256 cada uno.
Se conservan sin repintar. El builder elimina el fondo por indice de paleta,
usa viewport fijo y alinea los pies. Tired reproduce 25 frames a 90 ms.
LittleFS recorta solo padding transparente despues de cuantizar; el anclaje
inferior centrado mantiene exactamente colores y posicion sin reescalar.
Las demas animaciones y caches de Training no cambian.

Arte nocturno aprobado: `assets/backgrounds/concepts/night-v1.png`, generado
desde el escenario diurno y aprobado por el usuario antes de integrarlo.
La escena estatica se reconstruye solo al cambiar dia/noche o invalidarse;
no se agrega otro framebuffer. [Plan y evidencia](superpowers/plans/2026-10-18-sleep-routine.md).

La validacion host, la carga USB y la aceptacion fisica son comprobaciones
distintas. Fotos/uso de una noche real siguen siendo necesarios para aceptar
fluidez, reloj y descanso continuo en hardware.
