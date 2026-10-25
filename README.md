# vPet

Mascota virtual para la LILYGO TTGO T-Display clasica (ESP32, pantalla ST7789
de 240x135). El firmware usa PlatformIO, Arduino y TFT_eSPI. El simulador de
escritorio comparte las reglas, perfiles visuales y recursos generados con el
dispositivo.

La implementacion anterior para Raspberry Pi Pico W se conserva como plataforma
secundaria mediante los comandos terminados en `-pico`.

## Estado actual

Portal local: [vPet Hub](docs/vpet-hub.md), catalogo animado e importacion de
definiciones F1. Arranque: `.venv-platformio/bin/python scripts/hub_server.py`.
No instala paquetes ni modifica partidas; el transporte USB esta pendiente.

Resumen actualizado el 2026-10-24. Consulta la [guia por opcion](docs/product-guide.md),
el [estado y evidencia](docs/project-status.md) y el
[roadmap vigente](docs/superpowers/plans/2026-10-11-delivery-roadmap.md).
El [programa consolidado de entregas](docs/superpowers/plans/2026-10-23-consolidated-delivery-program.md)
separa funciones actuales, criterios aprobados y ampliaciones por implementar.

- Huevo animado que eclosiona en Sparkmon despues de 2 segundos de juego.
- Linea visual: Huevo -> Sparkmon -> Firemon -> Flamemon -> Dragfiremon.
- Firemon, Flamemon y Dragfiremon con idle, movimiento, comida, entrenamiento,
  descanso, ataque y transiciones de evolucion. Sparkmon incluye idle, caminar,
  comer y dormir; entrenamiento y batalla se habilitan desde Firemon.
- Menu superior de nueve iconos y navegacion completa con dos botones.
- Status en cuatro paginas: vitales, cuidado, combate y DNA.
- Exploracion en simulador y firmware: Patio, Jornada y Noche, con recibo
  persistente y reclamacion unica. Si se pierde la hora al apagar la placa,
  requiere ajustar Fecha/Hora; no inventa tiempo offline sin RTC respaldado.
- Evolucion automatica: Sparkmon (12 h 10 min y como maximo un error de
  cuidado), Firemon (24 h, barras y peso en firmware), Flamemon (36 h,
  15 batallas en esa forma y al menos 60% de victorias acumuladas).
  La placa usa scale 1; el sim usa 600. Arena aporta resultados decisivos.
  Nueva ficha de Evolucion aprobada e implementada localmente: tiempo
  restante, requisitos actuales/objetivos y paginas con NEXT. Pendiente de
  cargar y aceptar fisicamente. [Contrato](docs/evolution-progress.md).
- Alimentar ofrece Carne y Proteina ilimitadas. Mochila conserva objetos legacy
  y consumibles adoptados, con stock guardado en NVS y bolsa de Arena.
- Entrenamiento y cinco tecnicas en sim y firmware: Firemon equipa 2,
  Flamemon 3 y Dragfiremon 4. Aprender y equipar son acciones distintas.
- Rest ofrece apagar/encender luz y volver; no Backup ni Cold. La pausa
  de crianza esta en Opciones, junto a BLE, idioma, sonido, save/load,
  fecha/hora y EVOLVE (herramienta de desarrollo, no evolucion ganada).
- Fondo nocturno de 18:00 a 06:00 con reloj valido, cansancio, horario de
  descanso aprendido y guardado. Apagar luz oscurece fondo/pet e inicia
  descanso; Zzz fijo aparece encima del sprite. Gotas y carita dormida
  indican necesidades sin textos ni barras en Home.
- Bluetooth LE bajo demanda, visible como `vPet-XXXX` en Ajustes del iPhone
  (teclado HID) y en LightBlue o nRF Connect.
- Estado Bluetooth visible en Opciones: `OFF`, `ADVERTISING`, `CONNECTED` o
  `ERROR`. La primera fila de Opciones es Bluetooth.
- NVS schema 3: ADN/EV, especie, barras, edad, stageAge, CM, call, comidas,
  entrenos, batallas, wins/losses, peso, DP, proteina, inventario e idioma.
  Schema 1 migra con ceros. El anillo de eventos de cria es solo RAM.
- F2a local: [identidad, sexo y parentesco](docs/individual-profile.md)
  conservados al evolucionar y guardar; migracion de partida/reserva, sin
  nueva interfaz ni flasheo. F2b local: [potencial por ADN](docs/growth-integration.md)
  con stats hasta 320 y EV por etapa 84/168/252, tambien sin cargar.
- WiFi queda deshabilitado y fuera de la interfaz. Breeding, P2P, rivales
  guardados y TinyML siguen pendientes, no funciones disponibles en placa.
