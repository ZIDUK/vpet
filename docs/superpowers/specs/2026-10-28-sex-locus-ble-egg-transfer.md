# SPEC-GAME-GENETICS-BLE-001: Sexo Heredable Y Transferencia De Huevos

## Estado Y Aprobacion

scope-approved, 2026-10-28. El usuario aprobo que el sexo de la cria se herede
del padre elegido con probabilidad proporcional a la suma de sus seis IV; en
empate, 50/50. Tambien aprobo transferir huevos entre placas y retirar el
original del emisor solo despues de que el receptor confirme el commit durable.
La aprobacion de alcance no equivale a aceptacion fisica ni flash.

## Problema

El sexo M/F se conserva como metadato de perfil, no como locus heredable. BLE
solo anuncia HID y no mueve datos de juego. Los jugadores necesitan una cria
cuyo sexo se determine geneticamente al cruce y una forma consentida de regalar
huevos entre placas sin perdida ni duplicacion por desconexion.

## Objetivo

Persistir un locus sexual en el genoma, heredarlo usando el peso genetico
aprobado y ocultar su expresion en huevos. Incorporar una sala BLE de recepcion
y envio de un huevo con una transferencia confirmada, durable e idempotente.

## Alcance

Core Python/C++17, simulador T-Display, persistencia NVS/snapshot/coleccion,
panel de Coleccion y adaptador BLE NimBLE en ESP32 T-Display. Mantener BLE
optativo y WiFi deshabilitado.

## Exclusiones

Sin cambios a IV/EV, rasgos existentes, tasa/direccion de mutaciones, balance
de combate o crecimiento; sin compartir adultos, items, ADN arbitrario,
parejas entre lineas, P2P por WiFi o instalacion de paquetes. Sin promesa de
autenticidad criptografica del contenido ni proteccion anti-clon frente a
copias/restauraciones de respaldos. Sin flash en esta entrega.

## Requisitos

### REQ-GAME-GENETICS-001

Agregar un locus sexual genetico retrocompatible. Las partidas anteriores
derivanlo una sola vez de su sexo M/F persistido y conservan sus cuatro bytes
originales; nuevos huevos de cruce heredan M/F del padre elegido usando como
peso la suma de sus seis IV. Si ambas sumas son cero, elegir al azar 50/50.

### REQ-GAME-GENETICS-002

Fijar el resultado genetico en el huevo al confirmar el cruce; mostrar `?`
mientras sea huevo y revelar el mismo M/F al eclosionar, incluso tras reinicio.
El sexo de perfil debe coincidir con el locus despues de migrar o crear la cria.

### REQ-GAME-BLE-EGG-001

Permitir que una placa anuncie una sala de recepcion y que otra placa envie
un huevo no activo mediante BLE, con confirmacion explicita del receptor y
retirada durable del emisor solo tras confirmacion durable del receptor.

### REQ-GAME-BLE-EGG-002

Una transferencia identificada por token estable debe ser idempotente. Una
desconexion, reintento, receptor lleno, formato/version incompatible o fallo
de persistencia no puede borrar el original ni crear dos huevos receptores.
El receptor debe conservar identidad, padres, ADN, incubacion y recibo de
origen; nunca concede mochila ni hace activo el huevo automaticamente.
La coleccion conserva hasta 27 recibos; al agotarlos se rechaza la recepcion
sin emitir ACK ni retirar el original del emisor.

## Criterios De Aceptacion

### AC-GAME-GENETICS-001

Datos de prueba con sumas parentales 60 y 30 producen probabilidad exacta
2/3 para heredar el alelo del padre de 60; empate da 1/2. Python y C++ dan el
mismo resultado para semillas reservadas. Un estado v1 conserva DNA0..3 y
migra locus desde M/F sin cambiarlo en cargas posteriores.

### AC-GAME-GENETICS-002

El panel y roster muestran `?` para el huevo; tras incubar/reiniciar/eclosionar
se revela el alelo ya guardado sin nuevo sorteo. El perfil y locus nunca
divergen al guardar, migrar o cambiar de mascota.

### AC-GAME-BLE-EGG-001

El usuario puede abrir/cerrar una sala receptora en la placa; la placa receptora
anuncia un servicio vPet de transferencia y presenta el huevo entrante antes de
confirmar. El emisor selecciona y confirma un huevo no activo. Ambos roles
usan version de protocolo y limites de payload explicitos; HID sigue funcional.

### AC-GAME-BLE-EGG-002

Inyectar desconexion/fallo antes del commit receptor mantiene el origen intacto.
Tras commit receptor y antes del ACK, reintentar recupera el mismo recibo/huevo.
Solo al recibir ACK durable el emisor retira el origen. La capacidad llena,
huevo activo/eclosionado, ID duplicado o payload corrupto se rechazan sin mutar.
Una segunda entrega del mismo token no crea otra plaza.

## Contratos Y Compatibilidad

El ADN pasa de cuatro a cinco bytes: DNA0..3 y EV conservan significado; DNA4
codifica el alelo M/F. Se agrega clave NVS `dna4` y snapshot versionado nuevo;
lectores anteriores siguen aceptando sus versiones y la migracion escribe el
alelo derivado de `petProfile` cuando esta disponible. `restoreDna` de cuatro
bytes se mantiene como compatibilidad y deja el locus desconocido hasta que el
adaptador migre el perfil. No reinterpretar traits de DNA3.

BLE transfiere solo huevos validos en un envelope versionado con token,
identidad, perfil, cinco bytes de ADN, cuerpo/estado incubacion, padres y
checksum. El receptor usa compare-and-swap del CollectionStore antes del ACK.
El emisor conserva el token y huevo hasta un ACK autenticado por la conexion
bonded; la persistencia de borradores/ACK pendientes permite reintento seguro.
Las conexiones BLE actuales son Just Works, no una identidad criptografica de
propietario; ambos usuarios deben confirmar fisicamente.

## Errores Y Recuperacion

BLE fuera de servicio, peer desconectado, falta de espacio, almacenamiento
bloqueado o codec desconocido mantienen el huevo emisor. El receptor no confirma
antes de commit. Si el ACK se pierde despues del commit, el token persistido
devuelve el resultado existente. Registros corruptos o futuras versiones fallan
cerrado. Cerrar la sala detiene anuncios/escaneo y libera el stack cuando no
esta compartido con el HID.

## Riesgos

La capacidad de RAM/flash, duracion de conexion y seguridad NimBLE deben medirse
en hardware; pruebas host no prueban radio. Un respaldo antiguo puede restaurar
un huevo ya transferido; no existe autoridad externa anti-clon. La suma de IV
es una definicion de fuerza de este piloto, no una ley biologica. Cambiar a cinco
bytes exige revisar snapshots, coleccion, simulador y todos los adaptadores.

## Verificacion

Pruebas RED/GREEN de herencia y migracion con trazas Python/C++; codecs y
transacciones de transferencia con cortes y replay; pruebas del controlador BLE
con stubs; `make spec-check`, suite Python, PlatformIO native y build T-Display.
La aceptacion fisica requiere dos placas compatibles, validar ambos roles,
desconexion en cada fase, reintento y cierre limpio de la sala. No flashear aqui.

## Preguntas Pendientes

No hay decisiones de producto pendientes en el alcance aprobado. La inspeccion
radio/fisica queda pendiente de despliegue autorizado posterior.
