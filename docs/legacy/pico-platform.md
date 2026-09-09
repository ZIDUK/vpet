# Plataforma Pico W legada

La primera version de vPet utilizaba Raspberry Pi Pico W, CircuitPython 10 y
Waveshare Pico-LCD-1.44 con pantalla ST7735S de 128x128.

Se conserva para compatibilidad y comparacion, pero no es la plataforma
principal.

## Comandos

```bash
make sim-pico
make build-pico
make deploy-pico
```

## Hardware resumido

| Funcion | GPIO Pico W |
|---|---|
| LCD clock | GP10 |
| LCD MOSI | GP11 |
| LCD DC | GP8 |
| LCD CS | GP9 |
| LCD reset | GP12 |
| Backlight | GP13 |
| KEY0 | GP15 |
| KEY1 | GP17 |

El despliegue legado usa `/Volumes/CIRCUITPY`, archivos BMP y estado en
`/pet_save.json`. No uses estas rutas, pines o restricciones para la T-Display.

Las funciones nuevas deben implementarse primero en el firmware nativo ESP32.
