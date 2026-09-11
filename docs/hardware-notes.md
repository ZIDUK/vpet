# Notas practicas de T-Display

Este archivo contiene diagnosticos rapidos. La referencia estable esta en
[hardware.md](hardware.md).

## Pantalla con ruido o colores corruptos

1. Verifica que el target sea la T-Display clasica y no S3.
2. Comprueba `User_Setup.h`, rotacion y orden RGB565.
3. Usa carga a 115200 si el puente USB es inestable.
4. Ejecuta un build limpio del firmware y LittleFS.

## Parpadeo

No llames `fillScreen()` sobre el TFT para cada frame. El flujo correcto es
copiar `staticScene` al framebuffer, dibujar cambios y presentar una sola vez
con `pushSprite()` dentro de una transaccion SPI.

## Mascota invisible o deformada

- Confirma que el VPA empacado conserve offsets por frame.
- Verifica que transparencia sea el indice 0.
- Comprueba el frame con las pruebas de round-trip.
- No redimensiones los VPA despues de generarlos.

## Botones

```text
Izquierdo GPIO0  = NEXT / mantener para BACK
Derecho   GPIO35 = ACTION
```

GPIO35 no tiene pull-up interno. No intercambies los nombres por la posicion
que muestra una fotografia rotada.

## Bluetooth

Abre el engrane: la primera fila es `BLUETOOTH`. `ACTION` debe pasar a
`ADVERTISING`. En iPhone, Ajustes > Bluetooth, Otros dispositivos, toca
`vPet-XXXX` (en esta placa, `vPet-F908`). Tambien aparece en nRF Connect o
LightBlue. Tras conectar, la fila dice `CONNECTED`; al desconectar, vuelve a
anunciarse. No escribe teclas.

Si no sale en Ajustes, cierra LightBlue, olvida el accesorio y reinicia el
Bluetooth del telefono.

WiFi esta deshabilitado y no aparece en el menu actual.

## Recuperacion

Ejecuta primero:

```bash
make preflight
make deploy PORT=/dev/cu.usbserial-57040013171 UPLOAD_SPEED=115200
```

No uses `erase_flash` para resolver problemas visuales o de aplicacion. Un
borrado completo elimina estado, credenciales y cualquier contenido instalado.
