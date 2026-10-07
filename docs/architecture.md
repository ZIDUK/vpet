# Arquitectura de software

## Plataforma vigente

La plataforma principal es la LILYGO TTGO T-Display clasica con ESP32,
pantalla ST7789 de 240x135 y 16 MB de flash. El firmware es C++ sobre Arduino,
compilado con PlatformIO y renderizado con TFT_eSPI.

La implementacion Pico W/CircuitPython permanece disponible como compatibilidad
legada. No define la arquitectura principal ni el formato de despliegue actual.

## Flujo de datos

Revision documental: 2026-10-06. El arbol contiene cambios locales posteriores
al commit `3b98843`; el estado exacto se audita con `git status`.
Consulta [estado y diferencias conocidas](project-status.md) y la
[arquitectura Archify](../.archify/architecture-vpet-20261005/review-2/vpet-architecture.html).
El usuario confirma descubrimiento BLE desde su telefono, ausencia de WiFi en
el menu y mejora de fluidez. No se realizo un despliegue durante esta revision.

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
| Nucleo C++ | `firmware/t-display/lib/vpet_core/` | Estado, movimiento, navegacion y politica BLE portable |
| Plataforma ESP32 | `firmware/t-display/src/` | TFT, botones, BLE, NVS y LittleFS |
| Recursos generados | `firmware/t-display/data/` | Payload LittleFS; no se versiona |
| Catalogo generado | `firmware/t-display/include/generated/` | Registro C++ derivado; no se versiona |

Las reglas portables no incluyen Arduino, TFT_eSPI, WiFi ni Preferences. Esto
permite ejecutar sus pruebas como binarios nativos en macOS.

## Componentes del firmware

| Componente | Funcion |
|---|---|
| `main.cpp` | Inicializa pantalla, buffers, recursos, entradas y servicios |
| `App` | Coordina el loop, acciones, paneles, Bluetooth y persistencia |
| `Renderer` | Dibuja fondo, menu, selector y animaciones sin parpadeo |
| `Panels` | Dibuja estado, inventario, evolucion, opciones y fecha/hora |
| `AssetStore` | Monta LittleFS, valida VPA1 y dibuja frames indexados |
| `BoardInput` | Traduce GPIO0/GPIO35 a `Next`, `Action` y `Back` |
| `PetState` | Estadisticas, inventario gastable, acciones, descubrimientos y evolucion |
| `Motion` | Idle, caminar/volar, acciones y sueno en bucle acostado (frames 12-14) |
| `Navigation` | Menu superior, paneles, paginas de Status e inventario |
| `DateTimeMenu` | Filas +/- de fecha u hora; SAVE escribe el reloj ESP32 |
| `Strings.h` | Copy EN/ES de paneles |
| `SettingsStore` | Serializacion versionada de estado, inventario y preferencias |
| `PracticeBattle` | Motor portable de combate de practica con HP/MP y tecnicas |
| `PracticeSession` | Controlador portable C++ de Tech y batalla, integrado en App |
| `BleAdvertiseSession` | Primera vez configura el ADV; reconnect solo `start()` |
| `BleService` | NimBLE bajo demanda: HID teclado, DIS y bateria |
| `NvsKeyValueStore` | Adaptador de Preferences/NVS |

## Renderizado

La intro dura aproximadamente 2.2 segundos antes de cargar el estado. Las rutas
de arranque de firmware y simulador siguen separadas; la paridad visual completa
de la intro queda como tarea de firmware.

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
Egg --2 s--> Sparkmon --> Firemon --> Flamemon --> Dragfiremon
```

Una partida nueva comienza en `SpeciesId::Egg`. La eclosion (2 s, sin scale)
cambia y guarda el estado como `Baby/Sparkmon`. Despues, `Evolution` aplica
timers COLOR sobre `stageAge * CARE_TIME_SCALE` (placa 1, sim 600):

```text
Sparkmon --12 h 10 min + CM<=1--> Firemon
Firemon  --24 h + H/E/P>=55 HP>=75--> Flamemon
Flamemon --36 h + 15 batallas de forma--> Dragfiremon
```

Win ratio 0/0 no bloquea en este corte. `EVOLVE` de debug fuerza la linea
buena y resetea el snapshot de forma. Los valores persistidos originales
`Rookie=0`, `Champion=1` y `Ultimate=2` no se renumeran. El arbol muestra
tres nodos por ventana; Pedia pinta los umbrales reales del catalogo.

## Entrada

```text
Boton izquierdo / GPIO0
  corto   -> NEXT
  2 s     -> BACK

Boton derecho / GPIO35
  corto   -> ACTION
