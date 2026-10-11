# Sesion de entrenamiento por tandas (simulador)

## Revision vigente: 2026-10-11

**Plan historico, sustituido en el flujo normal.** El usuario aprobo START seguido
de entrenamiento automatico durante 10 segundos y guardado al completar, sin
exigir TRAIN/FINISH ni confirmacion manual del resultado. El contrato actual esta
en [training-session.md](../../training-session.md).

- [x] Flujo temporizado en Python y C++, cancelacion, rollback y reintento.
- [x] Integracion en `make sim` y firmware T-Display.
- [x] Compilacion y despliegue de firmware/recursos el 2026-10-11.
- [x] Pruebas de renderer compartido: 466 comparaciones Training/Tecnicas ES/EN.
- [ ] Aceptacion fisica de la ultima version: sesion completa, cancelar,
  repetir, persistencia tras reinicio y regreso por inactividad.

Los criterios manuales y las restricciones de "solo simulador" de las secciones
siguientes se conservan como historia, no como trabajo a reimplementar.
Seguimiento vigente: [plan de cierre](2026-10-11-delivery-roadmap.md).

## Registro original del 2026-10-07

**Estado:** implementado y verificado en simulador (2026-10-07).
- Suite Python: pasa (`pytest -q`). 84 tests UI del flujo batched + 39 de dominio + 31 de balance + tests de i18n, dos paginas de resultado, barras y extremos.
- `git diff --check`: limpio.
- `sim.py --training` arranca sin errores bajo `SDL_VIDEODRIVER=dummy`.
- Previews reproducibles en `out/practice-preview/training-*.png` (ES + EN + overview bilingue).
- No se toco firmware, NVS, BLE, WiFi ni `out/board-backups/`.
**Alcance de esta entrega:** simulador `make sim`; sin flashear ni conectar a la board.
**Entrada:** icono de la pesa > Entrenamiento.
**Diseno de referencia:** progreso de entrenamiento por sesion de Digimon World, adaptado al pet, controles NEXT/ACTION y pantalla 240x135 de vPet.

## 1. Objetivo y resultado esperado

El jugador selecciona una caracteristica y realiza una o varias repeticiones dentro de una sesion. Durante la sesion puede ver el costo reservado y el resultado proyectado, pero los EV y los stats efectivos no cambian todavia. Al elegir **FINALIZAR**, el sistema aplica de una sola vez el resultado acumulado, guarda y presenta un resumen legible **ANTES / CAMBIO / DESPUES**.

Esto reemplaza la sensacion actual de “presiono y el stat cambia inmediatamente” por un ciclo claro: **elegir > entrenar > revisar > confirmar resultado**. Cada ACTION de entrenamiento representa una repeticion; la cantidad permitida depende del costo real de energia, la elegibilidad y el EV restante hasta el tope.

## 2. Principios y reglas de producto

- La fuente de reglas es el dominio compartido en `src/core/`; la interfaz no duplica formulas ni inventa ganancias.
- Se entrenan los seis atributos existentes: HP, MP, OFF, DEF, SPD y BRN. Se usan nombres/iconos del catalogo actual; presentar OFF como ATAQUE y BRN como MENTE en espanol.
- IV es genetica de nacimiento: esta sesion **nunca cambia IV**. Solo cambia el EV del atributo seleccionado y los efectos secundarios de entrenamiento que el balance aprobado conserve.
- No se agrega nivel de personaje. El entrenamiento no debe otorgar niveles ni alterar hitos/desbloqueos de tecnicas o evolucion salvo que una regla actual ya lo especifique.
- El usuario decide cuando cerrar la sesion. No se aplica automaticamente al llegar a cero energia/tope: la pantalla bloquea nuevas repeticiones y mantiene accesible FINALIZAR.
- Una sesion sin repeticiones no cobra energia, no guarda y no cambia progreso.
- Los costos, gains, limites, elegibilidad y efectos secundarios deben importarse desde el modulo de dominio vigente despues de la tarea de balance; no copiar valores al renderer.
- En esta fase, la sesion pendiente vive en memoria del simulador. Cerrar/terminar el proceso antes de finalizar descarta la tanda completa: no se cobra energia ni se aplican EV. No introducir cambios de esquema NVS ni persistencia de sesion en firmware.

### 2.1 Contrato de repeticion

Al iniciar una sesion se congela el atributo seleccionado y se registra una instantanea de los valores iniciales necesarios para comparar el resultado. Cada repeticion valida las mismas reglas que el entrenamiento actual, consulta el costo y la ganancia canonicos, y solo actualiza el borrador de sesion:

