# Training: rendimiento de placa

## Reporte y alcance (2026-10-16)

El usuario confirma Training lento en T-Display. El simulador y los intervalos
nominales no certifican FPS ni latencia de hardware. App solicita Training
cada 33 ms, pero el dibujo sincronico puede superar ese periodo y retrasar
la siguiente lectura de botones.

AssetStore abria cada asset por frame; su cache de ocho paletas puede rotar
al dibujar diez iconos mas el retrato. Falta medir fisicamente para atribuir
toda la lentitud a esta causa.

## Cambio de firmware

- Diez entradas LRU para iconos estaticos `/training/` hasta 16x16, RGB565 y
  mascara de opacidad. Menos de 6 KiB adicionales estaticos, sin segunda pantalla.
- Conserva la cache de paletas existente; no la reduce en Status/Home.
- No almacena retratos ni animaciones completas. `begin()` invalida caches.
- Transparencia conserva fondo actual. Flip/tint/minLuma conservan la ruta
  original; otros menus no usan la cache nueva de iconos.
- Agrupa lecturas segun ancho: bitmap 68x68 ocupa tres bloques del scratch
  existente de 1920 bytes, antes nueve. Offset y paleta siguen leyendose
  cuando corresponde. Sin cambios en reglas, NVS ni velocidad del sim.

## Evidencia y aceptacion

`tests/test_asset_store_cache.py` compila AssetStore.cpp real con adaptadores
host LittleFS/TFT. Comprueba cero aperturas/lecturas tras calentar diez iconos
durante veinte refrescos, pixeles identicos, transparencia/fondos, modos
especiales, clipping, eviction, invalidacion y AssetStore menor a 13000 bytes.
El cuadro animado caliente necesita cuatro lecturas de offset y tres bloques.

Pendiente: tiempo por draw, latencia NEXT, heap libre/minimo durante Training
y prueba sostenida con BLE, ES/EN y las tres especies de combate. La
aceptacion visual del usuario queda registrada abajo; no se publican FPS
ni latencias instrumentadas a partir de esa observacion.

Validacion local final: 1078 pruebas Python aprobadas (7762 avisos), 191.20 s;
firmware compilado con RAM estatica 56028/327680 y flash 1007657/4194304 bytes.
La RAM estatica crecio 5840 bytes. No se flasheo esta optimizacion en esta entrega.
Entrega publicada en origin/master: `bdcf027` (2026-10-16).

## Despliegue USB (2026-10-17)

Optimizacion cargada por autorizacion explicita del usuario. Compilacion
actual correcta antes de escribir, con Status sin cambios. Respaldo nuevo
de particiones/NVS en `out/board-backups/20261017-training-cache/`.
No se borro NVS ni se reinicio/provisiono deliberadamente la mascota.

Firmware en 0x10000 (1014240 bytes) y LittleFS en 0x410000 (12451840 bytes)
coinciden por digest con sus imagenes locales. Arranque final VPET_READY:
heap libre 66660, minimo 66584; filesystem 9404416/12451840; manifest 1.
BLE emitio CONNECTED y PAIRED. Logs de deploy, verify y boot conservados en
`out/training-cache-board-deploy/`, con marcador TRAINING_CACHE_BOOT_OK.

Ese despliegue confirma carga y arranque. FPS, latencia NEXT y heap de
sesion larga siguen pendientes de medicion.

## Aceptacion visual del usuario (2026-10-18)

Tras verificar la ultima carga de firmware y assets por USB, el usuario
confirmo que Training esta perfecto y el vpet se mueve fluido en la placa.
Se cierra el reporte de lentitud visual en la pantalla probada. La
confirmacion no especifica especie ni idioma, ni valida por separado
Tecnicas, todas las opciones, latencia NEXT o sesiones prolongadas.
