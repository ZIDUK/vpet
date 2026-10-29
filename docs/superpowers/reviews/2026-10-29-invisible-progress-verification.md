# Persistencia Invisible: Verificacion Local 2026-10-29

SPEC-GAME-FLUID-001 y plan aprobados por el usuario. Requisitos implementados,
no aceptados fisicamente; release_ready=false. No sustituye el pendiente de
latencia real de REQ-GAME-PLAY-007/010 ni aprueba otros features del backlog.

## Resultado Local

- `.venv-platformio/bin/python -m pytest -q tests`: 2212 pasaron en 333.09 s.
  Reporte generado: `out/invisible-progress-pytest.xml`.
- PlatformIO native: 185/185, repetido despues de los cambios finales de core.
- Coordinador + adaptadores interrumpibles + CollectionStore: 81/81 despues de
  activar el mecanismo en main.cpp.
- `make spec-check`: 7 specs, 36 requisitos, 166 tests trazados recolectados.
- Assets regenerados desde fuente: 227 archivos, 10891653 bytes; no instalados.
- Build tdisplay con mecanismo activo: programa 1133909 bytes, RAM estatica
  54100 bytes. RAM dinamica/pila/latencia requieren observacion de placa.
- SHA256 firmware.bin:
  `2cc389487580ce9d1338848be2671a98640791a11c87319ef53e36d307c48214`.
- `git diff --check`: sin errores.

Las pruebas incluyen recibo conjunto de efectos/aprendizaje y reboot, stock
maximo, 64/65 eventos sin truncar, 512 acciones con consolidacion, corrupcion,
rechazo/aceptado pendiente, retorno seguro a Home, cola de ocho entradas y
rollback. Los adaptadores reales prueban cancelacion antes/durante publicacion,
politicas protegidas, respaldo preparado y reanudacion de checkpoint sin
enclavar un error. Los frames ES/EN de resultados pendientes usan el mismo
resultado normal, no GUARDANDO ni confirmacion durable anticipada.

## Respaldo Y Hardware

Se leyeron 24576 bytes desde 0x8000 de la placa ESP32 08f9e0d00788, puerto
`/dev/cu.usbserial-57040013171`. Archivo:
`out/board-backups/20261029-invisible-progress-critical.bin`.
SHA256: `96fd09190f84b6575740d8b32f50711d3df115ee5bf10fc55b383003ea54c295`.
La lectura reinicio la placa. No se borraron NVS, LittleFS ni respaldos.

El usuario retiro expresamente el 2026-10-29 el requisito de evidencia fisica
de las cuatro paginas Status antes del flash; AGENTS.md actualizado. La carga
firmware-only termino correctamente: heap_free=75980, heap_min=54444,
LittleFS=11862016/12451840 y manifest=1. Los cambios en Panels.cpp solo afectan
entrenamiento; scripts/sim_renderer.py y el layout Status quedan intactos.

Observacion de 180.145 s en
`out/board-backups/20261029-invisible-progress-observation.json`: 112 eventos de
entrada, 111 presentaciones medidas, sin fatal ni reinicio observado; heap
minimo 23308. p95 entrada-a-presentacion=610 ms, maximo=998 ms: NO cumple el
objetivo de 100 ms. loop_max_us=699077. No se confunden estos tiempos globales
con una medicion de 20 transiciones por cada flujo.

Los recibos compactos medidos tardaron 226-505 ms; checkpoints completos
3869-7452 ms. La consulta de espacio consume aproximadamente 2260-2324 ms;
hay una cancelacion real de checkpoint en 424 ms. No se detectaron recibos
rechazados en esta captura, pero retener el framebuffer durante mantenimiento
todavia produce una espera visible. La arquitectura esta implementada, NO se
declara resuelta ni aceptada la fluidez fisica. Falta optimizar/medir estos
recorridos y comprobar cortes de energia reales.

El usuario no pudo entrenar por falta de energia. La interfaz USB instalada
solo admite consultas STATUS/STORAGE, no cambios de energia. Recuperacion
soportada: Proteina en Comida (+20, una vez por ciclo) o Tonico de Mochila (+25,
si hay stock), ademas del sueno. No se edito NVS ni se concedieron recursos
mediante comandos ocultos.

## Historial De Fallos De Verificacion

La primera regresion observo escrituras completas por accion antes del codec
compacto. Hubo timeouts bajo compilaciones concurrentes; luego se repitieron
secuencialmente. Fixtures de version futura se movieron a VPCL v3, porque v2
ahora es soportada. Se corrigieron dependencias de enlace en pruebas App legacy
sin quitar sus aserciones. Una invocacion pytest sin directorio recolecto copias
historicas en out/; la suite valida se ejecuto explicitamente sobre tests/.
