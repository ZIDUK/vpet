# Alimentacion, peso, combate y evolucion: plan de implementacion

> **For agentic workers:** Ejecutar tarea por tarea con la skill `executing-plans` o `subagent-driven-development`, revisando los cambios existentes antes de editar. Los pasos usan checkboxes para registrar evidencia, no intencion.

**Goal:** Hacer que Alimentar tenga exactamente dos alimentos ilimitados, carne y proteina, con animacion de crianza y peso que afecte combate y evolucion. Los demas objetos de mejora de stats pertenecen a la mochila.

**Architecture:** Reglas deterministas en Python y `vpet_core` C++, verificadas con los mismos vectores. Mantener stats base separados de modificadores de condicion y aplicar una transaccion de alimentacion desde cualquier entrada. La UI consume resultados del dominio; no calcula hambre, peso o recompensas.

**Tech Stack:** Python, pytest, Pillow/pygame, C++ portable, PlatformIO native, ESP32 Arduino, TFT_eSPI, LittleFS y NVS.

Fecha: 2026-10-14. Estado: **implementacion integrada; Python validado (554 tests), chequeo sintactico C++ correcto; runner PlatformIO y aceptacion fisica pendientes**.
El usuario aprobo el concepto y solicito este plan despues de la evaluacion de impacto.
Las cifras de la seccion de balance son una **propuesta inicial para validar**, no resultados medidos ni cifras heredadas de Digimon World.

Correccion del usuario: **Alimentar solo contiene carne y proteina ilimitadas**. Filete, champinon y otros objetos se destinan a mejorar stats desde la mochila. Esta decision reemplaza la propuesta anterior de cuatro comidas en Alimentar.

## Restricciones globales

- Implementacion activa: `firmware/t-display/`, pantalla 240x135. Mantener paridad con el simulador T-Display.
- Dominio sin Arduino, TFT, NimBLE, reloj de pared ni acceso directo a archivos.
- Preservar IDs de especies, acciones, objetos existentes y enums persistidos. No reutilizar el indice actual de BACK como ID de un alimento.
- Mantener lectura de partidas NVS schema 1/2/3. Los datos nuevos requieren version propia, validacion y valores por defecto.
- Regenerar `build-tdisplay/`, catalogos generados y LittleFS; no editarlos a mano.
- No borrar `out/board-backups/`, reiniciar la mascota ni cambiar DNA/IV para introducir la funcion.
- Respetar el reparto de dominio/UI de `AGENTS.md`. Antes de ejecutar, coordinar archivos compartidos con Mavis/Cursor mediante el flujo autorizado; no enviar mensajes a otros chats por iniciativa propia.
- No incorporar cambios ajenos en commits. Al escribir este plan habia cambios de Training, AssetStore, App y documentacion sin commit.
- Las decisiones de dibujo y posiciones pertenecen a renderers/tests de Codex. Este documento fija comportamiento, datos y criterios de aceptacion.
- No ralentizar sprites, FPS, botones ni animaciones para representar una penalizacion de velocidad.
- Validar antes de desplegar y cumplir las precondiciones de Status de `AGENTS.md`. Un build o un log de arranque no acredita inspeccion fisica.

## 1. Alcance aprobado y limites

Se implementa:

1. Alimentar abre una seleccion de exactamente dos alimentos: carne y proteina, ambos ilimitados desde el primer uso. Toda comida aceptada reproduce el acto de comer del pet actual.
2. Alimentacion y entrenamiento modifican peso; peso bajo reduce fuerza/resistencia y exceso de peso reduce velocidad, con limites moderados.
3. El peso interviene en una transicion existente y se expone como requisito legible. No se inventan especies ni ramas jugables sin assets/reglas.
4. Filete, champinon y otros objetos de mejora de stats pertenecen a la mochila. Sus magnitudes, stats objetivo y fuentes deben definirse en su propio trabajo de catalogo; no son opciones de Alimentar ni una dependencia para lanzar sus dos alimentos.
5. La mochila conserva recuperacion y otros consumibles existentes. Carne/proteina se administran desde Alimentar; retirar sus entradas de uso duplicadas en la mochila y preservar las claves antiguas por compatibilidad.

No forma parte de este corte crear exploracion, HP/MP persistentes de combate, tienda, PvP, nuevas especies o una mecanica de esquiva. La practica actual no tiene evasion: no mostrar un fallo de ataque ficticio. La velocidad efectiva cambiara el orden de ataque; una futura evasion requerira su propia regla y pruebas.

## 2. Hallazgos que la implementacion debe corregir

