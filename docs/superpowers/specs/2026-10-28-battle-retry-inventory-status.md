# SPEC-GAME-PLAYABILITY-001: Reintento De Combate Y Legibilidad

## Estado Y Aprobacion

scope-approved por el reporte explicito del usuario del 2026-10-28: bloqueo
SAVE PENDING al combatir, BACK de Mochila sin salida y Status 4/4 poco legible.
Ampliacion explicita del mismo dia: SAVE PENDING tambien al entrenar.
Segundo reporte: tambien al regresar de exploracion.
Es aprobacion del alcance; no se inventa aprobacion del documento ni aceptacion
fisica. El alcance de carga/commit/push continua la solicitud previa del usuario.

## Problema

Un rechazo al guardar el resultado de combate conserva pendingAward pero activa
savePending y el fallo del controlador, impidiendo alcanzar su propio reintento.
BACK de Mochila tambien puede quedar atrapado durante un guardado de cuidado.
La ficha ADN tiene iconos pequenos y columnas con margenes insuficientes.

## Objetivo

Permitir recuperacion verificable del combate sin duplicar premios, salida de
Mochila como navegacion y columnas legibles en la pantalla de 240x135.

## Alcance

App/CollectionPanel/LearningRuntime y adaptador LittleFS, renderers ESP32 y
simulador, regresiones host y registro de evidencia fisica autorizado.

## Exclusiones

Sin borrar partida/diarios, conceder premios de prueba, cambiar balance,
cancelar viajes ni omitir checksums o confirmacion durable del resultado.

## Requisitos

### REQ-GAME-PLAY-001

Un resultado rechazado antes de publicacion debe mantener la opcion de
reintentar. Solo se desbloquea tras validar el mismo estado durable, cuerpo,
recibo de cuidado y politica. Si no pueden leerse, se mantiene el bloqueo hasta
recuperacion. Premios y aprendizaje se publican una sola vez. Registrar la fase
de fallo por USB sin incluir contenido completo de la partida.

### REQ-GAME-PLAY-002

BACK en Mochila es solo navegacion: no muestra detalle de item ni inicia un
guardado. ACTION cierra inmediatamente, incluso mientras hay un guardado de
cuidado pendiente, cuyo trabajo sigue conservando el consumo unico.

### REQ-GAME-PLAY-003

Status debe separar icono, etiqueta, valor, barra y EV. Los iconos ADN pasan a
12 px, los de cuidado a 12 px y combate a 14 px sin filtrar sus colores oscuros.
Los valores de tres cifras y EV no invaden otras columnas. Mantener seis stats,
cuatro paginas, codigo ADN completo y dominio de solo lectura.

### REQ-GAME-PLAY-004

Un entrenamiento cuyo resultado fue rechazado revierte EV, energia, recursos y
aprendizaje. Tras validar la misma vista durable, permite ACTION para reintentar
el resultado retenido o BACK para descartarlo e iniciar otra sesion sin
reiniciar la placa. No concede el resultado rechazado.
Si la lectura sigue fallando, conserva el bloqueo y reintenta validacion.
Registrar por USB la fase de rechazo sin volcar la partida.

### REQ-GAME-PLAY-005

Al rechazar la adquisicion de un regreso de exploracion, restaurar el viaje
previo sin conceder recompensa ni aprendizaje. Usar la misma recuperacion
validada que combate y entrenamiento, no otra ruta independiente. Permitir
reintentar la recogida solo tras validar la vista durable previa; lecturas
fallidas conservan el bloqueo. No cancelar viajes ni crear premios de prueba.
El diagnostico compartido identifica contexto, fase y resultado de recuperacion.

### REQ-GAME-PLAY-006

Los blobs de aprendizaje nuevos deben usar nombres de hasta 32 bytes, limite
del volumen instalado. La referencia compacta deriva del sobre completo (ID,
secuencia, contenido), conserva CRC y valida bytes existentes ante colision.
Seguir leyendo referencias legacy sin renombrar partidas ni formatear LittleFS.
HUB STORAGE solo consulta generaciones/presupuesto, no limpia ni guarda; se
rechaza si App no esta lista. No habilita importacion ni instalacion USB.

### REQ-GAME-PLAY-007

Propuesto, no implementado: medir y reducir la espera de CLAIM y Save del reloj
sin quitar comprobaciones de durabilidad ni repetir premios. Separar tiempo de
respuesta visual y commit, conservar recuperacion ante corte y comprobar margen
de memoria. El usuario confirma la recogida pero reporta lentitud en ambos flujos.

### REQ-GAME-PLAY-008

