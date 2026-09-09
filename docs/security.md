# Seguridad y proteccion del firmware

## Principio

No existe una tecnica que haga un dispositivo imposible de hackear. La meta es
reducir riesgo, proteger claves y datos, impedir firmware no autorizado y hacer
costosa la extraccion del producto.

La ofuscacion por si sola no es una frontera de seguridad. El C++ compilado
dificulta la lectura respecto a Python, pero un atacante puede extraer y
desensamblar un binario si la plataforma no esta protegida.

## Desarrollo frente a produccion

### Placas de desarrollo

Mantener:

- carga serial habilitada;
- logs y `VPET_READY`;
- JTAG/depuracion disponible cuando sea necesario;
- firmware y LittleFS sin cifrado irreversible;
- claves de prueba separadas de produccion.

Esto permite continuar desarrollando con `make deploy` sin bloquear la placa.

### Unidades de produccion

Evaluar un proceso de provisionamiento separado que habilite:

- Secure Boot v2;
- Flash Encryption en modo Release;
- NVS Encryption cuando aplique;
- actualizaciones OTA firmadas;
- anti-rollback;
- desactivacion de JTAG y modos de descarga no requeridos;
- clave de cifrado unica por dispositivo;
- custodia externa de la clave privada de firma.

Estas opciones programan eFuses. Algunas decisiones son irreversibles y pueden
impedir usar `esptool` de la forma habitual. Deben probarse primero en placas
descartables de provisionamiento, nunca directamente en la unica placa de
desarrollo.

## Contenido comunitario

Themes y mascotas no deben ejecutar codigo. El firmware interpreta datos VPA y
un manifiesto limitado. Esto reduce el riesgo de que un paquete tome control del
dispositivo.

Cada paquete publicado debe incluir:

- hashes de archivos;
- firma verificable;
- limites de compatibilidad;
- identidad y licencia del autor;
- analisis de rutas y tamano;
- version inmutable.

## Red

- Descargas y APIs usan HTTPS con verificacion de certificado.
- La prueba HTTP actual solo detecta si existe salida a Internet.
- Nunca se imprime la contrasena WiFi por serial.
- NVS no se agrega a backups publicos ni al repositorio.
- Tokens del catalogo deben ser cortos, revocables y de privilegio minimo.

## Repositorio

Se versionan codigo, pruebas, documentos y arte fuente necesario para un build
reproducible. Se excluyen:

- `.pio/`, `build-tdisplay/` y salidas generadas;
- `out/` y backups de flash;
- credenciales y dumps NVS;
- claves privadas, certificados privados y secretos CI;
- librerias binarias antiguas que pueden descargarse desde su proveedor.

## Plan recomendado

1. Mantener la placa actual en modo desarrollo.
2. Definir paquetes declarativos y firmas.
3. Implementar instalacion y OTA autenticadas.
4. Crear una configuracion de firmware `production` separada.
5. Automatizar provisionamiento de claves y eFuses.
6. Probar recuperacion, actualizacion y rollback en placas dedicadas.
7. Solo entonces fabricar unidades bloqueadas.