- Arquitectura OO existente con dependencias concretas de Firemon aun por
  extraer en el adaptador de arte original. F1 ya resuelve definiciones,
  Motion y vistas por metadatos localmente; no es un instalador en placa.
  [Contrato y presupuesto](docs/content-definitions.md). Paquetes plug and play, nuevas mascotas de premio como huevos,
  roster y breeding interno son requisitos, no funciones implementadas;
  la capacidad de mascotas/huevos sigue por definir. [Direccion tecnica](docs/content-packages.md).
- Intro de arranque en la T-Display: logo `vPET`, llama, pet y estado `READY`,
  con una duracion aproximada de 2.2 segundos. El simulador reproduce la misma
  secuencia aproximada, con texto FIREMON en lugar del sprite final.

## Estado validado en hardware

Ultima carga registrada: firmware ece6506 para posicion de Zzz, el
2026-10-23, con digest de aplicacion/recursos comprobado, NVS conservada y
VPET_READY. El usuario acepta Zzz encima del pet, tambien tumbado; previamente
acepto apagar/encender luz, la mejora de Training/NEXT, la escala de
Exploracion y el contraste de Evolucion. No equivale a validar todas las
funciones ni las cuatro paginas de Status. Noche completa, viajes/consumo
tras reiniciar, equipo ampliado y estabilidad prolongada siguen pendientes.
Detalle y evidencia historica en [estado del proyecto](docs/project-status.md).

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
La letra es grande (3 filas visibles). Hay una fila `EVOLVE` que fuerza
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

### Entrenamiento y combate

Training, Tecnicas y Arena estan integrados en simulador y firmware con NVS.
El catalogo tiene Golpe, Llama, Guardia, Rafaga e Inferno, con espacios 2/3/4
segun evolucion. Los resultados decisivos de Arena aportan al contador por
etapa y W/L para evolucion automatica; empate y retirada no aportan esos contadores.

- **Pesa:** ataque, defensa, velocidad, vida, MP, mente y aprendizaje de tecnicas.
  Cada sesion de atributo cuesta 8 ENE y suma 6 EV (maximo 252 por atributo).
  Conserva los IV; muestra el valor anterior y el resultado. Vida mejora el HP
  maximo de combate, no cura la barra HP de crianza. MP tampoco es ENE de crianza.
- **Espadas:** entrar directamente en batalla contra el rival de practica,
  con HP/MP y las tecnicas equipadas. No hay menu de preparacion intermedio.
  Aprender, consultar y equipar tecnicas se hace en Pesa > Tecnicas.

La cadencia y NEXT de Training/Tecnicas corregidos fueron aceptados por el
usuario; equipo de 3/4, evolucion ganada y persistencia fisica mantienen sus
pruebas pendientes. Contratos: [entrenamiento](docs/training-session.md),
[tecnicas](docs/techniques.md) y [Arena/evolucion](docs/superpowers/plans/2026-10-18-arena-evolution.md).

```sh
make sim-training
make sim-practice
```

`N` selecciona, `A` confirma, `B` vuelve y `Q` sale. En combate se sale mediante
RETIRARSE; retirarse o confirmar el resultado devuelve a Home con las espadas
seleccionadas. Estos dos comandos comparten `out/sim_practice_save.json`, separado
de la partida normal. En `make sim`, pesa y espadas abren los mismos menus
cuando la mascota es una etapa de combate habilitada y esta despierta, pero
guardan en la partida normal. Huevo y Sparkmon no entrenan ni pelean.

Previews reproducibles con los assets reales:
`.venv-platformio/bin/python scripts/preview_practice.py` genera
`out/practice-preview/overview.png` y `training-overview.png`.

### Referencias

- [Guia de funciones: las nueve opciones y sus limites](docs/product-guide.md)
- [Preparacion del video de lanzamiento y matriz de tomas](docs/launch-video.md)
- [Programa propuesto: genetica, encuentros y aprendizaje](docs/superpowers/plans/2026-10-23-social-genetics-learning-program.md)
- [Programa consolidado: base, Hub, paquetes, items y nuevas mascotas](docs/superpowers/plans/2026-10-23-consolidated-delivery-program.md)
- [Arquitectura](docs/architecture.md)
- [Flujo de desarrollo y despliegue](docs/development-workflow.md)
- [Hardware](docs/hardware.md)
- [Conectividad](docs/connectivity.md)
- [Paquetes y catalogo comunitario](docs/content-packages.md)
- [F1: definiciones, resolver y presupuesto](docs/content-definitions.md)
- [F2b: piloto de crecimiento, medidas y bloqueos de activacion](docs/growth-pilot.md)
- [F2b: crecimiento integrado, conservacion de EV y limites de esta revision](docs/growth-integration.md)
- [Decisiones: cuatro mascotas, stock compartido, crecimiento y breeding](docs/product-decisions-2026-10-23.md)
- [Seguridad y proteccion del firmware](docs/security.md)
- [Estado, alcance y pendientes](docs/project-status.md)
- [Arquitectura visual interactiva (Archify)](.archify/architecture-vpet-20261005/review-2/vpet-architecture.html)
