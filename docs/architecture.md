# Arquitectura de software

## Plataforma vigente

La plataforma principal es la LILYGO TTGO T-Display clasica con ESP32,
pantalla ST7789 de 240x135 y 16 MB de flash. El firmware es C++ sobre Arduino,
compilado con PlatformIO y renderizado con TFT_eSPI.

La implementacion Pico W/CircuitPython permanece disponible como compatibilidad
legada. No define la arquitectura principal ni el formato de despliegue actual.

## Flujo de datos

```text
assets/*.png + src/data
          |
          | scripts/build.py --profile tdisplay
          v
build-tdisplay/ (BMP y catalogo intermedio)
          |
          | scripts/build_tdisplay.py
          v
firmware/t-display/data/*.vpa + manifest.json
firmware/t-display/include/generated/catalog.h
          |
          | PlatformIO
          v
firmware.bin + littlefs.bin
          |
          | scripts/deploy_tdisplay.py
          v
ESP32 app partition + LittleFS
```

`make sim` consume el arte generado para T-Display. `make deploy` ejecuta el
mismo build antes de compilar y cargar la placa. Esto mantiene paridad visual
sin hacer de los directorios generados una fuente editable.

## Capas

| Capa | Ruta | Responsabilidad |
|---|---|---|
| Arte fuente | `assets/` | PNG originales del fondo, iconos y sprites |
| Modelo Python | `src/core/` | Reglas usadas por el simulador y pipeline legado |
| Herramientas | `scripts/` | Conversion VPA, simulador, validacion y despliegue |
| Nucleo C++ | `firmware/t-display/lib/vpet_core/` | Estado, movimiento, navegacion, opciones y red abstracta |
| Plataforma ESP32 | `firmware/t-display/src/` | TFT, botones, WiFi, NVS y LittleFS |
| Recursos generados | `firmware/t-display/data/` | Payload LittleFS; no se versiona |
| Catalogo generado | `firmware/t-display/include/generated/` | Registro C++ derivado; no se versiona |

Las reglas portables no incluyen Arduino, TFT_eSPI, WiFi ni Preferences. Esto
permite ejecutar sus pruebas como binarios nativos en macOS.

## Componentes del firmware

| Componente | Funcion |
|---|---|
| `main.cpp` | Inicializa pantalla, buffers, recursos, entradas y servicios |
| `App` | Coordina el loop, acciones, paneles, red y persistencia |
| `Renderer` | Dibuja fondo, menu, selector y animaciones sin parpadeo |
| `Panels` | Dibuja estado, inventario, evolucion, opciones y WiFi |
| `AssetStore` | Monta LittleFS, valida VPA1 y dibuja frames indexados |
| `BoardInput` | Traduce GPIO0/GPIO35 a `Next`, `Action` y `Back` |
| `PetState` | Estadisticas, acciones, descubrimientos y evolucion |
| `Motion` | Idle, caminar/volar y animaciones de una sola ejecucion |
| `Navigation` | Menu superior, paneles y seleccion interna |
| `SettingsStore` | Serializacion versionada de estado y preferencias |
| `NetworkService` | Flujo portable de conexion y politica de credenciales |
| `Esp32NetworkAdapter` | WiFi, DNS, HTTP y NTP sobre Arduino ESP32 |
| `NvsKeyValueStore` | Adaptador de Preferences/NVS |

## Renderizado

La pantalla trabaja en RGB565. Se mantienen dos sprites TFT de 240x135:

1. `staticScene` conserva fondo y menu sin elementos animados.
2. `framebuffer` recibe una copia completa de la escena estatica.
3. El selector y el frame actual de la mascota se dibujan en memoria.
4. `pushSprite()` presenta el frame completo en una sola transaccion SPI.

Este doble buffer evita limpiar directamente la pantalla y elimina el parpadeo
visible. Las animaciones normales usan frames de 88x88. Las evoluciones usan
111x111 y ocupan el area bajo el menu.

Los VPA1 contienen cabecera, paleta RGB565, offsets de frame y un byte indexado
por pixel. El indice transparente permite dibujar solamente los segmentos
opacos sobre el fondo.

## Ciclo de vida actual

```text
Egg --8 s--> Sparkmon --> Firemon --> Flamemon --> Dragfiremon
```

Una partida nueva comienza en `SpeciesId::Egg`. La eclosion cambia y guarda el
estado como `Baby/Sparkmon`; una partida NVS existente conserva su especie. Los
valores persistidos originales `Rookie=0`, `Champion=1` y `Ultimate=2` no se
renumeran. Los requisitos de Sparkmon a Firemon y Flamemon a Dragfiremon siguen
marcados como pendientes. El arbol muestra tres nodos por ventana y desplaza la
linea de izquierda a derecha; las etapas futuras permanecen ocultas.

## Entrada

```text
Boton izquierdo / GPIO0
  corto   -> NEXT
  largo   -> BACK

Boton derecho / GPIO35
  corto   -> ACTION
```

El debounce y la deteccion de pulsacion larga viven en `Input`, dentro del
nucleo portable. La interfaz principal siempre contiene ocho iconos.

## Persistencia

La particion NVS mide `0x5000` bytes y utiliza namespaces separados:

- `vpet_state`: mascota, estadisticas, descubrimientos y preferencias.
- `vpet_wifi`: SSID y contrasena aceptados.

El esquema actual es version 1. Las credenciales se guardan solo cuando la
asociacion WiFi y la prueba de Internet terminan correctamente. Un despliegue
normal no borra NVS.

LittleFS comienza en `0x410000`, mide `0xBE0000` y contiene exclusivamente
recursos reconstruibles. El estado del usuario nunca debe depender de LittleFS.

## Conectividad

La red sigue este estado:

```text
Idle -> Connecting -> InternetAvailable
                   -> LocalOnly
                   -> NoAssociation
```

El adaptador ejecuta escaneo asincrono, asociacion WiFi, resolucion DNS,
peticion HTTP de conectividad y NTP. El panel Opciones muestra el resultado.

Bluetooth no forma parte del firmware actual. La futura integracion sera BLE y
se mantendra detras de una interfaz de plataforma. Su uso recomendado es
aprovisionamiento, estado y comandos pequenos; los paquetes se transferiran por
WiFi o USB.

## Paquetes extensibles

La direccion aprobada es contenido declarativo y sin codigo ejecutable. Un
paquete externo tendra manifiesto versionado, hashes, compatibilidad, previews y
archivos VPA. El dispositivo validara identidad, tamano y firma antes de activar
un paquete. Consulta [content-packages.md](content-packages.md).

## Seguridad

El entorno de desarrollo conserva carga serial, logs y capacidad de recuperacion.
Secure Boot, Flash Encryption, bloqueo de interfaces y claves de produccion solo
se habilitaran en dispositivos destinados a usuarios finales. Consulta
[security.md](security.md).

## Contrato de despliegue

`make deploy`:

1. Regenera recursos.
2. Ejecuta pruebas Python y C++.
3. Compila firmware y LittleFS.
4. Detecta chip, revision y flash.
5. Valida presupuesto de app, LittleFS, RAM estatica y heap.
6. Crea backup antes de la primera escritura administrada.
7. Carga sin borrar toda la flash ni NVS.
8. Reinicia y exige telemetria `VPET_READY` valida.

La placa no se considera desplegada solo porque `esptool` termino sin error.
