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
| `SleepRoutine` | Cansancio por ADN/energia, habito gradual, sesiones y premio nocturno unico |
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

La pantalla trabaja en RGB565. Los lienzos que reciben paletas nativas
por `pushImage`, incluido el temporal del escalador, usan `setSwapBytes(true)`.
Se mantienen dos sprites TFT de 240x135:

1. `staticScene` conserva fondo y menu sin elementos animados.
2. `framebuffer` recibe una copia completa de la escena estatica.
3. El selector y el frame actual de la mascota se dibujan en memoria.
4. `pushSprite()` presenta el frame completo en una sola transaccion SPI.

Arena y Exploracion toman prestado `staticScene`: fondo y selector de pelea,
o cabecera de nueve iconos, respectivamente. App invalida la cache de Home
antes de prestarla; `Panels::invalidate()` descarta la cache del panel cuando
Home vuelve a usarla. No se reserva un tercer framebuffer. El selector de
Arena se recompone al cambiar cursor, equipamiento o estado terminal.
Exploracion refresca listas estaticas cada 1000ms en reposo y paginas animadas
cada 70ms; los eventos de boton siempre fuerzan el dibujo sin esperar ese plazo.

Este doble buffer evita limpiar directamente la pantalla y elimina el parpadeo
visible. Las animaciones normales usan frames de 88x88. Las evoluciones usan
111x111 y ocupan el area bajo el menu.

Los VPA1 contienen cabecera, paleta RGB565, offsets de frame y un byte indexado
por pixel. El indice transparente permite dibujar solamente los segmentos
opacos sobre el fondo.

El arranque comprueba la marca de formato del manifiesto generado mediante
`File::find`, sin cargar todo el JSON como un `String`. La lectura anterior
provocaba un pico de heap por reallocaciones. `VPET_HEAP` mide antes/despues de
assets y App; `VPET_READY` conserva los umbrales de despliegue sin rebajarlos.
La correccion y mediciones de placa estan en
[despliegue del 16 de octubre](superpowers/reviews/2026-10-16-board-deployment.md).

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

Status conserva cuatro paginas. Vital muestra HP / HAM / ENE / ANIMO;
Cuidado muestra edad, exceso, errores, esfuerzo, batallas y lesiones /15.
Combate conserva sus cinco filas. ADN muestra valor de combate, barra y EV
acumulado en columnas separadas. HERIDO/MUERTO tienen espacio sobre el
retrato, con prioridad de muerte. Ver [contrato Status](status-vitals-care-ev.md).
Un Call activo pinta `*` en el selector. `ACTION` o `BACK` vuelven a Home.

Alimentar ofrece carne y proteina ilimitadas; no consulta ni descuenta el
stock legado. La mochila conserva Energia, EXP, Anillo, botiquin y ATRAS.
`ACTION` consume un item valido, guarda la partida y permanece en el menu; si
el guardado falla, restaura la instantanea anterior. Stock 0 o una accion
bloqueada no cambia la partida. `ACTION` en ATRAS cierra.

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

El motor de Arena aplica nueve elementos compartidos por Python y C++:
fuego/planta/agua, electrico/viento/tierra, luz/oscuridad y neutral.
`elemental_damage` / `elementalDamage` multiplican por 3/2 (division entera)
solo con ventaja de la tecnica sobre el receptor; los demas cruces usan 1.
Guardia divide despues por 2, con minimo 1. Golpe es neutral, Llama fuego
y Guardia no tiene elemento. Las tres etapas de Firemon y el rival de
practica usan fuego. No se agregan atributos Vaccine/Data/Virus ni campos
elementales persistidos en NVS. La paridad numerica no certifica la paridad
visual de Panels ni el comportamiento fisico sin desplegar.

`scripts/practice_icons.py` define iconos pixel-art compartidos por ambas vistas.
Guardia y el ejercicio de defensa usan el atlas `block`; no se cambia el motor
de combate. Las sesiones pausan el tick de crianza. NEXT selecciona, ACTION
confirma y BACK vuelve; una sesion de atributo muestra su resultado durante
1.5 segundos sin repetir el premio por mantener pulsada una tecla.

`make sim-training` y `make sim-practice` abren estos flujos con un guardado
aislado compartido, `out/sim_practice_save.json`. Al entrar desde `make sim`,
guardan la partida normal. Desde 2026-10-18, los resultados decisivos de Arena
suman al contador de batallas de la forma actual y a W/L acumulados: victoria
suma batalla y victoria; derrota suma batalla y derrota. Empate, retirada y
pelea inconclusa no suman. No se ejecuta la accion legacy de combate aleatorio
ni se cobran DP, energia, lesiones o EV adicionales por registrar el resultado.

