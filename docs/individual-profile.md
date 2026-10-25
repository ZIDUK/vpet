# Perfil Individual F2a

Revision local 2026-10-24. Implementado en Python/simulador y C++/ESP32;
sin carga a placa ni validacion fisica. No modifica Status ni las reglas
de evolucion. [Plan y evidencia](superpowers/plans/2026-10-24-f2a-individual-profile.md).

## Modelo Y Ciclo De Vida

`Pet.profile` / `PetState.profile` contienen `PetProfile`, separado del
ADN y de `PetDefinition`. Un perfil asignado tiene ID de 128 bits, sexo M/F
y dos IDs de padres o ambos desconocidos. La eleccion es equiprobable por
individuo con entrada uniforme; no garantiza mitades exactas en una familia.
No hay ventaja de combate por sexo. El huevo ya conserva su sexo, pero esta
fase no lo muestra en pantalla ni decide un nuevo diseno de Status.

Eclosionar o evolucionar conserva ID, sexo y padres. Reiniciar una vida
limpia el perfil: el siguiente guardado productivo asigna otro ID antes de
publicar la nueva partida. La reserva existente conserva el perfil junto con
ADN, progreso, sueno y objetos. Copiar/restaurar un respaldo identificado
recupera al mismo individuo; no crea una cria ni una identidad nueva.

Un ID probabilistico no prueba autoria, propiedad ni autenticidad de un
paquete. No se publica por BLE ni se deriva de la MAC, ADN, especie o stats.
Sin roster/registro global no hay deteccion de clones ni garantia matematica
de ausencia de colisiones. Breeding, recombinacion y elegibilidad familiar
siguen pendientes; guardar referencias no implementa esas reglas.

## Contrato Portable

Registro canonico de una linea, maximo 102 caracteres:

```text
1:<32 hex minusculas>:M|F:<id-padre-a|->:<id-padre-b|->
1:00000002000000030000000400000005:M:-:-
```

`from_words` / `fromWords` recibe cuatro uint32; concatenacion hexadecimal
de ancho ocho, en el mismo orden. El bit inferior de la primera palabra
elige F si es uno, M si es cero. No utiliza ni altera genes. Rechaza ID
cero, mayusculas, delimitadores extra, sexo invalido, versiones desconocidas,
padres parciales, repetidos o el propio hijo. A/B son referencias sin orden
sexual asignado; el futuro servicio de breeding comprobara los perfiles.

Cadena vacia significa perfil aun no asignado, no una tercera identidad o
sexo comercial. El dominio permite ese estado para previews y fixtures sin
I/O. Los repositorios productivos inyectan la generacion; nunca se genera
un ID al dibujar, consultar stats o importar una definicion F1.

## Entropia De Plataforma

- Simulador: `os.urandom(16)`, en el adaptador, no dentro del core portable.
- ESP32: `ProfileRandom` siembra CTR-DRBG de mbedTLS al inicio de `setup`,
  antes de pantalla, ADC y BLE. Activa temporalmente la fuente SAR interna,
  recoge entropia para la siembra y la desactiva incluso si falla. Despues
  genera perfiles desde el DRBG sin activar radio ni acceder al ADC.
  No reabre la fuente durante juego; una peticion de reseed fuera del arranque
  falla cerrada. Un fallo inicial bloquea arranque con `PROFILE_ENTROPY`.

Este orden sigue la [documentacion de Espressif sobre RNG](https://docs.espressif.com/projects/esp-idf/en/v4.4.5/esp32/api-reference/system/random.html):
sin RF ni fuente interna habilitada no se debe asumir entropia continua
al llamar `esp_random()`. No habilitamos WiFi para generar IDs.
El test host del adaptador usa stubs para orden/fallos, no certifica entropia
fisica ni reemplaza las pruebas propias de mbedTLS.

## Persistencia Y Compatibilidad

JSON del simulador agrega `profile`; NVS agrega `petProfile` en los namespaces
existentes. Se conserva schema 3 y todos los enums anteriores. Snapshot v5
incluye el perfil en el mismo `saveTx`/`swapLive`/`swapBack` que el estado;
el lector sigue aceptando v1-v4. Un journal historico sin perfil no borra la
clave aditiva del destino. Fixtures sin generador pueden seguir emitiendo v4.

La carga productiva recupera journals primero, valida el perfil existente
y, si falta, crea un fundador y guarda antes de continuar. La reserva legacy
se migra al cargarla para un intercambio. La migracion de perfil no acredita
items, victorias, experiencia ni otra recompensa; los mecanismos legacy de
ADN/nutricion existentes siguen aplicandose a las partidas que los necesiten.
No cambia rutas de archivos ni elimina reservas.
Si la bandera legacy `life=0` requiere reiniciar una vida, la carga no la
cancela al migrar: App ejecuta su reinicio existente y asigna identidad al
huevo en ese guardado. No se crea un individuo adulto transitorio.

Un rechazo no publica la identidad candidata. Un intent aceptado pero aun
Pending conserva el candidato y bloquea nuevas acciones hasta sincronizar.
Si el intent no sobrevivio al corte, nunca hubo una nueva identidad duradera;
reintentar puede crear otra. Si sobrevivio, el replay reutiliza su ID, sexo y
padres, no vuelve a lanzar la generacion. Es la misma semantica de NVS ya
usada para comidas, premios y swaps.

`SettingsStore` recibe `ProfileGenerator` desde `main.cpp`; el constructor
sin proveedor se conserva para fixtures/compatibilidad. `save(PetState&)`
publica el candidato solo tras aceptar el intent. El overload const conserva
la API de snapshots anteriores, pero rechaza asignar una identidad que no
podria devolver al modelo. No usar un repositorio sin proveedor en produccion.

Simulador usa su reemplazo JSON atomico habitual; al fallar migracion restaura
todo el modelo y bloquea escrituras hasta una carga valida. Un perfil corrupto
o futuro no se sustituye por un fundador. Pruebas host no certifican todos los
modos de perdida de energia del sistema de archivos ni la flash fisica.
La ruta Pico legacy conserva el codec pero no incorpora esta nueva migracion
ni fuente de entropia: no se declara F2a desplegado en Pico.

## Verificacion Y Pendientes

Casos dedicados en `tests/test_pet_profile.py`, `tests/pet_profile.cpp` y
`tests/profile_random.cpp`; el adaptador NVS real se ejercita con su driver
stub en cuatro casos `profile_*` de `tests/test_platform_storage_ble.py`.
Incluyen 1024 registros identicos Python/C++, corpus de rechazo, parentesco,
nueva vida/evolucion, mismo ADN con distinto ID, sexo sin ventaja de stats,
migracion, fallo de reemplazo, cortes antes de cada escritura de migracion
y de ambos lados del swap, y Pending/reinicio con intent durable o perdido.

Pendiente: carga autorizada, reinicios/swap fisicos y confirmacion en placa,
visibilidad del sexo, roster de hasta cuatro, inventario compartido de
coleccion, premios/huevos, breeding y herencia conductual. No hay nuevos
permisos de radio, instalacion ni regalos activados por esta entrega.

Cierre local: 1768 Python/185 nativas aprobadas, ESP32 compilado; RAM estatica
56228 bytes y app 1044313 bytes. Registro reproducible y hashes en
`out/individual-profile/verification.json`. No equivale a medir heap/FPS ni
entropia o persistencia bajo perdida de energia de una placa fisica.