- `reps_completed` aumenta en uno si la repeticion es valida.
- `energy_reserved` acumula el costo; la energia real del pet no se reduce hasta confirmar.
- `pending_ev` acumula EV efectivos aceptados, limitados por `252 - EV_actual`.
- `projected_ev = min(252, EV_actual + pending_ev)`.
- `projected_stat` se calcula con la formula actual de IV+EV. Para HP/MP, la UI muestra el pool derivado, usando la conversion ya definida por el proyecto; no crear otra formula.
- Se computan `max_reps` y el motivo de bloqueo con la menor de estas restricciones: energia disponible / costo, espacio EV / ganancia por repeticion, elegibilidad y cualquier limite de dominio vigente.
- Si el EV restante no alcanza para una repeticion completa, permitir una ultima repeticion parcial solo si `train_attribute`/la regla canonica admite ganancias parciales. Si no las admite, mostrar bloqueo por tope y no cobrar costo. Es decision obligatoria de MiniMax: primero inspeccionar las reglas actuales y escribir una prueba que fije el comportamiento; no descartar EV silenciosamente.
- No contar como mejora de stat un cambio proyectado que la formula entera todavia no produce. Mostrar `EV +n` y `STAT =` si se acumula progreso sin cruzar umbral.

Al confirmar se recalcula/valida contra el estado actual para evitar aplicar un borrador obsoleto, se carga el costo total una sola vez, se aplica el EV agregado y los secundarios aprobados una vez por repeticion, y se guarda una vez. Si guardar falla, rollback completo en memoria y persistencia o mecanismo atomico equivalente; dejar al usuario reintentar sin duplicar. Si el adaptador save no ofrece rollback, MiniMax debe anadir una transaccion/test en el limite del dominio antes de conectar el flujo.

### 2.2 Significado de energia en la interfaz

- Antes de la sesion: `ENERGIA 32/100` (valor real).
- Durante la sesion: `DISP 8 | RES 24` (disponible real menos reserva, y reserva acumulada). `DISP` es lo que queda para esta tanda; no aparentar que se debitó permanentemente.
- En resumen, el cambio de energia refleja exactamente el costo confirmado: `32 -> 8` si las reglas aplican ese costo.
- Si el pet cambia de estado, se invalida o el save falla durante la tanda, no se deben aplicar solo partes de la transaccion.

## 3. Flujo e interaccion

### Mapeo de controles

- **NEXT (toque):** avanza al siguiente elemento enfocable de la pantalla actual.
- **ACTION (toque):** activa el elemento enfocado. En la pantalla de atributos elige atributo/inicia la tanda; en la tanda ejecuta una repeticion o finaliza segun el foco; en confirmacion confirma/descarta; en resultado sale.
- **BACK:** vuelve una pantalla si no existe progreso pendiente. Con progreso pendiente abre confirmacion `CONTINUAR / DESCARTAR`. La salida por long-press ya existente no debe robar eventos de NEXT/ACTION ni cerrar la tanda inadvertidamente.
- Las acciones de botones deben ser por flanco/debounce ya existente (un toque = una accion). Repeticiones rapidas permitidas solo tras terminar la animacion; mantener pulsado no debe disparar una salida ni multiples gastos no visibles.

### Estado A: Elegir atributo

El jugador recorre los seis atributos con NEXT. En cada uno puede inspeccionar su valor actual, EV, proyeccion de una repeticion, costo y maximo de repeticiones. ACTION abre la configuracion de tanda para ese atributo. Atributos inelegibles siguen visibles, pero con bloqueo explicado; no ocultar opciones.

### Estado B: Preparar tanda

Muestra el atributo confirmado, actual vs. proyectado por repeticion, energia actual, costo unitario, EV actual/tope y `MAX n REP`. NEXT alterna entre `INICIAR` y `VOLVER`; ACTION ejecuta. Si no cabe ninguna repeticion, `INICIAR` aparece deshabilitado y el mensaje explica si falta energia, se alcanzo el tope o el pet no es apto.

### Estado C: Sesion activa

Cada ACTION con foco en `ENTRENAR` agrega exactamente una repeticion al borrador y activa una animacion corta/reproducible del sprite segun `TRAINING_TYPES[stat].animation`. Mientras anima, bloquear otra repeticion para evitar doble input. Mostrar siempre el valor real sin cambio y el proyectado en paralelo, ademas de energia disponible/reservada y contador de repeticiones.

NEXT mueve el foco entre `ENTRENAR` y `FINALIZAR`; ACTION activa el foco. Una vez sin repeticiones validas, `ENTRENAR` se deshabilita, `FINALIZAR` permanece seleccionable y el mensaje informa el motivo. Tras FINALIZAR con al menos una repeticion, abrir confirmacion con resumen compacto; ACTION confirma, NEXT cambia a cancelar/seguir, BACK vuelve a la tanda.

### Estado D: Resultado

Solo aparece despues de guardar correctamente. Tabla de cambios `ANTES | CAMBIO | AHORA` para stat/pool relevante, EV, energia y secundarios que hayan cambiado y formen parte del balance aprobado. Presentar `GUARDADO` con icono. ACTION o BACK retorna al selector de atributos. No mostrar un falso `+1` en stat si solo aumentaron EV.

### Estado E: Cancelacion/error

