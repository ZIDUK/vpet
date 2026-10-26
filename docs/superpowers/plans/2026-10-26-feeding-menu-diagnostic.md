# Alimentacion Permanece En FEED: Diagnostico

Fecha: 2026-10-26. Estado: consumo capturado; salto de animacion reproducido
y corregido localmente, carga y aceptacion visual de la correccion pendientes.

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

## Carga Autorizada Y Verificada

El usuario responde "Si, cargar el diagnostico" para revision 607efbb,
solo firmware, conservando partida, Coleccion y graficos. Esta seccion
sustituye el pendiente de autorizacion/carga de los apartados historicos.
No cambia Status ni las reglas de alimentacion. Creator/Hub siguen fuera.

Build preflash aislado repetido en 3.260 s con los mismos 52236 bytes RAM
y 1104181 bytes app. App.cpp de la copia coincide con el checkout aprobado;
binario SHA-256 b12e37036b7b87b154c179a9d9be9381a2f7585abdd251a2dd2528daebdeab4a.
Prueba focalizada nueva aprobada en 5.59 s. Las 89 focalizadas y 185 nativas
anteriores son de la misma revision; no se presenta una nueva suite completa.

Placa verificada ESP32, 16 MiB, ID 08f9e0d00788. Respaldo NUEVO en
out/board-backups/feeding-diagnostic-20261026-131129/: critical.bin (particiones
y NVS), littlefs-before.bin completo de 12451840 bytes y firmware-before.bin
de 1110368 bytes. Checksums locales y comprobacion contra flash antes de
escribir. El LittleFS actual se reconstruye desde copia previa leyendo los
bloques cambiados y verificando MD5 de TODA la particion; no se restaura esa
copia ni se descartan cambios recientes de Coleccion.

SHA-256 de LittleFS actual:
68146ac45346657eeeeb84f6a39eb14b25e229e2ae4cbc33e52de2f0ef98e6eb.
La app anterior coincide con dabc2e7:
b9c75006b52e6ac078edd4dbf462a0796826635374b81c4dd11ecd7274b098f5.
No se borra ningun respaldo previo ni se publica contenido de partidas.

Write_flash escribe solo 1110752 bytes de aplicacion en 0x10000 (61.1 s).
No hay erase_flash/uploadfs ni escritura de bootloader/tabla/NVS. Se compara
el digest de app y se comprueba que LittleFS, NVS y todo 0..0x10000 siguen
identicos ANTES del reinicio final; despues puede haber checkpoints normales
del juego. Al fallar una comprobacion no se declara entrega correcta.

Arranque confirmado VPET_READY: heap libre 82948, minimo 73320, flash 16 MiB,
filesystem 11829248/12451840, manifest 1. Cumple minimos de heap de arranque.
Evidencia local: out/feeding-diagnostic/board-ready.json y verification.json
del directorio de respaldo. El agente no alimento, despauso ni cambio mascota
en nombre del usuario. Falta coordinar una captura de ACTION en MEAT; un arranque
correcto no cierra el fallo. No se deja un monitor aparentemente activo
despues de cerrar su ventana de lectura.

## Intento Real Capturado Y Correccion Del Reloj

El usuario confirma estar listo y recibe indicacion despues de abrir USB.
Captura de 68.251 s en
out/feeding-diagnostic/feeding-capture-20261026-132239.json. El puerto vuelve
a mostrar POWERON_RESET y arranque; reset solicitado false no significa
ausencia de arranque observado. Sin comandos USB enviados por el agente.

Se reciben eventos fisicos y el intento:

```text
VPET_FEED input index=0 hunger=96 energy=18 mood=0 paused=0 asleep=0 dead=0 away=0 pending=0 storage=1 saving=0 training=0 practice=0
VPET_FEED result=0 committed=1 hunger=100 energy=18 mood=0
```

La captura acredita comida aceptada y confirmada en almacenamiento; no
permite seguir explicandolo como rechazo por saciedad o pausa en ese intento.
El usuario responde "Sigue en FEED". No se deduce una captura de pantalla
Home a partir de esos registros. Loop maximo del intervalo: 5094923 us;
un intervalo anterior alcanzo 6334286 us. Heap minimo observado 56184,
sin fatal ni reinicio adicional entre muestras; BLE=0 no prueba radio.

App iniciaba Motion::startAction(Feed, nowMs) DESPUES de persistir usando
nowMs tomado antes del tick. Al siguiente tick el tiempo de almacenamiento
contaba como tiempo de la animacion. Un primer frame seguido de un salto
a Idle explica una animacion imperceptible; no se confunde con efecto doble.

Prueba RED real de comportamiento: Repository sintetico inyecta 5000 ms en
un commit. La asercion de seguir en Eat tras 500 ms de presentacion falla
antes del arreglo (6.19 s). Correccion: medir millis() al entrar en tick y
compensar nowMs con el tiempo real transcurrido al iniciar Eat despues del
commit. Solo cambia el reloj de presentacion de alimentacion; no NVS,
inventario, ADN, pausas ni reglas de nutricion. La resta uint32 conserva
el contrato cuando millis desborda; no se agregan temporizadores persistidos.

GREEN focalizado 5.66 s. Dieciocho combinaciones de Firemon/Flamemon cubren
alimentacion normal, cuidado agotado, rechazo, fallo de repositorio, guardado
lento y rollover. El guardado sigue aplicando el efecto UNA vez y la
finalizacion del clip no lo repite. Suite focalizada final: 89 aprobadas en
38.21 s con 150 advertencias existentes de Pillow; nativas 185 en 0.503 s.
No se ejecuta una nueva suite Python completa. git diff --check sin errores.

Build aislado de la correccion, sin Hub/Creator, aprobado en 7.925 s:
RAM 52236, app 1104233 bytes (+52 frente al diagnostico). Solo App.cpp y
App.h de produccion cambian; el header modifica una llamada privada y no
el contrato de persistencia. Binario/ELF: out/feeding-animation-fix/.
SHA-256: fb787513780e50f23ea2bef36244d8b925b8f24d21b3408fd6e3c602901cfc41.

La correccion esta preparada, NO instalada. Se solicita autorizacion nueva
firmware-only conservando partida/graficos. Falta comprobar visualmente la
animacion tras el nuevo despliegue. El tiempo bloqueante del guardado sigue
siendo una limitacion: este arreglo no lo elimina ni certifica fluidez.
