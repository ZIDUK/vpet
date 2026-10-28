# Desarrollo Guiado Por Especificaciones, Sin GitHub Actions

## Flujo Obligatorio Del Piloto

1. Crear spec desde docs/templates/spec.md: que debe cumplirse, limites y aceptacion.
2. Registrar SPEC/REQ/AC/DEL en docs/requirements.json. Nunca renumerar un ID publicado;
   un cambio incompatible requiere una revision explicita del contrato.
3. Revisar/aprobar la spec. La aprobacion de alcance no aprueba automaticamente el texto.
4. Crear un plan separado enlazando IDs: archivos, pasos, pruebas y evidencia.
5. Implementar con regresiones; ejecutar make spec-check y make verify-local.
6. Registrar entrega/commit y aprobacion aplicable. Para firmware, ejecutar tambien
   make verify-local-full y el gate fisico existente antes de afirmar aceptacion.

El piloto cubre Creator y el propio proceso, no toda la historia del juego.
Creator es una reconstruccion retrospective-review; no inventa aprobacion anterior.
Las aprobaciones registradas son declaraciones humanas, no firmas autenticadas.

## Comandos

```sh
make spec-check          # referencias/estructura y coleccion de tests, no ejecucion
make verify-local        # piloto Python, sintaxis JS y dos recorridos Chromium
make verify-local-full   # agrega suite completa, generados, native y build ESP32
make release-check       # exige aprobacion, evidencia y commit real; el piloto no pasa aun
```

No se crean workflows de GitHub Actions, hooks ni cambios de configuracion Git.
Los comandos locales pueden omitirse: la obligatoriedad es politica de desarrollo,
no una proteccion remota imposible de eludir. No hay CI remoto en esta entrega.
Ningun comando de esta pagina flashea, abre USB o publica.

## Dependencias

Python/Pillow/pygame/pytest de requirements-dev.txt. El perfil full requiere ademas
PlatformIO, compilador C++ y las dependencias de firmware de platformio.ini.
Las pruebas web requieren Node.js, Playwright resoluble y Chromium instalado:

```sh
# Entorno Node aislado fuera del codigo de la aplicacion:
npm install --prefix /tmp/vpet-verification playwright
NODE_PATH=/tmp/vpet-verification/node_modules node /tmp/vpet-verification/node_modules/playwright/cli.js install chromium
NODE_PATH=/tmp/vpet-verification/node_modules make verify-local
```

No se descargan dependencias automaticamente al verificar. Un Playwright ausente
falla con log y no se convierte en un test omitido aprobado. Puede usarse un
runtime ya instalado mediante NODE_PATH. El runner crea un servidor loopback
temporal en otro puerto, lo detiene al terminar y deja intacto el Hub del usuario.

Preflight de almacenamiento: perfil full requiere 6 GiB libres tanto en el
workspace como en temporales; Creator requiere 128 MiB. Es un margen preventivo,
no garantia frente a otros procesos. Se reserva 1 MiB para escribir el reporte
al terminar; si aun falla su persistencia, se imprime JSON de respaldo en stderr
y se devuelve fallo, nunca un resultado exitoso sin evidencia. Pytest detiene
el intento tras el primer fallo para evitar cascadas de errores por disco lleno.

## Registro Y Evidencia

schema=1 con tres tablas: specs, requirements y deliveries. Cada requisito enlaza
spec, heading de criterio, implementacion, pruebas y entrega. Un test Python usa
file.py::test_func[parametro] o file.py::Clase::test_func; los parametros se
resuelven de verdad con --collect. Un browser test enlaza un script .cjs completo.

Estados de spec: draft, scope-approved, retrospective-review, approved. Estados
de requisito: proposed, approved, implemented, verified. Las entregas empiezan
local-unreleased con commit=null: no usar el HEAD actual como supuesto commit
del codigo sin versionar. El runner no modifica estos estados.

out/local-verification/<fecha-UTC>-<id>/ conserva report.json, JUnit, comandos,
codigos de salida, duraciones y logs. La huella SHA-256 incluye rutas y contenido
de archivos Git versionados/no ignorados, incluidos cambios sin commit; no es el
hash de firmware. Si cambia el arbol durante el run, el resultado no es passed.
Los artefactos ignorados no forman parte de esa huella. No compartir logs/status
sin revisarlos por datos locales. Los reportes no se agregan automaticamente a Git.

Un resultado pasado acredita solamente los checks y el snapshot indicados.
Un requisito verificado referencia un reporte pasado que lo incluye; sigue
siendo necesaria revision de correspondencia semantica entre prueba y criterio.
Para release se exigen specs aprobadas con evidencia, requisitos verificados y
entregas con commit existente. Es control documental, no autenticacion criptografica.

El reporte declara acceptance=automated-only, hardware=not-run y published=false.
El perfil Creator no acredita C++/ESP32; el perfil full tampoco acredita placa,
radio, rendimiento fisico, publicacion ni licencia de contenido.

## Evidencia De Skills

En cada plan registrar que skills se consultaron y que verificaciones se completaron.
Una skill disponible o un nombre escrito no certifican que se aplicaron todos sus pasos.
En esta entrega se consultaron writing-plans, test-driven-development,
ai-debt-detector y verification-before-completion; los resultados ejecutados
quedan en el reporte local.
