# Necesidades y animo

Entrega del 2026-10-18. Senales informativas en Home y en la pagina vital
de Status; no cambian balance, Calls, faltas de cuidado ni guardado.

## Reglas portables

`src/core/cues.py` y `vpet/UiCue.h` resuelven la misma prioridad:

1. Lesion: necesita cuidado.
2. Hambre <=20 o Call Hunger: comida.
3. Energia <=20, cansancio de la rutina existente o Call Strength/Lights:
   descanso/apagar la luz.
4. Sin necesidad anterior: tristeza o enojo por animo bajo.

El hambre por si sola no implica enfado. La marca de enojo acompana comida
o descanso solo con animo <50. La cara de Status es triste con lesion;
en los demas casos, enojada con animo <20 o necesidad de comida/descanso
y animo <50; triste con animo <50; neutral entre 50 y 74; feliz desde 75.
Se recalcula al dibujar: resolver una necesidad elimina su globo o muestra
la siguiente. No hay avisos pendientes nuevos ni datos que migrar.

Home muestra un unico globo durante idle/walk. Se oculta en huevo, muerte,
congelacion, viaje, sueno, acciones y paneles. El menu conserva la senal
Call y su parpadeo; solo se retira el antiguo icono inferior derecho de
Home en T-Display. Las ventanas de atencion y penalidades no cambian.

No se implementan preferencias de ambiente, riesgo extra de enfermedad,
longevidad ni reglas de regano de otro juego.

## Motivo de descanso: 2026-10-22

Se separan las dos explicaciones aprobadas de la necesidad Rest existente:

- POCA ENERGIA / LOW ENERGY: gotas de cansancio, energia actual y meta de recuperacion 30/35/40,
  segun el mismo rasgo ADN y la histeresis de cansancio ya vigentes.
- Hora de dormir: solo globo con carita dormida, sin titulo, hora ni etiqueta
  negra. Se elige desde la hora preferida/aprendida hasta las 06:00 cuando
  hay una senal Rest activa.
  Si coincide con poca energia, tiene prioridad el horario de dormir.

Sin calendario valido no se inventa un horario actual. La lectura del
detalle no modifica la rutina ni su latch. Resolver el motivo recalcula
la senal; durante el sueno se oculta, no es un contador de horas dormidas.
Las prioridades de lesion/comida y las supresiones anteriores se conservan.
No cambian hambre, alimentacion, consumibles, efectos, Calls, guardado,
reglas de descanso ni Status. No se agregan contadores de comida ni toasts.

Revision visual solicitada tras la primera vista previa del 2026-10-22:
se sustituyen rayo y bombilla por originales transparentes generados,
`fatigue-drops-v1.png` y `sleepy-face-v1.png`, conservados en assets/ui/mood.
El builder mantiene sus alfa y contornos oscuros; reutiliza el globo y su
marca de enojo existentes. Solo cambian energy/energy_angry/rest/rest_angry;
los otros nueve VPA son byte-identicos. Se mantienen trece iconos en total,
sin framebuffer nuevo ni cambio de escala/cadencia del pet.
[Primera entrega](superpowers/plans/2026-10-22-rest-cue-clarity.md),
[revision vigente](superpowers/plans/2026-10-22-rest-symbols.md).

Para descansar, Rest -> APAGAR LUZ. La siesta diurna dura 30 minutos y
recupera +1 energia cada cinco minutos encendido; pueden necesitarse varias
para alcanzar la meta. De noche aplica la duracion nocturna existente, no
una siesta. ENCENDER LUZ interrumpe; pausar crianza o apagar la placa no
recupera energia. El globo se oculta mientras duerme y se recalcula al
despertar. [Reglas de descanso sin cambios](sleep-routine.md).

## Cuerpo Angry: seguimiento 2026-10-19

Los cuatro originales aportados por el usuario completan la expresion
corporal de Sparkmon, Firemon, Flamemon y Dragfiremon. Se muestran en Home
durante idle/walk cuando la cara existente es Angry y hay una senal no
suprimida: animo <20, o comida/descanso pendientes con animo <50.
Cansancio y acciones explicitas tienen prioridad. Lesion, pausa, viaje,
sueno, huevo o muerte no seleccionan Angry. Recuperar animo o resolver la
necesidad recalcula la expresion, sin un estado nuevo ni otra penalidad.
El globo sigue indicando la causa, no se sustituye por el cuerpo.

