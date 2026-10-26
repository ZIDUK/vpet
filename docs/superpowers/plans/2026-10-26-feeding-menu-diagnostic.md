# Alimentacion Permanece En FEED: Diagnostico

Fecha: 2026-10-26. Estado: abierto; valores recibidos, intento no capturado.

## Evidencia Del Usuario

IMG_4260 muestra dos individuos y dos plazas libres. El usuario confirma,
tras el recorrido solicitado, conservacion al guardar/reiniciar y stats
individuales con stock compartido al cambiar de mascota. No se infiere
aceptacion de incubacion o breeding a partir de esa confirmacion.

IMG_4262 muestra FEED con MEAT seleccionado. El usuario precisa que ACTION
permanece en el selector en vez de mostrar la animacion. No ha confirmado
si cambia la saciedad. Se pide foto del cuidado y estado actual de Pause Pet;
no se despausa, alimenta ni modifica la partida por el usuario.

## Flujo Inspeccionado

App::handlePanelInput aplica Nutrition::applyFood sobre el estado activo.
Solo Applied mas commit correcto inicia Motion::startAction(Feed) y Home.
Un rechazo conserva el panel. La carne rechaza con saciedad 100 y marca de
sobrealimentacion del ciclo; proteina rechaza tras su toma del ciclo o si
no cabe el aumento de energia. Tambien se rechazan huevo, muerte, pausa y
sueno. No se relajan esas reglas para mostrar una animacion de consumo.

Panels::drawFeeding dibuja UNLIMITED para carne incluso cuando el ciclo no
permite otra toma; el indicador de proteina solo explica su propio reposo.
Es un limite de claridad confirmado en codigo, no prueba del motivo exacto
en la mascota de la foto. Un fallo de guardado sigue siendo una alternativa
que requiere evidencia; no se presenta como reproducido.

## Comprobacion Host

tests/collection_app.cpp ejercita ocho combinaciones del App real con
CollectionStore sintetico: Firemon/Flamemon y carne aceptada, proteina
aceptada, carne rechazada por saciedad/ciclo, carne rechazada por pausa.
Comprueba estado Eat, fotogramas, efecto persistido unico y retorno desde
Eat; los rechazos conservan panel, cuerpo y almacenamiento. No escribe NVS
legacy ni usa datos reales. El renderer de prueba observa MotionState;
no dibuja assets ni certifica la animacion visible en el TFT.

La prueba focalizada pasa sin cambiar produccion: 1 aprobada en 5.57 s.
Esto caracteriza el comportamiento actual, no es una reproduccion RED de
un defecto ni una correccion cargada. No se vuelve a flashear ni se cambian
los limites de comida. La validacion del motivo real sigue abierta.

Verificacion ampliada: 89 pruebas focalizadas aprobadas en 36.54 s, con
150 advertencias existentes de Pillow. Incluye los siete consumidores del
renderer de prueba ampliado. git diff --check sin errores. No se ejecuta una
suite completa ni un build nuevo porque solo cambian pruebas y documentos.

## Valores Posteriores Y Observacion USB

Usuario confirma Pause Pet OFF. IMG_4263 muestra Firemon, salud 100,
saciedad 6, energia 0 y animo 0. Esos valores permiten aplicar carne;
no se mantiene saciedad llena como explicacion del estado de la foto.
El animo y energia cero tampoco bloquean por si solos Nutrition::applyFood.
Proteina puede seguir restringida por su marca del ciclo, no visible aqui.

Se amplia la caracterizacion a doce combinaciones: los dos adultos aceptan
carne y proteina con los valores de la foto y marcas iniciales de comida
libres, persisten un unico efecto y reproducen Eat. Prueba focalizada nueva:
1 aprobada en 5.59 s. No se reprodujo un defecto del App en ese fixture.