| Superficie actual | Evidencia en el repositorio | Consecuencia |
|---|---|---|
| Alimentar desde Home | `src/core/pet.py::feed` usa +25 HAM; `PetState.cpp::applyFeed(false)` usa +20 HAM y +5 ENE | Unificar efectos, no copiar solo una pantalla |
| Peso de comida | La comida normal de Home no suma peso; carne de inventario y sobrealimentar si | Centralizar la accion |
| Crecimiento gratis | Alimentar da +2 EV HP; proteina de inventario da +2 EV OFF | Al hacer suministro ilimitado, retirar EV de comida futura y conservar EV ya ganados |
| Proteina antigua | `applyProtein`/`use_protein` incrementan contadores y DP; el combate clasico penaliza ese contador | Separar el alimento nuevo de esa regla de sobredosis; no llamar sin mas a la funcion antigua |
| Entrenamiento | Resta 1 de peso por repeticion y puede llegar a 0 | Balancear perdida y evitar peso negativo o diferencias entre lote/individual |
| Metabolismo | No hay perdida de peso por consumo natural de alimento | Sin una regla compensatoria, comer normalmente produce sobrepeso con el tiempo |
| Combate | Practica usa OFF/DEF/SPD; combate clasico usa probabilidad y contadores | Cubrir ambas rutas activas sin convertir practica en victorias oficiales |
| Evolucion | Linea unica Sparkmon -> Firemon -> Flamemon -> Dragfiremon; no hay peso en `EvolutionRule` | Agregar un requisito acotado y mantener el resto de criterios |
| Persistencia | `SettingsStore::save` escribe claves una a una | El booleano de save no garantiza atomicidad ante corte de corriente |
| Origen de objetos | Solo existe el kit inicial; exploracion es documento | No anunciar botin de rutas como si ya se entregara |

Revisar estos hechos al ejecutar: describen el checkout observado el 2026-10-14, no una fotografia inmutable.

## 3. Propuesta de balance v1

### Alimentos y suministro

HAM representa saciedad: 0 = vacio, 100 = lleno. ENE sigue siendo energia de crianza/entrenamiento, no MP del combate. Fuerza de combate sigue siendo OFF; no crear otra barra de fuerza con el mismo nombre que energia.

| ID de alimento | Nombre ES / EN | Efecto por uso aceptado | Suministro | Condicion |
|---|---|---|---|---|
| `meat` | Carne / Meat | +20 HAM, +1 peso | Ilimitado, sin stock ni descuento | Pet vivo, despierto y disponible; sobrealimentacion regulada abajo |
| `protein` | Proteina / Protein | +20 ENE, +2 peso | Ilimitado, sin stock ni descuento | ENE <= 80; maximo una toma por ciclo metabolico |

Todos: uso en casa, efecto inmediato, sin EV/IV ni HP/MP de batalla. Proteina apoya entrenar al recuperar ENE; la fuerza permanente viene del entrenamiento. No otorga DP ni alimenta el contador antiguo de sobredosis. Mantener campos antiguos para lectura/historial; en la version nueva dejar de aplicar su penalizacion de combate. Incluir este cambio de balance explicitamente en la entrega.

Carne permite una toma de sobrealimentacion cuando HAM > 80: suma solo la saciedad que falta, +1 peso y +1 al contador de exceso. Bloquear otra toma de exceso hasta el siguiente ciclo metabolico. Reiniciar el ciclo cuando se hayan gastado 20 HAM reales, no al bajar de 100 a 99. Esto cierra el bucle de comer cada tick para sumar peso o progreso.

Ilimitado significa que no hay inventario que agotar; las condiciones de uso por saciedad, energia y ciclo son propuestas de balance y no cantidades de stock. Una accion bloqueada no da efecto ni ejecuta animacion de exito. Volver es un control de navegacion, no un tercer alimento.

### Objetos de mejora de stats: trabajo separado de mochila

Filete (`sirloin`) y champinon (`mushroom`) pasan a la familia de mejoras de stats. Se retiran de este plan sus efectos de hambre/peso, el stack 9, el kit inicial 1/1 y la asignacion a Patio: esos numeros pertenecian a la propuesta descartada de comidas especiales.

Antes de implementar esos objetos en la mochila:

- [ ] Definir para cada uno el stat objetivo y si el efecto es temporal, permanente o una mejora del entrenamiento. El usuario aprobo su finalidad, no una cantidad concreta de EV ni una duracion.
- [ ] Completar las 12 columnas del estandar de catalogo, incluidos efecto, magnitud, topes, stock y forma real de obtenerlo.
- [ ] Reconciliar una eventual mejora permanente directa con la politica del catalogo que favorece mejoras de entrenamiento; no asumir que esta aclaracion aprueba EV ilimitados.
- [ ] Implementar efectos, iconos y persistencia desde mochila con pruebas de consumo unico y limites, como entrega independiente.

