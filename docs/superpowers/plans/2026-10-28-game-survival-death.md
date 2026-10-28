# Plan: Supervivencia Y Muerte Por Descuido

Spec: [SPEC-GAME-SURVIVAL-001](../specs/2026-10-28-game-survival-death.md).
Requirement: REQ-GAME-SURVIVAL-001.

## Correccion De Compatibilidad 2026-10-28

REQ-GAME-SURVIVAL-002 / AC-GAME-SURVIVAL-002. Alcance de correccion inferido del
reporte del usuario y del despliegue autorizado; sin nueva aprobacion documental.

1. Respaldar NVS actual y conservar LittleFS.
2. Reproducir con snapshots historicos v1-v5 y diario compacto v5 sin timers.
3. Aceptar ausencia conjunta con defaults cero; conservar validacion estricta
   de v6 y extensiones parciales. No cambiar schema NVS ni claves/enums.
4. Ejecutar regresiones de persistencia, coleccion y App, suite completa/native,
   spec-check y build ESP32; cargar solo firmware y observar VPET_READY.
5. Registrar resultados sin confundir arranque con aceptacion visual de Status.

Skills consultadas: systematic-debugging y test-driven-development. Antes del
cambio de produccion, ambas regresiones nuevas fallaron al decodificar el
snapshot anterior (pytest: 2 failed, 20 deselected).

## Especificacion

- [x] Auditar hambre, energia, descanso, lesiones y muerte existentes.
- [x] Registrar comportamiento actual y criterios/decisiones pendientes.
- [x] Aprobar piloto: 12 horas a stat cero, rescate con stat > 0; sin acumular
  durante sueño, frio/pausa, exploracion, huevo ni tiempo offline.
- [x] Conservar muerte existente por lesiones: 15 eventos o 6 h continua.

## Implementacion

- [x] Definir timers saturados y defaults cero para guardados previos.
- [x] Implementar reglas portables y recuperacion por alimentar/restaurar energia.
- [x] Cubrir limites, guardado/carga y recuperacion en Python y C++.
- [x] Ejecutar pruebas focalizadas, PlatformIO native y build T-Display.
- [ ] Aceptacion fisica de alertas, descanso y recuperacion; pendiente de flash.

## Trazas

- REQ-GAME-SURVIVAL-001: `tests/test_pet.py::test_survival_grace_rescue_sleep_and_save_roundtrip`,
  `tests/test_pet.py::test_survival_pauses_in_cold_and_keeps_injury_rule` y
  `tests/persistence_atomic.cpp::survival_continuity`.

## Estado Local

## Verificacion Local 2026-10-28

- `make spec-check`: pasa, 5 specs y 21 requisitos; el registro no finge pruebas.
- `.venv-platformio/bin/pio test -d firmware/t-display -e native`: 185/185.
- `.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay`: pasa; RAM
  53,900/327,680 y flash 1,118,329/4,194,304 bytes.
- `.venv-platformio/bin/python -m pytest -q tests`: 2,096 pruebas pasan; incluye
  regresion para el locus DNA4 en el renderer Pico.
- Sin aceptacion en placa. El flash requiere ademas validar/capturar las cuatro
  paginas Status segun `AGENTS.md`; esa precondicion no se ha cumplido.

## Correccion Y Despliegue Posterior 2026-10-28

- Causa confirmada: el lector exigia los dos campos nuevos dentro del conjunto
  comun de claves a todas las versiones. La NVS conservada contiene diarios v5
  con CRC valido y sin esos campos; no eran registros corruptos.
- Respaldo nuevo: `out/board-backups/08f9e0d00788-20261028-recovery-critical.bin`,
  24,576 bytes, SHA-256
  `40a33576e89617898c0302b11a974016b92b89a650c6209eb8d8700cd3817599`.
  El intento de lectura completa a 460800 fallo por ruido serial; no se considera
  respaldo valido. La copia NVS se leyo correctamente a 115200.
- Dos diarios reales del respaldo fueron decodificados/restaurados en host,
  sin escrituras: base/revision 184/21 y 178/20, conservando identidad y stats.
- Regresiones de persistencia/Coleccion: 22 pasan; suite completa: 2,098 pasan
  en 316.74 s (advertencias existentes de Pillow/pytest). Native: 185/185.
- `make spec-check`: pasa, 5 specs y 22 requisitos. No se ejecuto el runner
  `verify-local-full` en esta correccion; los comandos anteriores fueron directos.
- Build ESP32: pasa, RAM 53,900/327,680, app 1,119,025/4,194,304 bytes.
  Firmware SHA-256:
  `2cd3b14eb273fc081aa4665ba1e7af82eaffa36a814441cc0ee7fb697de5c3d7`.
- Despliegue `--firmware-only` autorizado por las solicitudes reiteradas del
  usuario: termina `Deploy OK` tras recibir `VPET_READY`. Heap libre 78,892,
  minimo 68,168; LittleFS 11,845,632/12,451,840, manifest 1.
  Log: `out/board-backups/08f9e0d00788-20261028-recovery-deploy.log`.
- Observacion serial posterior: 25.149 s, dos muestras de runtime, sin reinicios
  entre muestras ni fallos fatales ni STORAGE_RECOVERY_BLOCKED; VPET_READY queda
  capturado tambien en
  `out/board-backups/08f9e0d00788-20261028-recovery-observation.json`.
  Heap libre 78,448 en ambas muestras. Sin pulsaciones: no acredita fluidez de
  acciones, batalla o revision visual.
- Se conserva LittleFS y la partida; no se vacio el diario para desbloquear.
  El arranque verificado no sustituye la revision visual de las cuatro paginas
  Status ni la aceptacion fisica de todas las reglas de supervivencia.
