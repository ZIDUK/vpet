# vPet Hub

Primera entrega local aprobada: catalogo de la linea builtin, animaciones por
etapa/accion e importacion de definiciones JSON internas F1. Sin cuentas ni tienda.

```sh
.venv-platformio/bin/python scripts/hub_server.py --port 8765
```

Abrir http://127.0.0.1:8765. Requiere arte preparado en build-tdisplay
(`make build-tdisplay`). El servidor solo escucha loopback y expone rutas explicitas;
no sirve el repositorio, NVS ni respaldos. No hay telemetria ni servicios externos.
Reiniciar el servidor tras regenerar los assets: las previews tienen cache de sesion.

El importador acepta hasta 64 KiB y reutiliza PetDefinition. Rechaza JSON
duplicado y metadatos incompatibles; nunca extrae ZIP ni escribe archivos.
La validacion NO verifica arte adjunto, firma, autor/licencia, espacio disponible
ni integridad de un paquete distribuible. Una definicion valida no concede huevos
ni items. Las vistas previas corresponden solo al contenido builtin preparado.

Dispositivo informa soporte Web Serial sin abrir puertos. Conexion e instalacion
estan deshabilitadas: faltan protocolo firmware, contrato publico, almacenamiento,
staging/rollback y verificacion de emisor. No hay progreso ficticio de instalacion.
No se modifica firmware, partida, esquema NVS ni inventario.

Archivos: scripts/hub_server.py (adaptador host), web/hub (cliente),
tests/test_hub_server.py (contrato). No se cambia el motor portable.

Pruebas: `.venv-platformio/bin/python -m pytest -q tests/test_hub_server.py`.
`tests/hub_browser.cjs` requiere Playwright/Chromium y el servidor local activo;
ejecutar con `node tests/hub_browser.cjs` donde Playwright sea resoluble.
Las capturas desktop/mobile quedan en out/, no se publican.

Verificacion 2026-10-23: 8 pruebas Hub y 34 F1 pasan; suite general del arbol
local: 1718 aprobadas en 277.69 s, con advertencias existentes Pillow/pytest.
Pruebas Chromium a 1280px y 390px aprobadas: etapas, canvas visible,
importacion valida/invalida, limites HTTP, rutas restringidas y USB deshabilitado.
