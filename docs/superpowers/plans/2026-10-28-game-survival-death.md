# Plan: Supervivencia Y Muerte Por Descuido

Spec: [SPEC-GAME-SURVIVAL-001](../specs/2026-10-28-game-survival-death.md).
Requirement: REQ-GAME-SURVIVAL-001.

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
