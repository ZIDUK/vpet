# SPEC-DEV-PROCESS-001: Trazabilidad Y Verificacion Local

## Estado Y Aprobacion

scope-approved, 2026-10-28. El usuario aprobo plantilla, registro, validador y
piloto Creator, con la condicion explicita de no usar GitHub Actions. Esto
registra aprobacion de alcance, no una firma de la redaccion final ni un release.

## Problema

Specs, pruebas y entregas estan documentadas, pero no hay un indice uniforme
ni una verificacion reproducible que detecte referencias rotas y falsas clausuras.

## Objetivo

Vincular requisitos a contratos, pruebas y entregas, conservando la diferencia
entre enlace estatico, prueba ejecutada, aprobacion humana y aceptacion fisica.

## Alcance

Control local del piloto Creator y del propio proceso. Nuevas funcionalidades
siguen esta estructura; la migracion de documentos historicos sera incremental.

## Exclusiones

Sin GitHub Actions ni otro servicio remoto; sin instalar hooks o cambiar Git;
sin flash, publicacion, aprobacion automatica, TinyML ni cambios del juego.
Un control local no impide que una persona omita ejecutarlo.

## Requisitos

### REQ-DEV-SDD-001

Un indice JSON mantiene IDs unicos de requisito, spec, criterio y entrega,
enlaces a implementacion y selectores de prueba existentes, con rutas confinadas.

### REQ-DEV-SDD-002

Una plantilla comun y secciones obligatorias separan contratos de specs y pasos
de planes. El piloto Creator se documenta como reconstruccion pendiente de revision.

### REQ-DEV-SDD-003

La ejecucion local registra comandos reales, codigos de salida, fallos/no ejecutado,
logs y huella del arbol Git incluyendo cambios sin commit. Detiene tras un fallo.

### REQ-DEV-SDD-004

Un enlace o chequeo estructural no marca una prueba pasada ni una entrega publicada.
La revision de release exige aprobacion registrada, evidencia y commit real.

## Criterios De Aceptacion

### AC-DEV-SDD-001

Dado el registro valido, el chequeo termina con cero. IDs duplicados, referencias
de archivo/funcion/criterio inexistentes y rutas externas causan salida distinta
de cero. --collect resuelve ademas los selectores parametrizados en pytest.

### AC-DEV-SDD-002

Una spec registrada sin cualquiera de las doce secciones falla. Cada requisito
figura en su seccion de spec y en su plan separado. La plantilla esta disponible
en docs/templates/spec.md. No se presenta la spec retrospectiva como aprobada.

### AC-DEV-SDD-003

Un comando que retorna 7 queda failed/7 y los siguientes quedan not-run. Una
prueba que retorna cero queda passed. Cambiar bytes sin commit altera la huella.
El runner no aprueba si el arbol cambia entre inicio y fin de la ejecucion.
Poco espacio bloquea full antes de crear el servidor o ejecutar tests; un fallo
al escribir reporte devuelve fallo explicito con JSON en stderr.

### AC-DEV-SDD-004

El registro piloto pasa estructura pero falla --release: Creator sigue pendiente
de revision, sus entregas son locales y no se declara commit de publicacion.
Ningun chequeo modifica el indice para convertir implementado en verificado.

## Contratos Y Compatibilidad

docs/requirements.json schema 1. scripts/spec_check.py usa solo biblioteca
estandar, AST de Python y headings Markdown acotados por esta plantilla.
Los tests de navegador son scripts .cjs y reciben HUB_URL desde el runner.
La verificabilidad estatica del test no acredita que sus aserciones cubran toda
la semantica: esa correspondencia requiere revision humana.

## Errores Y Recuperacion

JSON duplicado, esquema/rutas/IDs invalidos y referencias rotas fallan cerrado.
El runner conserva reporte/logs del intento fallido y detiene la secuencia.
Arranca y detiene solamente su propio servidor loopback; nunca abre USB.
Si no puede escribir el reporte, falla explicitamente y emite JSON en stderr.
Un preflight exige 6 GiB libres para full y 128 MiB para Creator en workspace
y temporales. Se reserva 1 MiB de espacio para el reporte final. No son una
garantia de capacidad futura si otros procesos siguen consumiendo disco.

## Riesgos

Un archivo local de aprobacion o reporte no es una firma autenticada. Las
referencias deben revisarse; no hay proteccion remota de rama sin otro mecanismo.
Dependencias de navegador, permisos y espacio pueden bloquear la verificacion.
Un perfil Creator no certifica el firmware ni el arbol completo.

## Verificacion

tests/test_spec_check.py y tests/test_verify_local.py cubren rechazo de errores,
estado de ejecucion y huella. make spec-check es estructural/coleccion; make
verify-local ejecuta el piloto; make verify-local-full agrega suite general,
generacion, pruebas nativas y compilacion ESP32. Ninguno flashea hardware.

## Preguntas Pendientes

La redaccion final de las specs y la publicacion de Creator necesitan revision
independiente del alcance aprobado. El servidor CI remoto queda expresamente fuera.
