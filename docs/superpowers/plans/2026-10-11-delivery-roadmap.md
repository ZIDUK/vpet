# Roadmap vigente de vPet

Actualizado: 2026-10-16. Prioridad: cerrar calidad y aceptacion de T-Display
antes de ampliar el juego. El [roadmap anterior](2026-10-11-delivery-roadmap-history-through-2026-10-16.md)
se conserva como historia; sus cifras y checkboxes no son el backlog actual.

## Estado real de entrega

| Bloque | Implementacion | Placa / aceptacion |
| --- | --- | --- |
| Status de cuatro paginas ES/EN | Sim y firmware | Desplegado; usuario confirmo las cuatro paginas. Regresiones de botones pendientes |
| Alimentar y peso | Dos alimentos ilimitados, metabolismo, peso, combate y evolucion | Desplegado; balance actual del sim cerrado por el usuario. Persistencia fisica pendiente |
| Training y Tecnicas | Sesion de 10 s, coste/recompensa unica, cancelacion y guardado | Desplegado; usuario reporta lentitud real. NO aceptado como fluido |
| Arena | Ataques automaticos, Guardia, impactos de 1200 ms y resultados | Desplegado; falta comparacion visual completa de Panels.cpp |
| Elementos | Nueve elementos, ventaja x3/2 antes de Guardia, minimo 1; sin Vaccine/Data/Virus | Python/C++ implementados; evidencia numerica no cierra la visual |
| Mochila | 40 consumibles, sprites, efectos, stock, adquisicion y journal | Desplegado; falta consumo y cortes de energia observados en placa |
| Exploracion | Patio/Jornada/Noche, vuelta anticipada, recibo, Guia, topes y snapshots | Portado y desplegado; falta prueba fisica de viajes/reinicios |
| Sprites evolucionados | Flamemon y Dragfiremon: block/hurt/happy/sad propios | Desplegados por USB; falta aceptacion visual fisica |

Fuentes: [arquitectura](../../architecture.md), [consumibles](../../adopted-items.md),
[exploracion](../../exploration.md), [Flamemon](../../flamemon-assets.md),
[Dragfiremon/despliegue](../../dragfiremon-assets.md).

## P0: Training fluido en placa

- [x] Registrar reporte de lentitud real. No confundir animacion del sim con hardware.
- [x] Revisar ruta: refresco nominal de 33 ms, pero AssetStore reabre iconos
  estaticos por frame y ocho paletas no cubren toda la pantalla de Training.
- [x] Cache acotada de diez iconos Training hasta 16x16; menos de 6 KiB
  estaticos adicionales, sin segunda pantalla ni cambios en NVS.
- [x] Agrupar lecturas segun ancho real: bitmap 68x68 pasa de nueve a tres
  bloques, mas la lectura del offset y paleta cuando corresponda.
- [x] Regresion sobre AssetStore.cpp real: veinte refrescos calientes sin
  E/S adicional de iconos; pixeles, transparencia, fondos, modos especiales,
  clipping, eviction e invalidacion comprobados.
- [ ] Desplegar esta optimizacion con autorizacion. El flash de sprites
  anterior NO incluia la cache.
- [ ] Medir duracion de dibujo, respuesta NEXT y heap libre/minimo en las
  seis opciones y Tecnicas, ES/EN, tres especies de combate y BLE activo.
- [ ] Aceptacion del usuario: movimiento natural, un cambio por pulsacion,
  sin saltos residuales. No declarar FPS reales a partir del host.

Contrato: [rendimiento de Training](../../training-board-performance.md).
Reducir E/S no demuestra por si solo la fluidez deseada en hardware.

## P0: funcionalidad y persistencia fisica

- [ ] NEXT: veinte pulsaciones cortas y pulsacion larga de 2 s; comprobar
  respuesta, salida a Home y ausencia de accion al soltar.
- [ ] Inactividad de 10 s: reinicia con botones; nunca interrumpe sesiones activas.
- [ ] Training: completar/cancelar/repetir; coste y EV una sola vez,
  tecnica equipada y partida conservadas tras reinicio.
