# Roadmap vigente de vPet

Actualizado: 2026-10-19. Prioridad: cerrar calidad y aceptacion de T-Display
antes de ampliar el juego. El [roadmap anterior](2026-10-11-delivery-roadmap-history-through-2026-10-16.md)
se conserva como historia; sus cifras y checkboxes no son el backlog actual.

## Estado real de entrega

| Bloque | Implementacion | Placa / aceptacion |
| --- | --- | --- |
| Status de cuatro paginas ES/EN | Sim y firmware: animo, lesiones /15, HERIDO/MUERTO y EV junto a barras | Cargado el 2026-10-17; firmware/LittleFS y arranque verificados por USB el 2026-10-18. Aceptacion visual y botones pendiente |
| Alimentar y peso | Dos alimentos ilimitados, metabolismo, peso, combate y evolucion | Desplegado; balance actual del sim cerrado por el usuario. Persistencia fisica pendiente |
| Training y Tecnicas | Sesion de 10 s, coste/recompensa unica, cancelacion y guardado | Training aceptado visualmente como fluido por el usuario el 2026-10-18. Tecnicas y pruebas instrumentadas pendientes |
| Tecnicas por evolucion | Firemon 2, Flamemon 3, Dragfiremon 4; Rafaga e Inferno, aprendizaje/equipo manual y guardado compatible | Firmware/FS cargados y verificados por digest el 2026-10-18; VPET_READY, aceptacion fisica del equipo ampliado pendiente |
| Arena | Ataques automaticos, Guardia, impactos de 1200 ms, celebracion completa, escala uniforme y cursor persistente | Correccion cargada el 2026-10-18 y verificada por digest; harness real de Panels.cpp. Falta paridad exacta y aceptacion visual fisica |
| Elementos | Nueve elementos, ventaja x3/2 antes de Guardia, minimo 1; sin Vaccine/Data/Virus | Python/C++ implementados; evidencia numerica no cierra la visual |
| Mochila | 40 consumibles, sprites, efectos, stock, adquisicion y journal | Desplegado; falta consumo y cortes de energia observados en placa |
| Exploracion | Patio/Jornada/Noche, vuelta anticipada, recibo, Guia, topes y snapshots | Portado y desplegado; falta prueba fisica de viajes/reinicios |
| Sprites evolucionados | Flamemon y Dragfiremon: block/hurt/happy/sad propios | Desplegados por USB; falta aceptacion visual fisica |
| Noche y personalidad de descanso | Fondo 18:00-06:00, tired en cuatro etapas, habito gradual y guardado v4 compatible | Firmware/FS cargados y verificados por digest el 2026-10-18; VPET_READY. Falta aceptacion visual y noche real |
| Globos y caras de animo | Comida/descanso/lesion/tristeza/enojo en Home; cuatro caras en el slot vital de Status, sin nuevos Calls ni persistencia | Firmware/FS cargados y verificados por digest el 2026-10-18; VPET_READY y BLE conectado. Aceptacion visual fisica pendiente |
| Rest y pausa | Rest solo luz/volver; Pausar crianza en Opciones; reserva conservada. Pausa detiene sueno y margen Call. Luz apagada oscurece Home sin alterar dia/noche | Menus aceptados por el usuario; seguimiento de oscuridad: 1324 Python/183 nativas aprobadas. Evidencia USB y aceptacion de luz en plan |

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
- [x] Optimizacion desplegada con autorizacion el 2026-10-17. Firmware y
  LittleFS verificados por digest; arranque final VPET_READY confirmado.
- [ ] Medir duracion de dibujo, respuesta NEXT y heap libre/minimo en las
  seis opciones y Tecnicas, ES/EN, tres especies de combate y BLE activo.
- [x] Aceptacion visual del usuario el 2026-10-18: Training perfecto y
  movimiento fluido del vpet en placa, en la pantalla probada.
- [ ] Validar NEXT sin saltos residuales y Tecnicas por separado; ampliar
  a especies e idiomas restantes. No declarar FPS a partir del host.

