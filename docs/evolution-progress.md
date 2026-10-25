# Detalle De Progreso Evolutivo

Diseno aprobado por el usuario el 2026-10-23. Implementado para simulador
T-Display y firmware; carga y aceptacion fisica de esta revision pendientes.
No cambia reglas de evolucion, guardado, ADN, premios ni paginas de Status.

## Flujo Y Significado

El arbol mantiene sus cinco etapas y oculta las futuras. ACTION sobre una
etapa descubierta abre su ficha. La etapa actual muestra los requisitos
para evolucionar DESDE ella, no los que sirvieron para alcanzarla.

- Sprite ampliado de 36 a 64 px y nombre completo; fondo oscuro y tinta clara.
- Hasta cuatro requisitos por pagina; NEXT cambia pagina sin cambiar etapa.
- ACTION/BACK regresa al mismo nodo del arbol. Cada entrada comienza en 1.
- Tiempo restante en horas/minutos, o <1m cuando queda menos de un minuto;
  no muestra segundos acumulados. El valor se redondea hacia arriba.
- Valores actuales frente a objetivo para comida, energia, animo, salud,
  combates y porcentaje de victorias. Peso muestra el intervalo permitido;
  errores de cuidado muestran un maximo, no una meta que alcanzar.
- Check para cumplido, cuadro vacio para pendiente y barra por condicion;
  no se inventa un porcentaje total de evolucion entre requisitos distintos.
- Etapas pasadas: ETAPA SUPERADA; futura: POR DESCUBRIR; huevo:
  ECLOSIONANDO; ultima: ETAPA FINAL. No mezclar barras actuales con una
  etapa pasada ni inventar requisitos para despues de la forma final.

Los indicadores son de solo lectura. Cumplirlos no fuerza un guardado ni
salta las protecciones de sueno, viaje, pausa o actividad del loop existente.

## Contrato Y Fuentes

Python: `src/core/evolution_progress.py` consume EVOLUTION_REGISTRY de
`src/config.py`. C++: `EvolutionProgress.h` consume Evolution::ruleFor.
Ambos producen filas tipadas, valores/objetivos, cumplimiento y paginas.
No reutilizan writeReachRequirements, que describe el sentido contrario.

El runtime Python YA contiene peso 8..14 para Firemon, igual que C++.
rookie.json y los catalogos generados no declaran todos esos campos; esa
duplicacion sigue siendo deuda para la modularidad, no una regla cambiada
por esta ficha. Las pruebas comparan las condiciones de ambos runtimes.

Time scale explicita: placa 1; el simulador interactivo pasa CARE_TIME_SCALE
600 para mostrar la espera real acelerada. Las previews por defecto usan 1
para representar la placa. No confundir 12h10 de requisito con espera real
del simulador. 0/0 W/L conserva el criterio existente del motor; se muestra
-- / 60% sin inventar porcentaje cuando no hay partidas registradas.

`EvolutionUi.h` dibuja sobre el framebuffer actual y reutiliza las fuentes
bitmap generadas para Training. Panels solo adapta el retrato existente y
el dibujo. No hay PNG/VPA nuevos ni tercer framebuffer. El escalado reserva
temporalmente el mismo scratch de 36x36 que admite AssetStore; no un atlas
completo. No se edita arte ni se modifica la cache de Training.

La pagina es estado transitorio de Navigation, no un enum nuevo ni clave
NVS. App calcula el numero de paginas desde las filas; el sim codifica
etapa+5*pagina en su indice transitorio y restaura la etapa al salir.

## Verificacion Reproducible

```sh
.venv-platformio/bin/python -m pytest -q tests/test_evolution_progress.py tests/test_evolution_progress_pixels.py
.venv-platformio/bin/python scripts/preview_evolution_progress.py
```

Las pruebas cubren fronteras de edad/peso/cuidado, ratio acumulado separado
de combates por etapa, escala temporal, no mutacion y paginacion en App real
sin escrituras de partida. El harness usa Panels.cpp/AssetStore.cpp reales
y raster de fuentes de produccion: 56 comparaciones de detalle ES/EN sin
diferencias de pixeles bajo la barra superior, mas 240 vectores de modelo.
La barra superior conserva la geometria de cada renderer, fuera de esa
comparacion. La galeria agrega 18 vistas ES/EN, todas con diferencia cero
en el detalle; no es una fotografia de la placa.

Salida local: `out/evolution-progress/gallery.png`, imagenes individuales
`01-ES-firmware.png` / `02-ES-firmware.png` para las dos paginas Firemon,
`firemon-pages.png` para verlas ampliadas y `report.json`. No abre ni
modifica la partida del usuario.

Suite completa: 1653 Python aprobadas en 340.54 s; 185 nativas en 7.99 s;
compilacion ESP32 aprobada, RAM estatica 56116 y app 1017761 bytes. Segunda
pasada focalizada de modelo/render/App: 51 aprobadas en 15.12 s. Se mantienen
advertencias existentes de herramientas; no son evidencia de placa.

Inspeccion fisica pendiente: legibilidad a 240x135, color y escala del
retrato, NEXT en ambas paginas, vuelta al mismo nodo y refresco del tiempo.
La validacion pendiente de Status no queda aceptada por estas pruebas.
El [plan de entrega](superpowers/plans/2026-10-23-evolution-progress.md)
conserva resultados de suites y compilacion cuando se ejecutan.
