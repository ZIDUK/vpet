# F1: Definiciones Y Resolucion De Contenido

Estado: fundamento de F1 implementado localmente, 2026-10-23. Sin carga
a placa, instalador externo, roster ni cambios de balance/guardado.

## Fuente Y Generacion

- `src/data/content/firemon.json`: definicion visual builtin de cinco roles,
  con nombres, recursos, frames, intervalos de Home, loops y fallbacks.
  No es el formato publico final `.vpetpack`.
- `src/core/content.py`: `PetDefinition`, resolucion pura por rol/accion/contexto
  y validacion de limites/conflictos de recursos.
- `scripts/content_definitions.py`: genera `content_builtin.py`,
  `BuiltinPet.generated.h`, `rules_builtin.py` y `EvolutionRules.generated.h`.
- `src/data/digimon/baby.json`, `rookie.json`, `champion.json`: unica fuente
  de las tres reglas automaticas para Python, C++ y catalogo. El peso 8..14
  ahora tambien figura en JSON/catalogo, sin cambiar la regla vigente.
- `scripts/build.py`: prepara el arte builtin mediante su adaptador legado
  y agrega `content.json` al intermedio T-Display.
- `scripts/build_tdisplay.py`: empaqueta una definicion validada y arte ya
  preparado, sin rutas de criaturas concretas en sus consumidores.

```sh
.venv-platformio/bin/python scripts/content_definitions.py
.venv-platformio/bin/python scripts/content_definitions.py --check
make build-tdisplay
.venv-platformio/bin/python scripts/content_budget.py firmware/t-display/data/manifest.json
```

Los generados no se editan a mano; el build rechaza generados desactualizados.
La metadata legacy del huevo de 8 s se conserva por compatibilidad; la
eclosion real sigue siendo de 2 s. F1 no cambia esa deuda anterior ni balance.

## Integracion

`Motion` recibe una definicion constante y publica esa referencia a Renderer;
frames/intervalos/bucle salen de metadatos. Overrides explicitos conservan
conteos legacy. `Panels`, TrainingUi, ExplorationUi y EvolutionUi reciben la
misma clase de definicion, builtin por defecto. Se resuelven Home, Status,
Training/Tecnicas, Arena, Exploracion y arbol/detalle de Evolucion.

AssetResolver es una responsabilidad de `PetDefinition.clip`, no otra
jerarquia virtual. Las cadencias comunes de herramientas (Training 90/120 ms)
siguen siendo del perfil visual, no del nombre de criatura. No se agregan
subclases por pet, framebuffer, red ni heap por frame. SpeciesId mantiene
sus valores y adapta los roles actuales, no identifica futuros individuos.

Las alternativas se inyectan al construir los consumidores. El mismo binario
nativo prueba dos tablas; no hay seleccion persistida ni carga/activacion
de definiciones externas en ESP32. Arte alternativo exige destinos de build
separados, no reemplazar el payload builtin del firmware normal. Eso es F5.

## Validacion

Rechaza perfiles/roles no soportados, caminos con escape, frames fuera de
1..64, intervalos fuera de 10..1000 ms, loops invalidos, fallbacks ciclicos,
claves JSON duplicadas, documentos mayores de 64 KiB y salidas incompatibles
con el mismo nombre. Verifica fuente, dimensiones y frames antes de limpiar
generados. Esto no sustituye la futura transaccion de instalacion en board.

Pruebas especificas: 680 resoluciones Python/C++ (dos definiciones, cinco
roles, cuatro contextos, 17 acciones); siete vistas C++ y siete del simulador
con el segundo contenido, sin atlas legacy ni mutacion de partida. El fixture
reutiliza arte existente con nombres/rutas/timing distintos: no es otra especie
comercial con arte independiente. Incluye generacion reproducible, errores,
preservacion de salida anterior y presupuesto de almacenamiento.

```sh
.venv-platformio/bin/python -m pytest -q tests/test_content_definitions.py --basetemp=out/f1-content-evidence
.venv-platformio/bin/python -m pytest -q
.venv-platformio/bin/pio test -d firmware/t-display -e native
.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay
```

Los stubs TFT verifican assets/pixeles y registran texto; las fuentes bitmap
de Training/Detalle se rasterizan realmente. No certifican fuentes TFT
fisicas, FPS, radio ni instalacion real. Ver evidencia en el plan F1.

## Presupuesto

Payload medido: 227 assets, 10891653 bytes. Recursos referenciados por la
linea: 10233972 bytes; resto compartido/legacy: 657681. No son uso real ni
espacio libre de LittleFS.

Dos lineas de ese tamano, cuatro registros provisionales de 4 KiB, 128 KiB
de journal, staging de una linea y 10% de reserva requieren 32752237 bytes,
frente a 12451840 de particion: NO cabe. El informe declara que el segundo
arte independiente no esta medido y que 4 KiB por registro es una reserva,
no el tamano de un roster ya serializado.

Cuatro individuos de la misma linea comparten arte. Cuatro lineas diferentes
no son viables con este presupuesto. Falta optimizar/medir almacenamiento y
recuperacion antes de fijar capacidad; no borrar partida ni reformatear.

F4/F5 siguen pendientes: referencias persistidas de paquete/version, stock
compartido con migracion unica, plazas/huevos, indice, emisor, staging/rollback
y Hub USB. Ver [decisiones](product-decisions-2026-10-23.md) y
[paquetes](content-packages.md).
