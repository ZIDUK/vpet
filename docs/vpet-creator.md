# Asistente Crear vPet

Entrega local 2026-10-24. Abrir vPet Hub y seleccionar Crear vPet.
No publica contenido, concede huevos ni escribe en la placa.

## Flujo Del Autor

1. Identidad: nombre del proyecto, ID como `tuautor.aquamon`, version `1.0.0`,
   autor, licencia y descripcion. El ID admite minusculas, digitos y separadores
   punto/guion; los nombres de etapa admiten ASCII y hasta 12 caracteres.
2. Etapas: huevo, bebe y tres formas adultas. Nombrar cada etapa y cargar su
   reposo propio. Seleccionar cada otra accion y elegir PNG propio o reutilizar
   una animacion propia de esa misma etapa. No se crean subclases por especie.
3. Recursos: un retrato PNG cuadrado por etapa (hasta 512px), fondo de dia
   opaco de 240x135px y fondo nocturno del mismo tamano, o reutilizacion del dia.
   Portada PNG opcional. No se generan fondos nocturnos automaticamente.
4. Revisar: el servidor valida graficos y genera content.json. Corregir los
   errores antes de descargar JSON o exportar el proyecto ZIP.

Guardar borrador descarga un JSON que incluye los PNG originales codificados.
Abrir borrador restaura los campos e imagenes; se vuelve a validar antes de
exportar. No se guarda automaticamente en servidor ni navegador. Conservar el
borrador antes de cerrar o recargar: los cambios no descargados se pierden.

## Preparacion De Sprites

Una hoja PNG por animacion, con cuadros cuadrados del mismo tamano en cuadricula.
Lectura de izquierda a derecha y de arriba abajo. Indicar columnas, filas y
numero de cuadros usados; se permiten celdas finales sin usar. Ejemplo: hoja
1280x1280 con celdas 256x256 -> 5 columnas, 5 filas; si solo hay 19 cuadros,
indicar 19, no 25. Las hojas cuadradas grandes divisibles por cinco se
preseleccionan como 5x5; revisar siempre los valores.

Tambien se admite una tira horizontal o un PNG de un solo cuadro. Cada celda
debe medir hasta 512x512px. No se admiten APNG, GIF ni una seleccion de archivos
individuales por cuadro en esta entrega. Se recomienda transparencia real;
un fondo pintado se conserva y genera una advertencia, no se elimina por color.

Hasta 64 cuadros, de 10 a 1000ms por cuadro. El bucle de dormir se introduce
en la interfaz desde 1; el JSON generado lo expresa desde 0. Si no se declara,
se repite el clip completo. Se rechazan cuadros totalmente transparentes.

Recorte comun por animacion, no por cuadro: conserva la posicion relativa y
evita cambios de escala durante la reproduccion. Se normaliza a celdas de
88px, con margen de 2px, centrado horizontal y apoyo inferior. Los retratos se
preparan a 40px. BMP preparado reserva indice cero para transparencia; el
build posterior cuantiza a RGB565/VPA con las herramientas existentes.
La vista previa usa la misma geometria de normalizacion; no certifica el color
RGB565 final, FPS ni tamano en una placa fisica.

## Formato Y Limites

Solicitud: schema 1, identity, stages por rol y resources. Cada clip propio
declara use=upload, asset.data en base64, columns, rows, frames, interval_ms y
loop opcional. Un clip reutilizado declara use con una accion propia de destino;
no se permiten cadenas/ciclos. El JSON de autor no es la definicion F1.

Hasta 4 MiB por PNG, 16 MiB de PNG decodificados en total, 24 MiB por solicitud
HTTP/borrador; hasta 4096px por dimension y 8 megapixeles por imagen. No se
extraen archivos recibidos ni se escriben rutas elegidas por el autor.

Exportacion:

- content.json: definicion F1 generada y validada por PetDefinition.
- project.json: identidad, creditos/licencia, layouts de las hojas y advertencias.
- sources/: PNG originales con nombres canonicos.
- prepared/: atlas BMP, retratos y fondos normalizados para el build host.
- README.txt: alcance de la exportacion.

El ZIP es un proyecto de autor, NO un `.vpetpack` instalable. No contiene firma,
autorizacion de proveedor ni recursos VPA finales. No declara que quepa en la
placa. No incorpora ADN, sexo, individuos, partidas ni reglas de balance:
esas responsabilidades siguen en el motor/roster y futuras entregas.

Para cumplir el contrato actual de Exploracion se materializa una copia de
walk cuando el autor reutiliza otra accion para caminar. No cambia las reglas.
Fondos/retratos son del paquete; los iconos comunes siguen siendo del motor.

## Arquitectura Y Pruebas

web/hub/creator.js y creator.css: formulario, preview y estado local.
scripts/hub_creator.py: validacion acotada, conversion y ZIP en memoria.
hub_server.py: POST /api/creator/check y /api/creator/export, mismo origen,
sin CORS abierto; conserva /api/validate con su limite original de 64 KiB.

Tests: tests/test_hub_creator.py valida el contenido y reabre el ZIP para
comprobarlo con validate_art; tests/hub_creator_browser.cjs prueba el recorrido
real, descargas, borrador, desktop/mobile y canvas no vacio. El fixture reutiliza
arte existente, no representa una nueva especie comercial.
