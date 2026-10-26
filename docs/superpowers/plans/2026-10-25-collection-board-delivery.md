# Entrega De Coleccion, Aprendizaje Y Breeding

Fecha: 2026-10-25. El usuario solicito commit, push y flasheo. Se conserva
la aceptacion de las cuatro paginas Status registrada en F1/F2; esta revision
no cambia su diseno. Creator concurrente y partidas/respaldos/logs quedan fuera
de la publicacion. No se activa WiFi ni se migra la coleccion del usuario.

## Publicacion Y Verificacion

- `df96305`: implementacion de cuatro plazas, mochila compartida, aprendizaje
  por individuo y cruce local; publicado en `https://github.com/ZIDUK/vpet.git`,
  rama `master`, junto al contrato previo `c861e01`.
- Arbol aislado desde el indice, sin Creator: 1984 Python aprobadas en 295.89 s.
  El primer intento aislado carecia del catalogo generado y dio 163 errores de
  preparacion; `make build-tdisplay` completo los recursos y la repeticion paso.
- Correccion de cache: 15 pruebas focalizadas aprobadas, incluida igualdad de
  pixeles y cache sin E/S repetida; prueba RED por API de liberacion ausente.
- Native posterior: 185 aprobadas en 0.544 s. ESP32 compilado en 8.739 s:
  RAM estatica 52228/327680, app 1098849/4194304. TOUCH_CS preexistente.
- Suite final repetida tras corregir la cache, desde arbol aislado sin Creator:
  1984 aprobadas, 13239 advertencias preexistentes, 295.99 s. Diff sin errores
  de whitespace. No se presenta la suite concurrente de Creator como entregada.

## Respaldo Y Carga

Respaldo completo de 16777216 bytes con SHA-256 comprobado, conservado en
`out/board-backups/collection-release-20261025-191125/`:

`e88fc757ce4363b6fe50d1b49c86a8715b5457e2a68b7cd4c7e8e9e6f0f0134d`.

Un intento a 460800 fallo por ruido serial antes de producir respaldo.
Lecturas criticas a 115200/230400 correctas; el respaldo completo a 230400
termino antes de cualquier escritura. Respaldos criticos nuevos antes de
cada carga. No se ejecuta erase_flash ni uploadfs.

La primera carga (`15979af8...`) arranco y conecto BLE, pero el control
`HEAP_STARTUP_LOW` rechazo 63892 bytes libres frente al minimo de 65536.
No se considero entrega valida ni se redujo el umbral. Se identificaron
5840 bytes de iconos Training residentes incluso fuera de esa actividad.
Ahora se reservan con `nothrow` bajo demanda, se reutilizan mientras entrenan
y se liberan con la invalidacion del panel. Si falla la reserva, se dibuja
desde archivo. Se conservan diez iconos, RGB565 y el scratch de lecturas.

Carga final: solo firmware, velocidad 115200, ESP32 de 16 MiB verificado.
SHA-256 de `firmware.bin`:

`5585fb9219b4213ef4fa5b857c38a3074e0863b4a938261236c4f2476d264b3d`.

SHA-256 de `firmware.elf`:

`ada59837a5ef22180b74554805f118353f6fe07bd3e74e342d34c6fae3d73c2c`.

`verify_flash` confirma el digest del binario en `0x10000` y de los
12451840 bytes de LittleFS en `0x410000` contra el respaldo previo: filesystem
identico. NVS no se reemplaza ni restaura; la partida puede seguir guardando
su progreso normalmente. No se publican los binarios de respaldo.

## Arranque Y Pendientes

`VPET_READY`: heap libre 69712, minimo 69636, flash 16777216, filesystem
11804672/12451840, manifest 1. BLE anuncia, reconoce el emparejamiento existente
y conecta como `vPet-F908`. Esto no prueba juego entre boards ni reconexion larga.

Observacion serial posterior, 70.145 segundos sin comandos ni reset solicitado:
seis muestras, heap libre estable 69712, minimo observado 64572, BLE conectado,
cero reinicios y cero fatal. Maximo de loop 574509 us, sin entradas de usuario:
no acredita FPS, latencia de NEXT ni rendimiento en Training/coleccion.

Quedan aceptacion visual de Coleccion/Training y conservacion de mascota/progreso,
migracion y reinicio supervisados, cruce/incubacion real, picos heap/pila con
politicas cargadas, cortes fisicos y sesiones largas. Las pruebas host no
certifican esos flujos en placa. No se conceden huevos ni objetos para validarlos.
