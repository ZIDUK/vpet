# SPEC-GAME-FLUID-001: Juego Fluido Con Persistencia Invisible

## Estado Y Aprobacion

Alcance aprobado por el usuario el 2026-10-29. Solicitud: "no quiero nada que
se congele y que no me diga guardando". A la propuesta de registro pequeno
recuperable, respaldo completo al dormir/en reposo y aviso ante fallo real,
respondio: "Si, guardar asi sin interrumpir el juego".

El documento tecnico tambien fue aprobado el 2026-10-29: "Si, continua con la
implementacion". No equivale a codigo terminado, release ni aceptacion en placa.
El firmware actual es 64addc8 y NO satisface esta especificacion.

## Problema

Entrenamiento confirma aprendizaje y una generacion completa de Coleccion.
El commit valida, escribe staging, comprueba bytes, copia previous y publica.
Combate, CLAIM y ajustes conservan caminos sincronicos en App. Entrenamiento
de fondo evita bloquear el hilo, pero presenta GUARDANDO y rechaza entradas
mientras espera. Ocultar la palabra no resuelve ninguno de estos contratos.

CareJournal ya permite guardar cuidado mediante una clave NVS atomica. No
incluye eventos de aprendizaje y actualmente no basta para guardar experiencias.

## Objetivo

Jugar sin pantalla, modal, indicador ni texto de guardado durante operaciones
normales. Las animaciones y la navegacion responden mientras se persiste.
La mascota conserva cambios confirmados tras reinicio, sin duplicar recompensas.

## Alcance

ESP32 T-Display 240x135: entrenamiento, Arena y su Mochila, exploracion/CLAIM,
alimentacion, objetos, luz/sueno, fecha/hora y ajustes. Incluye transiciones a
Coleccion, cambio de individuo y operaciones de huevos: tambien usan el escritor
de fondo, aunque sus transacciones estructurales sigan requiriendo checkpoint.
El dominio, codecs y coordinador deben poder probarse en host sin TFT/Arduino.

## Exclusiones

No guardar exclusivamente al dormir, no depender de bateria baja o apagado
ordenado, no introducir WiFi, no cambiar balance ni numeros de enums, no borrar
partidas ni reformatear LittleFS. No prometer latencia nula para flash defectuosa
o almacenamiento agotado. Los errores reales siguen siendo visibles y recuperables.

## Decision De Arquitectura

Se descartan guardar solo al dormir (arriesga el progreso diurno ante corte) y
mantener checkpoints completos con un spinner (mantiene la espera). Se elige
registro transaccional compacto mas consolidacion separada.

1. App mantiene mascota viva, navegacion y TFT. El escritor nunca los modifica.
2. Cada resultado genera un recibo con revision monotona, individuo, estado
   posterior, eventos de aprendizaje y checksum. Inventario/costos/premios y
   aprendizaje pertenecen al MISMO recibo, no a dos escrituras independientes.
3. El escritor confirma el recibo compacto. No recorre politicas, copia generaciones
   completas ni ejecuta GC en ese camino. No se anuncia un premio durable antes
   de confirmar su recibo. La presentacion mantiene el flujo propio del juego;
   no introduce una vista de espera disfrazada.
4. Al iniciar sueno o tras cinco segundos sin entradas se solicita consolidacion
   de un snapshot inmutable. Se conserva la generacion anterior y la nueva se
   publica atomicamente. Dormir no es el unico mecanismo de persistencia.
5. Una entrada durante mantenimiento solicita ceder/cancelar el staging antes de
   publicar. El renderer sigue atendiendo cuadros y navegacion. La accion se
   conserva y procesa una vez: no se descarta ni se ejecuta contra un estado
   parcial. Las fases largas necesitan puntos de cancelacion, no solo una tarea.
6. El checkpoint incorpora una revision de recibo. Un corte antes o despues de
   publicarlo permite distinguir eventos incorporados de eventos pendientes.
   Nunca se retira el unico recibo durable antes de publicar su checkpoint.

El recibo compacto evoluciona el journal existente, con lectura de VPCJ1. La
revision incorporada necesita un formato de Coleccion versionado y lectura de
VPCL v1. Settings/NVS schema 3 y VPL1 no cambian. Los lectores antiguos deben
rechazar un formato futuro; un downgrade exige consolidacion y exportacion
compatibles, nunca ignorar el journal nuevo.

## Requisitos

### REQ-GAME-FLUID-001

Persistir resultado, costos, inventario y aprendizaje en un recibo atomico
compacto. Recuperar la partida sin repetir eventos ni recompensas. Mantener
limites de longitud, checksum, identidad y secuencias. No usar como atajo el
guardado completo cuando el recibo no cabe: debe gestionar capacidad fuera del
camino de la accion y rechazar con error real si no existe una opcion segura.

### REQ-GAME-FLUID-002

Consolidar al dormir o en reposo mediante un snapshot separado, conservando el
respaldo. Una entrada interrumpe o cede el mantenimiento sin congelar UI ni
perder la accion. Conservar recibos concurrentes/no incorporados segun revision.
El diario tiene capacidad acotada: no se permite una cola creciente en RAM.

### REQ-GAME-FLUID-003

No mostrar GUARDANDO, SAVING, SAVE PENDING o indicadores de almacenamiento en
el recorrido normal. No sustituirlos por una animacion de espera obligatoria.
Animaciones/navegacion siguen vivas y las entradas no desaparecen al completar
el escritor. Un fallo real tiene un aviso distinto del guardado normal.

### REQ-GAME-FLUID-004