- Si `reps_completed == 0`, BACK vuelve sin confirmacion.
- Si hay repeticiones, confirmacion explicita: `SE PERDERAN n REP / DESCARTAR / SEGUIR`. Por seguridad, `SEGUIR` esta enfocado por defecto.
- En error de guardado, mensaje persistente `NO SE GUARDO`; opciones `REINTENTAR` y `DESCARTAR`. Nada de cobrar energia/aplicar EV antes del guardado exitoso. Retry es idempotente.

## 4. Wireframes 240x135

Wireframes de contenido, no coordenadas finales. Texto e iconos tienen que caber en 240x135; usar fuente pequena del simulador, valores abreviados consistentes y reservar bandas. No superponer sprite/texto. Los iconos deben venir de `practice_icons.py` o assets existentes, con nombres accesibles/textuales en tests; no reemplazar por emoji Unicode.

### 4.1 Selector de atributo

```text
 0         1         2         3         4         5
[HP]      [MP]      [ATK]     [DEF]     [SPD]     [MIND]
--------------------------------------------------------
        FIREMON       [sprite idle]
 VIDA / HP                    84 > 86 (+2)
 EV 18/252                    +6 EV / REP
 ENE 32/100                  MAX 4 REP
--------------------------------------------------------
       NEXT: ATRIBUTO             ACTION: ELEGIR
```

El selector puede ser carrusel de iconos como los menus actuales, pero debe dejar claro el atributo enfocado con borde/indicador y nombre escrito. `84 > 86` es ejemplo; derivar la cifra. Mostrar `EV -> EV` si el atributo no cruza umbral de stat.

### 4.2 Preparar tanda

```text
 [icono pesa] ENTRENAR: DEFENSA
 FIREMON [sprite listo]       DEF 13 > 14
 EV 18/252       +6 EV por repeticion
 ENERGIA 32/100  COSTO 8 x REP
 MAXIMO: 4 REPETICIONES
 [A] INICIAR       [ ] VOLVER
```

Todos los ejemplos de costo/gain son ilustrativos; sustituirlos por las reglas aprobadas por el balance.

### 4.3 Sesion activa (sin repeticiones y con repeticiones)

```text
 [icono pesa] SESION 2/4       DEFENSA
 [sprite haciendo ejercicio]
 DEF REAL 13       PROYECTADO 13
 EV 18 + 12 -> 30 / 252
 ENE DISP 16       RESERVA 16
 REPETICIONES 2/4
 [A] ENTRENAR       [>] FINALIZAR
```

Cuando una repeticion cruce el umbral, `PROYECTADO` refleja el nuevo valor; si no, mantenerlo igual y enfatizar EV pendiente. Durante la animacion mantener el texto estable y mostrar un indicador/progreso pixelado. Al agotarse la energia/tope:

```text
 [icono pesa] SESION COMPLETA  DEFENSA
 DEF REAL 13       PROYECTADO 14
 EV 18 + 24 -> 42 / 252
 ENE DISP 0        RESERVA 32
 REPETICIONES 4/4
 LIMITE: SIN ENERGIA
 [ ] ENTRENAR (bloqueado) [A] FINALIZAR
```

### 4.4 Confirmacion

```text
         CERRAR ENTRENAMIENTO?
         DEFENSA  x4 REP
         DEF 13 -> 14
         EV +24   ENE -32
 [A] CONFIRMAR       [>] SEGUIR
```

Confirmar nunca se asume por salir del menu. En el hardware las letras se sustituyen por indicador de foco; en simulador, mostrar NEXT/ACTION igual que los demas paneles.

### 4.5 Resultado guardado

```text
 [check] ENTRENAMIENTO GUARDADO
                ANTES  +CAMBIO  AHORA
 DEF             13      +1       14
 EV              18      +24      42
 ENERGIA         32      -32       0
 ESFUERZO        20       +8      28
 [sprite contento]                 [A] CONTINUAR
```

Filas de ESFUERZO/animo/peso aparecen unicamente si los efectos y unidades por repeticion se conservan en el balance final. Nunca inventar secundarios por UI. Si no hay cambio numerico de stat, usar `DEF 13 | EV +24` y no fabricar `+1`.

### 4.6 Descartar y error

```text
     DESCARTAR 3 REPETICIONES?
  No se cobrara energia ni cambiaran EV.
 [A] SEGUIR ENTRENANDO  [>] DESCARTAR
```

```text
       NO SE GUARDO
   Ningun cambio fue aplicado.
 [A] REINTENTAR         [>] DESCARTAR
```

## 5. Iconografia y jerarquia UX