La implementacion de Alimentar se completa sin estos objetos y se prueba aunque la mochila este vacia. Sus efectos siguen por definir; no presentarlos como implementados ni como sustitutos de carne/proteina.

### Condicion de peso

Unidades de juego, sin afirmar equivalencia biologica a kilogramos.

| Etapa | Peso de referencia | Zona saludable inclusiva |
|---|---:|---:|
| Sparkmon | 5 | 4-6 |
| Firemon | 10 | 8-12 |
| Flamemon | 20 | 16-24 |
| Dragfiremon | 35 | 28-42 |

Huevo: sin modificadores ni alimentacion. Peso jugable limitado a 1..99. Calculo entero identico en Python/C++:

```python
ratio = (100 * weight + reference // 2) // reference
low_penalty = min(15, (max(0, 80 - ratio) + 1) // 2)
high_penalty = min(20, (max(0, ratio - 120) + 1) // 2)
# OFF y DEF usan low_penalty; SPD usa high_penalty. HP, MP, BRN intactos.
effective = max(1, (base * (100 - penalty) + 50) // 100)
```

Ejemplos con Firemon y stat base 50: peso 10 -> OFF/DEF/SPD 50; peso 6 -> OFF/DEF 45, SPD 50; peso 14 -> OFF/DEF 50, SPD 45. No hay bonificacion ilimitada por engordar ni ventaja extra de velocidad por estar desnutrido.

El modificador no escribe DNA/EV ni sobrescribe el stat base. Capturar stats efectivos al empezar una pelea, no recalcular por cada frame.

### Ciclo de peso y entrenamiento

- Cada 20 puntos de HAM perdidos realmente por metabolismo: peso -1, hasta minimo 1; reabrir toma de proteina y sobrealimentacion. Guardar el resto 0..19.
- No contar HAM que ya estaba en 0, restauraciones, compras ni cambios de UI como gasto metabolico. Sin aplicar bajadas retroactivas por tiempo offline en este corte.
- Carne normal compensa esa perdida: una comida completa por ciclo debe mantener el peso aproximadamente estable sin entrenamiento.
- Entrenamiento: peso -1 por cada 4 repeticiones completadas, resto 0..3 persistido. Cancelar no consume resto ni cambia peso. Lotes y repeticiones individuales equivalentes.
- Conservamos costes y EV del entrenamiento; recalcular solo su efecto secundario de peso y su previsualizacion.
- Verificar que un pet bajo de peso puede recuperarse con carne/proteina sin depender de objetos de mochila ni entrar en un bloqueo circular por saciedad, energia o evolucion.
- Inyectar tiempo de cuidado para probar ambos runtimes. El sim tiene aceleraciones y un decay distinto al firmware: medir balance con reloj explicito de placa, no con segundos de pared del sim.

### Evolucion y partidas existentes

- Firemon -> Flamemon: agregar rango de origen 8..14, ademas de edad, HAM/ENE/animo/salud actuales. Sparkmon -> Firemon y Flamemon -> Dragfiremon no agregan candado de peso en v1.
- Consultar el peso antes de evolucionar. Al completar una evolucion, escalar peso al cuerpo nuevo manteniendo proporcion: `new = clamp((old * new_ref + old_ref // 2) // old_ref, 1, 99)`. Firemon 10 -> Flamemon 20; Firemon 14 -> Flamemon 28, sin borrar sobrepeso.
- Mantener fuerza/debug como bypass de requisitos, con la misma transformacion de peso. Restaurar una partida no es evolucionar y no debe reescalar nada.
- Para guardados anteriores al sistema, propuesta de transicion: una sola vez ajustar peso a la frontera saludable mas cercana de su etapa y conservar peso anterior en metadatos de migracion. Ejemplo: Flamemon legacy con peso 5 -> 16, sin tocar su especie, EV, DNA ni victorias. No volver a normalizar en cargas siguientes.
- Registrar y probar este ajuste de peso como parte explicita de la migracion propuesta. Mantener la regla junto a la version de nutricion para que cargar dos veces produzca exactamente el mismo resultado.
- Preservar las claves y cantidades antiguas de carne/proteina para compatibilidad, sin mostrarlas ni consumirlas en Alimentar. El suministro es ilimitado desde el primer uso y no consulta esos stocks. Sus usos futuros siguen la tabla nueva sin EV; los EV ya ganados se conservan.
- `energy`, `exp`, `ring`, `medkit` conservan sus efectos actuales en este corte. Su migracion a recuperacion pura seria otro cambio; el catalogo debe mostrarlo claramente.