- [ ] Alimentar: exactamente Carne/Proteina ilimitadas; hambre/energia/peso
  coherentes, sin descontar Mochila. No reabrir balance sin nueva instruccion.
- [ ] Mochila/Arena: consumo, efecto, adquisicion, limites y guardado unico.
- [ ] Explorar: tres rutas, retorno anticipado, cobro unico, recibo, Guia
  consumida una sola vez y topes semanales tras reinicio.
- [ ] Cortes controlados: journal, snapshots, swap/park y Pending sin
  duplicaciones/perdidas. Guardar fotos/video, build y logs.

Sin RTC respaldado: perder calendario exige ajustar Fecha/Hora antes de
enviar/reclamar; no prometer progreso sin alimentacion. Nunca borrar backups.

## P1: paridad visual y estabilidad

- [ ] Harness de imagen de Arena REAL de Panels.cpp, ES/EN, misma partida
  y reloj: esperando, ronda, victoria, derrota y empate.
- [ ] Comparar orden/accion/motivo y dano bidireccional sin superposiciones;
  Guardia/hit/hurt salen del resultado. No inventar evasion.
- [x] Multiplicador elemental portable y pruebas agua/fuego/planta.
- [x] Happy/sad propios de Rookie/Champion/Ultimate conectados en ambos lados.
  Flamemon usa punch para hit por aprobacion; Dragfiremon conserva punch como fallback.
- [ ] Sesiones prolongadas Training/Arena con BLE: latencia, heap y estabilidad.
- [ ] Telefono: ADVERTISING -> CONNECTED -> desconexion -> ADVERTISING.
  Pairing en un arranque aislado no certifica el ciclo sostenido.

## P1: versionado y documentacion

- [x] Actualizar roadmap y estado; separar implementacion, flash y aceptacion.
- [x] Conservar roadmap previo como historia, no backlog vivo.
- [ ] Commit y push actuales: codigo, tests, PNG fuente, docs y build Pico
  regenerado. Excluir backups, partidas, logs locales y secretos.
- [ ] Confirmar hash publicado y estado de origin/master.

## P2: ampliaciones separadas

- [ ] Especie planta y tecnica: alcance, nombre, potencia, assets y balance
  independientes. Las pruebas elementales actuales usan combatientes de prueba.
- [ ] Arte opcional: dodge de Dragfiremon y emociones Sparkmon; no necesita
  combate mientras esa etapa no pueda pelear.
- [ ] Verificar que MiniMax carga las skills instaladas por el usuario y
  entrega un asset importable probado. No marcar instalacion como ausente
  sin inspeccion; no delegar Training sin autorizacion.
- [ ] Futuro botin por ruta: ficha, limites/capacidad, probabilidades y
  reclamacion atomica antes de ampliar recompensas.
- [ ] App movil, vpetpack y [negocio del mall](2026-10-13-mall-business-plan.md)
  despues del cierre de placa.

Catalogo activo: 40 consumibles adoptados, no siete entradas legacy ni 128
referencias de Digimon World. Excluye evolucion, llaves/misiones, pesca,
mapas inexistentes y venta sin economia. No habilitar WiFi ni cambiar enums NVS.

## Evidencia y comandos

Entrega de sprites: 1077 pruebas Python, firmware/LittleFS verificados en placa.
Heap libre 72504, minimo 72436; filesystem 9404416/12451840; manifest 1.
Arranque final con PAIRED/CONNECTED y VPET_READY, no prueba visual ni sostenida.
La nueva cache es posterior a ese despliegue y requiere su propia carga/medicion.
Validacion local posterior: 1078 pruebas Python aprobadas; firmware con RAM
56028/327680 y flash 1007657/4194304 bytes. Cache aun sin flashear.

```sh
.venv-platformio/bin/python -m pytest -q
.venv-platformio/bin/pio test -d firmware/t-display -e native
make build-tdisplay
.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay
git diff --check
```

Core nativo cuando cambie dominio. USB requiere autorizacion y verificacion
separadas; su exito no cierra aceptacion visual.