- Reusar pesa para encabezado/actividad; usar el icono del atributo junto al nombre y valor. En una pantalla chica, icono **y** etiqueta textual siempre, no icono solo.
- Amarillo = foco/accion primaria; verde/cian = ganancia/proyeccion; rojo = bloqueado/error/cancelacion destructiva; gris = estado deshabilitado. Mantener paleta y estilo pixel-art del simulador existente.
- `REAL` y `PROYECTADO` deben distinguirse visualmente, no solo por color: etiquetas cortas explicitas y filas separadas.
- Barras de energia pueden complementar el numero, nunca reemplazarlo. La barra debe reflejar DISP y una marca/segmento distinto para RESERVA.
- En las pantallas de rutina no llenar el area con paneles decorativos; priorizar pet, stat elegido y progreso. Evitar que el sprite cubra valores.
- Mensajes breves y concretos: `SIN ENERGIA`, `EV AL MAXIMO`, `PET NO APTO`, `GUARDANDO`, `NO SE GUARDO`. El motivo tiene lugar fijo y no empuja el layout.

## 6. Contratos tecnicos y limites

- Mantener `TRAINING_TYPES`, `training_values`, elegibilidad y catalogo de balance como fuente canonica; ampliar helpers en `src/core/training.py` (o submodulo domain apropiado) para preview puro, max reps, borrador, finalize/cancel si el equipo lo estima adecuado.
- `TrainingSession` es orquestacion/UI; no debe tener formulas de EV/costos independientes del core. Mantener el guardado atraves de la interfaz que usa hoy el simulador y evitar escrituras por repeticion.
- Mantener el esquema actual de saves y compatibilidad NVS. No agregar claves NVS, migraciones, Wi-Fi, BLE ni cambios en firmware por esta historia.
- Mantener la seccion de lecciones de tecnicas accesible desde la pesa y sin interferir con la sesion de stats. Volver desde lecciones no debe finalizar/descartar silenciosamente una tanda pendiente.
- La animacion es visual y temporal, no cambia resultado determinista. El preview puede inyectar `now_ms`; no depender del reloj real para reglas.
- Aplicar pausa de crianza durante pantallas/sesion solo si el flujo actual ya la aplica; no iniciar tick adicional ni cronometro de entrenamiento accidental.

## 7. Pruebas requeridas

### Dominio / transaccion

1. Abrir tanda y ejecutar 1..N repeticiones no cambia pet real, EV, IV, stat, energia, animo, peso, esfuerzo ni save antes de confirmar.
2. Confirmar agrega exacto el costo y los EV efectivos; efectos secundarios coinciden con el numero de repeticiones segun balance final; persiste una sola vez.
3. Cancelar/descartar deja el pet y el save byte/logicamente iguales al estado inicial.
4. Energia insuficiente bloquea rep adicional, no deja saldo negativo y conserva FINALIZAR activo.
5. EV en 252 no permite ganancia; al acercarse al tope aplica politica parcial/completa definida en prueba, sin exceder 252 ni cobrar repeticion rechazada.
6. `projected_stat` usa IV existentes sin modificarlos; umbral entero EV=6 se refleja exactamente. HP/MP respetan conversiones y no curan HP actual por aumentar maximo.
7. Guardado antiguo sin nuevos campos continua cargando y no se agregan campos persistentes para el borrador.
8. Falla de save no produce cobro/gain; reintento exitoso aplica una vez; segundo ACTION no duplica.
9. Estados no aptos (egg/baby segun reglas actuales, dead, injured, cold u otras) producen bloqueo explicable en UI y core.
10. La mezcla de otros cambios de estado mientras la sesion esta abierta no debe permitir double-spend. Documentar y probar si el simulador pausa las demas acciones; como minimo revalidar antes de commit.

### Control / UI

1. NEXT recorre opciones en orden, wrap definido; ACTION tiene significado consistente; BACK no descarta pendientes.
2. Un evento de boton equivale a una sola repeticion; input durante animacion no duplica.
3. Probar todas las seis stats, mensajes de tope/energia/no apto, 0 repeticiones, 1 repeticion, max repeticiones y save fail/retry.
4. Pruebas de renderer/captura a 240x135 verifican no-overlap, bounds y textos reales por pantalla; longitud extrema/numeros maximos incluidos.
5. Capturar previews deterministas para selector, preparacion, tanda en progreso, tope, confirmacion, resultado, cancelacion/error y entrenamiento por tecnica.
6. Fijar reloj/edad en tests de render/serializacion; nada de flakiness por segundos monotonicos.

## 8. Plan de implementacion MiniMax

**Prerequisito:** cerrar el balance de entrenamiento en curso, ejecutar sus tests y tomar su tabla aprobada como unica fuente de costos y efectos. No mezclar balance inacabado con UI.

1. Escribir/ajustar tests del contrato de sesion y politica EV al tope antes del renderer.
2. Implementar preview puro y calculo max reps en core; no cambiar IV, formula combat_stat ni valores de save.
3. Implementar borrador `TrainingSession` con input/estados/foco, cancelacion, confirmacion y save transaccional/idempotente.
4. Implementar pantallas renderer 240x135 reusando iconos/sprite helpers; fijar coordenadas y testear contenido bounds/no overlap.
5. Integrar desde la pesa sin romper Tecnicas, HOME/BACK ni input debounce; confirmar una repeticion por toque.
6. Generar previews reproducibles y ajustar jerarquia tras inspeccion visual de todos los estados.
7. Actualizar docs de training/estado/arquitectura y resumen de balance con el flujo, politica de borrador y evidencia. No editar assets/build generados a mano.
8. Ejecutar al menos `.venv-platformio/bin/python -m pytest tests/test_training.py tests/test_practice_ui.py -q`, suite completa `.venv-platformio/bin/python -m pytest -q`, `make sim-training` y `git diff --check`. Si hay cambios C++/firmware, no forman parte de esta historia; pedir decision antes de ampliar alcance.
9. Reportar pruebas y rutas de previews. **No flashear, desplegar ni probar fisicamente**; dejar la board intacta.