## 4. Mapa de trabajo

| Area | Archivos existentes a revisar/editar | Nuevos previstos |
|---|---|---|
| Reglas nutricion y peso | `src/core/pet.py`, `src/core/training.py`, `firmware/t-display/lib/vpet_core/src/vpet/PetState.{h,cpp}`, `TrainingSession.h` en ese mismo directorio | `src/core/nutrition.py`, `firmware/t-display/lib/vpet_core/src/vpet/Nutrition.{h,cpp}` |
| Persistencia | `Pet.to_dict/load_from_dict` en `src/core/pet.py`, `src/core/save.py`, `scripts/sim_services.py`, `firmware/t-display/lib/vpet_core/src/vpet/SettingsStore.{h,cpp}` | Registro versionado de nutricion y diario de transaccion en los adaptadores existentes |
| Alimentar y mochila | `src/core/menu.py`, `src/core/inventory.py`, `scripts/sim.py`, `firmware/t-display/src/App.cpp`, `firmware/t-display/include/vpet/App.h`, `firmware/t-display/lib/vpet_core/src/vpet/Navigation.{h,cpp}` | `scripts/feeding_session.py`, `firmware/t-display/lib/vpet_core/src/vpet/FeedingSession.h` |
| Presentacion | `scripts/sim_renderer.py`, `scripts/training_renderer.py`, `firmware/t-display/src/Panels.cpp`, `firmware/t-display/include/vpet/Panels.h`, `src/core/status_card.py`, `src/core/i18n.py` | `scripts/feeding_renderer.py`; layout y harness decididos por Codex |
| Combate | `scripts/practice_session.py`, `src/core/practice.py`, `firmware/t-display/lib/vpet_core/src/vpet/PracticeSession.h`, `PracticeBattle.h`, `src/core/pet.py`, `PetState.cpp` | API de stats efectivos en Pet y funcion de ajuste de probabilidad clasica |
| Evolucion | `src/core/evolution.py`, `src/config.py`, `src/data/digimon/rookie.json`, `scripts/tdisplay_assets.py`, `firmware/t-display/lib/vpet_core/src/vpet/Evolution.{h,cpp}` | Campos opcionales de rango de peso en reglas |
| Assets | `scripts/item_icons.py`, `scripts/build.py`, `scripts/tdisplay_assets.py` | Reutilizar iconos de carne/proteina; regenerar salida solo si cambia su integracion |
| Pruebas | Suites actuales de inventory, menu, training, balance, practice, evolution, settings y paridad de pixels | `tests/test_nutrition.py`, `tests/test_nutrition_parity.py`, `tests/nutrition_trace.cpp`, `tests/test_feeding_session.py`, `tests/test_nutrition_persistence.py`, test nativo de nutricion |

Contratos nuevos previstos (nombres de funciones elegidos por este plan):

```text
Python core.nutrition:
  body_condition(species, weight) -> dict(reference, ratio, off_penalty, def_penalty, spd_penalty)
  effective_stat(base, penalty) -> int
  food_preview(pet, food_id, available=True, asleep=False) -> dict(allowed, reason, hunger_after, energy_after, weight_after)
  apply_food(pet, food_id, available=True, asleep=False) -> dict(applied, reason, changed_fields)
  consume_hunger(pet, lost_points) -> None
  complete_training_weight(pet, repetitions) -> int  # delta de peso real
  evolved_weight(from_species, to_species, weight) -> int

Pet: effective_combat_stat(stat) -> int; combat_stat(stat) conserva su significado base.
C++: BodyCondition, FoodPreview, FoodResult y funciones homonimas en camelCase;
     PetState::effectiveCombatStat(CombatStat) devuelve el valor efectivo.
```

`food_preview` no muta; `apply_food` vuelve a validar y solo lo invoca el controlador transaccional al confirmar. Solo admite los IDs `meat` y `protein`. Reasons estables: `ok`, `egg`, `dead`, `asleep`, `busy`, `full`, `overfeed_used`, `protein_cycle`, `invalid_food`. Los adaptadores pasan disponibilidad/sueno; no introducir dependencia de Motion en la formula numerica.

## 5. Secuencia de implementacion

### Evidencia de cierre de esta pasada (2026-10-14)

- Python completo: `554 passed`; incluye alimentacion, combate, evolucion,
  status, inventario, assets y guardado atomico del simulador.
