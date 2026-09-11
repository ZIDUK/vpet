# Referencia de hardware

## Placa objetivo

El dispositivo principal es la LILYGO TTGO T-Display clasica de 1.14 pulgadas,
no la T-Display S3. La unidad detectada por el proyecto reporta:

| Propiedad | Valor |
|---|---|
| Chip | ESP32-D0WDQ6-V3 revision 3.1 |
| CPU | Xtensa dual core, hasta 240 MHz |
| Flash fisica | 16 MB |
| PSRAM | No disponible |
| Pantalla | ST7789 IPS, 240x135, RGB565 |
| Conexion USB | Puente USB a UART |
| WiFi | 2.4 GHz 802.11 b/g/n; deshabilitado en vPet actual |
| Bluetooth | BLE NimBLE 2.5.1 bajo demanda; Classic no se usa |

vPet activa BLE solo desde Opciones (primera fila) y lo anuncia como
`vPet-XXXX` con perfil HID teclado para Ajustes de iOS. WiFi queda aplazado.

## Pantalla

La configuracion de TFT_eSPI vive en
`firmware/t-display/include/User_Setup.h`.

| Senal | GPIO |
|---|---|
| MOSI | 19 |
| SCLK | 18 |
| CS | 5 |
| DC | 16 |
| RST | 23 |
| Backlight | 4 |

El firmware usa rotacion horizontal y coordenadas logicas 240x135. El backlight
debe estar activo antes de dibujar.

La presentacion usa un framebuffer completo y una escena estatica adicional:

```text
240 * 135 * 2 bytes = 64,800 bytes por buffer
```

Los dos buffers consumen aproximadamente 129,600 bytes. Por eso cualquier
servicio nuevo, especialmente BLE, debe medirse en hardware y conservar margen
de heap.

## Botones

Mirando la placa con la pantalla de frente y el conector USB abajo:

| Boton | GPIO | Funcion |
|---|---|---|
| Izquierdo | 0 | NEXT; mantener 2 segundos para BACK |
| Derecho | 35 | ACTION |

GPIO0 usa pull-up interno. GPIO35 es solo entrada y no dispone de pull-up
interno; la placa proporciona su circuito de boton.

Una pulsacion corta emite su accion al detectarse y un bloqueo de 70 ms evita
rebotes. Mantener GPIO0 inicia con un `NEXT` y, al llegar a 2 segundos, emite
`BACK`. En Home y en Opciones ese `BACK` se ignora. Cada `NEXT` corto
avanza una fila al instante. En los demas paneles `BACK` cierra.

## Particiones

La tabla esta en `firmware/t-display/partitions.csv`:

| Particion | Offset | Tamano | Uso |
|---|---:|---:|---|
| NVS | `0x9000` | `0x5000` | Estado, preferencias y WiFi |
| App factory | `0x10000` | `0x400000` | Firmware |
| LittleFS | `0x410000` | `0xBE0000` | VPA y manifiesto |
| Coredump | `0xFF0000` | `0x10000` | Diagnostico |

El despliegue valida el chip y la flash antes de escribir. No uses una tabla de
4 MB en esta placa porque ocultaria la mayor parte de la capacidad disponible.

## Energia y temperatura

WiFi, pantalla y brillo elevan el consumo. Durante desarrollo:

- usa un cable USB estable;
- evita desconectar durante una escritura de flash;
- no cubras el regulador;
- reduce brillo y apaga Bluetooth cuando no se use;
- mide temperatura y consumo antes de definir un modo always-on.

El proyecto no controla todavia bateria ni carga LiPo.

## Restricciones

- No hay PSRAM: evita decodificar PNG o ZIP completos en RAM.
- LittleFS dispone de unos 12.45 MB, no de los 16 MB completos.
- Los sprites deben convertirse previamente a VPA indexado.
- WiFi y Bluetooth comparten el radio de 2.4 GHz y recursos internos; WiFi no
  se inicia en el firmware actual.
- Bluetooth se activa bajo demanda (HID + DIS + bonding) y debe medirse junto
  con los dos buffers TFT. El `VPET_READY` de arranque no incluye el heap de
  NimBLE; ese valor sale en `VPET_BLE` al anunciar.
- La pantalla no debe limpiarse entre frames; debe presentarse el framebuffer
  completo para evitar parpadeo.

## Deteccion y diagnostico

```bash
make preflight
```

Salida esperada, con valores que pueden variar:

```text
Board: ESP32-D0WDQ6-V3 (revision v3.1) flash=16777216
Budgets: app=.../4194304 littlefs=.../12451840 static_ram=.../327680
```

Despues de desplegar, el firmware imprime `VPET_READY` con heap y uso de
LittleFS. El despliegue falla si esa telemetria no aparece o si el margen es
insuficiente.

## Plataforma Pico legada

La referencia anterior Pico W + Waveshare Pico-LCD-1.44 permanece en el
historial Git y en `docs/legacy/`. No se debe usar su pinout para la T-Display.
