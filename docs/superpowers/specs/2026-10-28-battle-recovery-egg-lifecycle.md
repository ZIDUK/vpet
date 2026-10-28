# SPEC-GAME-RECOVERY-001: Recuperacion De Guardado Y Ciclo De Huevos

## Estado Y Aprobacion

scope-approved, 2026-10-28. El usuario solicito recuperar la navegacion tras
un guardado pendiente, desechar huevos y conservar breeding que genere huevos.
El cambio de modelo genetico de sexo queda registrado como propuesto; aun no
se aprueba una estrategia de migracion para ampliar el ADN persistido.

## Problema

Un fallo temporal al persistir puede reemplazar la pantalla de batalla por una
pantalla negra que consume todos los botones. La coleccion tampoco permite
desechar huevos. El sexo se guarda como identidad M/F, pero no se hereda como
locus genetico.

## Objetivo

Permitir salir de la pantalla de reintento sin descartar ni repetir una accion,
desechar huevos no activos de forma durable y hacer verificable que un cruce
elegible crea un huevo. Mantener trazable el trabajo pendiente de herencia del
sexo en ADN.

## Alcance

Firmware ESP32 T-Display, dominio/almacen de Collection y pruebas host C++.
Registro local SDD para requisitos implementados y pendientes.

## Exclusiones

Sin flasheo, borrado de partida, cambios de balances o enums persistidos,
recepcion de huevos externos, selector de inventario externo, ni cambios del
formato estadistico de cuatro bytes de ADN en esta entrega.

## Requisitos

### REQ-GAME-REC-001

Si un guardado queda pendiente, el usuario puede volver visualmente a Home;
la escritura sigue reintentandose y no se aceptan nuevas mutaciones mientras
el resultado durable sea incierto.

### REQ-GAME-REC-002

El usuario puede desechar con confirmacion un huevo no eclosionado que no sea
la mascota activa. El registro de coleccion y su cuerpo cambian en una sola
transaccion durable; una falla conserva el estado anterior.

### REQ-GAME-REC-003

Un cruce elegible con plaza libre crea exactamente un huevo con ADN heredado,
IDs de ambos padres, incubacion de 30 minutos y cooldown parental atomico.

### REQ-GAME-REC-004

El sexo debe pasar a ser un locus genetico heredable y persistido, sin mostrar
un sexo conocido antes de eclosionar. Hasta aprobar y migrar ese contrato, el
requisito permanece propuesto y el sexo actual se reconoce como metadato de
perfil, no como ADN heredado.

## Criterios De Aceptacion

### AC-GAME-REC-001

Dado un commit que falla, BACK permite mostrar Home y continuar los reintentos;
ningun ACTION/NEXT dispara una segunda mutacion hasta confirmar el commit.
Tras recuperar almacenamiento, el juego vuelve a operar sin reinicio.

### AC-GAME-REC-002

Dado un huevo no activo, confirmar desecho reduce el conteo en uno y libera su
plaza tras recargar. Cancelar o fallar el commit conserva el huevo. No se puede
desechar un individuo adulto, el huevo activo ni un individuo ya eclosionado.

### AC-GAME-REC-003

Dada una pareja valida y una plaza libre, una confirmacion agrega un solo huevo,
registra ambos padres, 30 minutos de incubacion y 24 horas de cooldown en el
mismo commit. Un reintento no duplica la cria.

### AC-GAME-REC-004

La implementacion no puede declararse cumplida mientras el sexo solo se derive
del ID o se asigne aleatoriamente sin herencia. La migracion debe conservar los
cuatro bytes de ADN y perfiles NVS existentes o definir lectura retrocompatible.

## Contratos Y Compatibilidad

No cambia el schema NVS ni el ADN estadistico de cuatro bytes. Desechar huevo
usa la transaccion compare-and-swap ya usada por CollectionStore. El huevo
activo no se elimina para preservar la referencia activa. El formato actual
PetProfile v1 conserva M/F como metadato; los registros existentes se leen sin
migracion.

## Errores Y Recuperacion

Un guardado incierto conserva el bloqueo de mutaciones, pero no debe ocultar
Home ni detener reintentos. Un descarte no confirmado o fallido no modifica la
coleccion durable. Fallos de lectura, checksum o CAS bloquean el descarte y
conservan el registro previo.

## Riesgos

La aceptacion host no prueba el comportamiento fisico del TFT. El flash de esta
revision esta sujeto a todas las precondiciones de AGENTS.md. La semantica de
herencia de sexo requiere diseno y migracion aparte antes de marcar REQ-004.

## Verificacion

Pruebas C++ nativas de App, CollectionStore y CollectionPanel; `pio run -d
firmware/t-display -e tdisplay`; chequeo SDD. La aceptacion fisica requiere una
carga autorizada posterior y probar fallo/recuperacion, descarte y breeding.

## Preguntas Pendientes

Definir el locus y la migracion retrocompatible para sexo heredable en ADN. La
recepcion y seleccion de huevos externos queda para una especificacion futura.
