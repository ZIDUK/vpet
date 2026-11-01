# Lossless Asset Sharing Implementation Plan

**Goal:** Reducir almacenamiento de graficos sin alterar apariencia o lector.
**Architecture:** Deduplicar bytes de frame tras cuantizacion, reutilizando la
tabla de offsets VPA1. Eliminar exportacion legacy no referenciada.
**Tech Stack:** Python/Pillow, pytest, C++/PlatformIO.

## Tasks

- [x] Crear regresion de offsets compartidos y observar fallo.
- [x] En encode_vpa construir offsets por bloque indexado unico, despues del
  recorte opcional, conservando la paleta y todos los indices temporales.
  Superponer solo el sufijo/prefijo transparente comun de bloques consecutivos.
  Probar frames completamente vacios y acceso aleatorio a offsets anteriores.
- [x] Quitar el segundo bucle rookie de package_training; validar que los cinco
  nombres legacy no tienen consumidores y los clips por especie permanecen.
- [x] Regenerar assets con scripts/build_tdisplay.py. Comparar decodificacion
  completa con snapshot anterior; registrar bytes y pruebas del lector C++.
- [x] Ejecutar pruebas focales, spec-check, native y compilacion ESP32.

## Constraints And Evidence

REQ-ASSET-SHARING-001 y REQ-ASSET-SHARING-002; sin cambio de guardados, particiones ni reserva.
Sin flash en este paso. Skills consultadas: brainstorming, writing-plans, TDD.
Cambios ajenos del worktree se conservan sin commit automatico.

## Despliegue Posterior Solicitado

El usuario solicita continuar, flashear y despues commit/push. Preparar imagen
offline con scripts/preserve_asset_update.py y tests/test_preserve_asset_update.py.
Respaldar flash completa; conservar placa detenida. Extraer y reconstruir LittleFS
con mklittlefs (-b 4096, -p 256, -s 12451840). Comprobar todos los hashes del
arbol reconstruido y el backup de particiones antes de escribir 0x410000.
No escribir particiones/NVS, no omitir archivos desconocidos. Verificar flash
y HUB STATUS antes de informar despliegue. El helper general sigue protegido.
Commit acotado a esta entrega, sin incorporar cambios ajenos del worktree.

Primer intento fisico: imagen candidata escrita y verificada, pero arranque bloqueado
en recuperacion. Se restauro LittleFS original, se verificaron digests de NVS,
firmware y filesystem, y volvio VPET_READY. Ese intento no desplego la optimizacion.
El preparador ahora exige inventario independiente de la placa; no volver a usar
solo la salida de mklittlefs como prueba de que se preservo la coleccion.
Consultar docs/superpowers/reviews/2026-10-31-lossless-asset-sharing.md.
REQ-ASSET-SHARING-003: bloqueo por inventario implementado y probado; protocolo
para exportar inventario vivo consistente pendiente, no simulado por el host.

## Aplicacion Solicitada Tras El Rollback

REQ-ASSET-SHARING-004: compilar lector separado maintenance/main.cpp, sin App y
sin API de escritura. Protocolo privado USB MAINT INVENTORY/READ, limitado a rutas
ASCII seguras; scripts/asset_maintenance.py verifica hashes y reconstruye copia
completa usando baseline solo cuando coincide con el inventario real. Tests en
tests/test_asset_maintenance.py: archivo ausente, tamper, rutas, EOF y contadores.
Conservar NVS actual y copia raw LittleFS mientras la placa esta detenida. Preparar
imagen con preserve_asset_update y ese inventario; reextraer y comparar hashes.
Escribir exclusivamente filesystem y restaurar app original; verificar digests
de NVS, app y filesystem antes de arrancar. Comprobar VPET_READY y fs libre.

Resultado aplicado: captura viva de 233 archivos; imagen instalada de 228 hashes
verificada desde la placa, cinco archivos no administrados preservados y 222 VPA
con pixels identicos. Firmware original restaurado; tres digests verificados.
VPET_READY y HUB STATUS confirman 1540096 bytes libres (antes 598016): 920 KiB
fisicos recuperados. Evidencia y limites en el review de esta entrega.
