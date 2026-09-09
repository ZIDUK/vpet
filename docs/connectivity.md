# Conectividad

## Matriz actual

| Funcion | Estado | Confirmacion visible |
|---|---|---|
| Escaneo WiFi | Implementado | Lista de redes o `SCANNING...` |
| Entrada de contrasena | Implementado | Campo enmascarado y teclado de dos botones |
| Asociacion WiFi | Implementado | Estado en la fila WiFi |
| Acceso a Internet | Implementado | `WIFI: ONLINE` |
| Reconexion al arrancar | Implementado | Usa credenciales NVS guardadas |
| Sincronizacion NTP | Implementado | Se inicia al confirmar Internet |
| Bluetooth Classic | No implementado | Ninguno |
| Bluetooth LE | No implementado | Ninguno |
| Descarga remota de paquetes | Disenado, no implementado | Ninguno |

## Conectar la placa a Internet

1. Pulsa brevemente el boton izquierdo hasta seleccionar el engrane.
2. Pulsa el boton derecho para abrir Opciones.
3. Con el izquierdo, selecciona `WIFI`.
4. Pulsa el derecho y espera a que termine `SCANNING...`.
5. Selecciona el SSID con el izquierdo y confirma con el derecho.
6. En `WIFI PASSWORD`, recorre caracteres con el izquierdo y agregalos con el
   derecho.
7. Selecciona `MODE` para cambiar entre `UPPER`, `LOWER`, `NUM` y `SYM`.
8. Usa `DEL` para borrar, `CANCEL` para cancelar o `CONNECT` para conectar.
9. Regresa a Opciones y revisa la fila WiFi.

Una pulsacion larga del boton izquierdo regresa a la pantalla anterior.

## Estados WiFi

| Texto | Significado |
|---|---|
| `WIFI: OFF` | No hay intento ni credenciales activas |
| `WIFI: CONNECTING` | Asociacion en progreso |
| `WIFI: FAILED` | No se asocio antes del timeout |
| `WIFI: NO INTERNET` | Tiene red local, pero fallo la prueba externa |
| `WIFI: ONLINE` | Asociacion, DNS y HTTP confirmados |

El estado `ONLINE` es el indicador actual. Todavia no existe un glifo WiFi
permanente sobre el escenario, para no cubrir la mascota ni los ocho iconos.

## Implementacion

`Esp32NetworkAdapter` usa modo station:

1. `WiFi.scanNetworks()` busca puntos de acceso.
2. `WiFi.begin()` inicia la asociacion.
3. `WiFi.hostByName()` confirma DNS.
4. Una solicitud a `connectivitycheck.gstatic.com/generate_204` confirma salida.
5. `configTzTime()` configura la zona `America/Bogota` mediante NTP.

La prueba de conectividad usa HTTP solo para detectar salida. Cualquier dato,
cuenta, firmware o paquete futuro debe descargarse por HTTPS con verificacion de
certificado.

## Credenciales

El namespace NVS `vpet_wifi` guarda `ssid` y `password` solo despues de obtener
`InternetAvailable`. El password se muestra enmascarado, pero queda accesible al
firmware en texto recuperable. Flash Encryption puede protegerlo en dispositivos
de produccion.

Nunca guardes credenciales en:

- `platformio.ini`;
- `settings.toml`;
- archivos bajo `assets/`;
- pruebas o capturas;
- GitHub Actions sin secrets protegidos.

## Bluetooth

La placa soporta Bluetooth, pero vPet no incluye actualmente stack, servicio
GATT, advertising, emparejamiento ni opcion de activacion. Un telefono no puede
conectarse todavia al vPet por Bluetooth.

La implementacion recomendada es BLE con estas responsabilidades:

- anunciar identidad y version del dispositivo;
- aprovisionar WiFi desde un telefono;
- informar bateria, firmware y conectividad;
- solicitar una descarga por WiFi;
- indicar `OFF`, `ADVERTISING`, `CONNECTED` o `ERROR` en Opciones.

BLE no debe transportar paquetes graficos grandes. WiFi o USB son los canales
de instalacion.

Antes de activar BLE hay que medir heap con pantalla y WiFi activos. La placa no
tiene PSRAM y mantiene dos buffers RGB565 completos.

## Diagnostico

Si no aparece la red:

- confirma que sea una red 2.4 GHz;
- repite el escaneo cerca del punto de acceso;
- evita caracteres no incluidos por el editor actual;
- verifica la contrasena y el modo de seguridad del router;
- reinicia la placa para probar la reconexion NVS.

El siguiente incremento de diagnostico debe agregar telemetria serial
`VPET_NET status=<estado> ssid=<red>` sin imprimir contrasenas.
