# Despliegue T-Display: 2026-10-16

## Autorizacion y alcance

El usuario respondio "Si" a la confirmacion de las cuatro paginas de Status y
la carga del build con sus ajustes actuales. Es una confirmacion del usuario
sobre la placa previa; no se recibieron fotos/video nuevos ni se inspeccionaron
visualmente todos los menus despues de este despliegue.

Baseline publicado: `2e170322a2adced4d8335f97d4f245aa62a77d60`.
Sobre ese baseline, esta entrega corrige AssetStore.cpp, agrega mediciones de
heap en main.cpp y una regresion en tests/test_app_persistence.py. El codigo
compilado y cargado es el de esos archivos en esta revision, no el binario
anterior del baseline. Los SHA-256 inferiores identifican los artefactos exactos.

Placa ESP32-D0WDQ6-V3, revision v3.1, flash fisica 16 MB, puerto detectado
`/dev/cu.usbserial-57040013171`; nombre BLE observado `vPet-F908`.
Se guardo un respaldo nuevo de tabla de particiones/NVS en
`out/board-backups/predeploy-2026-10-16-2e17032-critical.bin`.
No se borro NVS ni se reinicio deliberadamente la mascota; las escrituras
de carga se limitaron a bootloader, particiones, boot_app0, firmware y LittleFS.
El respaldo y las partidas permanecen privados y fuera de Git.

## Incidencia detectada y correccion

La primera carga termino, pero deploy_tdisplay rechazo la telemetria con
HEAP_MIN_LOW: heap_free=73092, heap_min=22852, bajo el minimo de 49152 bytes.
No fue un fallo de transferencia: verify_flash confirmo firmware y filesystem.

Se instrumentaron las fronteras de arranque, sin cambiar el umbral:

| Etapa | Heap libre antes de corregir | Minimo acumulado |
|---|---:|---:|
| Antes de assets | 98940 | 94184 |
| Despues de assets | 96884 | 22852 |
| Antes de App/BLE | 94328 | 22852 |
| Despues de App/BLE | 73092 | 22852 |

El pico estaba dentro de AssetStore::begin, antes de BLE. manifest.readString
cargaba el JSON completo y su String crecia mediante reallocaciones; durante
una ampliacion podia coexistir el buffer anterior con el nuevo.
Se sustituyo por File::find en streaming para la misma marca de formato del
manifiesto generado. No se introduce un instalador o validador JSON general.
No se cambian assets, balance, enums, NVS ni umbrales de memoria.

La regresion nueva fallo con readString antes de corregir y paso despues.
El firmware corregido se compilo y cargo por USB; no hizo falta reescribir
LittleFS porque no cambiaron sus recursos.

## Resultado comprobado en placa

La verificacion final por esptool comparo las regiones instaladas:

```text
0x10000: firmware.bin, 996992 bytes -- verify OK (digest matched)
0x410000: littlefs.bin, 12451840 bytes -- verify OK (digest matched)
```

LittleFS incluye los 162 assets, los 40 sprites de objetos adoptados y las
animaciones happy/sad de Firemon. Su presencia se acredita por la igualdad
del filesystem instalado con la imagen del build, no por inspeccion visual.

Extracto del arranque final capturado durante 25 segundos:

```text
VPET_HEAP stage=before_assets heap_free=98960 heap_min=95884
VPET_HEAP stage=after_assets heap_free=96904 heap_min=91772
VPET_HEAP stage=before_app heap_free=94348 heap_min=91752
VPET_BLE status=ADVERTISING name=vPet-F908 heap_free=73104 heap_min=73000
VPET_HEAP stage=after_app heap_free=73104 heap_min=72944
VPET_BLE status=PAIRED name=vPet-F908
VPET_BLE status=CONNECTED name=vPet-F908
VPET_READY heap_free=73104 heap_min=72944 flash=16777216 fs_used=7860224 fs_total=12451840 manifest=1
FINAL_BOOT_CHECK_OK
```

Se observo un solo VPET_READY, sin Guru Meditation, VPET_FATAL ni bloqueo de
recuperacion durante la ventana. Ambos limites de heap pasan: libre >=65536 y
minimo >=49152. Los mensajes NOT_FOUND corresponden a claves opcionales/journals
ausentes de la partida antigua; no hubo STORAGE_RECOVERY_BLOCKED.
PAIR/CONNECTED acreditan una conexion BLE real durante el arranque, no una
prueba de reconexion repetida ni una certificacion de estabilidad prolongada.

## Pruebas y procedencia

- Suite completa posterior a la correccion: 770 passed, 6514 avisos existentes,
  147.93 s. Regresiones enfocadas de App/assets/despliegue: 18 passed.
- PlatformIO native posterior a la correccion: 172 casos aprobados.
- Build ESP32 final: RAM 50020/327680, Flash 990409/4194304 bytes.
- Assets regenerados: 162 archivos, 7162780 bytes; manifiesto 1.
- Logs completos locales: out/deploy-2026-10-16/ (carga inicial, diagnostico,
  carga final, verify-flash, arranque y pytest). No publicar dumps NVS.

```text
SHA-256 firmware.bin
44c8ebf56f304b3e8e1b1e0683bc67f9112173117992d609616fcae0b68bb2a5
SHA-256 littlefs.bin
e3a202937e22df5580c4ed787cf91a891a656f37746b26528252f4a3c57d13da
SHA-256 manifest.json
faa0c3919b1a39f7ef75731861c590cc49acbbee182e8179e9e596b9967a2409
```

## Lo que este despliegue no cierra

- Inspeccion visual posterior de todos los menus, respuesta de botones y
  animaciones; fotos/video actuales de las cuatro paginas Status ES/EN.
- Arena: harness de paridad visual completo de Panels.cpp en ES/EN.
- Cortes fisicos durante guardado y desgaste/GC de NVS.
- Estres BLE y mediciones de latencia/heap durante sesiones largas.
- Exploracion de placa: sigue sin motor C++/persistencia NVS; flashear los
  assets no porta Patio/Jornada/Noche desde el simulador.
- Reconciliacion de los documentos antiguos identificados en la
  [auditoria documental](2026-10-15-document-traceability.md).
