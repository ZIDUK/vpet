# Persistencia Invisible Implementation Plan

> **For agentic workers:** Execute inline with executing-plans, task by task.
> Steps use checkboxes. No delegated task or hardware acceptance is implied.

**Goal:** Juego fluido sin vistas de guardado, conservando progreso recuperable.

**Architecture:** Recibo compacto atomico para cambios ordinarios. Checkpoint de
snapshot separado al dormir/en reposo, con cancelacion/cesion ante entradas,
revision incorporada y recuperacion idempotente. App es propietario unico del
estado vivo, TFT y navegacion; el escritor recibe datos inmutables.

**Tech Stack:** C++17 portable, Arduino/FreeRTOS, NVS/LittleFS, pytest y PlatformIO.

## Global Constraints

- Spec: SPEC-GAME-FLUID-001; alcance aprobado, revision escrita pendiente.
- No cambiar Settings/NVS schema 3, VPL1 ni numeros de enums existentes.
- Leer VPCL v1 y VPCJ1 antes de introducir escrituras versionadas nuevas.
- No reformatear LittleFS, borrar partidas ni borrar out/board-backups/.
- Diario <=3950 bytes, 64 eventos acumulados y ocho entradas pendientes como
  limites de piloto sujetos a prueba; sin truncamiento ni cola ilimitada.
- Ninguna E/S completa, GC ni espera de FreeRTOS en el hilo del dibujo.
- No usar GUARDANDO/SAVING normal; un error real conserva un aviso recuperable.
- No desplegar una etapa parcial como si ya satisficiera la experiencia aprobada.

## Revision Previa

- [x] Revisar App, CareJournal, CollectionStore, LearningRuntime y NVS adapter.
- [x] Aprobacion humana del alcance: "Si, guardar asi sin interrumpir el juego".
- [x] Registrar el diseno y los contratos de recuperacion/capacidad.
- [ ] Revision del documento escrito antes de cambiar persistencia de produccion.

## Task 1: Recibo De Progreso Y Recuperacion

**Files:** core CareJournal.h/Collection.h/CollectionStore.h/.cpp; platform
LearningRuntime.h/.cpp; tests/collection_store.cpp, tests/esp32_learning_app.cpp,
tests/test_collection_store.py y tests/test_esp32_learning_runtime.py.

**Interfaces:** mantener saveCare, load/readPet y commit existentes para fixtures
legacy. Agregar recibo versionado con base, revision global, identidad, snapshot,
eventos ordenados de aprendizaje y checksum. Checkpoint conoce la revision que
incorpora; la aplicacion puede consultar estado durable sin escribir.

- [ ] Escribir regresion con contadores de repositorios: tras saveExperience con
  journal activo, assert(beginCalls == 0 && policyPrepareCalls == 0). Reboot
  debe mostrar EV/costos/aprendizaje del mismo recibo, una sola vez.
- [ ] Ejecutar `.venv-platformio/bin/python -m pytest -q
  tests/test_collection_store.py tests/test_esp32_learning_runtime.py` y capturar
  el fallo de comportamiento previo; no aceptar un error de compilacion como prueba.
- [ ] Implementar lectura historica, codec acotado, guardia de secuencia/identidad,
  commit compacto y replay atomico. saveCare conserva experiencias pendientes.
- [ ] Cortar antes/despues de commit/sync, inyectar CRC incorrecto, evento duplicado,
  salto de secuencia, snapshot maximo, NVS lleno y 64/65 eventos. No fallback a
  saveActive sincrono. Conservar originals ante rechazo, futuro o corrupcion.
- [ ] Verificar REQ-GAME-FLUID-001 y REQ-GAME-FLUID-004 localmente sin promover
  estado fisico. El nuevo formato solo se activa tras superar esta tarea.

## Task 2: Escritor Y Checkpoint Interrumpible

**Files:** firmware/t-display/include/vpet/SaveTask.h, FreeRtosSaveTask.h,
App.h, src/App.cpp, CollectionPanel.cpp y LittleFsCollectionRepository.cpp;
tests/collection_app.cpp y tests/esp32_learning_app.cpp.