```

El debounce y la deteccion de pulsacion larga viven en `Input`, dentro del
nucleo portable. Un flanco de GPIO0 emite `NEXT` al instante; a los 2 s emite
`BACK`. En Home, `BACK` se ignora. En Opciones, `BACK` tambien se ignora. En el resto,
`BACK` vuelve a Home (o al arbol desde el detalle de evolucion). `NEXT`
emite en el flanco de pulsacion; mantenerlo repite tras 400 ms cada 90 ms.

Opciones muestra tres filas grandes. El orden real es Bluetooth, idioma,
sonido, guardar, cargar, fecha, hora, evolucionar y volver. `EVOLVE` fuerza
la siguiente forma, guarda NVS y reproduce la animacion en Home. En
Dragfiremon, `EVOLVE` reinicia la partida en huevo.

El estado `Sleep` se acuesta una vez y luego buclea los frames 12-14 (acostado).
Solo volver a activar el icono del foco ejecuta `wake`; navegar o abrir otro
panel no despierta a la mascota.

Status pagina 1 muestra barras HP / HAM / ENE. `NEXT` cicla a la pagina 2
(edad de etapa, esfuerzo, batallas de forma, CM, call y reloj). Un Call
activo pinta `*` en el selector. `ACTION` o `BACK` vuelven a Home.

Inventario: Carne, Energia, EXP, Anillo y ATRAS. `ACTION` gasta un item
(+20 HAM / +25 ENE / +8 ESF / +15 animo), baja el stock y se queda en el
menu. Stock 0 no hace nada. El huevo no gasta. `ACTION` en ATRAS cierra.

El simulador T-Display separa dos entradas para Firemon despierto:

- Pesa: `TrainingSession` y `render_training` permiten elegir ataque, defensa,
  velocidad, HP maximo, MP maximo o mente, ademas de abrir las lecciones de
  tecnicas. `src/core/training.py` aplica 6 EV al atributo elegido (tope 252),
  cuesta 8 ENE y conserva DNA/IV. Se reutilizan los campos EV persistidos.
- Espadas: `PracticeSession` inicia directamente el encuentro con el rival y
  `render_practice` muestra HP/MP y las ordenes equipadas. No hay preparacion ni
  catalogo intermedio. Consultar/equipar tecnicas queda en Pesa > Tecnicas.
  Retirarse o confirmar un resultado cierra la sesion y devuelve a Home con
  las espadas seleccionadas. Abrir el icono no ejecuta la primera ronda.

`scripts/practice_icons.py` define iconos pixel-art compartidos por ambas vistas.
Guardia y el ejercicio de defensa usan el atlas `block`; no se cambia el motor
de combate. Las sesiones pausan el tick de crianza. NEXT selecciona, ACTION
confirma y BACK vuelve; una sesion de atributo muestra su resultado durante
1.5 segundos sin repetir el premio por mantener pulsada una tecla.

`make sim-training` y `make sim-practice` abren estos flujos con un guardado
aislado compartido, `out/sim_practice_save.json`. Al entrar desde `make sim`,
guardan la partida normal. La practica no modifica victorias oficiales.

La nueva pesa y el rediseno visual estan pendientes de traslado a C++.
El firmware conecta el flujo anterior mediante `PracticeSession`, `App`
y `Panels::drawPractice`. `PetState` posee el progreso y SettingsStore lo
guarda con la mascota, incluido su respaldo; una nueva vida lo reinicia.
Las claves `techVer`, `techTrain`, `techBond`, `techM0..2`, `techEquip` son
opcionales dentro del schema 3. Versiones de progreso desconocidas usan defaults.
La validacion de pantalla fisica y heap con BLE sigue pendiente.

## Persistencia

El esquema actual es 3 e incluye ADN/EV. Admite migracion de 1 y 2.
`vpet_bak` guarda una mascota de respaldo para Descanso. El inventario tambien
incluye proteina y medicina. Status tiene vistas adicionales de ADN.

La particion NVS mide `0x5000` bytes y utiliza namespaces separados:

- `vpet_state` schema 3: especie, barras, edad total, `stageAge`, `cm`,
  `call`, `meals`, `training`, `battles`, `wins`, `losses`, `weight` (5),
  `dp`, `protein`, idioma, sonido, `bluetooth` e inventario
  (`invMeat`, `invEner`, `invExp`, `invRing`; defaults 3/2/1/1).
- `vpet_wifi`: namespace legado reservado; el firmware actual no lo consulta.

Schema 1 migra con ceros y `stageAge=0` (no evo instantanea). Schema `>3`
es Unsupported y `App::begin` deja un huevo nuevo. El anillo de 32 eventos
de cria vive solo en RAM. Autosave ocurre al eclosionar, evolucionar, sumar
un care mistake, gastar un item o guardar a mano. Un despliegue normal no
borra NVS. `App::begin` aplica `bluetoothEnabled` al radio al arrancar.

LittleFS comienza en `0x410000`, mide `0xBE0000` y contiene exclusivamente
recursos reconstruibles. El estado del usuario nunca debe depender de LittleFS.

## Conectividad

Bluetooth se controla desde Opciones (indice 0) y sigue este estado:

```text
Off -> Advertising <-> Connected
        |
        -> Error
```

`BleService` vive solo en la placa. Usa `h2zero/NimBLE-Arduino@2.5.1` como
periferico (central y observer desactivados, una conexion). Al activarse:

1. Inicia NimBLE con nombre `vPet-XXXX`, donde `XXXX` son los 16 bits bajos
   de `ESP.getEfuseMac()` (en esta placa, `vPet-F908`).
2. Activa bonding Just Works (`setSecurityAuth(true, false, true)`).
3. Crea `NimBLEHIDDevice`: HID `0x1812` (teclado, appearance `0x03C1`),
   Device Information `0x180A` y Battery `0x180F`.
4. Publica DIS de solo lectura: modelo `vPet T-Display`, firmware `0.1.0`,
   serial igual al nombre.
5. Anuncia el UUID HID y el nombre. El mapa HID existe para iOS Settings;
   no se envian informes de teclas.
6. `BleAdvertiseSession` configura el payload ADV una sola vez; un
   disconnect solo reanuda el anuncio (`advertiseOnDisconnect`).

El simulador 240x135 refleja el toggle y el texto de estado. No usa la radio
del Mac. WiFi esta deshabilitado hasta una futura fase de aprovisionamiento.
Los paquetes se transferiran por WiFi o USB, nunca por BLE.

Consulta [connectivity.md](connectivity.md) para el flujo de telefono.

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
