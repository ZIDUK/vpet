# SPEC-HUB-CREATOR-001: Asistente Local De Autor

## Estado Y Aprobacion

retrospective-review, 2026-10-28. Reconstruccion del comportamiento implementado
el 2026-10-24; el usuario aprobo el asistente entonces y el proceso de trazabilidad
ahora. Esta redaccion aun no tiene aprobacion final. No implica release ni flash.

## Problema

Crear otra linea de mascotas requiere describir etapas, acciones y rutas F1;
el autor necesita un formulario que prepare los recursos sin editar JSON a mano.

## Objetivo

Producir un proyecto local de autor validado, manteniendo separadas identidad
del contenido, individuos/ADN, instalacion y premios.

## Alcance

Cuatro pasos en Hub: identidad; cinco etapas y animaciones; retratos/fondos;
revision/exportacion. Incluye borradores descargables/reabribles en navegador.

## Exclusiones

Sin cuentas, catalogo publico, firma, vpetpack instalable, escritura en placa,
transferencia de items, concesion de huevos ni cambio de reglas o partidas.

## Requisitos

### REQ-HUB-CRT-001

Exportar un ZIP de autor con definicion F1 valida, creditos, PNG originales y
BMP preparados; no etiquetarlo como instalable.

### REQ-HUB-CRT-002

Validar cuadriculas cuadradas, 1..64 cuadros, 10..1000ms por cuadro y loops validos;
las reutilizaciones apuntan directamente a una animacion propia de la misma etapa.

### REQ-HUB-CRT-003

Recursos obligatorios ausentes bloquean exportacion sin generar un archivo parcial.

### REQ-HUB-CRT-004

Limitar imagenes/solicitudes, rechazar PNG invalidos y cuadros vacios, y comprobar
retratos cuadrados hasta 512px y fondos opacos de 240x135.

### REQ-HUB-CRT-005

Inspeccionar/exportar no muta el proyecto de entrada ni crea ADN, individuos o stock.

### REQ-HUB-CRT-006

Conservar autoria y layouts de las hojas fuente separados del contrato F1 estricto.

### REQ-HUB-CRT-007

El autor puede cargar PNG, ver animaciones, descargar JSON/ZIP y reabrir un borrador
con los graficos, en desktop y movil sin errores JS ni desbordamiento horizontal.

### REQ-HUB-CRT-008

La importacion F1 del Hub sigue limitada a metadatos y nunca equivale a verificar
assets, instalar contenido o modificar partidas.

## Criterios De Aceptacion

### AC-HUB-CRT-001

Un proyecto completo produce ZIP con rutas unicas/relativas y content.json aceptado
por PetDefinition; validate_art acepta los recursos preparados y transparencia indice cero.

### AC-HUB-CRT-002

Los casos parametrizados grid, frames, interval, alias y loop invalidos se rechazan.
La animacion reutilizada resuelve el clip declarado sin ciclos.

### AC-HUB-CRT-003

Al quitar el retrato de baby, inspect_project devuelve valid=false y export_project
lanza ValueError; la UI mantiene deshabilitada la exportacion de proyectos incompletos.

### AC-HUB-CRT-004

PNG de mas de 4 MiB y total decodificado mayor de 16 MiB se rechazan. Tambien
fondos/retratos de dimensiones incompatibles y cuadros completamente transparentes.
Cada solicitud del asistente admite como maximo 24 MiB de JSON.

### AC-HUB-CRT-005

La entrada coincide byte a byte logicamente con su copia tras inspeccion; la
definicion generada no agrega un campo dna ni hace operaciones de guardado de mascota.

### AC-HUB-CRT-006

project.json conserva autor y source_layouts; estos layouts no contienen asset.data.
content.json conserva el esquema visual F1, sin mezclar metadata editorial.

### AC-HUB-CRT-007

El recorrido Chromium a 1280 y 390px descarga JSON/ZIP reales, reabre borrador con
su identidad y PNG, vuelve a validar, muestra canvas no vacio y no arroja errores JS.

### AC-HUB-CRT-008

La validacion F1 devuelve assets_verified=false e installable=false para el builtin;
una definicion valida por si sola no acredita sus recursos ni abre USB.

## Contratos Y Compatibilidad

Autor schema 1: identity, stages por cinco roles y resources. PetDefinition recibe
otro documento F1 generado. El ZIP contiene content.json, project.json, README.txt,
sources/ y prepared/. Las celdas se normalizan a 88px y retratos a 40px.
Dormir usa indices base uno en UI y base cero en la definicion. ADN y reglas quedan
en el motor. Detalle operativo: docs/vpet-creator.md.

## Errores Y Recuperacion

Validacion devuelve errores y no permite exportar un proyecto invalido. Los
borradores son archivos descargados explicitamente, no autosave. Recargar sin
guardar puede perder cambios en memoria; no se promete recuperacion automatica.

## Riesgos

Un ZIP valido no prueba licencia/autoria, espacio en placa ni colores/FPS fisicos.
Los PNG opacos conservan su fondo. Sin backend publico no hay publicacion.
El plan historico informa ENOSPC en la suite general; no atribuir sus pruebas a otro commit.

## Verificacion

Requisitos y pruebas estan en docs/requirements.json. La matriz combina tests
Python y recorrido navegador con archivos reales de prueba; no arte comercial nuevo.
Publicacion e instalacion necesitan specs y aceptaciones separadas.

## Preguntas Pendientes

Aprobacion de esta reconstruccion final. El formato publico firmado, compatibilidad
del instalador y catalogo publicado siguen fuera del contrato de este asistente.