## 9. Criterios de aceptacion PO

- El usuario puede recorrer los seis atributos claramente y sabe exactamente cual eligio.
- Una ACTION de entrenamiento produce una sola repeticion y feedback/animacion; NEXT no consume energia.
- Antes de finalizar no cambian stat/EV/energia reales ni save; la UI etiqueta actual vs. proyectado y reserva.
- Finalizar pide confirmacion y presenta Antes/Cambio/Ahora solo despues de un save exitoso.
- Descartar y errores no cobran ni duplican nada; MP/HP derivado, IV/EV, topes y saves se mantienen compatibles.
- Todo texto/indicador cabe en la pantalla 240x135, con icono y etiqueta, y previews/test demuestran los estados limites.
- Unitarias y suite completa pasan; `make sim-training` abre/genera el flujo de entrenamiento actualizado.
- No hay cambios de firmware/board ni despliegue fisico.

## 10. Implementacion (2026-10-07)

### 10.1 Dominio (`src/core/training.py`)

- `training_index_for(stat)` mapea stat name → index de `TRAINING_TYPES`.
- `batch_block_reason(pet, stat)` retorna `""` si la rep es elegible o el
  motivo canonico (`TIPO INVALIDO`, `PET NO APTO`, `EV AL MAXIMO`,
  `FALTA ENERGIA`). Esta funcion es la unica fuente de verdad para
  bloqueo de reps en estados A y B.
- `batch_max_reps(pet, stat)` retorna `(n, reason)`. `n` es el minimo
  entre `floor(energia / TRAINING_ENERGY_COST)` y
  `ceil(headroom / TRAINING_EV_GAIN)`. Cuando headroom < gain, el
  rep parcial esta permitido (cabe 1 rep con gain = headroom) y NO se
  permiten reps con gain = 0.
- `batch_plan_one_rep(pet, stat)` describe la proxima rep sin mutar:
  `ev_added = min(TRAINING_EV_GAIN, headroom)`, costo y secundarios.
- `batch_projected_value(pet, stat, ev_delta)` retorna `(current,
  projected)` aplicando la conversion pool de HP/MP (`40 + cs*2` /
  `10 + cs`) y la formula `combat_stat` para los demas. Es la unica
  fuente del `(ANTES, AHORA)` en la pantalla D.
- `batch_apply(pet, stat, reps)` aplica `reps` sesiones con costo y
  secundarios calculados una vez; el ultimo rep puede ser parcial.
- `batch_commit(pet, stat, reps, save)` es la transaccion atomica:
  captura `pet.to_dict()`, llama `batch_apply`, y si `save` retorna
  falsy restaura con `pet.load_from_dict(snapshot)` y lanza
  `BatchSaveError`. La unica forma de doble cobro es que el
  orquestador llame `batch_commit` dos veces; los tests pin que se
  llama una vez por confirmacion.
- `BatchSaveError` se lanza desde `batch_commit`; el orquestador la
  captura y abre estado E (error) con retry idempotente.

Politica EV al tope: partial last-rep allowed (gain = headroom cuando
headroom < TRAINING_EV_GAIN), zero-gain reps bloqueadas cuando
`cumulative (real ev + pending_ev) >= 252`.

`train_menu` ya no toca `pet.stats["p"]`: la felicidad la sigue
aplicando `apply_action(2) = ACTION_EFFECTS[2] = {"p": +15}` y
agregarla tambien duplicaria el efecto (66 vs 65 esperado por
`test_training_menu_applies_training_and_starts_punch_animation`).

### 10.2 Orquestador (`scripts/training_session.py`)

- Estados: `SELECT`, `PREPARE`, `SESSION` (con sub-estados `confirm`
  y `cancel`), `RESULT`, `ERROR`. Cada estado expone los focos
  validos para NEXT/ACTION/BACK.
- `TrainingSession.input(event, now_ms) -> bool` mantiene el contrato
  que consume `sim.py`; el handler dispatcha por estado y por foco.
- `busy()` retorna True durante 1500 ms despues de una rep; bloquea
  solo ACTION con foco `train` en `SESSION`. NEXT nunca se bloquea.
- Foco en `SESSION`:
  - `train` por defecto al entrar.
  - NEXT alterna `train` ↔ `finalize`.
  - ACTION con foco `train` llama `batch_plan_one_rep`; si `can`,
    avanza `reps` y `pending_ev`; si no, abre estado E si la razon es
    save-fail, sino solo marca bloqueo visual.
  - ACTION con foco `finalize` abre `SESSION.confirm` sub-estado.
