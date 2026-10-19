# Descanso y validacion de placa

Cambio aprobado el 2026-10-19: Rest queda limitado a APAGAR LUZ / ENCENDER
LUZ y VOLVER (LIGHTS OFF / LIGHTS ON y BACK). Abrir el menu no cambia el
sueno; hay que elegir la accion. No ofrece Cold ni Backup.

El usuario confirmo fisicamente los nuevos comandos en Rest y Opciones.
Reporto despues que apagar la luz acostaba al pet pero dejaba el escenario
claro: la seleccion dia/noche solo dependia del reloj. El seguimiento separa
el ciclo horario de la luz apagada, sin modificar las reglas de descanso.
El usuario confirmo despues que apagar la luz oscurece y encenderla restaura
el brillo. Queda aceptada fisicamente esa correccion; no equivale a validar
una noche completa ni el ciclo de pausa/reanudacion.

## Pausa y reserva

Cold era el estado interno de pausa, no temperatura ni enfermedad.
Opciones lo presenta ahora como PAUSAR CRIANZA: SI/NO o PAUSE PET: ON/OFF.
Detiene cuidado, edad, lesiones, evolucion y avance del descanso; conserva
el margen de un Call pendiente. Se puede reanudar desde la misma opcion.

Se mantiene la clave NVS `cold` y schema 3. Back conserva el indice 8;
Pause usa 9 y el orden visual lo coloca antes de Back, sin renumerar los
demas comandos. Python agrega `cold` al JSON con default false para
partidas antiguas. Un guardado rechazado revierte el cambio en memoria.

La reserva era una segunda mascota aparcada/intercambiable, no el respaldo
automatico de seguridad. Se retira su accion de Rest, pero no se borra
`vpet_bak`, no se crea otro huevo, no se intercambia la mascota actual y
se conservan lectores, journals y snapshots de recuperacion existentes.
Los respaldos USB de `out/board-backups/` tambien permanecen intactos.

La auditoria encontro una diferencia concreta: C++ seguia avanzando
`sleep.advanceMs` aunque `cold` estuviera activo. Se congela esa rama y
el reloj de Motion, como ya hacia el servicio de descanso Python. Una
regresion sobre App.cpp demuestra el fallo previo y la correccion.

## Observacion real sin comandos

El firmware emite `VPET_RUNTIME` cada diez segundos mientras App esta listo:
uptime, heap libre, minimo de heap, mayor duracion del ciclo de aplicacion
del intervalo y estado BLE (0 apagado, 1 anunciando, 2 conectado, 3 error).
`loop_max_us` mide el ciclo con botones/logica/dibujo, no FPS ni latencia
de un boton. No agrega comandos de control ni escrituras de la partida.

`scripts/observe_tdisplay.py` escucha USB, sin escribir bytes ni solicitar
reset. Configura DTR/RTS desactivados antes de abrir el puerto y lo cierra
al terminar. Resume muestras, memoria, eventos de entrada, estados BLE,
reinicios aparentes y errores fatales. El JSON conserva tambien las lineas
originales. Sin dos muestras de runtime no declara actividad comprobada.

```sh
.venv-platformio/bin/python scripts/observe_tdisplay.py \
  --port /dev/cu.usbserial-57040013171 --seconds 300 \
  > out/rest-board-deploy/observation.json
```

No abrir otro monitor ni flashear mientras este comando usa el puerto.
Una sesion de cinco minutos es una observacion acotada, no una noche ni
una prueba prolongada de Training/Arena. Sin eventos de botones no puede
afirmarse que el usuario ejercito esos menus. Un unico estado BLE conectado
no valida desconectar y reconectar desde el telefono.

Primera observacion, antes de corregir la oscuridad: 300.024 s, 29 muestras,
7 eventos de entrada, heap libre 66060..66132 bytes, minimo historico 43876,
BLE conectado y sin fatal ni regresion de uptime entre muestras. El mayor
ciclo fue 927148 us; hubo uno de 800189 us junto a eventos de entrada.
Despues del segundo 60 los maximos por intervalo rondaron 78..80 ms.
No demuestra ausencia de fugas ni latencia perceptual: conserva los picos
y el minimo de memoria como puntos de seguimiento en sesiones activas.
Evidencia local: `out/rest-board-deploy/observation.json` (no se publica).

## Matriz abierta

El [plan y evidencia](superpowers/plans/2026-10-19-rest-and-board-validation.md)
separa implementacion, pruebas host, USB y aceptacion fisica. Permanecen
abiertos los globos antes/despues de resolver necesidades, una noche real,
equipo 3/4 y evolucion ganada, viajes/consumo tras reiniciar y sesiones
activas prolongadas con reconexion BLE. No se modifican necesidades,
lesiones, especie ni calendario del pet del usuario para fingir esos casos.

Antes de cualquier ensayo con apagados controlados, guardar una copia
actual y registrar especie, stock, equipo, recompensas y rutina. Cualquier
prueba acelerada o partida separada debe identificarse como tal; no cuenta
como una noche real ni como una accion observada en la mascota del usuario.