Contrato: [rendimiento de Training](../../training-board-performance.md).
El usuario acepta la fluidez observada. La matriz ampliada y las mediciones
de hardware mantienen su alcance pendiente.

## P0: funcionalidad y persistencia fisica

- [x] El usuario confirma Rest simplificado y Pausar crianza en Opciones.
- [ ] Aceptar visualmente la correccion de luz apagada y el ciclo completo
  de pausa/reanudacion, sin tocar la reserva. El observador
  USB solo lee memoria/ciclos/eventos; no prueba FPS ni una noche real.
  [Contrato](../../rest-and-board-validation.md), [matriz](2026-10-19-rest-and-board-validation.md).

- [ ] Aceptar globos en Home y caras de Status en placa: comida sin enojo,
  comida/descanso con animo bajo, lesiones y desaparicion al resolver la
  necesidad. Sin recortes al caminar ni overlay durante acciones/paneles.
  [Contrato](../../mood-cues.md).

- [ ] Aceptar noche/descanso en placa: limites 18:00/06:00, cuatro sprites,
  acostarse temprano/tarde, interrupcion, reinicio, energia y premio unico.
  El amanecer no despierta antes de completar la sesion. Sin credito apagado.
  [Contrato](../../sleep-routine.md).

- [ ] Observar Status ampliado en placa: cuatro barras, seis filas de cuidado,
  HERIDO/MUERTO y columna EV sin recortes, ES/EN. La aprobacion anterior
  cubria la distribucion previa. [Contrato](../../status-vitals-care-ev.md).
- [ ] NEXT: veinte pulsaciones cortas y pulsacion larga de 2 s; comprobar
  respuesta, salida a Home y ausencia de accion al soltar.
- [ ] Inactividad de 10 s: reinicia con botones; nunca interrumpe sesiones activas.
- [ ] Training: completar/cancelar/repetir; coste y EV una sola vez,
  tecnica equipada y partida conservadas tras reinicio.
- [ ] Tecnicas ampliadas en placa: aprender Rafaga/Inferno, equipar 3/4,
  seleccionar cada orden de Arena y conservar equipo/dominio tras reinicio.
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

- [x] Globos de necesidades y caras happy/neutral/sad/angry portables,
  once iconos empaquetados y misma geometria de Status. 1536 vectores
  Python/C++, pixeles de Renderer/Panels/AssetStore reales y regresion de
  las cuatro especies cansadas con fondos dia/noche. [Entrega](2026-10-18-mood-bubbles.md).

- [x] Rutina de descanso portable Python/C++, aprendizaje gradual por ADN y
  habitos, cansancio suave sin faltas por Lights y guardado atomico v4 que
  lee v1/v2/v3. Cuatro originales tired y fondo nocturno aprobados.

- [x] Espacios 2/3/4 por evolucion; catalogo de cinco, Rafaga/Inferno de fuego,
  iconos propios, seleccion manual y requisitos por etapa/lecciones. Guardado
  aditivo techM3/4, snapshots v3 con lectura v1/v2, regresiones de cortes y
  trazas Python/C++. [Contrato](../../techniques.md).

- [x] Arena aporta resultados decisivos a evolucion automatica: contador
  por etapa y W/L acumulados; resultado/premio guardados juntos con saveTx,
  reintento y recuperacion sin duplicados. [Plan](2026-10-18-arena-evolution.md).
- [ ] Aceptacion fisica de evolucion automatica tras completar requisitos
  mediante Arena. No reconstruir resultados historicos no guardados.
- [x] Reproducir/corregir intercambio RGB565 del escalador (IMG_4004).
  Reutilizar fondo/selector de Arena y cabecera de Exploracion; pruebas
  cache/sin cache, invalidacion y respuesta inmediata de App en host.
- [ ] Aceptacion fisica de color y fluidez tras IMG_4004. La distribucion de
  Arena fue aceptada; contadores de E/S no equivalen a FPS de placa.