El contador, premio, dominio y vinculo se confirman juntos. App usa el journal
completo `saveTx` para el flujo de Arena; `itemTx` antiguo mantiene su formato
y recuperacion para los otros consumidores. Un rechazo restaura el pet y
permite Reintentar; una confirmacion pendiente bloquea entrada hasta recuperar
el snapshot aceptado. Repetir ticks, reintentar o reiniciar no reaplica el premio.

La evolucion permanece automatica al regresar a Home, sin interrumpir el
resultado de Arena. Champion->Ultimate mantiene 36 horas de edad de etapa,
15 batallas en esa forma y 60% de victorias entre W/L acumulados de la vida
actual (no un ratio nuevo por etapa). La edad y contador de etapa se reinician
al evolucionar; W/L, tecnicas, dominio y stock conservan las reglas anteriores.
En Make Sim, `SimulatorServices.evolve_and_save` confirma el JSON atomico
antes de iniciar la animacion; si falla, restaura el pet y no muestra una
evolucion no guardada. Las peleas historicas de Arena no se reconstruyen.

La pesa y Tecnicas se dibujan en C++ mediante TrainingUi. El firmware conecta
`PracticeSession`, `App` y `Panels::drawPractice`. `PetState` posee el progreso y SettingsStore lo
guarda con la mascota, incluido su respaldo; una nueva vida lo reinicia.
Las claves `techVer`, `techTrain`, `techBond`, `techM0..4`, `techEquip` son
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

Nutricion conserva el schema general 3 y usa `nutVer`, `nutHunRem`,
`nutTrainRem` y `nutProtein` para sus campos versionados. `foodTx` es un
registro idempotente de la ultima comida confirmada: se escribe antes de
actualizar las claves afectadas y se reproduce al cargar si hubo un corte a
mitad de NVS. El simulador reemplaza el JSON mediante archivo temporal y
`os.replace`, por lo que una comida persiste el snapshot completo o conserva
el anterior.

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

## Catalogo adoptado y compatibilidad

`src/core/adopted_items.py` define los 40 consumibles adoptados el 2026-10-15.
`scripts/export_adopted_items.py` genera JSON de desarrollo, fichas oficiales,
sprites RGBA y `AdoptedItems.generated.h`. No se instala SQLite en ESP32.
`build_tdisplay.py` empaqueta estos iconos a 16x16 en `ui/items/*.vpa`.
`ConsumableEffects.h` y `PracticeBattle.use_item` ejecutan recuperacion
porcentual y bonos temporales sin modificar reglas de dano ni EV.
Mochila y Arena consumen el stock separado de objetos adoptados. El kit
inicial se migra una vez; victorias de practica otorgan un objeto mediante
rotacion determinista persistida. Manual y Guia no acumulan bonos.
Sim persiste `adopted_items` v1 dentro del JSON atomico; ESP32 usa las claves
aditivas `adoptBag`/`itemTx` con journal y recuperacion idempotente. La
operacion distingue rechazo, aceptacion pendiente y commit confirmado.
Solo un rechazo restaura efecto/stock; una confirmacion ambigua bloquea nuevas
acciones y muestra guardado pendiente hasta sincronizar y recuperar el journal.
El schema NVS principal permanece en 3. Registros incompatibles no se
sobrescriben con una mascota nueva. No cambia ningun enum antiguo.
Ver [adquisicion y limites](adopted-items.md). Validacion fisica pendiente.

## Tecnicas por etapa

El catalogo portable mantiene los indices 0 Golpe, 1 Llama y 2 Guardia;
agrega 3 Rafaga (Champion+, 4 lecciones) y 4 Inferno (Ultimate, 6 lecciones).
Firemon/Flamemon/Dragfiremon equipan 2/3/4. Aprender no equipa y evolucionar
no rellena espacios nuevos. Python y C++ usan el mismo poder, MP, recarga,
elemento y umbral. El rival Firemon conserva su catalogo inicial.
[Contrato y tablas](techniques.md).

NVS conserva schema 3 y techVer 1; agrega techM3/4 y extiende los bits de
techEquip. Los snapshots internos v4 leen v1/v2/v3, conservando la recuperacion
atomica de partidas e intercambios. Dominio, recarga y usos de combate son
bytes acotados; Battle sigue por debajo del presupuesto de 256 bytes.

## Recuperacion de snapshots e intercambio

`sleepState` v1 agrega rutina y sesion de descanso sin cambiar schema NVS 3.
Se guarda junto con energia y premios; restaurar no acredita tiempo apagado.
Home usa calendario para dia/noche, no el estado de Motion. El sprite cansado
no inicia sueno ni interrumpe actividades. [Contrato completo](sleep-routine.md).

