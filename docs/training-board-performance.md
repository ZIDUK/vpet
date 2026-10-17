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

Pendiente: carga autorizada, tiempo por draw, latencia NEXT, heap libre/minimo
y prueba sostenida con BLE, ES/EN y las tres especies de combate. No publicar
FPS ni declarar resuelto el reporte antes de medirlo en placa.

Validacion local final: 1078 pruebas Python aprobadas (7762 avisos), 191.20 s;
firmware compilado con RAM estatica 56028/327680 y flash 1007657/4194304 bytes.
La RAM estatica crecio 5840 bytes. No se flasheo esta optimizacion en esta entrega.
