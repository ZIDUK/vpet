# Carga De Motivos De Bloqueo De Coleccion

## Alcance Y Consentimiento

El usuario reporta "Not Available" y aclara que su vPet estaba en Home.
No se infiere sueno, pausa o viaje solo por estar en Home. Autoriza cargar
los mensajes especificos ES/EN de `dabc2e7`, solo firmware, sin activar
Coleccion ni crear huevos por el. La restriccion existente no se elimina.
Status, assets, schema, reglas de evolucion y breeding permanecen iguales.

## Verificacion Previa

24 pruebas focalizadas repetidas: aprobadas en 22.16 s, con las 24
advertencias existentes de Pillow. Incluyen ocho motivos del controlador
real, ambos idiomas, limites de textos y rechazo sin escrituras ni nuevas
identidades. Native previamente verificado para la misma revision:
185 aprobadas en 0.674 s. Build preflash nuevo: 3.435 s, RAM estatica
52236/327680, app 1103785/4194304. No se acredita una nueva suite Python
completa para esta revision; las 2038 anteriores corresponden a la entrega
de correccion de pila.

## Respaldo Y Carga

Placa ESP32 revision 3.1, 16 MiB, ID `08f9e0d00788`.
Respaldo critico nuevo y de la imagen de firmware instalada (1109328 bytes)
en `out/board-backups/20261026-collection-blocker-messages/`. La imagen
anterior coincide con `7bc1cfea295c2bd7b2ab09a13bfd7c47f9cbaf9e02f6665cb8b3c1258aa61da1`.
Es respaldo de la imagen, no de toda la particion app ni otro dump de 16 MiB.
LittleFS coincide antes de cargar con la copia completa extraida del respaldo
de 16 MiB conservado del 2026-10-25. Respaldos antiguos intactos.

Carga firmware-only completada, sin uploadfs ni erase_flash. SHA-256 nuevo:
`b9c75006b52e6ac078edd4dbf462a0796826635374b81c4dd11ecd7274b098f5`.
Arranque `VPET_READY`: heap libre 90888/minimo 88220; filesystem
11804672/12451840, manifest 1. Telemetria no acredita radio ni aceptacion
visual de mensajes. Evidencia local en `out/collection-blocker-message-verification/`.
Verificacion posterior por digest: firmware en 0x10000 coincide con el binario
nuevo; LittleFS en 0x410000 coincide con la copia completa conservada.
Observacion de 70.207 s: seis muestras runtime, heap libre estable 90888,
minimo 85748, sin reinicios adicionales ni fatal. BLE=0 y cero eventos de
entrada; no acredita radio, navegacion ni aceptacion del mensaje. Arranque
tras la verificacion separado de la prueba manual pendiente.

## Pendiente Fisico

Repetir Enable desde el dispositivo y leer el motivo exacto o confirmar que
la activacion termina. No se sustituye esta prueba por un arranque correcto,
ni se deduce que el aviso previo fuera causado por sueno. Ninguna activacion,
fundador, cruce o cambio de mascota ejecutado por el agente.

## Evidencia Posterior Del Usuario

Fotos IMG_4257/4258/4259 muestran cuadricula 2/4 con Firemon M y Flamemon F,
ficha de Flamemon activo y Home con Flamemon. Confirman acceso real a la
coleccion/ficha y cambio visible de activo, no breeding ni incubacion.
El aviso anterior desaparecio segun el usuario; su condicion exacta no se
identifico en ese instante y no se atribuye retrospectivamente a una pausa.

Home inmovil posterior: el usuario confirma "Pause Pet ON". Ese estado
congela tambien fotogramas, por diseno. Se solicita poner OFF y comprobar
la animacion; no hay cambio de firmware, reset solicitado ni escritura de
partida por el agente. Observacion de 70.083 s con 17 entradas, heap libre
82948/minimo 73372 y sin reinicios adicionales/fatal. La reanudacion visual
permanece pendiente hasta confirmacion del usuario.

## Reporte De OFF Sin Reanudacion

El usuario indica que poner Pause Pet OFF no reanuda los fotogramas. El
diagnostico inicial de pausa no basta para cerrar el fallo. No se aplica una
despausa automatica ni se cambia firmware, reglas o partida.

Respaldo nuevo `out/board-backups/20261026-home-resume-diagnostic/`:
particiones/NVS y LittleFS completo de 12451840 bytes, sin escrituras flash.
La conexion de lectura por bootloader implica reinicio tecnico al terminar.
MD5 LittleFS `d9fa8df5a5e2389f199fc59d05381e7d`; SHA-256
`b02665574709164d62fe31bd16638dfdf8ab3c95f3a161be726bb4803c9656fd`.
Ya contiene Coleccion y no coincide con el respaldo anterior de solo assets.
No se debe restaurar ese filesystem anterior para comprobar este fallo.

El mklittlefs antiguo extrae assets pero omite la carpeta runtime Coleccion;
no se utiliza su listado para concluir que falta la partida. Lector temporal
littlefs-python 0.19.0, montaje explicito sin autoformato, contexto de solo
lectura sobre copia en memoria y carga mediante CollectionStore real:
`current.bin` secuencia 7 tiene Flamemon activo pausado; `previous.bin`
secuencia 6 tiene pausa OFF. Ambas mascotas tienen energia 0. No hay sueno,
viaje ni accion pendiente. No se publican identidades ni datos completos.

Los dos guardados prueban una transicion OFF seguida de ON, no su causa.
No se atribuye a doble pulsacion ni a un fallo de persistencia sin evidencia.
Se pide foto de la etiqueta actual y respuesta de NEXT. La prueba host usa
el App real para cambiar a una reserva pausada y agotada, comprobar Home
sin fotogramas y reanudar tras OFF. Esta comprobacion sintetica no reproduce
un fallo de reanudacion ni acredita que la placa ya este corregida.

Verificacion de esta ampliacion: 89 pruebas focalizadas aprobadas en
37.31 s, con 150 advertencias existentes de Pillow. Se cubren los siete
consumidores de tests/app_stubs/Renderer.h. No cambia codigo de produccion;
no se compila ni flashea un firmware nuevo. Cambios concurrentes de Hub y
Creator, incluido su adaptador serie en main.cpp, quedan fuera de la entrega.
