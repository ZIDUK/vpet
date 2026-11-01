# Optimizacion Local De Recursos

## Cambios

- VPA1 reutiliza bloques de fotogramas identicos y superpone unicamente bytes
  transparentes del final/inicio de bloques. Mantiene numero de frames,
  dimensiones, paleta, orden y acceso aleatorio; AssetStore no cambia.
- Se elimina la exportacion de cinco animaciones legacy de training duplicadas:
  idle, walk, punch, block, cast. Los clips por especie permanecen. TrainingUi
  consume definition.clip(..., Context::Training), no estos nombres legacy.
- compare_vpa_assets compara todas las imagenes decodificadas entre dos arboles.

## Medicion

Snapshot generado previo: /tmp/vpet-assets-before-20261031.
Solo recursos VPA, no ocupacion LittleFS ni NVS:

| Grupo | Antes bytes | Despues bytes |
|---|---:|---:|
| Total | 10891653 | 9992132 |

Ahorro local: 899521 bytes (aproximadamente 878 KiB). La comparacion de 222
recursos debe conservar todos los pixels; solo se eliminan los cinco legacy.
No se redujeron tamanos de dibujo, colores, frames o reserva de instalacion.

## Verificacion Y Limites

Las regresiones de sharing y padding se observaron fallar antes del cambio.
Los resultados finales se conservan en out/local-verification/ y se reportan
por separado. El primer intento full no pudo abrir localhost en sandbox.
Se reinicio con permiso; su snapshot inicial no acredita cambios posteriores.

En la fase inicial no se flasheo ni borro LittleFS de la placa. Recuperar este espacio fisicamente
requiere preservar primero todos los datos mutables de LittleFS, no solo NVS.
No implica que el paquete piloto cree un individuo: esa integracion sigue
pendiente. No estimar criaturas instalables solo
con el tamano del ZIP; reservar staging, contenido expandido y rollback.

## Intento De Despliegue Y Rollback

El usuario solicito despues flashear y hacer commit/push. Se creo respaldo
completo de 16 MiB con SHA-256 bajo out/board-backups/asset-sharing-20261031/.
Lecturas a 921600 y 460800 fallaron antes de escribir; 230400 funciono. No se
modifico NVS ni firmware. La tabla de particiones coincidio con el build.

Se preparo una imagen desde la extraccion de mklittlefs, se verificaron los
hashes de sus 224 archivos y los pixels de 222 assets. Se escribio solo LittleFS
en 0x410000 y verify_flash confirmo su digest, el del firmware y el de NVS.
Sin embargo, el arranque produjo VPET_STORAGE_RECOVERY_BLOCKED, no VPET_READY.
La extraccion host no representaba suficientemente el estado que necesita el
firmware para recuperar la coleccion. No se determina aqui la causa interna
del desacuerdo entre el lector host y el dispositivo.

Se restauro LittleFS original desde el respaldo sin modificar, se verificaron
de nuevo sus digests y los de firmware/NVS. El siguiente arranque produjo
VPET_READY y HUB STATUS: fs_used=11853824, fs_total=12451840 (598016 libres).
La placa queda con los recursos originales, NO con el ahorro local desplegado.
Aceptacion visual y de juego posterior al rollback pendiente del usuario.

scripts/preserve_asset_update.py ahora exige inventario independiente de rutas
y hashes leido desde el dispositivo en estado coherente. No aceptar inventario
reconstruido por el mismo unpacker como evidencia independiente. Sin inventario
el preparador rechaza LIVE_INVENTORY_REQUIRED. El deploy general sigue bloqueando
reemplazos LittleFS; este intento no certifica una ruta de actualizacion segura.

## Pruebas Del Despliegue

Todos los controles de out/local-verification/20261101T012602Z-7308b45a/report.json
terminaron con codigo cero: 2284 pytest, native, firmware, generados y navegador.
El resultado global es failed porque source_unchanged=false: no presentarlo como
snapshot completo aprobado. Tras agregar el bloqueo por inventario se ejecutaron
17 pruebas focales de preservacion, VPA y lector real, todas aprobadas.
Los respaldos, imagenes y registros del dispositivo permanecen ignorados por Git.