Reporte 2026-10-29: reducir E/S redundante al confirmar aprendizaje al final del
entrenamiento. Validar cada generacion con un flujo de lectura por operacion,
sin reabrir ni buscar por cada bloque consecutivo. Mantener limites, CRC completo,
validacion de cuerpos y cierre comprobado antes del GC. No reutilizar bytes o
validaciones entre operaciones ni mostrar como confirmado un resultado rechazado.
Medir duracion del guardado de entrenamiento por USB antes de afirmar fluidez.

## Criterios De Aceptacion

### AC-GAME-PLAY-001

Con Coleccion, politica y diario compacto reales en host, rechazar preparacion
de politica o commit de Coleccion deja un resultado reintentable. Si falla la
lectura durante recuperacion, no permite mutaciones; al restablecer lectura,
ACTION publica un resultado y reiniciar conserva una batalla y un premio como
maximo. Un registro fisico debe identificar cualquier fallo residual antes de
afirmar que el recorrido en placa quedo aceptado.

### AC-GAME-PLAY-002

Usar item, dejar la tarea diferida pendiente, seleccionar BACK y pulsar ACTION
dibuja Home sin iniciar otra tarea. Terminar el trabajo conserva un consumo.
El preview izquierdo de BACK no muestra nombre, icono ni CLOSE BAG.

### AC-GAME-PLAY-003

Con ADN/EV maximos en Ultimate, seis iconos >=12 px y cajas de texto/barra
separadas por al menos 2 px; todo cabe en 240x135 sin mutar Pet. Revisar la
vista previa y declarar por separado la aceptacion visual en placa.

### AC-GAME-PLAY-004

Con App y almacenamiento real en host, rechazar politica o Coleccion durante
entrenamiento no altera energia/EV guardados ni secuencia de aprendizaje.
Lectura indisponible mantiene bloqueo hasta recuperar. Una nueva sesion publica
un unico resultado, conservado al reiniciar. Validacion fisica queda separada.

### AC-GAME-PLAY-005

Con App, journal compacto, Coleccion y politica reales en host, rechazos de
politica o Coleccion al recoger no conceden el regreso. La lectura fallida
bloquea hasta recuperacion. Un reintento publica una sola experiencia y recibo;
reconocer el resumen y reiniciar no vuelven a concederlo. Una captura USB debe
identificar la fase inicial antes de afirmar que la causa fisica esta resuelta.

### AC-GAME-PLAY-006

Con rename limitado a basenames de 32 bytes, preparar y confirmar experiencias
de entrenamiento, combate y exploracion funciona, incluso con 270 eventos y
reinicio. Leer blobs legacy y compactos valida el propietario y CRC; inspeccion
no elimina huerfanos. En placa, confirmar una recogida sin policy_publish.

### AC-GAME-PLAY-007

Registrar tiempos por fase de CLAIM y Save del reloj en placa antes y despues
del cambio, con regresiones de reloj, premios y reinicio conservadas. Definir el
presupuesto de respuesta en su plan antes de declarar aceptacion de fluidez.
Las pruebas funcionales actuales no prueban latencia; pendiente de implementacion.

### AC-GAME-PLAY-008

Con dos mascotas en ambas generaciones, el escaneo real usa dos aperturas,
dos cierres y hasta seis seeks frente a las 44 aperturas/seeks previas.
Corrupcion de bytes posterior a un escaneo y fallo de cierre bloquean el siguiente
escaneo sin descriptores abiertos ni GC. Regresiones de premio unico, rechazo,
reinicio y nombres de 32 bytes siguen pasando. Capturar VPET_TRAINING_SAVE en
placa y separar menor E/S host de aceptacion fisica del congelamiento.

## Contratos Y Compatibilidad

No cambia NVS, enums ni formatos persistidos. Un false de commit de Coleccion
significa rechazo anterior al rename; los true pendientes se siguen resolviendo
por su recibo. La recuperacion no transforma un registro corrupto en vacio.

## Errores Y Recuperacion

Un fallo de lectura o una secuencia durable diferente impiden desbloquear.
El resultado retenido puede reintentar la adquisicion, no repetir el combate
ni aplicar un delta ya comprometido. No se modifica el estado de exploracion.

## Riesgos

La prueba host no reproduce limites de flash/heap de ESP32. Un fallo inicial de
almacenamiento en placa puede tener otra causa: el registro capturado antes de
esta correccion no contenia SAVE PENDING y no permite atribuirla.

## Verificacion

Ver plan separado; pruebas C++ de App real, persistencia, pixel bounds Python,
native, build y prueba fisica de combate autorizada. No confundir arranque con
aceptacion de batalla, guardado o Status.

## Preguntas Pendientes

Confirmar el recorrido de combate y la revision visual en la placa conservada.