- [x] Corregir celebracion recortada por fuente 20px, escala de acciones,
  feedback sobre iconos y reinicio del cursor a AUTO. Harness de produccion
  Panels.cpp/AssetStore.cpp: 24 casos ES/EN y tres especies. El adaptador
  captura texto; no certifica rasterizacion de fuentes TFT.
  [Evidencia](../../arena-presentation-fixes.md).
- [ ] Harness de imagen de Arena REAL de Panels.cpp, ES/EN, misma partida
  y reloj: esperando, ronda, victoria, derrota y empate.
- [ ] Comparar accion y dano bidireccional; Guardia/hit/hurt salen del
  resultado. ORDER/DID/WHY se retiraron por solicitud, no restaurarlos.
  No inventar evasion.
- [x] Multiplicador elemental portable y pruebas agua/fuego/planta.
- [x] Happy/sad propios de Rookie/Champion/Ultimate conectados en ambos lados.
  Flamemon usa punch para hit por aprobacion; Dragfiremon conserva punch como fallback.
- [ ] Sesiones prolongadas Training/Arena con BLE: latencia, heap y estabilidad.
- [ ] Telefono: ADVERTISING -> CONNECTED -> desconexion -> ADVERTISING.
  Pairing en un arranque aislado no certifica el ciclo sostenido.

## P1: versionado y documentacion

- [x] Actualizar roadmap y estado; separar implementacion, flash y aceptacion.
- [x] Conservar roadmap previo como historia, no backlog vivo.
- [x] Entrega anterior versionada: codigo, tests, PNG fuente, docs y build
  Pico regenerado. Excluir backups, partidas, logs locales y secretos.
- [x] Entrega `bdcf027` publicada en origin/master el 2026-10-16. El cierre
  documental posterior no cambia el firmware validado ni lo flashea.

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

Ultima entrega, globos y caras: 1292 pruebas Python, 183 nativas, Make Sim
90 frames, Pico regenerado y compilacion ESP32 correctos. RAM estatica
56100/327680, app 1014749/4194304; 219 assets, 11075765 bytes de payload.
Firmware/FS cargados y verificados por digest independiente; reinicio de
18s VPET_READY, heap libre 66572/minimo 66528, FS 11943936/12451840,
manifest 1, BLE conectado y sin fatal. No sustituye aceptacion visual.
[Plan, hashes y limites de evidencia](2026-10-18-mood-bubbles.md).

Entrega anterior, noche/descanso: 1237 pruebas Python, 180 nativas; carga y
verificacion USB correctas, falta noche real. [Evidencia](2026-10-18-sleep-routine.md).

Entrega anterior, tecnicas 2/3/4: 1132 pruebas Python, 175 nativas, Make Sim
y compilacion correctos. RAM 56044/327680, flash 1009965/4194304; 204 assets.
Firmware/FS cargados y digest verificado en ambas particiones; VPET_READY
heap libre 66640/minimo 66564, filesystem 11309056/12451840, manifest 1.
[Plan, hashes y limites de evidencia](2026-10-18-technique-expansion.md).

Los numeros siguientes son cortes anteriores de sprites/cache, no la ultima
carga de tecnicas.

Entrega de sprites: 1077 pruebas Python, firmware/LittleFS verificados en placa.
Heap libre 72504, minimo 72436; filesystem 9404416/12451840; manifest 1.
Arranque final con PAIRED/CONNECTED y VPET_READY, no prueba visual ni sostenida.
La cache se desplego posteriormente el 2026-10-17: heap libre 66660, minimo
66584, mismo filesystem y manifest 1. Falta medir rendimiento en Training.
Validacion local posterior: 1078 pruebas Python aprobadas; firmware con RAM
56028/327680 y flash 1007657/4194304 bytes. Cache ya cargada en placa.

```sh
.venv-platformio/bin/python -m pytest -q
.venv-platformio/bin/pio test -d firmware/t-display -e native
make build-tdisplay
.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay
git diff --check
```

Core nativo cuando cambie dominio. USB requiere autorizacion y verificacion
separadas; su exito no cierra aceptacion visual.
