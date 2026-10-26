# Coleccion, Experiencia Y Reproduccion

Revision local: 2026-10-25. Contrato implementado en esta rama, no desplegado
en placa. Ver [diseno aprobado](superpowers/specs/2026-10-25-collection-learning-breeding-design.md)
y [plan y evidencia](superpowers/plans/2026-10-25-collection-learning-breeding.md).
La ultima entrega fisica sigue siendo F1/F2; no confundir compilar con flashear.

## Coleccion E Inventario

- Cuatro plazas totales: un huevo ocupa la misma plaza que un adulto.
- Un individuo activo; los otros quedan congelados, sin crianza, EV, viajes
  ni descanso acreditados mientras estan inactivos.
- La mochila del individuo activo se convierte en el inventario compartido.
  La reserva antigua se conserva; su inventario no se suma automaticamente.
- Migrar, crear fundador, cambiar y cruzar requieren confirmacion explicita.
  Cancelar o abrir la pantalla no crea huevos ni concede objetos.
- El fundador local tiene identidad y ADN propios fijados al crearlo. No
  reemplaza mascotas al llenarse las plazas ni concede inventario inicial extra.
- Cuatro individuos reutilizan el arte instalado. No significa cuatro paquetes
  graficos ni cuatro lineas instalables; el instalador sigue fuera de alcance.

## Reglas Del Cruce

Dos individuos distintos, M/F, de la misma linea instalada y etapa adulta
(actualmente Firemon, Flamemon o Dragfiremon). Ambos sanos, despiertos,
sin lesion, viaje, pausa ni actividad incompatible. Salud >=80, saciedad >=60,
energia >=70 y animo >=60. El sexo no concede ventajas de combate.

Se rechazan parentescos detectables con padres y abuelos registrados. Esto
no prueba ausencia de parentesco mas remoto o desconocido. Cada padre recibe
24 horas de cooldown de tiempo encendido y no pausado de la coleccion.

La cria recibe nueva identidad, sexo independiente, ambos padres y nuevo ADN.
No hereda EV, victorias, dominio de tecnicas, inventario ni recuerdos completos.
El huevo de cruce necesita 30 minutos activo, encendido y sin pausa. Apagar o
dejarlo inactivo no lo incuba; solo se acredita tiempo confirmado por checkpoints.
Los huevos fundadores conservan la eclosion corta habitual.

## ADN Y Mutaciones

Cuatro bytes contienen ocho genes de cuatro bits, cada uno entre 0 y 15.
Los primeros seis corresponden a HP, MP, ataque, defensa, velocidad y mente.
Los otros dos forman el byte de rasgos ya usado por las reglas existentes.

Cada gen se toma de un padre. La seleccion de origen obliga a que ambos
aporten genes de stats, aunque sus valores puedan ser iguales. Por gen hay
una probabilidad de 1/32 (3,125 %) de intentar cambiarlo en -1 o +1, acotado
a 0..15. En los extremos un intento puede no cambiar el valor. Un huevo puede
tener cero, una o varias mutaciones. No genera colores, sprites, especies,
elementos ni tecnicas nuevos. Los genes cambian potencial, no EV entrenados.

Por ejemplo, un gen de velocidad heredado con valor 10 puede mutar a 11:
la cria cambia su techo genetico de velocidad, pero debe entrenar para
aprovecharlo. Los rasgos aportan predisposiciones iniciales al combate y al
descanso; no fijan para siempre sus habitos ni su humor. Entrenar no reescribe
el ADN. Estos cambios se deciden al crear el huevo de cruce.

Shiny y Evil/Umbrio son propuestas futuras, no variantes implementadas ni
resultados posibles del cruce actual. Requeririan un contrato versionado de
variante y recursos visuales compatibles, sin reinterpretar el ADN guardado.
El enojo temporal no convierte por si solo una mascota en una variante oscura.

El recibo conserva semilla, padres y version de reglas. Reintentar el mismo
comando no vuelve a tirar genes ni crea otro huevo. Nueva identidad no exige
que su ADN sea numericamente distinto del de todos los individuos existentes.

## Aprendizaje Acotado

Politica determinista por individuo, sin TinyML ni servicios externos.
Tres dominios: entrenamiento, combate y exploracion; hasta 32 contextos y
ocho acciones por contexto. Historial circular de 256 eventos y secuencia
estricta: el replay no aprende dos veces. Medias adaptativas enteras y
contadores saturados; la experiencia nueva puede cambiar preferencias antiguas.