**Interfaces:** capacity-one writer, acquire/release terminado, solicitud de
cancelacion de mantenimiento y un recibo de revision durable. La accion de
usuario pendiente tiene orden/revision; no es un segundo PetState por tecla.

- [ ] Retener el escritor con DeferredSaveTask; inyectar ocho entradas y comprobar
  actualizacion del cursor, accion posterior ejecutada una vez y cola acotada.
- [ ] Separar operacion compacta de mantenimiento. Copiar snapshot inmutable y
  reservar una sola tarea; main nunca invoca wait durante un tick.
- [ ] Solicitar checkpoint al iniciar sueno o tras 5000 ms sin entradas. Comprobar
  cancelacion entre chunks de 256 bytes y antes de publicar. No eliminar un
  recibo antes de confirmar su incorporacion en la generacion nueva.
- [ ] Probar teclas antes/durante/despues de rename, sleep/wake durante consolidacion,
  cancelacion repetida, journal lleno, cuatro individuos y 512 acciones. Revisar
  que capacidad/espacio no fuerzan un bloqueo UI en el peor caso.
- [ ] Verificar REQ-GAME-FLUID-002 y recuperar todos los puntos de corte de Task 1.

## Task 3: Integracion Del Juego Sin Vista De Guardado

**Files:** src/App.cpp/Panels.cpp, include/vpet/TrainingUi.h, renderer y sesiones
Python correspondientes; tests/test_training_pixel_parity.py,
tests/test_training_panel.py, tests/test_exploration_app.py,
tests/test_app_persistence.py y tests/test_esp32_learning_runtime.py.

**Interfaces:** resultados del dominio y revisiones durables; UI distingue
trabajo normal de fallo real, sin convertir ambos en savePending global.

- [ ] Agregar pruebas ES/EN que retienen escrituras y fallan si aparece texto de
  guardado o si las entradas se descartan durante/completando un trabajo.
- [ ] Migrar entrenamiento, Arena, CLAIM, cuidado y ajustes al coordinador. Mantener
  resultado/costo/recibo coherentes y guardar reloj fuera de su handler UI.
- [ ] Retirar la vista GUARDANDO normal, no ocultar errores reales. Mantener dibujo
  sin contencion de assets durante checkpoint: reutilizar memoria grafica existente,
  medir lecturas y no inventar una animacion que alargue el ejercicio.
- [ ] Probar cambio de individuo y huevos con commit en segundo plano: ni acuse BLE
  prematuro ni cambios sobre generaciones parciales. Ningun recorrido conserva
  guardado completo sincrono por descuido.
- [ ] Verificar REQ-GAME-FLUID-003 con paridad de pixeles, limites 240x135 y fallos
  recuperables. No sustituir pruebas existentes eliminando aserciones de premios.

## Task 4: Evidencia, Documentacion Y Carga

**Files:** docs/requirements.json, docs/architecture.md, arquitectura Archify
fuente/render segun su skill y evidencias de ejecucion locales.

- [ ] Ejecutar `make spec-check`, suite Python completa, PlatformIO native y build
  tdisplay nuevo. Revisar diff, memoria, pila y consistencia de formatos.
- [ ] Actualizar arquitectura textual y grafica distinguiendo baseline, implementado
  y aceptado. REQ-GAME-PLAY-007/010 no se cierran solo por este nuevo enlace.
- [ ] Con autorizacion vigente y precondiciones de AGENTS, respaldo fresco y carga
  firmware-only. No sustituir graficos ni datos del volumen instalado.
- [ ] Capturar al menos 20 transiciones por flujo; p95 de respuesta visual <=100 ms,
  intervalos de cuadros <=200 ms y resultado <=200 ms despues de su animacion.
  Probar tambien boton durante mantenimiento: arranque READY no es esa prueba.
- [ ] Registrar fallos reales/heap minimo y aprobacion visual. Si una medicion falla,
  mantener requisito abierto y corregir antes de declarar fluidez o release.

## Estado De Ejecucion

Solo diseno y plan escritos. No hay implementacion ni pruebas nuevas ejecutadas
de esta arquitectura; los tests referenciados en el registro son la linea base
que se ampliara. No se ha flasheado ni declarado resuelta esta entrega.
