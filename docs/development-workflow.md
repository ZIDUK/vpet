# Flujo de desarrollo y despliegue

## Principio

El repositorio es la fuente de verdad. La placa contiene una copia ejecutable,
no una version editable del proyecto.

```text
PNG + codigo + datos -> build reproducible -> simulador y T-Display
```

No actives Secure Boot ni Flash Encryption durante el desarrollo cotidiano.
Esas protecciones pertenecen al proceso de fabricacion de una version final.

## Preparacion inicial

```bash
git clone https://github.com/ZIDUK/vpet.git
cd vpet
python3 -m pip install -r requirements-dev.txt
make bootstrap-pio
```

Comprueba la placa:

```bash
ls /dev/cu.usbserial*
make preflight
```

El puerto detectado durante esta migracion fue
`/dev/cu.usbserial-57040013171`; puede cambiar entre puertos USB o equipos.

## Ciclo diario

1. Cambia codigo bajo `src/`, `scripts/` o `firmware/t-display/`.
2. Cambia arte fuente bajo las rutas curadas de `assets/`.
3. Ejecuta `make sim` para revisar el resultado a 240x135.
4. Ejecuta `make test` y `make native-test`.
5. Ejecuta `make deploy` con la placa conectada.
6. Confirma `VPET_READY` y prueba los dos botones.

Comandos individuales:

```bash
make build-tdisplay
make firmware
make preflight PORT=/dev/cu.usbserial-57040013171
make deploy PORT=/dev/cu.usbserial-57040013171
```

## Fuentes y salidas

| Ruta | Tipo | Versionada |
|---|---|---|
| `assets/backgrounds/` | Fondo PNG fuente | Si |
| `assets/digimon/digimon1/` | Sprites PNG fuente | Si |
| `assets/ui/icons/` | Iconos PNG fuente | Si |
| `src/` | Modelo/simulador Python | Si |
| `firmware/t-display/` | Firmware y pruebas C++ | Si |
| `build-tdisplay/` | Arte intermedio generado | No |
| `firmware/t-display/data/` | LittleFS generado | No |
| `firmware/t-display/include/generated/` | Catalogo generado | No |
| `firmware/t-display/.pio/` | Build PlatformIO | No |
| `out/` | Capturas y backups locales | No |

No agregues credenciales, dumps NVS, backups completos de flash ni claves
privadas al repositorio.

## Agregar una mascota o animacion

Mientras el formato comunitario no este implementado:

1. Coloca los PNG en `assets/digimon/<linea>/<etapa>/idle/`.
2. Usa una hoja de 5x5 celdas cuando corresponda; el huevo actual usa 4x4.
3. Registra especie, accion, numero de frames y archivo en `scripts/build.py`.
4. Agrega la evolucion al registro de datos.
5. Agrega pruebas para catalogo, transparencia y seleccion de animacion.
6. Ejecuta `make build-tdisplay`; debe crear VPA y `catalog.h`.
7. Verifica el simulador antes de cargar hardware.

Estados esperados por una mascota completa:

```text
idle
walk o fly
eat
punch
sleep
cast
evolution, salvo la etapa final
```

Una etapa puede declarar menos acciones. Sparkmon, por ejemplo, no acepta
`punch` ni `cast`; por eso entrenamiento y batalla se rechazan hasta Firemon.

No edites archivos VPA ni `catalog.h` manualmente.

## Agregar un theme

Actualmente existe un fondo diurno y uno nocturno generado desde
`assets/backgrounds/bg5 1.png`. Para agregar un theme:

1. Conserva la relacion 240x135 para T-Display.
2. Genera variantes dia y noche.
3. Registra ambas en el builder.
4. Comprueba que menu, mascota e indicadores mantengan contraste.
5. Agrega una prueba de dimensiones y una captura del simulador.

La instalacion dinamica de themes se implementara mediante los paquetes
descritos en [content-packages.md](content-packages.md).

## Pruebas

`make test` cubre:

- logica de mascota y evolucion;
- inventario y opciones;
- render del simulador;
- generacion VPA y manifiestos;
- limites y seguridad del despliegue.

`make native-test` compila y prueba el nucleo C++ sin hardware. `make firmware`
es adicionalmente obligatorio porque detecta errores en adaptadores Arduino,
TFT, NimBLE, NVS y LittleFS que el target nativo no enlaza.

## Despliegue seguro

`make deploy` nunca debe ejecutar un borrado completo. El script:

- detecta el ESP32 y verifica que tenga 16 MB;
- comprueba app, LittleFS, RAM y heap esperado;
- conserva NVS;
- mantiene un backup local de recuperacion;
- carga app y LittleFS;
- espera `VPET_READY` despues del reinicio.

Los recursos LittleFS son reemplazables. El estado y las credenciales viven en
NVS y sobreviven al despliegue.

## Bluetooth durante desarrollo

No hay UI WiFi. Para probar radio:

1. Despliega con `make deploy`.
2. Abre engrane; la primera fila es Bluetooth.
3. Activa hasta `ADVERTISING`.
4. Empareja desde Ajustes del iPhone o abre LightBlue / nRF Connect.
5. Confirma `CONNECTED` en la placa y `VPET_BLE` en serial.

La preferencia vive en `vpet_state` / `bluetooth`. Consulta
[connectivity.md](connectivity.md).

## Compatibilidad Pico

La plataforma anterior se conserva con:

```bash
make sim-pico
make build-pico
make deploy-pico
```

No agregues nuevas funciones exclusivamente a Pico. Toda funcion de producto
nueva debe funcionar primero en T-Display y mantener paridad razonable en el
simulador.

## Recuperacion

Si una carga falla:

1. Desconecta y vuelve a conectar USB.
2. Ejecuta `make preflight`.
3. Repite `make deploy` a 115200 baudios.
4. Usa el backup de `out/` solamente si app, tabla de particiones o LittleFS no
   pueden recuperarse mediante un despliegue normal.

No restaures NVS desde otra placa: puede contener credenciales y estado privado.
