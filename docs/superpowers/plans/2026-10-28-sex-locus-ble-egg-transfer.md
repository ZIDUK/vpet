# Plan: Sexo Heredable Y Transferencia BLE De Huevos

Spec: [SPEC-GAME-GENETICS-BLE-001](../specs/2026-10-28-sex-locus-ble-egg-transfer.md).
Requirements: REQ-GAME-GENETICS-001/002, REQ-GAME-BLE-EGG-001/002.

## Core Genetico

- [x] Peso proporcional a suma de seis IV, empate y trazas Python/C++.
- [x] Agregar DNA4 y compatibilidad de perfil heredado; conservar DNA0..3.
- [x] Persistir DNA4 en NVS, snapshot y coleccion con migracion idempotente.
- [x] Crear huevo con el alelo heredado y ocultarlo hasta eclosion.

## Transporte BLE

- [x] Envelope portable estricto, token, checksum, replay idempotente, capacidad y fallos de commit.
- [x] Commit de huevo recibido y recibo estable atomicos en CollectionStore.
- [ ] Integrar GATT para escuchar/enviar en NimBLE sin bloquear callbacks ni juego.
- [ ] Añadir pantallas de sala, elegir huevo, confirmar y estado/recuperacion.
- [ ] Preservar el perfil HID existente y apagar la sala limpiamente.

## Verificacion Y Documentacion

- [x] Pruebas Python focalizadas, PlatformIO native y build T-Display.
- [ ] Revisar memoria/tamano de payload, migraciones y regresion de snapshots.
- [ ] Actualizar conectividad, contrato local, estado del proyecto y Archify.
- [ ] No flashear; documentar que radio requiere dos placas y despliegue autorizado.

## Resultado

Registrar reportes reales en esta seccion sin promover SDD automaticamente.
Separar compilacion local de aceptacion fisica y del eventual release.

### Ejecucion Local 2026-10-28

- `make spec-check`: pasa, 5 specs y 21 requisitos con trazabilidad estructural.
- `.venv-platformio/bin/pio test -d firmware/t-display -e native`: pasa, 185 tests.
- `.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay`: pasa; RAM 53,900/327,680 y flash 1,118,329/4,194,304 bytes.
- `.venv-platformio/bin/python -m pytest -q tests`: 2,096 pruebas pasan, incluida una regresion para el locus DNA4 en el renderer Pico.
- Dos placas, GATT/UI y transferencia fisica no implementados; no hay validacion de radio ni flash. El HTML Archify conserva fuentes de un commit anterior y no se actualizo en esta entrega.

## Trazas De Requisito

- REQ-GAME-GENETICS-001: Python `tests/test_breeding.py`; firmware `tests/breeding_trace.cpp`.
- REQ-GAME-GENETICS-002: `tests/test_collection.py::test_bred_egg_keeps_hidden_inherited_sex_through_hatch`; firmware `tests/pet_profile.cpp`.
- REQ-GAME-BLE-EGG-001: `tests/test_ble_egg_transfer.py::test_room_state_and_disconnect_resume` cubre solo el modelo portable; GATT/UI siguen pendientes.
- REQ-GAME-BLE-EGG-002: `tests/test_ble_egg_transfer.py::test_transfer_commit_ack_and_retry_exactly_once`; `tests/test_collection_store.py::test_collection_repository[egg_transfer]` cubre commit durable y replay en C++.

El receptor retiene como maximo 27 recibos de transferencia por coleccion. Al
alcanzar el limite falla cerrado: no confirma ni retira el huevo emisor. Esta
cota conserva `CollectionState` dentro del limite de RAM de 2 KiB.