- `SESSION.confirm`:
  - Foco `confirm` por defecto al entrar.
  - ACTION `confirm` llama `batch_commit` una sola vez; exito abre
    `RESULT`, fallo abre `ERROR` con snapshot pre-apply disponible
    para retry.
  - NEXT alterna `confirm` ↔ `follow` (donde `follow` = volver a
    `SESSION` sin cobrar).
- `SESSION.cancel` (sub-estado):
  - Solo se abre desde BACK en `SESSION` con `reps > 0`.
  - Foco `follow` por defecto (CONTINUAR), `discard` con NEXT.
  - ACTION `discard` llama `_reset_full` y vuelve a `SELECT`.
- `SELECT`:
  - NEXT cicla entre los 6 stats en `MENU_TRAIN_STATS` + `TRAINING_TYPES`
    (HP, MP, OFF, DEF, SPD, BRN) con wrap.
  - ACTION `start` valida `batch_block_reason`; si pasa, abre
    `PREPARE` con `_chosen_stat` congelado.
  - BACK vuelve a la pesa.
- `PREPARE`:
  - Foco `start` (INICIAR) por defecto, `back` (VOLVER) con NEXT.
  - ACTION `start` abre `SESSION`.
  - BACK vuelve a `SELECT` (sin perdida porque no hubo progreso).
- `RESULT`:
  - Muestra `ANTES | CAMBIO | AHORA` solo donde el delta no es 0;
    usa `batch_projected_value` para derivar el pool antes/despues
    y nunca inventa `+1 stat` cuando solo aumento EV.
  - ACTION `continue` vuelve a `SELECT`.
- `ERROR`:
  - Foco `retry` por defecto, `discard` con NEXT.
  - ACTION `retry` re-llama `batch_commit` con el mismo `reps` y
    `save` callback. Si el segundo intento tiene exito, abre
    `RESULT`; si falla de nuevo, se queda en `ERROR`.
  - ACTION `discard` llama `_reset_full` y vuelve a `SELECT`.

### 10.3 Renderer (`scripts/training_renderer.py`)

- Dispatch por estado a `_render_select`, `_render_prepare`,
  `_render_session`, `_render_confirm`, `_render_cancel`,
  `_render_result`, `_render_error`. Cada uno dibuja bandas claras:
  - Header (y=0..19): icono pesa + label estado + stat activa.
  - Sprite + datos (y=23..110): pet sprite, valores REAL/PROYECTADO,
    ENE DISP/RES, EV +n / 252, contador de reps.
  - Action buttons (y=115..132): dos icon-buttons NEXT/ACTION con
    label de foco.
- Reusa `pet_sprite`, `info_icon`, `info_label`, `icon_button`, `text`
  de `scripts/practice_renderer.py`. No inventa iconos; usa el catalogo
  existente (HP/MP/OFF/DEF/SPD/BRN + check + alert).
- En `RESULT` la tabla ANTES/CAMBIO/AHORA pinta solo filas con delta
  no-cero; el renderer lee `batch_projected_value` directamente y no
  recalcula formulas.
- Las pruebas deterministas congelan `time.monotonic` via
  `monkeypatch` para que la edad del pet y los offsets de animacion
  no generen flake.

### 10.4 Tests

- `tests/test_batched_training.py` (39 tests): contrato transaccional,
  politica EV al tope, `batch_block_reason` para los 6 stats,
  `batch_max_reps` y partial-last-rep, `batch_plan_one_rep` no muta,
  `batch_projected_value` y conversiones HP/MP, `batch_commit`
  exito/rollback/doble-rollback, `BatchSaveError`, idempotencia de
  retry, snapshot pre-apply, cero EV ganancia cuando pending ya
  >= 252.
- `tests/test_batched_training_ui.py` (57 tests): bounds 240x135
  para cada estado, no overlap entre header/sprite/botones, NEXT
  cicla con wrap, ACTION respeta foco, BACK con/sin progreso,
  congelar tiempo para edad, no repeticion durante animacion,
  `RESULT` solo pinta filas con delta, retry idempotente, los 6
  atributos cubiertos (HP/MP/OFF/DEF/SPD/BRN).
- `tests/test_balance_sim.py` (31 simulaciones): reproduce el
  balance v1 con el dominio real y compara contra la tabla
  aprobada.
- `tests/test_training.py` y `tests/test_practice_ui.py` actualizados
  al nuevo flujo A→B→C→confirm; el test legacy
  `test_care_and_items_gain_ev` se ajusto al balance v1
  (`off +1` por menu training, no `+2` legacy). El test
  `test_training_menu_applies_training_and_starts_punch_animation`
  sigue pasando porque `train_menu` ya no duplica la felicidad de
  `apply_action(2) = {"p": +15}`.