Lectura mediante observe_tdisplay.py durante 90.058 s, comandos enviados 0,
reset solicitado false. El registro SI incluye un arranque POWERON_RESET;
no se presenta esta captura como prueba de que no hubo arranque al abrir el
puerto. No se identifica la causa de ese arranque. Despues, ocho muestras,
heap libre estable 82944, minimo 65188, loop maximo 605300 us, BLE=0,
sin otro reinicio ni fatal. Cero eventos de entrada: no acredita recepcion
de ACTION, consumo, rechazo de comida o resultado de guardado durante el intento.

Sigue pendiente observar una pulsacion real y comparar cuidado antes/despues.
No se cambia firmware, limites, graficos ni partida para encubrir el fallo.

## Instrumentacion Preparada, No Instalada

El usuario confirma de nuevo que queda en FEED. La captura anterior ya
habia terminado: esa respuesta no se presenta como accion capturada por USB.
Se inspeccionan Navigation, BoardInput y la cola, sin atribuirles un defecto
no reproducido. Se prepara una revision exclusivamente de diagnostico.

App emite VPET_FEED input al recibir ACTION con panel interno Feeding,
antes de sus retornos por almacenamiento o actividad. Incluye indice,
saciedad/energia/animo y flags de pausa, sueno, muerte, viaje, accion,
almacenamiento, guardado, entrenamiento y practica. Al llegar a applyFood,
emite VPET_FEED result y committed con valores finales o rollback.
No incluye ID, parentesco, ADN ni contenido completo de la partida; solo
sale por USB local. No se anaden comandos entrantes, WiFi o acciones nuevas.

Interpretacion de FoodResult, sin renumerar enums:

| result | Motivo |
| --- | --- |
| 0 | Applied: debe seguir committed=1 para iniciar Eat |
| 1 | Alimento invalido |
| 2 | Huevo |
| 3 | Muerto |
| 4 | Pausa |
| 5 | Energia sin margen para proteina |
| 6 | Limite del ciclo de comida |
| 7 | Dormido |

Applied con committed=0 identifica rechazo/fallo de persistencia, no una
comida completada. Input sin result se interpreta con flags y ruta real;
indice 2 es Volver y no debe aplicar comida. Si solo aparece VPET_INPUT y
no VPET_FEED input, comprobar panel interno y ruta previa, sin atribuirlo
automaticamente a Nutrition. Ausencia de VPET_INPUT no prueba rechazo de comida.

Prueba RED: falta de VPET_FEED input confirmada en 5.34 s antes de cambiar
App; GREEN focalizado 4.98 s tras instrumentar. Esta RED verifica capacidad
de diagnostico nueva, no reproduce la causa del fallo fisico. Incluye comida
aceptada y rechazos de pausa/ciclo; se amplia tambien a fallo de repositorio
con rollback y otra entrada durante guardado pendiente, sin segunda comida.

Build aislado desde HEAD 34e4e0b mas App instrumentado, con cabecera generada
TrainingArtwork existente. main.cpp de la copia coincide con HEAD, SHA-256
2ba7d11a8e8a7f7de7c8e25d0439b625af1fe8f40e68400cf78010b93a37879f;
no incluye el adaptador Hub concurrente del checkout. Build tdisplay aprobado
en 17.526 s: RAM estatica 52236, app 1104181 bytes, particiones 16 MiB.
Binario y ELF conservados en out/feeding-diagnostic/. SHA-256 del binario:
b12e37036b7b87b154c179a9d9be9381a2f7585abdd251a2dd2528daebdeab4a.
Nativas: 185 aprobadas en 0.503 s; focalizadas previas 89 en 37.63 s con
150 advertencias existentes de Pillow. Verificacion final con las catorce
combinaciones y fallo de repositorio: 89 focalizadas aprobadas en 36.05 s,
con las mismas 150 advertencias. Sin cambios de Status ni assets.

Carga solicitada expresamente, pendiente de respuesta. No se instala sin
confirmacion y respaldo actual, ni se reemplaza LittleFS. Este diagnostico
no se anuncia como correccion ni como prueba fisica de consumo.