- `SettingsStore.cpp` y `Nutrition.cpp` pasan `c++ -std=c++11 -fsyntax-only`.
- El test nativo de NVS incluye un fallo parcial y verifica recuperacion
  idempotente del journal `foodTx`; aun falta ejecutar el runner PlatformIO.
- PlatformIO se detuvo antes de compilar: no puede crear
  `~/.platformio/platforms.lock` por permisos del home. No se modificaron
  permisos globales ni se flasheo.
- La pagina Status enseña peso actual y el rango saludable de su etapa; el tile
  del backpack usa fondo oscuro para no parecer seleccionado.
- Pendiente de balance/catalogo: definir stat objetivo, magnitud, topes y origen
  de filete/champinon antes de implementar sus efectos en la mochila.
- Pendiente de placa: build final, captura/validacion de las cuatro paginas de
  Status y comprobacion tras reinicio antes de cualquier despliegue.

### Tarea 1: fijar baseline y contrato de balance

- [ ] Leer `AGENTS.md`, `git status --short` y diffs de los archivos compartidos; registrar el HEAD y el trabajo previo sin modificarlo.
- [ ] Revalidar las rutas ejecutadas por Home, alimentar, practica, batalla clasica y evolucion; marcar como legacy el `src/core/battle.py` si sigue sin ser una entrada activa. No ampliar un motor sin consumidores.
- [ ] Crear los vectores numericos de la seccion 3 en `tests/test_nutrition.py`, separados de tests de UI. Mantener los parametros juntos en `core.nutrition` y su tabla espejo C++.
- [ ] Registrar las cifras como version de balance 1 y ejecutar simulaciones para aceptarlas o corregirlas en este documento. El concepto esta aprobado; los numeros se cierran con evidencia.

Ejemplo de test de contrato a crear:

```python
from core.nutrition import body_condition, effective_stat

def test_overweight_affects_speed_without_granting_attack():
    c = body_condition("rookie", 14)
    assert c["spd_penalty"] == 10
    assert c["off_penalty"] == 0
    assert effective_stat(50, c["spd_penalty"]) == 45
```

Ejecutar `.venv-platformio/bin/python -m pytest tests/test_nutrition.py -q` antes de implementar para confirmar que falta el contrato y luego para verificarlo. No tratar fallos previos de otras tareas como propios ni borrar sus tests.

Salida: tabla numerica y expectativas concretas listas para revisar; no integrar comida ilimitada hasta cerrar sus efectos.

### Tarea 2: implementar condicion corporal y ciclo de peso

- [ ] Crear `src/core/nutrition.py` y `vpet/Nutrition.{h,cpp}` con las tablas, calculos enteros y los contratos anteriores, sin I/O.
- [ ] Integrar gasto real de HAM y contador metabolico en los ticks; limitar peso a 1..99 para pets vivos.
- [ ] Inicializar peso 5 al eclosionar y el peso de referencia al crear una fixture de una etapa viva. El constructor de una partida nueva, el debug y la carga legacy siguen caminos distintos y probados.
- [ ] Sustituir descuento de peso por repeticion en las rutas de entrenamiento por el contador de cuatro repeticiones. Calcular preview y resumen con el delta real, incluso cuando el limite impide bajar mas.
- [ ] Incluir esos contadores en snapshot/rollback de `TrainingSession` y `scripts/training_session.py` para que cancelar o fallar al guardar no cambie el siguiente entrenamiento.
- [ ] Agregar `effective_combat_stat`/`effectiveCombatStat`; mantener `combat_stat`/`combatStat` base para DNA, EV y proyecciones.
- [ ] Crear `tests/nutrition_trace.cpp` y `tests/test_nutrition_parity.py`, siguiendo el harness compilado de `tests/test_practice.py`. Comparar tablas, pesos 1..99, etapas vivas, stats base 1/50/99 y redondeos.
- [ ] Probar equivalencia de cuatro repeticiones individuales frente a lote, cancelacion en la cuarta y recuperacion de peso desde el minimo.

Salida: mismas formulas y mismo ciclo en Python/C++, sin penalizaciones aplicadas por el renderer.

### Tarea 3: guardar y migrar sin reiniciar al pet