- Suite completa: `pytest -q` → **443 passed** en 48.75 s.
- `git diff --check`: limpio.

### 10.5 Previews reproducibles (`scripts/preview_practice.py`)

Genera 12 PNGs en `out/practice-preview/`:

- `training-select.png`, `training-select-def.png`: estado A,
  atributo ATAQUE y DEFENSA respectivamente.
- `training-prepare.png`: estado B con INICIAR enfocado.
- `training-session.png`: estado C, 2/4 reps, sprite activo.
- `training-session-cap.png`: estado C en tope (4/4 + LIMITE).
- `training-confirm.png`: sub-estado `confirm` de SESSION.
- `training-result.png`: estado D con tabla ANTES/CAMBIO/AHORA.
- `training-result-legacy.png`: comparativa de la pantalla vieja
  de dumbbell para no-regresion visual.
- `training-cancel.png`: sub-estado `cancel` (DESCARTAR x rep).
- `training-error.png`: estado E (NO SE GUARDO, REINTENTAR).
- `training-overview.png` y `training-batched-overview.png`:
  composicion 4x2 con los 8 estados canonicos del flujo nuevo.

### 10.6 Decisiones de producto registradas

- **Atomicidad via snapshot**: `batch_commit` usa `pet.to_dict()` /
  `pet.load_from_dict()` en lugar de operaciones inversas calculadas
  porque la unidad de rollback debe ser la misma que la unidad de
  save (migracion de campos, defaults, etc).
- **No zero-gain reps**: cuando `pending_ev + real_ev >= 252`, la
  proxima rep se bloquea. Decisin pinneada en
  `test_training_cap_invalid_input_and_no_repeat_during_animation`.
- **Bloqueo solo en `train`**: `busy()` solo bloquea ACTION con foco
  `train`; NEXT, `finalize` y demas siguen respondiendo. Asi el
  jugador puede finalizar una tanda aunque la animacion no haya
  terminado.
- **Felicidad no doble-cobrada**: `apply_action(2) = {"p": +15}` ya
  carga la felicidad; `train_menu` solo agrega `effort+2`,
  `training_sessions+1`, `menu_train_sessions+1` y resta 3 ENE.
- **BACK con progreso abre cancel, BACK sin progreso vuelve a
  select**: politica explicita para no perder trabajo accidental y
  no pedir confirmacion innecesaria.

### 10.7 Salidas de evidencia