El guardado general usa `saveTx`, snapshot interno v4 con campos conocidos
(lector compatible con v1/v2/v3),
rangos y terminador obligatorio. Primero registra el estado absoluto; despues
reproduce las claves legacy del schema 3. Omite escrituras de valores iguales.
`swapLive` y `swapBack` preparan snapshots separados (cada uno menor de 3800
bytes); `swapTx=1` acepta el intercambio de las dos mascotas. El marcador se
limpia solo despues de recuperar ambos lados. La carga recupera estas
operaciones antes de leer campos; registros incompatibles fallan cerrados.

`StoreCommit` distingue Rejected/Pending/Committed. El adaptador conserva un
handle si NVS acepta un valor pero falla `nvs_commit`; `sync()` debe confirmar
ese handle antes de reproducir o iniciar otra operacion. No se interpreta un
fallo de confirmacion como rechazo del journal. Tampoco se usan lecturas de
cache como prueba de durabilidad. App conserva el modelo pendiente, bloquea
entrada y tiempo de cuidado, y reintenta una vez por segundo sin repetir el
efecto. Solo muestra exito cuando sync y recuperacion terminan.

`injuredMs` es opcional y acotado a seis horas; saves antiguos parten de cero.
Se guarda al cambiar el estado y cada minuto mientras hay herida. Un corte
puede perder como maximo el progreso desde el ultimo checkpoint; no se cuenta
tiempo apagado. Training/Arena mantienen la pausa de cuidado aprobada.
`VPET_READY` se emite despues de recuperar almacenamiento e iniciar el BLE
configurado. Las callbacks solo cambian estado atomico y usan nombre inmutable;
el desmontaje espera a detener el host antes de liberar sus objetos.

Ver [correcciones y pruebas](superpowers/plans/2026-10-15-board-audit-fixes.md).

`src/core/item_catalog.py` mantiene los siete objetos legacy activos:
IDs, nombres/descripciones ES/EN, familias, rareza, sprites, stock, efectos
tipados, magnitudes, duracion, limites y origen. No admite evolucion.
`scripts/export_item_catalog.py` genera `ItemCatalog.generated.h`, las fichas
de `docs/items-and-rewards.md` y siete PNG RGBA en `assets/ui/items/`.
La compilacion de assets comprueba que esas salidas esten actualizadas.
Inventario y nutricion Python consumen los datos; C++ consume los nombres,
iconos, cantidades y defaults generados. No se renumeran los seis IDs legacy,
Volver=6 ni las claves NVS; Guia=7 conserva su disponibilidad solo en sim.
El arte editable es pixel-art determinista en `scripts/item_icons.py` y se
exporta sin fondo para uso independiente, con marco neutral en el runtime.

## Exploracion en Make Sim y firmware

Port de placa del 2026-10-16: `Exploration` es un dominio C++ portable,
`ExplorationSession` controla opciones, `ExplorationUi` dibuja tablas en
Panels.cpp y App aplica transacciones completas. Navigation y MenuBar usan
nueve entradas; Exploration se agrega al final de PanelId sin renumerar.
La clave `expState` v1 se captura en snapshots `saveTx` v4 compatibles con v1/v2/v3.
La hora fiable se valida separadamente del reloj de animacion; sin calendario
tras un corte de alimentacion se requiere ajuste manual. Durante viaje se pausan
cuidado/evolucion y las acciones no disponibles abren la expedicion.
Contrato y formato: [Exploracion](exploration.md).

La exploracion de Make Sim usa `core.exploration` para reglas deterministas,
`scripts/exploration_session.py` para transacciones/navegacion y
`scripts/exploration_renderer.py` para ES/EN a 240x135. El registro versionado
forma parte del snapshot de Pet; salida, premio, recibo y Guia se guardan con
reemplazo atomico JSON. `batch_commit` consume la Guia junto al EV de la sesion.
El reloj de expedicion del simulador avanza y se restaura con la partida.
El firmware usa el registro expState y la validacion de calendario descritos arriba.
Contrato detallado y pruebas: [exploration.md](exploration.md).

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

## Cache de iconos Training (2026-10-16)

AssetStore conserva diez iconos estaticos Training de hasta 16x16 en RGB565
con mascara de opacidad, menos de 6 KiB estaticos adicionales. La cache LRU
es independiente de las ocho paletas existentes, no crece con las especies
y se invalida al montar assets. No reserva otra pantalla ni cachea atlas
animados completos. Las lecturas usan el ancho del bitmap para aprovechar
el scratch de 1920 bytes: tres bloques para un cuadro 68x68 en vez de nueve.

Las regresiones ejecutan el adaptador real AssetStore.cpp sobre LittleFS/TFT
de host, contando E/S y comparando pixeles. La carga USB se verifico el
2026-10-17; medicion fisica de latencia/heap durante Training sigue pendiente:
[rendimiento de Training](training-board-performance.md).