- [ ] Agregar estado de nutricion versionado: peso previo de migracion, resto metabolico 0..19, resto de entrenamiento 0..3, disponibilidad de proteina y version de balance. No agregar stocks al sistema Alimentar.
- [ ] Cargar valores nuevos ausentes sin entregar objetos adicionales. Leer y preservar stocks antiguos por sus claves originales, sin conectarlos a disponibilidad ni consumo de carne/proteina.
- [ ] Implementar la migracion de peso una sola vez. Validar valores antes de convertir a `uint8_t`, para que -1 o 300 no se conviertan silenciosamente en pesos validos distintos.
- [ ] Separar restauracion, eclosion y evolucion real; `SettingsStore::load` y `Pet.load_from_dict` nunca deben activar la transformacion de peso de evolucion.
- [ ] Implementar un diario de comida en una clave NVS nueva, escrita con `putString`: version, ID transaccion y valores finales absolutos de todos los campos modificados. Serializacion estricta con longitud, tipos y limites validados; reutilizar parser estructurado disponible en el adaptador, sin dependencias de plataforma en dominio.
- [ ] Orden de commit: validar y preparar resultado -> guardar diario -> aplicar estado final -> guardar campos afectados -> limpiar diario. Si falla antes del diario, no aplicar; si falla despues, bloquear otra comida y reintentar ese mismo estado final. Al arrancar, recuperar el diario antes de ticks/entradas/evolucion. Nunca volver a sumar deltas al recuperar.
- [ ] Aplicar el mismo protocolo al guardado del sim mediante su adaptador. No afirmar atomicidad solo porque `save()` devuelve bool.
- [ ] Probar cortes/fallos en cada frontera, doble confirmacion, diario invalido, NVS 1/2/3, reinicio, park/swap y nueva vida. El registro de nutricion tiene que viajar con la mascota al aparcarla.
- [ ] Verificar invariantes: misma especie, DNA, EV, historial de victorias y tecnicas; stocks existentes intactos al alimentar; migracion repetida no vuelve a ajustar peso. Comprobar tolerancia de lectura antigua y documentar que volver a ejecutar un firmware antiguo no garantiza preservar reglas nuevas.

Salida: partidas existentes utilizables y consumo de comida recuperable, sin reset ni duplicacion tras reinicio. El diario cubre alimentacion; no promete transacciones globales de todas las funciones del juego.

### Tarea 4: comida unica y separacion del inventario

- [ ] Implementar preview/validacion/efecto segun la tabla. Retirar EV de usos futuros de carne/proteina y la ganancia de DP/sobredosis de la proteina nueva. Mantener EV acumulados.
- [ ] Modificar `src/core/menu.py`, `Pet.feed`, `PetState::completeAction` y los manejadores de inventario para que ninguna ruta antigua siga aplicando efectos por su cuenta.
- [ ] Dejar exactamente carne/proteina en la seleccion Alimentar, conservando sus claves/stock legacy sin consumo. Mantener un mapa explicito entre ID de objeto y seleccion UI: BACK no es un objeto persistido.
- [ ] Probar que filete, champinon y cualquier otro ID se rechazan como alimento y no aparecen en ese menu. La disponibilidad de las dos opciones es independiente del stock de la mochila.
- [ ] Implementar controlador de alimentacion con estados seleccionar, animar, completar/error. Confirmar aplica una sola transaccion; ignorar ACTION repetido durante la animacion y revalidar al confirmar.
- [ ] Home abre el flujo Alimentar; retirar el uso directo duplicado de carne/proteina en mochila. Volver cancela antes del commit; una vez confirmada la comida no se revierte por cambiar de pantalla.
- [ ] Probar 100 intentos de comida/proteina: cero EV nuevos sin entrenamiento, limites de saciedad/energia/peso respetados, uso de proteina bloqueado hasta nuevo ciclo y ausencia de curacion de lesiones/HP/MP encubierta.

Salida: exactamente dos alimentos ilimitados, efectos claros y una sola animacion de crianza por uso aceptado.

### Tarea 5: aplicar peso al combate

- [ ] Cambiar creacion de Fighter en `scripts/practice_session.py` y `vpet/PracticeSession.h` para usar stats efectivos capturados al inicio. Los rivales sin perfil de peso se consideran neutrales, no se les atribuye peso 0.
- [ ] Mantener formulas de dano, Guardia y seleccion de tecnica; OFF/DEF efectivos entran al calculo existente, SPD efectiva al orden de golpes. Mantener duracion de ronda y FPS.
- [ ] En `finish_battle`/`resolveBattle`, usar la condicion para una deduccion acotada de probabilidad: `condition_penalty = (off_penalty + def_penalty + spd_penalty + 2) // 3`; restarla a la probabilidad base, con sus limites 15..90. Eliminar la penalizacion antigua de sobredosis para la nueva version de nutricion, incluida la lesion por victoria asociada a ese contador.
- [ ] Mantener costes de batalla, registro de victorias y lesiones de derrota. Practica sigue sin aumentar contadores oficiales de evolucion.
- [ ] Comparar trazas Python/C++ con mismo pet, rival, stats base y peso: neutral conserva la mecanica base; exceso puede invertir iniciativa; bajo peso puede reducir dano y aumentar dano recibido; volver al rango sano recupera stats efectivos sin entrenar otra vez.
- [ ] Adaptar casos de sobredosis antigua para que prueben explicitamente la nueva politica versionada, sin borrar cobertura de derrotas/lesiones.