- Plan: este archivo.
- Status: `docs/project-status.md` (entrada "Balance de entrenamiento
  v1" + entrada "Sesion por tandas 2026-10-07" debajo).
- Previews: `out/practice-preview/training-*.png` (12 archivos).
- Codigo: `src/core/training.py`, `src/core/menu.py`,
  `src/core/pet.py`, `scripts/training_session.py`,
  `scripts/training_renderer.py`, `scripts/preview_practice.py`.
- Tests: `tests/test_batched_training.py`,
  `tests/test_batched_training_ui.py`, `tests/test_balance_sim.py`,
  `tests/test_training.py`, `tests/test_practice_ui.py`,
  `tests/test_dna.py` (legacy ajustado), `tests/test_menu.py`
  (sin cambios, ya alineado con v1).
- Suite: 443/443 pasan. `git diff --check` limpio.
- `sim.py --training` arranca sin errores.

## 11. Localizacion y resultado navegable (2026-10-07)

### 11.1 Catalogo i18n (`src/core/i18n.py`)

- Constante `TRAINING_STRINGS` (ES/EN) y `STAT_STRINGS` (ES/EN). Todos
  los pares son no-vacios; cualquier string nuevo que se agregue al
  renderer sin entrada en ambos idiomas rompe el test
  `test_i18n_every_used_key_is_bilingual`.
- `tr(pet, key, *args)` resuelve la key segun `pet.language`; cualquier
  valor fuera de `("ES", "EN")` cae a `DEFAULT_LANGUAGE = "ES"`. Esto
  preserva la lectura del proyecto legacy cuando el campo `language`
  esta ausente.
- `tr_stat(pet, stat)` devuelve el nombre a mostrar del stat (ATAQUE
  / ATTACK, MENTE / MIND, etc.). El routing sigue usando el nombre
  canonico del stat (`off`, `def`, `brn`).
- El renderer no embebe strings visibles. `test_renderer_has_no_hardcoded_user_facing_strings`
  fija la lista de tokens prohibidos (espanol legacy). Cada uno debe
  pasar por `tr()`.

### 11.2 Estado D con dos paginas navegables

- `STATE_RESULT` ahora tiene `_result_page` que alterna entre
  `RESULT_PAGE_SUMMARY` (default) y `RESULT_PAGE_STATS`.
- NEXT toggle de pagina; ACTION / BACK vuelven al selector y resetean
  `_result_page = "summary"`.
- `RESULT_PAGE_SUMMARY` mantiene la tabla compacta de hasta cuatro
  filas (stat / EV / ENE / ESF) con ANTES | +CAMBIO | AHORA; el
  renderer solo pinta la columna delta cuando el delta no es 0 (no
  se inventa `+1 stat` cuando solo subio EV).
- `RESULT_PAGE_STATS` pinta una cuadricula de 6 filas con barras
  compactas:
  - Escala documentada: `_stat_bar_width(ev) = round(ev / 252 * 96)`
    pixeles (96 px de ancho maximo, cap 252 EV, clamp a [0, 96]).
  - La stat entrenada se resalta con barra amarilla + label amarillo +
    delta en amarillo; las demas usan MUTED outline + GREEN fill.
  - Filas sin delta muestran solo el valor actual en gris (no se
    fabrica delta).
  - Indicador de pagina `RESUMEN | STATS` arriba a la derecha; la
    pagina activa va en amarillo, la otra en gris.
  - Distribucion vertical: y=40 + i*12 (i=0..5) → ultima fila en
    y=100, con boton `CONTINUAR` (o `CONTINUE`) en y=115. No
    solapamiento.
- `RESULT_PAGE_SUMMARY` y `RESULT_PAGE_STATS` comparten el mismo
  boton `CONTINUAR` / `CONTINUE` (estado D no tiene foco entre
  opciones, solo NEXT/ACTION/BACK). El NEXT nunca avanza el state
  machine, solo flipea la pagina.

### 11.3 Tests adicionales

- `test_i18n_tr_returns_spanish_for_spanish_pet` / `_english_` /
  `_falls_back_to_spanish_for_unknown_language`.
- `test_i18n_tr_supports_string_format_arguments` (verifica `%d`).
- `test_i18n_missing_key_raises` (catalogo es explicito: olvidar una
  key rompe el test, no la pantalla).
- `test_i18n_every_used_key_is_bilingual` (regex con word boundary
  para que `getattr(` no matchee `tr(`).
- `test_renderer_has_no_hardcoded_user_facing_strings` (lista negra
  de tokens).
- `test_result_default_page_is_summary` /
  `test_next_in_result_toggles_page` /
  `test_action_in_result_returns_to_select_from_summary` /
  `_from_stats` / `test_back_in_result_returns_to_select`.
- `test_result_summary_paints_within_bounds` /
  `test_result_stats_paints_within_bounds` (texto + bounds).
- `test_result_stats_renders_all_six_attributes` (verifica que cada
  uno de los 6 stats aparece como label de fila).
- `test_result_summary_no_text_overlap` /
  `test_result_stats_no_text_overlap` (helper de cajas).
- `test_stat_bar_width_clamps_to_zero_and_cap` /
  `test_stat_bar_width_is_monotone`.
- `test_result_stats_handles_extreme_ev` parametrizado 0/50/252.
- `test_result_summary_with_zero_deltas_does_not_show_fake_deltas`.
- `test_result_in_spanish_uses_es_strings` /
  `test_result_in_english_uses_en_strings` (chequea tokens
  `ANTES`/`AHORA`/`BEFORE`/`AFTER`).
- `test_next_on_result_does_not_advance_state` (NEXT solo flipea la
  pagina, no avanza el state machine).
- `test_input_pipeline_freeze_time_for_result_pages` (la edad del
  pet es estable entre paginas).

### 11.4 Previews bilingues (`scripts/preview_practice.py`)

- 16 PNGs nuevos en `out/practice-preview/`:
  `training-{select,select-def,prepare,session,session-cap,confirm,result,result-stats}-{es,en}.png`.
- `training-bilingual-overview.png`: 8x2 grid con ES arriba y EN
  abajo, 1920x540 px.
- Para que las barras del STATS page se vean utiles, el preview
  refleja el EV post-apply en el pet (`pet.ev[stat] = ev_added`,
  `pet.e["e"] -= energy_charged`, `pet.effort += effort_added`)
  antes de capturar. El renderer no muta nada durante un render.
- Las pruebas deterministas congelan `time.monotonic` via
  `monkeypatch` para que la edad del pet y los offsets de animacion
  no generen flake.

### 11.5 Decisiones de producto registradas

- **Stat names en resultado**: la pagina SUMMARY muestra el nombre
  localizado (ATAQUE / ATTACK). La pagina STATS trunca a 4 caracteres
  (ATAQ / ATTA) para caber en 240 px.
- **Barras con escala 252**: el cap canonico se usa como denominador
  para que las barras sean comparables entre stats y entre tandas
  de diferentes longitudes.
- **Solo el stat entrenado se resalta en amarillo**: las otras 5
  barras usan MUTED outline + GREEN fill para mantener la jerarquia
  visual sin gritar todo.
- **Indicador bilingue arriba a la derecha** en vez de tabs o
  paginas completas: cabe en 4 px de alto, no requiere hardware de
  navegacion nuevo, y la accion NEXT esta ya documentada.
- **Fallback ES para lenguajes no soportados**: cualquier valor que
  no sea `"EN"` cae a `"ES"`. Esto preserva el comportamiento legacy
  del proyecto y evita que un campo corrupto deje la UI en blanco.
