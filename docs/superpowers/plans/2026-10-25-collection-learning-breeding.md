# Coleccion, Aprendizaje Y Breeding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** conservar hasta cuatro individuos con mochila compartida, experiencias propias y huevos con herencia limitada.

**Architecture:** modulos portables por composicion; repositorio atomico fuera del core de decisiones, adaptadores sim/ESP32 separados. Un estado de coleccion confirma padres/hijo/inventario juntos.

**Tech Stack:** Python, C++17 core, PlatformIO Arduino ESP32, pytest, snapshots legacy y filesystem con generaciones.

## Global Constraints

- Cuatro plazas totales incluyendo huevos; solo un individuo activo.
- Stock activo como mochila compartida inicial; reserva original sin sumar ni borrar.
- Fundador local requiere confirmacion y no concede inventario.
- No tocar Creator, enums legacy, reglas de evolucion, WiFi o P2P; no flash.
- IDs se asignan fuera de la logica determinista; recibos/secuencias no dependen de fecha editable.

## Task 1: Politica De Aprendizaje Portable

Files: `src/core/learning.py`, `firmware/t-display/lib/vpet_core/src/vpet/Learning.h`, `tests/test_learning.py`, `tests/learning_trace.cpp`.

Interfaces: LearningState con `record(sequence, domain, context, action, reward)`, `choose(domain, context, legal_mask, fallback)`, `encode/decode`, `inherited` para sesgo parental. Tres dominios, 32 contextos, ocho acciones, contadores acotados. Secuencia estricta; replay no aprende otra vez.

- [x] RED: `assert not state.record(1,0,0,0,100)` tras aplicar el mismo evento una vez; historial/codec/paridad y acciones ilegales.
- [x] Ejecutar `.venv-platformio/bin/python -m pytest -q tests/test_learning.py` y comprobar fallo por funcion ausente.
- [x] Implementar media adaptativa entera, codec estricto, sesgo acotado y eleccion con mascara/fallback; sin efectos EV/items.
- [x] GREEN y evaluacion de cambio de recompensa, contadores saturados, corrupcion e historial circular.

## Task 2: Reproduccion Determinista

Files: `src/core/breeding.py`, `firmware/t-display/lib/vpet_core/src/vpet/Breeding.h`, `tests/test_breeding.py`, `tests/breeding_trace.cpp`.

Interfaces: Parent describe ID/sexo/linea/etapa/cuidado/padres/abuelos/cooldown. `check_pair` rechaza inelegibles; `offspring_dna(a,b,seed)` mezcla ocho nibbles con mutacion acotada; `child_profile(words,a,b)` reutiliza PetProfile. El repositorio genera y persiste seed/ID, no el core.

- [x] RED: parientes/IDs repetidos, misma linea, umbrales, cooldown y comparacion exacta Python/C++ para semillas 1..1024.
- [x] Implementar mezcla/validacion pura, sin gasto, RNG de plataforma o creacion de individuos.
- [x] GREEN: mismos parametros reproducen el mismo hijo, IV 0..15, mascara de ambos padres e IDs independientes.

## Task 3: Coleccion Y Repositorio

Files: `src/core/collection.py`, `scripts/collection_store.py`, core C++ `Collection.h`, `CollectionStore.h/.cpp`, pruebas `tests/test_collection.py` y `tests/collection_store.cpp`.

Interfaces: coleccion con slots/active/shared stock/receipt sequence; `adopt_founder`, `switch`, `breed`, `advance`; repositorio load/commit con generaciones y validacion. PetState/SnapshotStore existentes suministran cuerpo individual; aprendizaje y ancestry pertenecen al individuo.

- [x] RED: cinco individuos rechazados, cambiar no repone stock, mismo recibo no crea otro huevo, cancelacion no cambia partida.
- [x] Implementar copia candidata, confirmacion atomica, migracion legacy idempotente sin leer partida personal durante pruebas.
- [x] RED/GREEN de cortes por escritura, futuro/corrupto, reserva intacta y limites de bytes; un error bloquea sin crear fundador alternativo.

## Task 4: Integracion De Experiencias Y UI

Files: Pet/PetState y snapshots, Training/Practice/Exploration sessions, sim services, App y panel separado de coleccion, opciones, tests de app/sim.

- [x] RED: finalizar sesion aplica efecto/experiencia una vez; cancelar/fallo de save no aprende; AUTO filtra por MP/equipo/cooldown.
- [x] Integrar el estado aprendido en la misma transaccion que el resultado confirmado; contadores nuevos no usan IDs del frame.
- [x] Agregar entrada Coleccion y vistas compactas; abrir/cancelar no modifica datos. No editar Status.
- [x] Probar fundador, seleccionar mascota, elegir padres, confirmar y huevo activo con 30 minutos; reinicio no vuelve a lanzar ADN.