Salida: efectos comprobados en las dos rutas activas; UI puede explicar base, modificador y efectivo sin falsos cambios permanentes.

### Tarea 6: requisito y cambio de peso al evolucionar

- [ ] Agregar campos opcionales `min_weight`/`max_weight` en la regla Python y equivalentes en `EvolutionRule`. Ausentes significa sin condicion, para conservar contratos de otras reglas.
- [ ] Aplicar Firemon -> Flamemon 8..14; mantener edad, barras y cuidados. Sin candado extra para las otras dos transiciones.
- [ ] Sincronizar `src/config.py`, el JSON de rookie, `Evolution.cpp` y el catalogo emitido por `scripts/tdisplay_assets.py`. Probar consistencia para no mostrar un requisito distinto del que evalua la placa.
- [ ] Evaluar requisito antes de transformar peso; realizar transformacion una vez al evolucionar, incluido debug. Limpiar restos metabolico/entrenamiento y abrir toma de proteina para la etapa nueva, dejando peso proporcional.
- [ ] Exponer la razon de bloqueo por peso y el rango en la consulta de evolucion incluso para una forma futura oculta. El nombre/sprite pueden permanecer ocultos; el requisito de cuidado no debe ser inaccesible.
- [ ] Probar pesos 7/8/14/15, todos los demas requisitos individualmente, debug, guardar/cargar tras evolucion y evolucion desde sobrepeso sin convertirlo automaticamente en peso ideal.

Salida: un requisito jugable y recuperable, sin ramas inventadas ni transformacion repetida en load.

### Tarea 7: integrar experiencia y assets en sim/placa

- [ ] Conectar controlador nuevo en `scripts/sim.py` y `firmware/t-display/src/App.cpp`; agregar panel sin renumerar enums existentes.
- [ ] Implementar presentacion bajo Codex: carne/proteina, suministro ilimitado, efectos reales y motivo de bloqueo. No mostrar contadores de stock en Alimentar. Usar un unico idioma ES/EN y distinguir ENE de MP, OFF de energia.
- [ ] Mostrar peso/rango y penalizacion relevante en consulta de estado/combate, manteniendo las cuatro paginas de Status y contratos consumidos por renderers. El detalle visual se fija en codigo y tests de layout.
- [ ] Seleccionar animacion de comer por especie actual en Sparkmon, Firemon, Flamemon y Dragfiremon; verificar que el fallback sea de esa especie si falta una pose.
- [ ] Reutilizar los iconos de carne/proteina del pipeline existente y regenerar BMP/VPA si cambia su integracion. Validar que se cargan en placa, no solo en el simulador.
- [ ] BACK conserva el contenido al enfocar el icono y sale al confirmar; no crea una pagina vacia. Inactividad 10 s en seleccion, pausada durante la animacion/commit activo y contada de nuevo al terminar.
- [ ] Verificar NEXT de 20 pulsaciones y pulsacion mantenida, sin eventos en cola. Comparar fluidez con Home, sin volver a abrir archivos/decodificar atlas completo por frame.
- [ ] Capturar casos ES/EN con mochila vacia y stocks legacy 0/1/99, extremos de peso, saciedad completa, proteina bloqueada, guardado fallido y cuatro especies. Alimentar siempre muestra las mismas dos opciones ilimitadas. Reusar metodologia de paridad de `tests/test_training_pixel_parity.py` para el nuevo flujo.

Salida: las mismas acciones, datos, sprites y controles en simulador y dispositivo.

### Tarea 8: validar balance, documentar y entregar

