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
- Estado, mochila, guia visual de evolucion y opciones persistentes.
- Fondo nocturno durante el descanso.
- WiFi con escaneo, teclado de contrasena, reconexion, verificacion de Internet
  y sincronizacion NTP.
- Estado WiFi visible en Opciones: `OFF`, `CONNECTING`, `FAILED`,
  `NO INTERNET` u `ONLINE`.
- Guardado de mascota, descubrimientos, idioma, sonido y WiFi en NVS.
- Bluetooth pendiente; el firmware actual no anuncia ningun servicio BLE.
- Criterios de Sparkmon a Firemon y de Flamemon a Dragfiremon pendientes.

## Hardware principal

| Componente | Configuracion |
|---|---|
| Placa | LILYGO TTGO T-Display clasica |
| MCU | ESP32-D0WDQ6-V3, sin PSRAM |
| Flash | 16 MB |
| Pantalla | ST7789, 1.14 pulgadas, 240x135 |
| Boton izquierdo | GPIO0, `NEXT`; mantener para `BACK` |
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
- Pulsacion larga del boton izquierdo: regresar.
- Pulsacion corta del boton derecho: seleccionar o ejecutar.

En el simulador:

- `n`: siguiente.
- `a`: seleccionar o ejecutar.
- `b`: regresar.
- `e`: forzar una evolucion para desarrollo.
- `r`: reiniciar el estado simulado.
- `q` o `Esc`: salir.

## Conectar a Internet

1. Con `NEXT`, mueve el borde amarillo hasta el engrane.
2. Pulsa `ACTION` para abrir Opciones.
3. Selecciona `WIFI` y pulsa `ACTION`.
4. Selecciona una red encontrada y pulsa `ACTION`.
5. En el editor, `NEXT` recorre letras y comandos; `ACTION` agrega el caracter.
6. Usa `MODE` para mayusculas, minusculas, numeros y simbolos.
7. Selecciona `CONNECT` y pulsa `ACTION`.
8. Regresa a Opciones y comprueba `WIFI: ONLINE`.

`WIFI: NO INTERNET` significa que existe asociacion local pero fallo la prueba
externa. `WIFI: FAILED` indica que no fue posible asociarse al punto de acceso.
Las credenciales solo se guardan despues de confirmar acceso a Internet.

Consulta [connectivity.md](docs/connectivity.md) para diagnostico y seguridad de
red. Bluetooth todavia no esta disponible en la interfaz.

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
