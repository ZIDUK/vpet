# Paquetes de mascotas y themes

## Objetivo

Permitir que autores publiquen mascotas y themes en un catalogo web, que los
usuarios puedan previsualizarlos e instalarlos sin recompilar el firmware.

Esto es posible con la T-Display actual. LittleFS ofrece aproximadamente 12.45
MB, por lo que el instalador debe comprobar capacidad y permitir desinstalar
contenido.

## Enfoque recomendado

La plataforma se divide en tres piezas:

1. Catalogo web con previews, autor, licencia, versiones y archivos firmados.
2. Paquete declarativo `.vpetpack`, sin codigo ejecutable.
3. Instalador por USB/Web Serial inicialmente y descarga HTTPS posteriormente.

BLE se usa para aprovisionamiento y comandos pequenos, no para copiar sprites.

## Formato propuesto

`.vpetpack` es un ZIP utilizado para distribucion. El navegador o herramienta
de escritorio lo valida y envia sus archivos individualmente al dispositivo.

```text
manifest.json
preview.png
animations/idle.vpa
animations/walk.vpa
animations/eat.vpa
animations/punch.vpa
animations/sleep.vpa
animations/cast.vpa
animations/evolution.vpa
portraits/default.vpa
backgrounds/day.vpa
backgrounds/night.vpa
signature.json
```

Un paquete puede ser `pet`, `theme` o `bundle`. No todos los tipos requieren
todos los archivos.

## Manifiesto minimo

```json
{
  "schema_version": 1,
  "package_id": "author.firemon",
  "package_type": "pet",
  "version": "1.0.0",
  "name": "Firemon",
  "author": "Author name",
  "license": "CC-BY-4.0",
  "min_firmware": "1.0.0",
  "display_profile": "tdisplay-240x135",
  "files": [
    {"path": "animations/idle.vpa", "sha256": "...", "bytes": 12345}
  ]
}
```

La especificacion final debe agregar especies, acciones, numero de frames,
duracion por frame, puntos de anclaje y relaciones de evolucion.

## Reglas de seguridad

- Solo datos: no C++, Python, JavaScript ni bytecode.
- Rutas relativas normalizadas; se rechazan `..` y rutas absolutas.
- Limites estrictos de archivos, dimensiones, frames y bytes.
- SHA-256 para integridad de cada archivo.
- Firma del catalogo y de paquetes aprobados.
- Activacion atomica: el paquete incompleto nunca se vuelve activo.
- Rollback al paquete anterior si validacion o carga falla.
- Licencia y atribucion obligatorias.

## Almacenamiento en dispositivo

```text
/packs/<package_id>/<version>/manifest.json
/packs/<package_id>/<version>/...
```

NVS conserva el ID/version activa y el inventario de paquetes. Los archivos
permanecen en LittleFS. La mascota guardada debe referenciar un `package_id`
estable, no una ruta concreta.

## Instalacion fase 1: USB

El sitio puede usar Web Serial desde Chrome o Edge. El firmware expone un
protocolo de instalacion que:

1. consulta version y espacio;
2. abre una transaccion;
3. recibe manifiesto y archivos por bloques;
4. valida hashes y limites;
5. confirma o revierte;
6. activa el paquete seleccionado.

No se debe reemplazar toda LittleFS con cada instalacion porque eliminaria otros
paquetes. Tampoco se debe borrar NVS.

## Instalacion fase 2: WiFi

El usuario elige contenido en la web y recibe un codigo corto. En el vPet
introduce ese codigo; el dispositivo consulta el catalogo por HTTPS, descarga el
paquete, verifica su firma y lo activa.

Esta opcion evita navegar un catalogo complejo en 240x135.

## Flujo para autores

1. Descargar una plantilla de paquete.
2. Agregar PNG fuente y metadata.
3. Ejecutar un validador local que produce VPA y previews.
4. Probar el paquete en el simulador.
5. Enviar el paquete al catalogo.
6. Ejecutar validacion automatica, licencia y moderacion.
7. Firmar y publicar una version inmutable.

## Compatibilidad

El firmware debe ignorar campos desconocidos y rechazar versiones de esquema
mayores a las soportadas. Una nueva version del paquete nunca debe modificar en
sitio una version publicada; se publica con otro numero semantico.

## Estado de implementacion

El proyecto ya tiene VPA1, manifest generado, LittleFS y validacion de capacidad.
Faltan el esquema publico, validador de paquetes, protocolo USB, catalogo web,
firmas y gestor de instalaciones. Este documento define la direccion, no afirma
que esas piezas ya existan.