## Task 5: Verificacion Y Documentacion

- [x] `.venv-platformio/bin/python -m pytest -q` con fixtures temporales y espacio suficiente.
- [x] `.venv-platformio/bin/pio test -d firmware/t-display -e native`.
- [x] `.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay`.
- [x] Revision de diff, limites de serializacion/memoria y no escrituras de usuario; actualizar evidencia y manual sin incluir Creator.
- [x] Informar por separado core probado, integracion, compilacion y aceptacion fisica. No activar despliegue sin respaldo de coleccion y autorizacion.

## Evidencia Parcial 2026-10-25

- Primera suite amplia: 1982 aprobadas y nueve fallos; no se declara verde.
  Identificados rollback de politica, arrays de Opciones con 10/11 entradas,
  scroll Pico y pruebas antiguas que suponian Volver justo despues de Pausa.
  Corregidos con regresiones; suite final pendiente de congelar firmware.
- 197 pruebas focalizadas de aprendizaje/genetica/coleccion y limites aprobadas.
- 63 pruebas de servicios, Arena, Mochila y experiencia aprobadas.
- Prueba real del loop pygame: botones -> activar coleccion -> fundador ->
  cambiar -> eclosion -> reinicio, todo con partidas temporales, aprobada.
- 33 pruebas de coleccion/servicios/E2E aprobadas tras agregar commit incierto,
  cambio justo en eclosion, cero genes, JSON profundo y cuatro historiales llenos.
- PlatformIO native: 185 aprobadas, 3.09 s. El primer intento fue bloqueado
  por el sandbox al escribir cache; repeticion autorizada sin acceso a USB.
- Galeria `out/collection-preview.png` regenerada e inspeccionada a 240x135,
  escalada sin interpolacion. No acredita aspecto ni rendimiento fisicos.
- Sin flash, WiFi, lectura de partida personal ni publicacion de Creator.

Integracion ESP32 congelada: 13 pruebas focalizadas aprobadas en 20.16 s
(`test_esp32_learning_runtime`, `test_collection_app`, `test_collection_store`).
App real confirma atributos, tecnicas, Arena, viajes, cruce con aprendizaje,
rollback, reserva dormida accesible, ajustes compartidos tras reinicio y ADN
cero preservado. GC protege referencias actual/anterior; no crecimiento de
archivos huerfanos sin limite. No modifica el algoritmo ni los enums legacy.

Compilacion final con C++17 configurado, no flags temporales: ESP32 SUCCESS
18.15 s, RAM estatica 58068/327680, flash app 1098693/4194304. Native final:
185 aprobadas en 1.37 s. Advertencia TOUCH_CS preexistente; sin error de build.
No equivale a medir heap/pila/FPS fisicos. SHA-256 firmware.bin:
`15979af811a48c022643f3fdf0ed7339f2b64f2cb4cc42420f4638ec6648a45d`.

Suite final completa: **2003 aprobadas, 13239 advertencias, 304.15 s**.
Sin fallos. Incluye archivos locales de Creator que ya existian; haberlos
ejecutado no autoriza publicarlos junto a esta entrega. Los cambios propios
de documentacion compartida preservan sus secciones concurrentes.
`git diff --check` correcto. Logs y hashes en `out/collection-verification/`.
34 pruebas finales de coleccion tambien cubren lock de escritor POSIX no
bloqueante y rechazo de incubacion en un cuerpo no compatible.

Pendiente fuera de la verificacion host: respaldo/restauracion completo de
LittleFS con coleccion, autorizacion y carga, aceptacion visual, cortes reales,
pico heap/pila, latencia de guardado y sesiones largas con BLE. No se accedio
a USB ni se flasheo esta revision. No se publico el codigo funcional.

## Entrega Posterior Autorizada

El usuario solicito commit, push y flash. Codigo funcional publicado como
`df96305` y firmware cargado el 2026-10-25, conservando LittleFS y NVS.
La primera carga incumplio el margen de heap; la correccion reserva los diez
iconos Training bajo demanda y los libera al invalidar Panels, sin reducir
colores, cache ni cuadros. RAM estatica 52228; segunda carga aceptada por los
controles de memoria. Las restricciones "no flash" y los pendientes anteriores
describen la fase de implementacion, no esta entrega posterior. Evidencia,
limites y pruebas finales en [registro de carga](2026-10-25-collection-board-delivery.md).
