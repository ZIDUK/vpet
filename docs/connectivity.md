# Conectividad

## Estado actual

| Funcion | Estado | Confirmacion visible |
|---|---|---|
| Bluetooth LE | Implementado bajo demanda | `BLUETOOTH: ADVERTISING` o `CONNECTED` |
| HID teclado | Anunciado; no envia teclas | iOS Ajustes > Bluetooth |
| Device Information | Solo lectura | Modelo, firmware y serial |
| Bateria GATT | Fija al 100% | Caracteristica `0x2A19` |
| Emparejamiento | Just Works, sin PIN | Serial `VPET_BLE status=PAIRED` |
| WiFi | Aplazado y deshabilitado | No aparece en Opciones |
| Descarga remota de paquetes | Disenado, no implementado | Ninguno |

## Activar Bluetooth

1. Pulsa `NEXT` hasta el engrane y abrelo con `ACTION`.
2. La primera fila ya es `BLUETOOTH`. Pulsa `ACTION` para encenderlo.
3. Con `ADVERTISING`, en el iPhone abre Ajustes > Bluetooth.
   `vPet-XXXX` debe aparecer en Otros dispositivos. Pulsalo para emparejar.
   iOS lo trata como teclado BLE y no escribe teclas.
4. Tambien puedes abrirlo en nRF Connect o LightBlue.
5. Al conectar, la fila de Opciones cambia a `CONNECTED`.
6. Cada `NEXT` corto baja una fila al instante. Baja hasta `BACK` y pulsa
   `ACTION` para salir. La fila `EVOLVE` fuerza la siguiente forma en la placa.

El sufijo `XXXX` es `ESP.getEfuseMac() & 0xFFFF` en hexadecimal. En la placa
de desarrollo actual el nombre es `vPet-F908`. La preferencia se guarda en
NVS (`bluetooth`, apagada por defecto) y se restaura al reiniciar. Para
apagar Bluetooth, selecciona la misma fila y pulsa `ACTION` otra vez.

Si un cliente ya estaba unido (por ejemplo LightBlue), cierralo o olvida el
accesorio en Ajustes antes de volver a emparejar.

## Contrato BLE

Stack: `h2zero/NimBLE-Arduino@2.5.1`. No se usa Bluetooth Classic. El radio
solo vive mientras la opcion esta activa; `setEnabled(false)` hace
`NimBLEDevice::deinit(true)`.

| Pieza | UUID / valor | Notas |
|---|---|---|
| Nombre ADV | `vPet-XXXX` | Tambien en scan response |
| Appearance | `0x03C1` (HID keyboard) | Necesario para Ajustes de iOS |
| HID | `0x1812` | Mapa de teclado; cero informes enviados |
| Battery | `0x180F` / `0x2A19` | Nivel fijo 100 |
| DIS modelo | `0x180A` / `0x2A24` | `vPet T-Display` |
| DIS firmware | `0x2A26` | `0.1.0` |
| DIS serial | `0x2A25` | Igual al nombre ADV |
| DIS fabricante | `0x2A29` | `vPet` |

La seguridad es bonding Just Works (`bonding=true`, `MITM=false`,
Secure Connections=`true`, IO cap `NO_IO`). Al conectar, el firmware llama
`startSecurity`. El serial imprime `PAIRED` o `PAIR_FAILED`.

`BleAdvertiseSession` evita volver a meter nombre y UUID en el payload ADV
tras cada disconnect. NimBLE 2.x no anuncia nombre ni scan response por
defecto; ambos se configuran una vez al activar.

Esto permite ver la placa en Ajustes o en un scanner sin app propia. No hay
aprovisionamiento, comandos remotos ni transferencia de sprites por BLE.

## Opciones

Orden en firmware y simulador T-Display:

1. Bluetooth (indice 0)
2. Language
3. Sound
4. Save
5. Load
6. Date
7. Time
8. Evolve
9. Back

El panel muestra cuatro filas a la vez. Language y Sound se guardan en NVS
y el firmware pinta `IDIOMA`/`LANGUAGE` y `SONIDO`/`SOUND` segun el idioma.

## Estados

| Texto | Significado |
|---|---|
| `BLUETOOTH: OFF` | Stack BLE detenido y radio no anunciado por vPet |
| `BLUETOOTH: ADVERTISING` | Visible y listo para una conexion o emparejamiento |
| `BLUETOOTH: CONNECTED` | Un cliente BLE esta conectado |
| `BLUETOOTH: ERROR` | No se pudo iniciar el stack; revisar serial |

Al desconectarse el telefono, vPet vuelve a `ADVERTISING`.

## WiFi futuro

WiFi se retiro de la interfaz. Las credenciales previas en `vpet_wifi` no se
leen ni se usan. La proxima fase podra aprovisionar WiFi desde una app y usar
HTTPS para catalogo y descargas. BLE no transportara paquetes graficos.

## Diagnostico

Si `vPet-XXXX` no aparece en Ajustes:

- confirma `BLUETOOTH: ADVERTISING` en la placa;
- espera en Otros dispositivos, no en Mis dispositivos, si nunca se emparejo;
- apaga y enciende Bluetooth del telefono;
- olvida un emparejamiento previo o cierra LightBlue;
- detén e inicia de nuevo el escaneo en nRF Connect o LightBlue;
- revisa serial: `VPET_BLE status=ADVERTISING name=...` y luego `PAIRED`;
- mantén la pantalla y el telefono cerca.

Heap de arranque (antes de activar BLE) se imprime en `VPET_READY`. Al
anunciar, `VPET_BLE` incluye `heap_free` y `heap_min`.

No publiques secretos ni credenciales en el nombre BLE, serial, logs o
capturas.
