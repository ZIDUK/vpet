# Plan: Reintento De Combate Y Legibilidad

Spec: [SPEC-GAME-PLAYABILITY-001](../specs/2026-10-28-battle-retry-inventory-status.md).

1. Capturar registro USB del recorrido reportado sin modificar progreso.
2. Reproducir rechazo al guardar el resultado con App, LittleFS, politica y
   CareJournal; agregar rechazo de Coleccion e indisponibilidad de lectura.
3. Validar estado durable antes de desbloquear el reintento de adquisicion;
   conservar premio unico e informar fase de fallo.
4. Probar BACK durante tarea diferida; cerrar solo la navegacion.
5. Reorganizar columnas y aumentar iconos en ambos renderers. Comparar textos,
   valores maximos, no mutacion y vista previa.
6. Ejecutar regresiones/suite, native, build y spec-check. Respaldar NVS,
   cargar solo firmware y pedir prueba de combate con registro abierto.
7. Registrar observaciones fisicas y publicar commit/push autorizado.

## Trazas

- REQ-GAME-PLAY-001: `tests/test_esp32_learning_runtime.py::test_actual_esp32_app_learning_hooks_and_review_fixes`.
- REQ-GAME-PLAY-002: `tests/test_collection_app.py::test_collection_app_runtime_and_transactions`,
  `tests/test_status_pages.py::test_inventory_back_has_no_item_detail`.
- REQ-GAME-PLAY-003: `tests/test_status_pages.py::test_dna_icons_and_maximum_values_have_separate_columns`.

## Evidencia Inicial

Se aplican systematic-debugging y test-driven-development, ya consultadas en
esta sesion. Antes de cambiar produccion: falla el escenario de rechazo al
terminar combate por app.ready=false; falla BACK durante tarea diferida porque
no dibuja Home; falla el tamano minimo de iconos ADN (10 px previos).

Registro `out/board-backups/20261028-battle-pending-observation.json`: 300.053 s,
58 eventos de entrada, 29 muestras runtime, sin reinicios ni fallos fatales;
no aparece SAVE PENDING en esa captura. Se observa inicio de exploracion.
No acredita recuperacion del fallo original ni autoriza cancelar el viaje.

## Evidencia Final

- Suite Python final: 2103 passed, 13278 warnings, 336.96 s. Las advertencias
  son deprecaciones existentes de Pillow/pytest; no hubo fallos.
- PlatformIO native: 185/185; build tdisplay correcto, app 1120173 bytes,
  RAM estatica 53916 bytes. spec-check: 6 specs, 25 requisitos, 59 targets.
- Recuperacion limitada por bandera RAM al rechazo del resultado de combate;
  nunca reutiliza este camino para un cuidado aceptado pendiente de confirmar.
- Vista previa `out/status-preview/status-overview-es.png` inspeccionada;
  columnas separadas e iconos mayores. No equivale a aceptacion visual fisica.
- Respaldo NVS fresco `out/board-backups/20261028-playability-critical.bin`,
  SHA256 `df4ace1fc8a0b19d2078ad4951921b745bf8eb5824f9e37b11899e9ba8bb0a37`.
- Carga solo firmware completada en ESP32 `08f9e0d00788`, sin reemplazar
  LittleFS. Registro `out/board-backups/20261028-playability-deploy.log`:
  VPET_READY, heap libre 78836, minimo 67920, FS 11845632/12451840.
  Firmware SHA256 `70c304dcc483e94126333a12d7a7a18cef61a7647daf9683ef575f6c06580116`.
- Observacion posterior de 120 s, sin comandos: registro
  `out/board-backups/20261028-playability-live.log`, 11 muestras runtime,
  sin entradas, fallos fatales ni reinicios posteriores al arranque.
  Se solicito al usuario probar batalla y BACK. No se capturo un combate ni
  SAVE PENDING; causa inicial fisica y aceptacion del recorrido siguen abiertas.
- Cambios preparados para commit/push autorizado. Implementado no significa
  aceptado en hardware; la entrega no se marca como release verificada.
