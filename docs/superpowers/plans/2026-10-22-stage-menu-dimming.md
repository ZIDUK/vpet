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
- No agrega textos, candados ni avisos. La primera carga conservaba NEXT;
  tras probarla, el usuario solicita que tambien salte los iconos atenuados.

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
Usuario confirma visualmente atenuacion y globos sin textos. Solicita
ademas saltar los iconos bloqueados al recorrer NEXT.

## Revision: Saltar Actividades Bloqueadas

La misma regla portable alimenta el cursor y la atenuacion en cada runtime.
MenuAccess.h se comparte entre Navigation y MenuBar; core.menu comparte
el contrato entre el simulador y su renderer. Solo cambia NEXT en Home
T-Display; los cursores internos y el perfil Pico conservan su recorrido.

- Huevo: Status -> Mochila -> Pedia -> Opciones -> Status.
- Sparkmon: Status -> Alimentar -> Descanso -> Mochila -> Pedia -> Opciones.
- Firemon y posteriores: las nueve opciones, en su orden original.
- Se usa la especie actual antes de procesar la primera tecla tras cargar
  o evolucionar, no la especie consultada en Pedia.
- Sin cambios en assets, balance, consumo, guardado o enums numericos.

Pruebas nuevas: recorrido y vuelta completa, seleccion Pedia independiente,
primera tecla de App en cinco etapas, input pygame T-Display/Pico y consumo
persistido de un objeto de cuidado desde el handler real de Mochila.
Las pruebas del kit inicial distinguen combate, lesion, animo lleno y sueno.
No identifican por si mismas la causa de bloqueo en la partida del usuario.

La regresion C++ fallo primero porque NEXT aun visitaba Alimentar en
Huevo; el handler App tambien fallo en su primera tecla. Ambas pasan
con el filtro por etapa. La seleccion de Pedia no habilita actividades.

185 pruebas nativas aprobadas. Compilacion final ESP32 correcta:
RAM estatica 56116/327680 (sin aumento), app 1015453/4194304.
Pico y T-Display regenerados por los builders; los assets conservan
225 archivos y 10789125 bytes de payload. Las copias generadas de menu.py
son identicas al fuente. No hay recursos ni framebuffer nuevos.

Suite Python completa: 1492 aprobadas en 259.59 s; avisos existentes
conservados. Comprobacion final de diff sin errores de espacios.
Firmware preparado SHA-256:
`9acf10321e49a51c66819ec4e3e54655b1f36e1db522806f77a75d093849b167`.
Puerto USB presente, pero no se ha escrito esta revision: se solicita
autorizacion nueva para omitir la validacion previa pendiente de Status.
La excepcion anterior no se extiende automaticamente a esta nueva carga.
