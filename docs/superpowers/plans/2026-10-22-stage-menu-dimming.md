# Menus Atenuados Por Etapa

## Solicitud Y Alcance

El usuario solicita que los menus todavia no disponibles por etapa se
vean mas desvanecidos, por ejemplo Batalla en Sparkmon.

- Huevo: atenuar Alimentar, Entrenar, Explorar, Batalla y Descanso.
- Sparkmon: atenuar Entrenar, Explorar y Batalla.
- Firemon, Flamemon y Dragfiremon: mantener brillo normal.
- Status, Mochila, Enciclopedia y Opciones permiten consultar sus vistas
  en las etapas iniciales; sus iconos conservan brillo normal.
- Solo representa restricciones por etapa. No agrega bloqueos por hambre,
  lesion, pausa o sueno, ni cambia acciones, equipo, balance o NVS.
- No agrega textos, candados, avisos ni saltos al recorrer NEXT.

## Implementacion

MenuBar.h contiene la disponibilidad visual y aplica media intensidad a
cada canal RGB565, conservando color y seleccion. Home y Exploracion
dibujan la atenuacion una sola vez en sus buffers existentes. La especie
forma parte de sus claves de cache; evolucionar reconstruye la barra sin
pedir al usuario que salga del menu. Los paneles normales detectan el
cambio de especie para redibujar su chrome. La ruta sin buffer de escena
en Exploracion usa la misma transformacion.

El simulador aplica la misma mitad de intensidad en RGB unicamente en el
perfil T-Display. Pico mantiene su presentacion anterior. No hay assets
nuevos, framebuffer adicional ni lecturas de iconos por refresco estable.

## Verificacion

- Prueba roja: el renderer C++ real conservaba iconos brillantes en huevo.
- 35 casos nuevos: cinco etapas, nueve selecciones, Home/Status/Exploracion
  con/sin escena en placa y Home/Status/Exploracion en simulador.
- Comparacion pixel a pixel: solo cambian los iconos bloqueados; se
  conservan iconos habilitados y bordes de seleccion, sin oscurecer dos
  veces al refrescar. Se usa la misma instancia tras cambiar especie.
- La comprobacion de E/S excluye Pedia del recuento porque Exploracion
  tambien lo dibuja dentro de su lista de rutas; los otros ocho iconos
  de barra no vuelven a abrirse despues de calentar.
- 69 pruebas focalizadas aprobadas, incluyendo Arena y Training reales;
  185 pruebas nativas aprobadas.
- Suite general final: 1478 Python aprobadas en 289.01 s, incluidos los
  cambios previos de descanso sin textos. Avisos existentes de Pillow/pytest
  conservados. `git diff --check` limpio.
- Compilacion ESP32 correcta: RAM estatica 56116/327680 (+8 bytes),
  app 1015369/4194304. Compatible con el compilador Arduino C++11.
- Vista previa del renderer C++ real inspeccionada:
  `out/stage-menu-dimming/menu-stages.png` y capturas completas por etapa.
- Revision independiente sin hallazgos: cache por especie, atenuacion
  acumulada, RGB565/readPixel, ruta sin escena y memoria comprobados.

## Carga Preparada

Incluye tambien la correccion anterior de avisos de descanso sin textos,
que no pudo cargarse por desconexion USB. El usuario reconecta la placa
y autoriza ambas mejoras sin completar antes la validacion fisica
pendiente de las cuatro paginas de Status; esa aceptacion no queda cerrada.
No se modifica la distribucion ni los valores de Status, solo sus iconos
de barra cuando corresponde por etapa.

Respaldo critico nuevo en
`out/board-backups/20261022-stage-menu-dimming/08f9e0d00788-20261022-192926-critical.bin`.
24576 bytes; SHA-256
`dad12e258392b241c01938569b4a80c3a1b37c6be957254cc8754b0ff0924215`.
Placa ESP32-D0WDQ6-V3 revision 3.1, ID 08f9e0d00788, flash 16 MB.
SHA-256 del firmware preparado:
`529e7374819ff1859e3582be8e051a606b8b6d69938a16589fae237b00aacb22`.
No implica verificacion de flash ni aceptacion visual fisica.

## Escritura USB

Firmware escrito en 0x10000: imagen de 1021952 bytes a 115200 baudios.
`verify_flash` independiente confirma digest identico al preparado.
Solo se escribe la aplicacion; LittleFS, tabla de particiones y NVS no
se reescriben. Registros: `out/stage-menu-dimming/upload.log` y
`verify-flash.log`. La misma carga incluye los globos sin texto, contador
ni barra del commit anterior `9d7fe31`.

Arranque normal confirmado: VPET_READY, manifest 1, flash 16777216,
FS 11685888/12451840, heap libre 66128 y minimo inicial 66108.
Observacion posterior de 45 s: cuatro muestras, heap libre estable en
66128, minimo 61000, BLE conectado, sin fatal ni reinicios. No hubo
eventos de botones en ese intervalo; no mide FPS ni latencia de uso.
Registros `board-boot.log` y `board-runtime.json` en el mismo directorio.
Se solicita al usuario aceptar visualmente atenuacion, seleccion y
ausencia de etiquetas en los globos; sigue pendiente esa confirmacion.
