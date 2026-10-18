# Status: animo, lesiones y EV

Distribucion aprobada el 2026-10-17 para Make Sim y T-Display 240x135.

| Pagina | Datos visibles |
| --- | --- |
| Vital 1/4 | Salud de cuidado, hambre, energia y animo (0..100) |
| Cuidado 2/4 | Edad, exceso de comida, errores de cuidado, esfuerzo, batallas y lesiones acumuladas /15 |
| Combate 3/4 | Conserva peso, DP, victorias, proteina y W-L |
| ADN 4/4 | Conserva codigo completo, helice, seis valores de combate y sus barras; agrega columna EV (0..252) |

Animo lee `stats["p"]` / `PetState::happiness()`. Lesiones lee `injuries`;
no es el numero de heridas activas ni HP restante. El umbral 15 no sustituye
la otra causa existente de muerte por lesion sin tratar durante seis horas.
HERIDO/HURT depende de `injured`; MUERTO/DEAD depende de `dead` y tiene
prioridad. El rotulo queda sobre un retrato de 76x76 o la tumba, separado de
sus pixeles. Una mascota sana conserva su retrato de 88x88.

EV muestra el acumulado de cada atributo, separado del valor de combate;
no es una recompensa nueva ni modifica su formula. Los renderers no mutan
la partida, los enums, el balance ni el formato NVS.

Vital usa cuatro filas de 20 px, separadas por 1 px, desde y=49. Cuidado
usa seis filas con paso de 14 px desde y=48. ADN conserva su columna
x=145..237: valor x=179, barra x=193 (18 px), EV x=215..233.

El escalador de AssetStore admite ahora una fuente cuadrada explicita de
hasta 88 px (20 por defecto para iconos). El retrato se reduce completo,
incluidos los pies; scratch temporal maximo 15488 bytes, sin otra copia
completa en stack. Las rutas normales de Training conservan su cache.

## Verificacion

- Bateria completa: 1081 pruebas Python y 172 casos nativos aprobados.
- Firmware compilado: RAM estatica 56028/327680 bytes, flash
  1008145/4194304 bytes; 186 assets, 8635006 bytes antes de filesystem.
- Capturas reproducibles ES/EN: `scripts/preview_status.py`, salida local
  `out/status-preview/`, incluidas condiciones sano/herido/muerto.
- `tests/test_status_pages.py`: limites de texto, EV 252, cuatro paginas,
  prioridad de muerte, animo 0/100 y ausencia de mutacion.
- `tests/asset_store_cache.cpp`: decodificador C++ real, muestreo de los
  88x88 completos a 76x76, transparencia y limites; cache previa conservada.
- Validacion fisica de estas nuevas filas pendiente de observacion del
  usuario. Capturas del simulador y arranque serial no la sustituyen.

## Carga a placa: 2026-10-17

Firmware y LittleFS cargados por USB, `Deploy OK` tras `VPET_READY`.
Heap libre 66660, minimo 66616; filesystem 9404416/12451840, manifest 1.
Partida preservada; respaldo nuevo:
`out/board-backups/20261017-status-vitals-ev/08f9e0d00788-20261017-060116-critical.bin`.
Logs locales: `out/status-board-deploy/`.

SHA-256 del firmware compilado:
`d86419f3de869d722b5199e12fac7513b87ea6481ea863fe10239ced98ada98e`.
SHA-256 de LittleFS:
`ebf316bef37e15e2b5d9f696e02803eef80ed481392747a013bb5295dedfdbd4`.
Este es el hash final del paquete LittleFS generado durante el despliegue.

El 2026-10-18, tras reconectar USB, `verify_flash` confirmo ambos binarios
con `digest matched`. Arranque posterior observado durante 18 segundos:
`VPET_READY`, heap libre 66652, minimo 66576, flash 16777216,
filesystem 9404416/12451840, manifest 1; BLE ADVERTISING/PAIRED/CONNECTED.
Sin VPET_FATAL, Guru Meditation, brownout ni abort durante esa ventana.
Las claves opcionales swapTx/itemTx ausentes emitieron NOT_FOUND; el
arranque continuo. La mascota reporto llamada HUNGER.
Logs: `vpet-status-verify-reconnected.log` y
`vpet-status-boot-reconnected.log` en `out/status-board-deploy/`.
Sigue pendiente la observacion visual fisica de las nuevas filas.
