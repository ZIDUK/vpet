# vPet

Mascota virtual para la LILYGO TTGO T-Display clasica (ESP32, pantalla ST7789
de 240x135). El firmware usa PlatformIO, Arduino y TFT_eSPI. El simulador de
escritorio comparte las reglas, perfiles visuales y recursos generados con el
dispositivo.

La implementacion anterior para Raspberry Pi Pico W se conserva como plataforma
secundaria mediante los comandos terminados en `-pico`.

## Estado actual

- Huevo animado que eclosiona en Sparkmon despues de 8 segundos en una partida nueva.
- Linea visual: Huevo -> Sparkmon -> Firemon -> Flamemon -> Dragfiremon.
- Firemon, Flamemon y Dragfiremon con idle, movimiento, comida, entrenamiento,
  descanso, ataque y transiciones de evolucion. Sparkmon incluye idle, caminar,
  comer y dormir; entrenamiento y batalla se habilitan desde Firemon.
- Menu superior de ocho iconos y navegacion completa con dos botones.
- Estado en dos paginas: barras HP/HAM/ENE; NEXT muestra edad, esfuerzo,
  batallas, animo y reloj.
- Mochila gastable: Carne, Energia, EXP y Anillo. ACTION consume y se queda
  en el menu; ATRAS cierra. El stock se guarda en NVS.
- Guia visual de evolucion y opciones persistentes (BLE, idioma, sonido,
  save/load, fecha/hora, EVOLVE).
- El foco alterna descanso persistente: fondo nocturno y sprite acostado
  (loop 12-14) hasta volver a pulsar el mismo icono.
- Bluetooth LE bajo demanda, visible como `vPet-XXXX` en Ajustes del iPhone
  (teclado HID) y en LightBlue o nRF Connect.
- Estado Bluetooth visible en Opciones: `OFF`, `ADVERTISING`, `CONNECTED` o
  `ERROR`. La primera fila de Opciones es Bluetooth.
- Guardado de especie, estadisticas, inventario, idioma, sonido y Bluetooth
  en NVS. Los descubrimientos, comidas, entrenos y batallas no se persisten.
- WiFi queda deshabilitado y fuera de la interfaz hasta el siguiente feature.
- Criterios de Sparkmon a Firemon y de Flamemon a Dragfiremon pendientes.

## Hardware principal

| Componente | Configuracion |
|---|---|
| Placa | LILYGO TTGO T-Display clasica |
| MCU | ESP32-D0WDQ6-V3, sin PSRAM |
| Flash | 16 MB |
| Pantalla | ST7789, 1.14 pulgadas, 240x135 |
| Boton izquierdo | GPIO0, `NEXT`; mantener 2 segundos para `BACK` |
| Boton derecho | GPIO35, `ACTION` |
| Framework | Arduino ESP32 2.0.17 |
| Build | PlatformIO, `platformio/espressif32@7.0.1` |
| Graficos | TFT_eSPI 2.5.43, RGB565, framebuffer completo |
| Recursos | LittleFS, formato VPA indexado |
| Estado | Preferences/NVS |

Consulta [hardware.md](docs/hardware.md) para pines y limites.

## Preparacion

```bash
python3 -m pip install -r requirements-dev.txt
make bootstrap-pio
```

## Comandos

| Comando | Resultado |
|---|---|
| `make sim` | Genera recursos T-Display y abre el simulador 240x135 |
| `make test` | Ejecuta las pruebas Python |
| `make native-test` | Prueba la logica C++ portable |
| `make firmware` | Compila el firmware ESP32 y LittleFS |
| `make preflight` | Detecta la placa y valida capacidad sin escribirla |
| `make deploy` | Pruebas, build, backup, carga y diagnostico serial |
| `make sim-pico` | Abre el simulador legado 128x128 |
| `make deploy-pico` | Despliega la version CircuitPython conservada |

Para indicar un puerto manualmente:

```bash
make deploy PORT=/dev/cu.usbserial-57040013171
```

No se ejecuta `erase_flash` durante un despliegue normal. NVS y los datos de la
mascota se conservan.

## Controles

En la placa:

- Pulsacion corta del boton izquierdo: siguiente.
- Mantener el boton izquierdo durante 2 segundos: regresar.
- Pulsacion corta del boton derecho: seleccionar o ejecutar.

En Opciones, cada `NEXT` corto baja una fila al instante y envuelve.
La letra es grande (4 filas visibles). Hay una fila `EVOLVE` que fuerza
la siguiente forma y muestra la animacion. Para salir, baja hasta `BACK`
y pulsa `ACTION`. El hold de 2 s no cierra Opciones. Fuera de Opciones,
ese `BACK` cierra el panel (en Home se ignora).

En el simulador:

- `n`: siguiente.
- `a`: seleccionar o ejecutar.
- `b`: regresar.
- `e`: forzar una evolucion para desarrollo.
- `r`: reiniciar el estado simulado.
- `q` o `Esc`: salir.

## Conectar por Bluetooth

1. Con `NEXT`, mueve el borde amarillo hasta el engrane.
2. Pulsa `ACTION` para abrir Opciones. La primera fila es `BLUETOOTH`.
3. Pulsa `ACTION` otra vez. La fila cambia a `BLUETOOTH: ADVERTISING`.
4. En el iPhone, Ajustes > Bluetooth. `vPet-XXXX` aparece en Otros
   dispositivos; pulsalo para emparejar. Tambien vale nRF Connect o LightBlue.
5. Al conectarse, la fila muestra `BLUETOOTH: CONNECTED`.

Pulsa `ACTION` de nuevo para apagarlo. iOS pide emparejamiento Just Works (sin
PIN) porque el anuncio es un teclado HID; vPet no envia teclas ni archivos.
WiFi esta aplazado y no puede configurarse desde el dispositivo.

Consulta [connectivity.md](docs/connectivity.md) para diagnostico y el contrato
BLE.

## Estructura del repositorio

```text
assets/                         PNG fuente requeridos por el build
src/                            modelo y simulador Python compartido
scripts/                        generacion, simulacion y despliegue
firmware/t-display/             firmware nativo ESP32
  include/vpet/                 interfaces de plataforma y UI
  lib/vpet_core/src/vpet/       logica C++ portable
  src/                          adaptadores ESP32 y render TFT
  test/test_native/             pruebas C++ en macOS
tests/                          pruebas Python y del pipeline
docs/                           arquitectura, hardware y operacion
build/                          salida Pico generada/legada
build-tdisplay/                 salida T-Display generada, ignorada
out/                            capturas, backups y archivos temporales
```

Los PNG usados para generar el firmware forman parte del repositorio. Las
salidas `build-tdisplay/`, `.pio/`, backups y credenciales del dispositivo no se
versionan.

## Agregar contenido

El formato interno actual es VPA1. La arquitectura propuesta para paquetes de
la comunidad se describe en [content-packages.md](docs/content-packages.md).
Hasta implementar el instalador, agrega los PNG bajo `assets/`, registra el
contenido en `scripts/build.py`, ejecuta las pruebas y despliega normalmente.

## Documentacion

- [Arquitectura](docs/architecture.md)
- [Flujo de desarrollo y despliegue](docs/development-workflow.md)
- [Hardware](docs/hardware.md)
- [Conectividad](docs/connectivity.md)
- [Paquetes y catalogo comunitario](docs/content-packages.md)
- [Seguridad y proteccion del firmware](docs/security.md)