- [ ] Ampliar `tests/test_balance_sim.py` con escenarios deterministas por etapa: 24 h de cuidado normal sin entrenar, carne repetida, exceso repetido, entrenamiento intensivo con proteina y recuperacion de peso bajo. No usar timers acelerados del sim como si fueran tiempo de placa.
- [ ] Criterios: carne a cada 20 HAM gastados mantiene peso en +/-1 del inicio; ninguna comida concede EV; los modificadores respetan topes; bajar de peso no da SPD superior al base; se puede salir de bajo peso/sobrepeso mediante acciones disponibles sin objetos especiales obligatorios.
- [ ] Medir sesiones de entrenamiento posibles por hora antes/despues, energia obtenida por comida/proteina/reposo, frecuencia de alimentacion y tiempo de recuperacion de peso. Registrar resultados y modificar parametros si el cuidado exige acciones excesivas o anula reposo/entrenamiento. No presentar cifras propuestas como balance validado.
- [ ] Actualizar `docs/items-and-rewards.md`, `docs/training-session.md`, `docs/architecture.md` y las especificaciones de evolucion/catalogo con comportamiento ya comprobado, politica de migracion y excepciones legacy. Documentar filete/champinon como mejoras de stats de mochila cuyo balance e implementacion pertenecen al trabajo separado.
- [ ] Ejecutar validacion completa una vez integrados los cambios y resolver regresiones atribuibles al corte.
- [ ] Revisar diff, preparar commits por entregables comprobables y preservar trabajo ajeno. Push/flash se realizan en la entrega autorizada, con el build actual y los requisitos de placa cumplidos.
- [ ] Tras despliegue, comprobar consumo, reinicio, cuatro paginas de Status, hambre/peso, alimentacion y combate con cada evolucion. Guardar evidencia del build y observacion fisica; no cerrar casillas con solo un log serial.

## 6. Comandos y evidencias

Durante implementacion, las suites nuevas se crean en las tareas anteriores:

```sh
.venv-platformio/bin/python -m pytest tests/test_nutrition.py tests/test_nutrition_parity.py tests/test_feeding_session.py tests/test_nutrition_persistence.py -q
.venv-platformio/bin/python -m pytest tests/test_inventory.py tests/test_menu.py tests/test_training.py tests/test_batched_training.py tests/test_practice.py tests/test_evolution.py tests/test_balance_sim.py -q
.venv-platformio/bin/pio test -d firmware/t-display -e native
```

Integracion final:

```sh
.venv-platformio/bin/python -m pytest -q
make build-tdisplay
.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay
git diff --check
```

Esperado: todas las pruebas aplicables pasan, native y firmware terminan con exito, assets reproducibles y diff sin errores de whitespace. No fijar un numero de tests historico como requisito. Si aparecen errores preexistentes, registrar su reproduccion y no declarar validacion completa.

La comprobacion de placa usa `make preflight` y posteriormente `make deploy` cuando corresponde la entrega, con la evidencia de Status exigida por `AGENTS.md`. Usar la deteccion del script y, si hay varios dispositivos, el puerto del T-Display identificado. No copiar puertos historicos ni binarios anteriores.

## 7. Orden y criterio de terminado

Dependencias: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8. Los tests de contrato se escriben junto a cada tarea; la UI consume contratos estabilizados. Los iconos pueden prepararse tras fijar el catalogo, sin modificar dominio en paralelo con otro agente.

El corte esta terminado cuando:

- [ ] Alimentar contiene exactamente carne/proteina ilimitadas, funciona con mochila vacia y se anima para todas las evoluciones; muestra efectos reales.
- [ ] Peso puede mantenerse, recuperarse y reducirse con cuidados disponibles; no produce progresion permanente por pulsaciones repetidas.
- [ ] Fuerza/defensa/velocidad efectivas coinciden en sim y core C++; la animacion mantiene su fluidez.
- [ ] El requisito de evolucion coincide con el mostrado y no aparece un bloqueo imposible de resolver.
- [ ] Partidas antiguas conservan progreso y stocks; el ajuste de peso inicial esta documentado y ocurre una sola vez.
- [ ] Interrupcion/reintento no entrega dos efectos; park/swap conserva nutricion y Alimentar nunca descuenta inventario.
- [ ] Filete/champinon estan fuera de Alimentar y documentados como mejoras de stats de mochila; sus cifras y origen no se anuncian como implementados.
- [ ] Pruebas, build y comprobacion visual de placa cuentan con evidencia separada.

## Referencias

- [Roadmap vigente](2026-10-11-delivery-roadmap.md)
- [Catalogo actual de objetos](../../items-and-rewards.md)
- [Estandar de catalogo](../specs/2026-10-14-item-catalog-standard.md)
- [Exploracion y recompensas](../specs/2026-10-11-exploration-design.md)
- [Criterios actuales de evolucion](../specs/2026-09-10-evolution-criteria-design.md)
- [Entrenamiento por lotes](2026-10-07-batched-training-session.md)

Los documentos anteriores describen reglas vigentes o disenos propios. Este plan introduce la migracion futura de alimentacion; no reetiquetar sus propuestas como codigo entregado.
