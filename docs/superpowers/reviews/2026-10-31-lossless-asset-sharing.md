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
Tras ese primer intento la placa quedo con los recursos originales, sin ahorro.
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

## Despliegue Corregido Aplicado

El lector temporal de mantenimiento, sin App ni API de escritura, obtuvo un
inventario independiente de 233 archivos desde la placa. La extraccion host
anterior omitia cuatro archivos vivos de coleccion: current, previous y dos
politicas. Se recuperaron sus bytes por USB y se verificaron sus SHA-256.
No se atribuye aqui el desacuerdo a una causa interna del unpacker no demostrada.

Con respaldo raw actual y NVS preservado, se preparo una imagen de 228 archivos:
solo desaparecen cinco recursos legacy duplicados. Los cinco archivos no
administrados se conservaron identicos; los 222 VPA retenidos tienen los mismos
pixels decodificados. El inventario leido de la imagen instalada en la propia
placa coincide exactamente con los 228 hashes esperados.

Se restauro el firmware de juego que estaba instalado antes del mantenimiento.
verify_flash confirmo los tres digests: NVS/particiones, firmware y LittleFS.
El juego arranco con VPET_READY y HUB STATUS confirmo:

- Antes: fs_used=11853824; libres=598016 bytes.
- Despues: fs_used=10911744; libres=1540096 bytes, total=12451840.
- Espacio fisico recuperado: 942080 bytes (920 KiB).
- Ahorro de payload VPA: 899521 bytes; la diferencia fisica incluye bloques
  y metadatos del filesystem reconstruido.

Evidencia local en out/board-backups/asset-sharing-live-20261031/:
live-inventory.json, merge-report.json, pixel-report.json,
installed-inventory.json, verify-final.log y runtime-final.log.
No se incluyen datos privados del guardado en Git. La aceptacion visual y de
juego sigue pendiente; no se afirma que la instalacion del pet piloto en
Collection este terminada, ni que se hayan resuelto las pausas de checkpoints.

Verificacion local completa: out/local-verification/20261101T022738Z-0ecd4cb1/report.json,
2294 pytest, native, firmware, generados y ambos navegadores aprobados,
source_unchanged=true. Perfil Creator tambien aprobado en
out/local-verification/20261101T022855Z-8e89fd66/report.json.
Estos perfiles automatizados no sustituyen la evidencia fisica separada anterior.