Leer partida historica sin normalizar ni perder datos. Conservar snapshots y
respaldo anterior durante la migracion. No desplegar hasta demostrar recuperacion
ante cortes, limites de NVS/heap y comportamiento de los recorridos completos.

## Criterios De Aceptacion

### AC-GAME-FLUID-001

Con Coleccion real y journal habilitado, completar entrenamiento, una batalla,
CLAIM y un consumo causa cero begin/commit de generaciones VPCL y cero prepare
de politicas VPL1 en la transaccion compacta. Tras cortar/reiniciar en cada
frontera de escritura, el estado es el previo o el posterior completo, nunca
mezcla de efectos y aprendizaje. Reintentar el mismo recibo no duplica efectos.
Corrupcion, identidad incorrecta y huecos de secuencia bloquean escritura y
conservan originales. El backend debe medir el tiempo real del recibo.

### AC-GAME-FLUID-002

Un checkpoint iniciado al dormir o en reposo conserva una copia anterior valida.
ACTION/NEXT/BACK inyectados durante cada fase actualizan UI y la accion conserva
su orden. Un corte alrededor del rename y de la retirada/rebase del diario no
pierde ni reproduce eventos. Llenar el diario o rechazar el escritor no provoca
un checkpoint sincrono de emergencia en App::tick. Las colas y snapshots tienen
limites explicitos verificados, incluyendo 512 acciones consecutivas y cuatro
individuos sin incremento monotono de heap.

### AC-GAME-FLUID-003

En ES/EN y con trabajo retenido artificialmente: ninguna pantalla normal muestra
texto/indicador de guardado; los cuadros y el cursor cambian, y la entrada del
tick de finalizacion no desaparece. Medir en placa al menos 20 transiciones por
flujo: input a respuesta visual p95 <=100 ms y ningun intervalo de cuadros >200
ms atribuible al guardado. Transicion de resultado <=200 ms tras terminar su
animacion propia; no alargar entrenamiento o impactos para esconder E/S.
El aviso de fallo no concede un premio rechazado, permite salir/reintentar y
nunca se usa como estado normal de espera.

### AC-GAME-FLUID-004

Cargar fixtures VPCL v1/VPCJ1 y Settings schema 3; conservar identidad, ADN,
sexo, cuatro plazas, objetos, incubacion, sueno, mortalidad, politicas y recibos
de transferencia. Migrar sin reemplazar el volumen ni eliminar respaldo.
Ejecutar Python, native, build tdisplay, chequeos de pila/heap y pruebas de
cortes. Reportar arranque y aceptacion fisica por separado. Cualquier fracaso
de recuperacion o de latencia impide declarar la entrega fluida/terminada.

## Contratos Y Compatibilidad

Una revision de operacion no equivale al numero de generacion del checkpoint.
Guardar ajustes o cuidado no puede sobrescribir experiencias pendientes. Cambiar
de individuo, crear/eliminar huevos y transferirlos resuelve antes los recibos
que afecten a esas identidades, siempre fuera del hilo UI. La confirmacion BLE
externa solo se emite despues del commit durable; UI no puede simularla.

Capacidad propuesta para el piloto: journal atomico <=3950 bytes por clave,
hasta 64 eventos de aprendizaje por recibo acumulado y hasta ocho entradas de
usuario pendientes, sin reservar ocho PetState/LearningState completos. Debe
medirse con el snapshot maximo real antes de activar. Si no cumple, se revisa
el formato/presupuesto antes del despliegue, no se truncan eventos.

Esta especificacion sustituye la vista GUARDANDO de REQ-GAME-PLAY-009 como
objetivo de producto; no altera la evidencia historica de esa implementacion.
REQ-GAME-PLAY-007 y REQ-GAME-PLAY-010 quedan cubiertos por estos recorridos, pero
permanecen abiertos hasta su verificacion real, no se marcan cumplidos por enlaces.

## Errores Y Recuperacion

Rechazado: no confirmar efectos; conservar reintento o restaurar el estado
anterior coherente. Aceptado pendiente: no volver a conceder ni revertir como
si nunca hubiera existido; resolver por revision/recibo. Corrupcion/futuro:
conservar bytes y mostrar aviso recuperable; no transformar en mascota nueva.
No perder teclas durante recuperacion; aplicar limites sin silencios ni colas
ilimitadas. Un almacenamiento permanentemente averiado puede impedir mutaciones,
pero no debe detener el dibujo ni impedir volver a una vista segura.

## Riesgos

NVS de 20 KiB y heap observado limitados. No duplicar politicas completas de
9240 bytes en un recibo NVS ni asignar un framebuffer adicional. TFT/lecturas
de assets comparten LittleFS con checkpoints: mover una llamada a FreeRTOS no
elimina esa contencion. Las fases indivisibles y la cache grafica requieren
medicion; si incumplen el presupuesto se bloquea la entrega, no se oculta.
Recoleccion de politicas protege referencias del diario y ambas generaciones.

## Verificacion

Plan: ../plans/2026-10-29-invisible-progress-journal.md. Los tests actuales de
CollectionStore, App/aprendizaje, exploracion, persistencia y pixeles son linea
base, NO prueban este comportamiento nuevo. Las nuevas regresiones se escriben
y observan fallar antes de implementar. No hay pruebas fisicas de esta arquitectura.

## Preguntas Pendientes

Documento tecnico aprobado por el usuario el 2026-10-29:
"Si, continua con la implementacion". La aprobacion del alcance consta arriba.
No se requiere volver a decidir si el producto debe mostrar GUARDANDO: ya fue
rechazado. Las decisiones de limites propuestas se validan mediante las pruebas
de capacidad/memoria del piloto antes de promover requisitos a implemented.
