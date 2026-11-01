# SPEC-ASSET-SHARING-001: Recursos Sin Duplicacion

## Estado Y Aprobacion

scope-approved. El usuario aprobo el 2026-10-31 eliminar duplicacion, medir el
ahorro y conservar apariencia, fluidez y guardados. No acredita despliegue.

## Problema

El generador repite fotogramas completos y cinco animaciones legacy de training.

## Objetivo

Reducir bytes instalados sin cambiar calidad, secuencia ni tiempos.

## Alcance

Generador VPA1 y empaquetador training.

## Exclusiones

No cambia NVS, particiones, reserva,
assets fuente, tamanos visuales ni instalador/Collection en esta entrega.
La integracion de contenido sigue en SPEC-CONTENT-DELIVERY-001.

## Requisitos

### REQ-ASSET-SHARING-001

Fotogramas indexados identicos comparten offset VPA1; numero y orden permanecen.
Los bloques consecutivos tambien pueden compartir bytes transparentes finales
e iniciales; conservar la lectura completa de ancho por alto desde cada offset.
No agregar descompresion ni asignaciones de RAM al reproductor.

### REQ-ASSET-SHARING-002

Dejar de exportar cinco copias legacy sin consumidores; mantener los clips por
especie utilizados por el catalogo. Regenerar, no editar datos generados a mano.

### REQ-ASSET-SHARING-003

El preparador offline rechaza la operacion si no recibe un inventario independiente
del dispositivo o si este no coincide con los archivos extraidos. No escribe flash.

## Criterios De Aceptacion

### AC-ASSET-SHARING-001

La secuencia rojo/azul/rojo/rojo/azul almacena dos bloques de pixels y decodifica
cinco frames equivalentes. Transparencia distinta no se combina.
Compartir padding no recorta dimensiones ni modifica los pixels de frames
vacios o con contenido; los offsets siguen siendo validos en cualquier orden.

### AC-ASSET-SHARING-002

Comparar todos los VPA antes/despues: mismos pixels, dimensiones y numero de
frames salvo eliminacion explicita de las cinco copias legacy. Reportar bytes.
El reproductor C++ real sigue reproduciendo offsets repetidos correctamente.

### AC-ASSET-SHARING-003

Sin inventario se obtiene LIVE_INVENTORY_REQUIRED y no se crea salida. Si falta
un archivo del inventario en la extraccion, se rechaza sin preparar imagen.
Los tests de inventario sintetico no acreditan exportacion real desde la placa.

## Contratos Y Compatibilidad

Formato VPA1 y lector se conservan. Mantener offsets validos de acceso aleatorio.

## Errores Y Recuperacion

No borrar archivos de placa ni desplegar filesystem sin respaldo completo y
procedimiento de preservacion de contenido mutable.
Para el despliegue solicitado despues por el usuario: respaldar flash completa,
mantener placa en bootloader, extraer LittleFS y reemplazar exclusivamente los
assets declarados en manifest tras verificar sus hashes. Conservar todos los
archivos no declarados, incluso desconocidos, y rechazar colisiones. Comparar
el arbol reextraido de la imagen candidata con hashes esperados antes de escribir.
Verificar digest de flash escrita. No relajar el bloqueo de deploy_tdisplay.py.
La extraccion host debe coincidir con un inventario independiente de rutas y
SHA-256 obtenido del dispositivo en un estado detenido/coherente. Sin ese
inventario, rechazar con LIVE_INVENTORY_REQUIRED antes de preparar la imagen.
Una reextraccion host de la imagen reconstruida no sustituye esta comprobacion.
La aceptacion exige VPET_READY; ante bloqueo, restaurar y verificar el original.

## Riesgos

El ahorro local no es espacio
ya recuperado en hardware. No prometer mayor capacidad antes de medir.

## Verificacion

tests/test_asset_frame_sharing.py, tests/test_tdisplay_assets.py,
tests/test_asset_store_cache.py; build de assets, native y ESP32.

## Preguntas Pendientes

Ninguna para esta optimizacion acotada. Instalador requiere entrega separada.
