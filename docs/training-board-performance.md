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

## Reapertura: velocidad y Tecnicas (2026-10-22)

El usuario informa animacion demasiado rapida solo en Training y caida
pronunciada de animacion/NEXT al llegar a Tecnicas. Las fotos son evidencia
de la pantalla, no una medicion temporal.

Reproduccion con Panels.cpp y AssetStore.cpp reales, assets generados y
adaptadores TFT/LittleFS de host: Select 7/8 y 8/8 requieren doce iconos
distintos, mas el retrato. La LRU de diez iconos rota continuamente:
trece aperturas por refresco caliente, frente a una en las seis opciones
de atributos. Esto explica trabajo de E/S adicional, no certifica por si
solo una latencia ni FPS concretos de placa.

Correccion: conservar los 20 px inferiores de Select en el framebuffer
de escena existente, como Arena. Se reconstruye al cambiar cursor/escena;
App invalida el fondo de Home antes de prestar ese buffer. No aumenta la
cache de iconos, no agrega framebuffer y conserva la ruta sin escena.
Tras calentar, solo el retrato lee flash. NEXT sigue solicitando dibujo
inmediato, sin retrasos ni cambios de debounce.

Cadencia local a Training/Tecnicas: acciones 90 ms (antes 40 ms en Training,
50 ms en Tecnicas), reposo 120 ms (antes 85 ms en Training). Home, Arena,
duracion de sesiones de 10 s, energia, EV, equipo y NVS no cambian.

`tests/test_training_panel.py` cubre ocho opciones, visitas repetidas,
cinco etapas, ES/EN, pixeles con/sin escena, E/S caliente, invalidacion,
Exploracion, subpagina de Tecnicas y transiciones de sesion. El contrato
de App verifica invalidacion al dibujar Training. La paridad completa
Python/C++ comprueba tambien las nuevas cadencias.

El usuario autoriza cargar solo firmware de esta correccion sin repetir
la validacion fisica previa de Status; no modifica Status ni assets y no
cierra la aceptacion pendiente de sus cuatro paginas.

Validacion final local: 1443 pruebas Python (10093 avisos preexistentes de
Pillow/pytest), 185 nativas y compilacion ESP32 aprobadas. RAM estatica
56108/327680 sin aumento; app 1015349/4194304. Prueba roja previa: 13
aperturas en cursor 6; prueba verde: una por refresco tras calentar,
incluyendo comparacion pixel a pixel con la ruta sin cache de footer.
Revisadas capturas del renderer C++ real; revision independiente sin hallazgos.

### Carga y aceptacion renovada

Cargado solo firmware en 0x10000 por esptool a 115200; 1021920 bytes de
imagen, verificacion independiente `verify_flash` correcta. No se escribio
LittleFS, NVS ni particiones. SHA-256 del firmware:
`d549c62aa378fadc2996c9504e3143f66d92fb9334cde17ef0c6f16afaeeaa21`.

Respaldo critico nuevo de 24576 bytes verificado en
`out/board-backups/20261022-training-cadence/08f9e0d00788-20261022-144213-critical.bin`;
SHA-256 `0e43715b9511e29d83e7cd078a92b68461e0beeba022723dff87e0cd69666ac1`.
Logs y capturas en `out/training-cadence/`: upload, verify-flash, board-boot
y board-runtime. Arranque VPET_READY: heap libre 66132, minimo inicial
66064, manifest 1, flash 16777216, FS 11685888/12451840.
Observacion 45 s: cuatro muestras, heap libre 66132 estable, minimo 60936,
BLE conectado, sin fatal ni reinicio. No hubo eventos de botones registrados
en ese intervalo; esos datos no son una medicion de Training.

Despues de cargar y verificar, el usuario recorrio Training/Tecnicas y
respondio: "Si, ambos mejoraron" a velocidad natural del sprite y fluidez
de NEXT. Se acepta la mejora en la pantalla probada; siguen pendientes
latencias instrumentadas, especies/idiomas restantes y sesiones largas.
