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