Los adaptadores del simulador registran sesiones de atributos completadas,
lecciones de tecnicas, tecnicas ejecutadas en encuentros terminados y viajes
reclamados. Usan contexto 0 por dominio; lecciones de tecnicas usan combate,
contexto 1, separado de los resultados de Arena. Cancelar, abrir vistas o
fallar el guardado no acredita experiencia. No hay premio extra de EV/items.

AUTO puede elegir una tecnica aprendida solo entre acciones legales por
equipo, MP y cooldown; conserva el criterio anterior como desempate. Las
ordenes explicitas mantienen sus reglas anteriores. No gasta items ni inicia
entrenamientos o viajes por su cuenta. Preferencias de entrenamiento/viajes
son observables, no decisiones autonomas ni un nuevo sistema de animo.

La herencia conductual transmite solo sesgos relativos entre -25 y +25.
La cria comienza con medias, contadores, secuencias e historial vacios; no
copia experiencia completa ni estados pasajeros como enojo o cansancio.
El contrato portable existe en Python y C++. ESP32 conecta estos eventos y
AUTO mediante `LearningRuntime`, activo despues de confirmar Coleccion.
Mientras siga en modo NVS legacy no acredita politicas nuevas. El simulador
puede guardarlas en su JSON legacy antes de migrar, sin cambiar ADN.

## Arquitectura Y Persistencia

Composicion, no una subclase distinta por especie:

```text
PetDefinition -> apariencia y resolucion de recursos
Pet/PetState + PetProfile -> cuerpo, identidad y parentesco
LearningState -> experiencia y sesgos propios
Collection -> cuatro individuos + mochila unica + recibos
CollectionRepository -> commit atomico y comprobaciones
SimulatorServices / CollectionPanel -> interfaz y efectos de plataforma
```

Las reglas portables no abren archivos ni dependen de Arduino/TFT/NimBLE.
El simulador conserva generaciones JSON con SHA-256 y lectura estricta,
limite de 64 KiB y control de version/escritor. Un registro corrupto/futuro
bloquea, sin volver silenciosamente a una mochila antigua.
El adaptador desktop usa lock de escritor POSIX no bloqueante durante el
commit completo: dos simuladores no pueden confirmar sobre la misma generacion.
En hosts sin `fcntl` se rechaza el guardado de coleccion, sin escribirla.

ESP32 conserva snapshots de cuerpos y metadatos de coleccion en LittleFS,
con actual/anterior/staging, CRC y limite de 24 KiB por generacion. Los cuerpos
se leen por separado: no hay cuatro estados residentes por las cuatro plazas.
Solo se conserva la politica activa; carga, commit y cruce usan candidatas y
politicas parentales temporales. No confundir el coste residente con ese pico.
NVS legacy y su reserva quedan intactos tras la migracion explicita. Una vez
migrado, los guardados ordinarios van a coleccion y no resucitan stock legacy.
Las politicas ESP32 son blobs inmutables ligados a ID, version, secuencia y
CRC, preparados antes del commit que los referencia. La limpieza conserva
las referencias de ambas generaciones y elimina solo huerfanos propios.
Presupuesto separado de politicas: 128 KiB; bloques maximos de 12 KiB.
Politica activa/candidatas y scratch van al heap, no al stack del loop.
Los picos reales de heap/pila y las latencias quedan pendientes de placa.

No se permite reemplazar todo LittleFS con `make deploy`: borraria individuos
y aprendizaje. `make deploy-firmware` preserva el filesystem y exige assets
instalados compatibles, respaldo y autorizacion. La herramienta aun no ofrece
actualizador de assets que preserve datos ni respaldo/restauracion completo
de coleccion. Ninguna prueba host equivale a tolerancia fisica certificada.

## Guion De Demostracion

1. Opciones -> Coleccion: explicar cuatro plazas, incluyendo huevos.
2. Activar coleccion con confirmacion; mostrar mochila sin stock adicional.
3. Nuevo huevo -> confirmar: mostrar identidad independiente, no una skin.
4. Activar otra mascota y volver: inventario compartido, progreso individual.
5. Con dos adultos aptos: elegir padres, confirmar cruce y mostrar huevo.
6. Explicar incubacion activa, cooldown y potencial genetico, sin prometer
   nuevas formas visuales por mutacion.
7. En el simulador, entrenar/batallar/explorar y consultar Preferencias;
   distinguirlo de TinyML y de lo efectivamente validado en la placa.

Antes de video comercial faltan aceptacion fisica, reinicios/cortes,
sesion larga con BLE y pruebas de politica en el dispositivo real.
