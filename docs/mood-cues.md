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
longevidad ni reglas de regano de otro juego. Tampoco se inventa una nueva
animacion corporal Angry: la expresion actual usa los iconos aprobados.

## Assets y limites

- Originales aprobados en `assets/ui/mood/`: `food-angry-v1.png` y
  `mood-atlas-v1.png`. El atlas contiene happy/neutral/sad y
  angry/globo vacio/marca de enojo. Las fuentes se conservan sin retocar.
- `scripts/mood_assets.py` extrae las celdas, elimina alfa tenue, recorta,
  reduce con vecino cercano y reserva indice transparente 0. Reutiliza
  Carne, luz y medicina del catalogo actual. No descarga assets al jugar.
- El build produce siete globos 32x28 y cuatro caras 20x20, 11.477 bytes
  VPA en total. Pico los empaqueta para mantener un artefacto reproducible;
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
