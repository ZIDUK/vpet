# Coleccion Visual Implementation Plan

**Goal:** reemplazar las pantallas de coleccion basadas en filas por criaturas,
plazas y parejas identificables en simulador y firmware.

**Architecture:** presentacion separada en `scripts/collection_renderer.py` y
`firmware/t-display/src/CollectionView.cpp`; controladores conservan las
transacciones existentes. Candidatos se calculan al entrar/cambiar seleccion,
no durante cada frame. Preferencias de placa consultan la politica residente.

**Tech Stack:** Pillow, C++17, adaptador TFT y harness de pixeles existente.

## Constraints

Cuatro plazas, dos botones, ES/EN, sin assets nuevos, sin tocar Status/Creator.
No migrar ni leer la partida personal para construir fixtures. No flashear una
revision sin compilar ni confundir una galeria con aceptacion fisica.

## Tasks

- [x] RED: `tests/test_collection_visual.py` exige sprites grandes en bienvenida,
  ficha, fundador y ambos padres; comprueba cuadricula, ambos idiomas, limites
  y que renderizar/cancelar no cambie `collection.encode()`.
- [x] Controlador sim: cuatro plazas y comandos estables, primer padre fijado,
  candidatos elegibles, confirmacion separada y vuelta sin escribir.
- [x] Renderer sim con retratos originales y galeria de fixtures temporales:
  `.venv-platformio/bin/python scripts/preview_collection.py`.
- [x] Adaptador ESP32 con la misma composicion, bienvenida sin "Migrar", cache
  minima del preview y consulta de preferencias activas sin otra politica.
- [x] Harness de TFT real: `tests/collection_visual.cpp`, prueba de pixeles,
  textos dentro de pantalla y ambas criaturas antes de confirmar.
- [x] Ejecutar pruebas focalizadas, suite Python completa, native y compilacion
  tdisplay; inspeccionar galeria a escala entera y memoria estatica.
- [x] Actualizar contrato/manual con disponibilidad real y registrar limites.

## Evidencia Local

Suite completa: 2038 aprobadas, 13278 advertencias, 313.11 s. Incluye Creator
concurrente solo como prueba, no como parte de esta entrega. Native: 185 en
2.894 s. Compilacion tdisplay: 16.207 s; RAM 52236/327680 (+8), app
1102817/4194304. Sin cambios de assets ni de Status.

38 pruebas focalizadas de visuales/transacciones y 22 de integracion aprobadas.
El RED del render capturo falta de retratos grandes y API de preview; otro
RED detecto recorte de atlas. La regresion exige la celda entera, con pies,
antes de reducir a 68px. Galeria de ocho estados ES inspeccionada en
`out/collection-visual-preview.png`, con fixtures temporales.
Clang -Wall/-Wextra/-Werror y -fstack-usage: draw 304 bytes de marco propio
en host; no equivale a medir el pico de pila/heap en ESP32. Las fuentes TFT
se verifican por posiciones/labels; la galeria es del simulador, no una foto.

El usuario aprueba cargar solo firmware, conservando partida y sin activar la
coleccion ni crear huevos. Respaldo y telemetria de carga se registran aparte;
la compilacion y estas pruebas no acreditan aun aceptacion fisica de la UI.

## Carga Autorizada

Placa `08f9e0d00788`, ESP32 revision 3.1, 16 MiB. Solo firmware;
sin uploadfs, erase_flash, activacion de coleccion ni creacion de huevos.
SHA-256 firmware:
`306d30b47c53803a04773187bb841be1ba67a6870288a40037aacac003a3ba36`.
Digest instalado y LittleFS original coinciden tras la carga mediante
`esptool verify_flash` en 0x10000 y 0x410000, respectivamente.

Respaldo critico y app completa anteriores a esta carga en
`out/board-backups/20261026-collection-visual/`. App anterior de 4 MiB:
`3c32242de331fd81a4addcb865db3a6db96cbd05b12409d0ae5da770dfeb93d4`.
LittleFS coincide antes y despues con la copia extraida del respaldo completo
de 16 MiB conservado en `out/board-backups/collection-release-20261025-191125/`.
No es un nuevo respaldo completo de 16 MiB, sino app/critico nuevos y copia
completa previa del filesystem aun identica.

Arranque `VPET_READY`: heap libre 90888, minimo 88220; filesystem
11804672/12451840, manifest 1. Esta telemetria no confirma conexion BLE ni
aceptacion visual. Se solicito al usuario abrir y volver de Coleccion sin
confirmar activacion para comprobar la bienvenida fisica.

Observacion de 70.024 s, sin comandos ni reset solicitados: seis muestras
runtime; heap libre estable en 90888, minimo 85732, BLE=0, sin entradas,
reinicios adicionales ni lineas fatal. Maximo de loop 588303 us durante
arranque, posteriores aproximadamente 153000 us; no mide la fluidez de
Coleccion ni una sesion larga. Evidencia local en
`out/collection-visual-verification/`, incluida telemetria, build y pruebas.