Cada hoja conserva sus 25 frames, a 90ms, y usa viewport fijo/anclaje
inferior de 88px; no se agregan enums Motion ni claves de guardado. Status
conserva su retrato anterior y el icono de cara; Pico conserva su flujo
legado aunque empaqueta los originales para reproducibilidad.

Los originales se copian sin repintar a `assets/digimon/digimon1/`, en
`baby/idle/sparkmon_angry.png`, `rookie/idle/firemon_angry.png`,
`champion/idle/flamemon_angry.png` y `ultimate/idle/dragfiremon_angry.png`.
Fuente: sparkmon-angry.png y los tres archivos *-angry-v1.png adjuntos.

Para conservar margen LittleFS se reutiliza el recorte de padding alfa
despues de cuantizar, tambien en animaciones de acciones de Home. Se
mantiene VPA1, su tabla de offsets, paleta, frames y anclaje; no hay
compresion nueva ni reduccion de colores o frames. Idle, happy/sad de
resultados, Training, battle y Status quedan sin recortar. Las pruebas
reconstruyen cada frame recortado a su canvas original y comparan todos
sus bytes RGBA; el renderer real comprueba posiciones y colores.

Paquete final local: 223 assets, 10786603 bytes de payload y 10843912
con manifiesto; margen de presupuesto 12.91% sobre 12451840. El umbral
de preflight sigue en 10%; el overhead real de LittleFS se reporta aparte
en el arranque, no se confunde con bytes de payload.
Preview aislado: `scripts/preview_angry.py`, `out/angry-preview/overview.png`.
La [evidencia de entrega](superpowers/plans/2026-10-19-angry-sprites.md)
separa host, carga USB y aceptacion visual, sin bajar el animo de la partida real.

## Assets y limites

- Originales aprobados en `assets/ui/mood/`: `food-angry-v1.png` y
  `mood-atlas-v1.png`. El atlas contiene happy/neutral/sad y
  angry/globo vacio/marca de enojo. Las fuentes se conservan sin retocar.
- `scripts/mood_assets.py` extrae las celdas, elimina alfa tenue, recorta,
  reduce con vecino cercano y reserva indice transparente 0. Reutiliza
  Carne, luz y medicina del catalogo actual. No descarga assets al jugar.
- El build produce nueve globos 32x28 y cuatro caras 20x20. Pico los
  empaqueta para mantener un artefacto reproducible;
  el overlay nuevo es exclusivo del target T-Display.
- Status conserva exactamente su icono 16x16, barras, valores y cuatro
  paginas. La cara usa alfa real sin descartar su contorno oscuro.
- El globo sigue cabeza/direccion y cambia de lado en los bordes. Nunca
  cambia escala, frames o cadencia del pet. No agrega framebuffer ni cache
  global; los 56.100 bytes de RAM estatica permanecen iguales.
- No se tocan NVS schema 3, snapshots v4, enums persistidos, Training,
  Arena ni las reglas de la rutina de descanso.

## Verificacion

Pruebas de fronteras y prioridad, lectura sin mutaciones, supresion de
necesidades y 1.536 vectores compartidos Python/C++. Harness con
Renderer.cpp, Panels.cpp y AssetStore.cpp reales: colores y transparencia
de los siete globos en izquierda/centro/derecha, caras dentro de su slot
y ocultacion en estados especiales. Tambien comprueba ambos renderizadores
y el alias `status_visible`, para evitar un globo sobre Status.

La regresion de descanso conserva las cuatro especies y los fondos de
dia/noche, agregando el globo de descanso a sus expectativas. La bateria
general mantiene Arena/Training, ES/EN y las cuatro paginas de Status.

`scripts/preview_mood.py` genera `out/mood-bubbles-preview/overview.png`
sin abrir partidas; `scripts/preview_status.py` captura las cuatro paginas
ES/EN. Estos archivos son evidencia local, no una foto ni medida de FPS
de la placa. El [plan de entrega](superpowers/plans/2026-10-18-mood-bubbles.md)
registra pruebas, hashes, respaldo y alcance de la validacion USB.
