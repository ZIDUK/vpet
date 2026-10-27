# Estado y alcance del proyecto

## Estado vigente: 2026-10-27

## Mochila, Luz Y Comidas Seguidas: Cargada, Fluidez Rechazada En Placa

El usuario reporta espera en Mochila, al cambiar luz y al volver a alimentar.
La primera correccion solo adelantaba Eat y bloqueaba otra transaccion durante
el guardado; Mochila/luz seguian sincronas. Se prepara `CareSave` compartido para
las tres rutas y menos I/O en Coleccion, sin colas ilimitadas ni consumo doble.
Prueba de archivo con dos mascotas: 56 -> 9 aperturas y 81 -> 5 seeks; conserva
CRC, generacion anterior, sync y rename atomico. No equivale a una aceleracion
fisica medida. No cambia reglas de comida, schema, graficos ni Status.
Suite final aislada sin Creator: 2021 aprobadas en 305.91 s; 54 focalizadas
en 29.74 s y 185 nativas en 1.793 s. Revision independiente sin hallazgos
accionables. Build final: 7.670 s, RAM estatica 53284 y app 1106513 bytes.
El usuario autoriza firmware-only 643ca42. Build preflash repetido: 3.544 s;
12 focalizadas aprobadas en 13.59 s. Fuentes aisladas y SHA coinciden, sin
Creator. Respaldo actual: out/board-backups/responsive-care-20261026-194021/.
App escrita solo en 0x10000; hashes verificados, LittleFS, NVS, bootloader y
particiones identicos antes del reinicio. Al retomar el 2026-10-27 se confirma
el proceso completado, sin volver a cargar. VPET_READY: heap 80892/minimo
71368, flash 16 MiB, manifest 1. Bin/ELF en out/responsive-care.
Captura real 20261027-054159: luz presenta en 134/142 ms y guarda en
5924/7016 ms; item presenta en 211 ms y guarda en 4175 ms; dos MEAT presentan
en 84 ms y guardan en 6963/6636 ms. Son tiempos desde el handler, no desde el
contacto fisico del boton. Cinco commits settled=1, cero comandos enviados por
el agente; una secuencia de arranque al abrir USB y ninguna linea fatal.
Pila libre minima del worker 3648 bytes, heap minimo 44364; loop maximo
3122339 us. La pila no se agoto en esta captura, pero el heap bajo carga no
acredita un margen amplio. BLE=0, sin validacion de radio.
El usuario confirma que comienza la animacion y luego queda quieta en luz,
MEAT y Mochila. Se rechaza la fluidez de 643ca42: reducir aperturas en host
no elimino las pausas reales. La partida no se restaura ni se repiten consumos
por el agente. Siguiente propuesta, aun no implementada/autorizada: persistencia
compacta transaccional de cuidado, separada de checkpoints completos de Coleccion.
[Plan y evidencia](superpowers/plans/2026-10-26-responsive-care.md).

## Alimentacion Inmediata Y Guardado De Fondo: Respuesta Visual Aceptada

Implementado para MEAT/PROTEIN: primer dibujo Home/Eat antes de iniciar el
escritor FreeRTOS, un snapshot pendiente como maximo y NEXT disponible mientras
ACTION/Back no abren transacciones dependientes. No comparte mascota mutable
con el worker ni considera guardada una accion encolada. Collection combina
tiempo/cooldown/incubacion y cuerpo en un commit; legacy conserva el snapshot
completo por saveTx para no perder evolucion/cuidado ocurridos al alimentar.
Rechazo restaura estado y cancela Eat; journals aceptados pero sin replay
completo bloquean nuevos cambios, con reintento espaciado y tiempo conservado.

Suite aislada sin Creator: 2020 aprobadas en 292.43 s. Tras el ultimo ajuste
de cancelacion se repiten 104 focalizadas: aprobadas en 58.78 s. No es una
segunda suite completa sobre ese ajuste. Build aislado final aprobado en
19.628 s: RAM estatica 52244 y app 1106637 bytes; tarea lazy de 8192 bytes.
Nativas finales: 185 aprobadas en 0.933 s.
El usuario autoriza cargar y validar; firmware-only 0752e79 cargado el
2026-10-26 sin Creator. Build preflash repetido: 3.218 s; dos pruebas
focalizadas aprobadas en 6.34 s. Fuentes aisladas y SHA del binario coinciden.
Respaldo actual: out/board-backups/responsive-feeding-20261026-183627/.
App escrita solo en 0x10000; hashes de app, LittleFS, NVS, bootloader y
particiones verificados antes del reinicio. VPET_READY: heap 82520/minimo
72936, flash 16 MiB, manifest 1. Estas medidas preceden la creacion lazy
del worker. Ante la pregunta por inicio inmediato y animacion sin pausas en
FEED -> MEAT, el usuario confirma "ahora si". Aceptacion visual cualitativa,
no medida de latencia. La captura 20261026-184635 duro 180.061 s y no registro
entradas ni resultados de comida; la respuesta llego despues del cierre.
Siguen pendientes tiempos numericos, pila/heap durante guardado, PROTEIN y BLE.
No cambia Status, graficos ni schema. Corte de energia antes del commit puede
perder la ultima comida pendiente. [Plan y evidencia](superpowers/plans/2026-10-26-responsive-feeding.md).

## Alimentacion: Animacion De MEAT Validada En Placa

Captura real 20261026-132239: ACTION recibido en Feeding, result=0 y
committed=1; saciedad 96 -> 100, energia 18 y animo 0. En ese intento el
usuario seguia percibiendo FEED. Se observa un ciclo de 5094923 us;
la animacion usaba
el timestamp anterior al guardado y podia agotarse en la espera. Regresion
RED con demora de 5000 ms reproduce el salto; GREEN al iniciar Eat con
el tiempo compensado desde el inicio de tick, sin alterar efectos de comida.
Incluye rollover uint32 y dos adultos, consumo unico y rollback previos.
89 focalizadas (38.21 s), 185 nativas (0.503 s) y build aislado (7.925 s)
aprobados; RAM 52236 y app 1104233 bytes. No cambia assets, Status ni schema.
El usuario autoriza firmware-only y se carga 81cee4b, sin Hub/Creator.
Build preflash repetido (3.470 s), prueba focalizada (5.66 s) y hashes de
fuentes/binario verificados. Respaldo actual en out/board-backups/
feeding-animation-fix-20261026-135552/. App cargada solo en 0x10000;
hashes de app, LittleFS, NVS, bootloader/particiones verificados antes del
reinicio. VPET_READY: heap 82948/minimo 73328, manifest 1. El usuario confirma
el 2026-10-26: "Si, aparece la animacion completa" al probar MEAT. Se cierra
el salto de Eat para esa comprobacion fisica; no acredita PROTEIN ni BLE.
El agente no ejecuta comida por el usuario. El guardado de varios segundos
no se optimiza en esta correccion. Detalle en el registro abajo.

## Alimentacion: Diagnostico Serie Cargado

El usuario vuelve a confirmar que ACTION permanece en FEED. Los valores
reportados (salud 100, saciedad 6, energia/animo 0, pausa OFF) no explican
rechazo por saciedad. Se prepara instrumentacion acotada de App: entrada,
guardas, FoodResult y resultado del commit, sin cambiar reglas ni interfaz.
La captura USB anterior ya habia terminado y no registro el nuevo intento.
El usuario autoriza firmware-only 607efbb. Build aislado repetido en 3.260 s,
sin Hub/Creator concurrentes: RAM 52236, app 1104181 bytes. Prueba focalizada
preflash aprobada en 5.59 s. Respaldo nuevo completo de LittleFS actual,
particiones/NVS y app anterior en out/board-backups/feeding-diagnostic-20261026-131129/.
Carga solo en 0x10000, digest de app verificado, LittleFS/NVS/bootloader y
particiones identicos antes de arrancar. VPET_READY: heap 82948/minimo 73320,
manifest 1. El agente no ejecuta comida por el usuario. El diagnostico
ya esta instalado; el intento posterior capturado se describe arriba. Ver
[registro y lectura de trazas](superpowers/plans/2026-10-26-feeding-menu-diagnostic.md).

## Coleccion: Guardado Y Cambio Aceptados; Alimentacion En Diagnostico

IMG_4260 muestra 2/4: Firemon M activo y Flamemon F. Tras solicitar guardar,
reiniciar y comparar, el usuario confirma conservacion de individuos, activo,
progreso y mochila. Tambien confirma stats propios al cambiar de mascota y
cantidades iguales en la mochila compartida. No acredita aun cuatro plazas,
fundador, cruce, herencia, incubacion ni cooldown en placa.

Durante la preparacion de padres reporta que confirmar MEAT permanece en
FEED sin animacion; IMG_4262 muestra el selector, no los valores de cuidado.
No se atribuye a pausa, saciedad ni guardado sin esos datos. El App real
con Coleccion sintetica si inicia Eat y avanza fotogramas al aceptar carne
y proteina en Firemon/Flamemon; rechazar por saciedad/ciclo o pausa mantiene
FEED sin mutacion. La etiqueta UNLIMITED actual no explica esos rechazos.
IMG_4263 posterior muestra Firemon con salud 100, saciedad 6, energia 0 y
animo 0; usuario confirma Pause Pet OFF. Esos valores no justifican rechazo
por saciedad; sigue pendiente capturar la accion y su resultado real. Una
lectura USB de 90.058 s incluye arranque, ocho muestras runtime estables y
cero entradas; no reproduce el intento. Sin cambios de produccion, reglas de
alimentacion, partida ni firmware instalado. Ver
[diagnostico acotado](superpowers/plans/2026-10-26-feeding-menu-diagnostic.md).

## Coleccion Visible Y Reanudacion De Home Confirmadas

Confirmacion fisica posterior del usuario: "si lo coloco off, ya se mueve".
Queda verificada la reanudacion de Home al desactivar Pause Pet en la placa,
sin otra carga de firmware ni despausa automatica por el agente. El origen
de la transicion anterior OFF -> ON no quedo identificado; esta aceptacion
no acredita ausencia de recurrencias ni sesiones largas. El diagnostico
inferior conserva la secuencia de reportes y comprobaciones anteriores.

El usuario aporta IMG_4257/4258/4259: cuadricula de cuatro plazas, dos
individuos (Firemon M y Flamemon F), ficha y Flamemon activo en Home.
Esto confirma apertura de coleccion/ficha y cambio de activo en pantalla;
no certifica breeding, huevos nuevos, sesiones largas ni todos los reinicios.
Las notas de aceptacion pendiente de las entregas inferiores describen el
estado previo a estas fotos.

Nuevo reporte de Home sin cambiar fotogramas: usuario confirma "Pause Pet ON".
App::tick conserva ese comportamiento de pausa mediante motion.alignClock,
sin avanzar los fotogramas. Se indica poner OFF sin reiniciar ni flashear;
el usuario responde que OFF no reanuda la animacion. No se considera resuelto
por haber identificado inicialmente ON. No se modifica la partida ni se
despausa automaticamente por el usuario.
Observacion USB de 70.083 s: seis muestras, 17 entradas, heap libre estable
82948/minimo 73372, sin reinicios adicionales ni fatal, BLE=0. No demuestra
por si sola animacion. Evidencia: `out/home-pause-verification/observation.json`.

Diagnostico posterior: respaldo nuevo de NVS/particiones y LittleFS actual en
`out/board-backups/20261026-home-resume-diagnostic/`, sin escrituras flash;
la lectura por bootloader requiere reinicio tecnico al terminar. LittleFS
completo verificado por digest, incluyendo los archivos actuales de Coleccion.
El lector LittleFS moderno y CollectionStore real confirman activo Flamemon,
pausa ON, despierto, sin viaje ni accion pendiente, energia 0. La generacion
anterior tiene pausa OFF. Esto acredita ambos guardados, no demuestra por
que volvio a ON ni si hubo otra pulsacion. Se pide comprobar etiqueta actual
y respuesta de NEXT. No se carga otro firmware ni se restaura el respaldo
antiguo de solo assets: ahora existen partidas de Coleccion en el filesystem.
La prueba host del App real cubre activar una reserva pausada y agotada,
volver a Home y quitar pausa desde Opciones; no sustituye aceptacion fisica.
89 pruebas focalizadas aprobadas en 37.31 s (App, persistencia, Arena,
evolucion, aprendizaje, exploracion y sueno); advertencias existentes de
Pillow. Solo se anaden pruebas y diagnostico, sin otra carga en placa.

## Coleccion: Motivo Del Bloqueo Cargado

El usuario reporta "Not Available" tras la correccion de pila. En la ruta de
confirmacion ese aviso generico corresponde a una proteccion de sesion; aun
no se ha confirmado que condicion estaba activa en su mascota. Se precisa
el motivo y accion ES/EN sin relajar las restricciones de sueno, pausa,
viaje, entrenamiento, batalla, accion pendiente o guardado/almacenamiento.
24 pruebas focalizadas aprobadas, con ocho causas del controlador real en
ambos idiomas y ninguna escritura ni identidad nueva al bloquear. Native:
185 aprobadas; ESP32 compilado en 9.320 s. Sin cambios de assets, Status,
schema o reglas de evolucion. Usuario autoriza y se carga firmware-only
`dabc2e7`, conservando la correccion de pila, NVS y LittleFS. Compilacion
preflash repetida en 3.435 s y 24 pruebas repetidas en 22.16 s; RAM estatica
52236, app 1103785 bytes. Arranque `VPET_READY`, heap libre 90888/minimo
88220, manifest 1. El usuario indica que estaba en Home; eso no identifica
por si solo el bloqueo. Mensaje concreto y activacion fisica siguen pendientes.
Ver [registro de carga](superpowers/plans/2026-10-26-collection-blocker-messages-delivery.md).

## Activacion De Coleccion: Correccion Cargada

El usuario acepta visualmente el rediseno pero detecta reinicio al confirmar
Enable. Captura serie y backtrace confirman desbordamiento de pila loopTask
durante la serializacion en CollectionStore::migrate. Se reducen temporales
de pila con RAII; no se cambian datos, reglas ni schema. Prueba preventiva
de host pasa de 3072 a 1024 bytes por frame; migracion Xtensa 2384 -> 304.
33 pruebas focalizadas, 2038 Python completas y 185 nativas aprobadas;
compilacion ESP32 con RAM estatica 52236 y app 1102745 bytes. Respaldo critico
y app nuevos verificados. Usuario autoriza firmware corregido, cargado sin
activar Coleccion por el: `VPET_READY`, heap libre 90896/minimo 87524,
manifest 1. Validacion fisica de la activacion sigue pendiente; un arranque
correcto no acredita aun resuelto el flujo que fallaba.
Ver [diagnostico y entrega](superpowers/plans/2026-10-26-collection-enable-stack.md).

## Coleccion Visual: Cargada En Placa

Redisenada con cuatro plazas ilustradas, ficha grande, preferencias y seleccion
visual de dos padres antes de confirmar el huevo. Bienvenida con la mascota
actual y "Tu coleccion" en lugar de "Migrar"; abrirla no activa la coleccion.
No cambian reglas de breeding, ADN, inventario ni persistencia. Presentacion
separada en `CollectionView.cpp`, sin otro framebuffer ni assets nuevos.

2038 pruebas Python y 185 nativas aprobadas; firmware compilado: RAM estatica
52236 bytes (+8), app 1102817 bytes. La suite incluye Creator concurrente
solo como pruebas; sus cambios siguen fuera de esta entrega. Firmware nuevo
cargado con autorizacion expresa, respaldo critico y de app nuevos, mas copia
completa anterior de LittleFS comprobada contra el dispositivo. Digests de
firmware y LittleFS coinciden despues de cargar; no se reemplazo el filesystem
ni se borro NVS. Arranque `VPET_READY`: heap libre 90888/minimo 88220,
manifest 1. No se activo la coleccion, creo huevos ni cruzo mascotas por el
usuario. Aceptacion visual de esta revision y flujos reales siguen pendientes.
Observacion serie de 70 s: seis muestras, heap libre estable 90888 y minimo
85732; sin reinicios adicionales ni fatal. BLE=0, sin eventos de entrada:
no acredita radio, navegacion ni fluidez de Coleccion.
Ver [plan y evidencia](superpowers/plans/2026-10-26-visual-collection.md)
y [manual](product-guide.md).

## Coleccion, Aprendizaje Y Breeding: Cargados En Placa

Cuatro plazas contando huevos, mochila compartida sin sumar la reserva,
fundador local confirmado y cruce determinista con mutacion acotada. Core
portable Python/C++, generacion de recibos, repositorio con fallos inyectados
y UI de coleccion local. Simulador registra experiencias y consulta politica
en AUTO; ESP32 conecta los mismos eventos, herencia y AUTO tras activar
Coleccion. Politicas inmutables con GC que conserva ambas generaciones.
Verificacion final aislada, sin Creator: 1984 Python aprobadas (295.99 s),
185 nativas (0.544 s) y ESP32 compilado (8.739 s). RAM estatica 52228,
app 1098849 bytes. La suite previa de 2003 incluia archivos locales de Creator.
Advertencias existentes de Pillow/pytest y TOUCH_CS; sin fallos.
Firmware cargado el 2026-10-25, sin reemplazar LittleFS ni NVS. Respaldo
completo de 16 MiB verificado; app instalada y filesystem original comprobados
por digest. La primera carga detecto heap de 63892 bytes, por debajo del
minimo de 65536: no se declaro correcta. Cache Training bajo demanda recupera
5840 bytes estaticos sin reducir sus diez iconos, RGB565 ni reutilizacion.
Segunda carga: `VPET_READY`, heap 69712/minimo 69636, manifest 1, BLE conectado.
Observacion serial de 70 s: seis muestras, heap libre estable 69712, minimo
64572, sin reinicios ni fatal; sin eventos de entrada, no certifica fluidez.
Nueva aceptacion fisica de los flujos pendiente. Creator concurrente
se conserva y sigue fuera de esta entrega. Ver [contrato y guion](collection-learning-breeding.md)
y [plan verificable](superpowers/plans/2026-10-25-collection-learning-breeding.md).
Codigo funcional publicado como `df96305` en origin/master; correccion de RAM
y evidencia de carga en [registro de entrega](superpowers/plans/2026-10-25-collection-board-delivery.md).
Preferencias visibles por ahora en el simulador; las nuevas
vistas de firmware siguen pendientes de aceptacion fisica, no de compilacion.

## Entrega F1/F2 Cargada En Placa

Firmware y LittleFS de F1/F2 cargados el 2026-10-24, con respaldo critico
nuevo, digests comprobados contra la placa y arranque `VPET_READY` confirmado.
El usuario confirma que Status se ve bien tras solicitar recorrer sus cuatro
paginas. La conservacion de mascota/progreso y la identidad tras reiniciar
siguen pendientes de confirmacion. [Registro de entrega](superpowers/plans/2026-10-24-f1-f2-board-delivery.md).
Creator queda fuera del commit por decision expresa; sus cambios locales
concurrentes se conservan. Las notas inferiores de F1/F2 "sin flashear"
describen comprobaciones previas a esta carga, no el estado de despliegue actual.

vPet Hub local: catalogo, previews por etapa/accion e importacion de JSON F1
con validacion de metadatos. Sin cuentas, tienda ni escrituras en placa.
Instalacion USB deshabilitada hasta implementar el protocolo y recuperacion.
Ver [alcance y arranque](vpet-hub.md).

Roadmap actualizado: [prioridades vigentes](superpowers/plans/2026-10-11-delivery-roadmap.md).

## F2a: Perfil Individual Integrado Localmente, Sin Flashear

`PetProfile` por composicion en Pet/PetState: ID de 128 bits, sexo M/F
equiprobable y referencias de padres; conservados al evolucionar y con nueva
identidad al reiniciar una vida. Fundadores legacy con padres desconocidos.
No hay ventaja de stats por sexo ni nuevo indicador en Status.

Migracion de simulador/NVS y reserva, journal v5 compatible con v1-v4,
schema principal 3 intacto. Entropia fuera del core: OS en sim, mbedTLS
sembrado antes de RF/ADC en ESP32, sin activar WiFi. Carga invalida/futura
bloquea migracion, no inventa otra identidad. No acredita recompensas.
[Contrato](individual-profile.md), [plan](superpowers/plans/2026-10-24-f2a-individual-profile.md).

Verificacion final con codigo congelado: 1768 Python aprobadas en 286.54 s,
185 nativas en 1.40 s, ESP32 compilado en 8.89 s. RAM 56228/327680,
app 1044313/4194304; sin cambios de assets. Se conservan las 13239 advertencias
Python preexistentes y TOUCH_CS de TFT. Evidencia y hashes en
`out/individual-profile/verification.json`. Sin acceso a partida personal,
carga a placa, commit ni push. Breeding, roster, inventario compartido de coleccion,
premios, instalacion y aprendizaje siguen pendientes.

## F2b: Crecimiento Integrado Localmente, Sin Flashear

El usuario autoriza continuar del piloto a la integracion. Perfil por rango
y ADN ya conectado en Python/C++: EV 84/168/252, potencial 200+8*IV y hasta
320 por stat permanente. PetState, penalizaciones y bases de boost ampliados;
boost temporal hasta 448 y HP/MP hasta 680/330. Cuidado permanece en 0..100.

Training, previews, bonus, Exploracion y chips respetan caps; EXP sin efecto
no consume. Repeticiones sin EV no cobran ni guardan. EV legacy se conserva
en carga/reserva y al sumar, sin cambiar schema NVS 3 ni enums. Arena usa
rival de referencia 61/108/156 por rango, sin escalar con cada entrenamiento.
No se cambia cadencia ni pausa de Mochila, ni se implemento F2a o breeding
en esa entrega (F2a local posterior se documenta arriba).

57 pruebas especificas aprobadas: 12.144 puntos del PetState real, guardado
y reserva, rollback, boosts amplios, tres etapas y seis genes. Incluyen 18
comparaciones pixel-perfect de Training C++/Python con valores amplios, y
Status con seis 320 dentro de sus columnas. Galerias inspeccionadas, no
validacion fisica de tipografia. [Contrato y limites](growth-integration.md),
[plan](superpowers/plans/2026-10-23-f2b-growth-integration.md).

Cierre 2026-10-24: suite completa 1752 aprobadas en 288.75 s, 185 nativas
en 1.02 s y firmware compilado en 9.56 s. RAM 56068/327680 (+16 vs F1),
app 1031545/4194304. Recursos regenerados: 227 assets, 10891653 bytes, sin
aumento. Se mantienen advertencias preexistentes de Pillow/pytest/TFT.
Verificaciones reforzadas cubren 72864 valores del calculador Python activo
(seis genes) y 12144 del PetState C++ real frente al candidato independiente.
Sin flasheo, WiFi, lectura de partida personal, commit ni push en esta entrega.

Las secciones siguientes conservan evidencia historica; sus notas de techo
99 o piloto sin activar describen la revision anterior, no este codigo local.

## F2b: Piloto Previo, Sin Activar En Esa Revision

Continuacion autorizada de la simulacion recomendada tras F1. Calculador
puro Python y referencia C++ opt-in; ningun consumidor activo incorpora la
curva. Formula vigente, techo 99, PetState, NVS, menus y recursos sin cambios.
F2a (identidad/sexo/parentesco), migracion e integracion de F2b siguen abiertas.

12.144 puntos escalares: cero stats inferiores a la formula actual y cero
retrocesos de evolucion en el perfil de tres rangos. Paridad de 97.152
proyecciones Python/C++; pruebas de EV legacy retenido, ganancia parcial,
bonus y no gasto al llegar al cap. Se proponen 84/168/252 EV (14 repeticiones
por atributo y tramo), aun sin aprobar balance. Mayor salto observado: +107.

218 encuentros host reutilizan el motor real, sin items/peso ni guardado.
Mediana de rivales iguales: 7 rondas vigente, 9 piloto; rival fijo de Arena
demasiado debil y empates defensivos al limite de 30. Aumentar stats no
resuelve navegar Mochila. Probe de boost en fixture >99 baja 264 a 99:
bloqueo para integrar el candidato, no ruta nueva activa de la placa.

23 pruebas nuevas; suite completa 1710 aprobadas en 279.39 s con las 12617
advertencias existentes. Nativas: 185 aprobadas en 4.49 s. ESP32 compilado
en 23.81 s: RAM 56052/327680 y app 1030989/4194304, igual que F1.
No se flasheo, accedio a USB, cambio partida ni publico esta revision.
Artefactos reproducibles en `out/growth-pilot/`; [informe y limites](growth-pilot.md),
[plan y evidencia](superpowers/plans/2026-10-23-f2-growth-pilot.md).

## F1: Definiciones Implementadas Y Probadas Localmente

El usuario prioriza implementar F1 y pruebas sin cerrar aun F0 en placa.
Definicion visual builtin validada, resolver portable Python/C++, Motion y
vistas reales integrados. Las tres reglas automaticas se generan desde JSON
sin cambiar balance; el peso 8..14 ya coincide tambien en catalogos.
La ficha evolutiva local anterior se conserva. Sin cambios NVS, WiFi o carga.

1687 Python aprobadas en 255.05 s y 185 nativas en 1.29 s. Pruebas F1:
34 casos, 680 resoluciones cruzadas y siete vistas por cada plataforma con
otra definicion de prueba; sin atlas legacy ni mutacion de partida. Arte de
fixture derivado del existente, no otra mascota comercial independiente.
ESP32 compilado: RAM 56052/327680, app 1030989/4194304; sin afirmar FPS fisicos.
Se conservan advertencias existentes de Pillow/pytest/TFT.

Presupuesto: payload 10891653 bytes, linea referenciada 10233972. Dos lineas
modeladas de ese tamano con staging, journals, reserva y cuatro registros
provisionales necesitan 32752237 bytes frente a 12451840: no caben. Cuatro
individuos pueden compartir arte, pero capacidad efectiva/roster aun no medidos.
Instalador USB, segunda linea comercial y optimizacion de almacenamiento siguen
pendientes. [Contrato F1](content-definitions.md),
[plan](superpowers/plans/2026-10-23-f1-content-definitions.md).

Inventario compartido confirmado; objetivo de hasta cuatro mascotas, no
garantia de cuatro paquetes. Curva piloto, plazas de huevos, breeding e
items por turno/cadencia de Arena siguen propuestas, detalladas en
[decisiones de producto](product-decisions-2026-10-23.md). No se activaron en F1.

## Programa Consolidado De Implementacion

Se consolida a solicitud del usuario lo existente, requisitos, aprobaciones
y orden recomendado en el [programa de entregas](superpowers/plans/2026-10-23-consolidated-delivery-program.md).
F0 calidad; F1 definiciones/presupuesto; F2 identidad/potencial; F3 Hub de
consulta/respaldo; F4 roster; F5 instalacion y premios/items; F6 aprendizaje;
F7 breeding interno; F8 encuentros/regalos P2P; F9 TinyML opcional/lanzamiento.
Las fases se especifican por separado; ni este indice ni los ejemplos de
balance autorizan migraciones o despliegues. El techo visible de 99 queda
como problema a resolver, no una restriccion de producto aceptada.
Solo documentacion en esta consolidacion; no se repitieron suites ni USB.

## Herencia Conductual Moderada Aprobada

El usuario aprueba que la cria reciba temperamento y una influencia inicial
moderada de tacticas/preferencias parentales, sin ser una copia entrenada.
Su experiencia propia puede cambiar ese estilo. No hereda EV, victorias,
dominio de tecnicas, recuerdos completos ni malestar temporal. Se actualiza
el [programa genetico](superpowers/plans/2026-10-23-social-genetics-learning-program.md)
con separacion entre predisposicion y experiencia, recibos reproducibles y
pruebas entre generaciones. Pesos/mezcla/topes aun por especificar y aprobar;
criterio documentado, no implementado en simulador ni firmware.

## Recepcion De Items De Terceros

El usuario requiere recibir items de otras personas o proveedores. Se amplia
el [diseno de paquetes](content-packages.md) para distinguir definicion/assets
de entrega de unidades, con validacion de emisor/destinatario, compatibilidad,
capacidad y recuperacion sin duplicar acreditaciones. Hub USB primero como
propuesta; regalos entre usuarios deben coordinar debito y credito. Servidor,
confianza y prevencion de doble gasto tras restaurar respaldos aun por definir.
Solo documentado: no hay protocolo, servicio, transferencia BLE ni cambios
de inventario/firmware implementados por este requisito.

## Identidad Y Sexo: Criterio Aprobado

El usuario aprueba identidad propia, sexo y parentesco conservados al
evolucionar; distribucion macho/hembra 50/50 y sin ventajas de combate por
sexo. Se registra en el [programa genetico](superpowers/plans/2026-10-23-social-genetics-learning-program.md).
Fue la decision de producto previa a F2a. La implementacion local posterior
se documenta arriba; no implica breeding, programa completo ni carga a placa.

## Detalle Evolutivo Aprobado E Implementado Localmente

Usuario aprueba el rediseno de IMG_4245. Nueva ficha de solo lectura con
requisitos para salir de la etapa actual, tiempo restante, valores frente
a objetivos, peso en rango y maximo de errores. Fondo oscuro, nombre completo,
retrato 64 px, cuatro filas por pagina y marcadores cumplido/pendiente.
NEXT pagina; ACTION/BACK vuelve al mismo nodo del arbol. Etapas anteriores,
futuras, huevo y final no muestran comparaciones falsas con stats actuales.
No cambian condiciones, recursos, guardado, NVS, enums ni Status.

189 pruebas focalizadas aprobadas. 240 vectores de modelo Python/C++, 56
comparaciones de detalle del renderer real de C++ contra sim y 18 previews
adicionales ES/EN sin diferencias de pixeles bajo la barra de navegacion.
App real recorre paginas y vuelve sin escrituras de partida; galeria
inspeccionada. Suite completa: 1653 Python aprobadas en 340.54 s y 185
nativas en 7.99 s. ESP32 compilado: RAM 56116, sin aumento estatico;
app 1017761 bytes. Advertencias existentes de Pillow/pytest/TFT conservadas.
No se ha cargado la placa por esta aprobacion de implementacion; legibilidad,
botones y aceptacion fisica de la nueva ficha pendientes.
[Contrato](evolution-progress.md), [plan](superpowers/plans/2026-10-23-evolution-progress.md).

Precision sobre el reporte anterior: el peso 8..14 ya coincide en el runtime
Python (config.py) y C++. Falta en JSON/catalogos generados; esa deuda de
fuente unica no significa que el simulador jugable omita esa regla.

## Arquitectura OO, Paquetes E Individuos

Usuario solicita una arquitectura que permita recibir otra mascota como
huevo de premio, criar individuos distintos y hacer breeding interno en
una board. No es una skin; cantidades de mascotas y huevos aun por definir.
Se actualizan [arquitectura](architecture.md) y [paquetes](content-packages.md)
con inventario de dependencias actuales y direccion propuesta por composicion:
motor/reglas comunes, definiciones, clips/resolver, paquetes compartidos,
roster/individuos y recepcion de huevos transaccional. El plan genetico
incorpora modalidad interna sin BLE; la modalidad entre boards sigue separada.

El firmware ya es OO, pero nombres/rutas, frames, cinco especies y reglas
duplicadas aun impiden el plug and play. La inspeccion del codigo no equivale
a un refactor implementado. No hay instalador, roster ni breeding disponibles.
Los 16 MB no son capacidad de mascotas: ultima carga registra 659456 bytes
libres en LittleFS; hacen falta medir arte compartido, registros y rollback.
No se fija una cantidad ni politica de incubacion/stock sin presupuesto y
aprobacion; no se cambia ni se flashea codigo por esta revision documental.
La vista Archify antigua queda identificada como instantanea historica.
Revision documental de esta ampliacion: 142 enlaces locales en nueve
documentos, sin destinos ausentes ni espacios finales; diff comprobado.
No se ejecutaron tests de codigo ni nuevos ensayos de USB/capacidad por
editar arquitectura. Las cifras de memoria son del registro de carga anterior.

## Documentacion De Producto Y Preparacion Del Lanzamiento

El usuario solicita mantener documentadas todas las opciones para preparar
un video promocional al lanzar el producto. Se agrega la
[guia funcional](product-guide.md), con nueve menus, subopciones, condiciones,
efectos y limites, y la [matriz audiovisual](launch-video.md), con tomas,
evidencias y criterios de publicacion. Son borradores de preparacion; no
hay video producido ni aprobacion de lanzamiento. README y workflow apuntan
a esos documentos y separan funciones actuales, propuestas y validacion fisica.
Revision documental: 112 enlaces locales existentes y sin errores de espacios
en los siete documentos revisados; no se ejecutan suites Python/C++ ni una
nueva carga por estos cambios exclusivamente documentales. Los bloques de
entregas anteriores conservan su evidencia historica; las actualizaciones mas
recientes prevalecen para identificar la ultima carga y aceptacion.

El [programa social/genetico/de aprendizaje](superpowers/plans/2026-10-23-social-genetics-learning-program.md)
es una propuesta, no implementacion: el usuario confirma disponer de una
sola board. Sexo, breeding, rivales guardados, P2P, limites por ADN y TinyML
no se anuncian como disponibles. No se cambia firmware ni se flashea por
esta actualizacion documental; los resultados de pruebas anteriores siguen
siendo evidencia de sus revisiones, no ejecuciones nuevas.

## Reporte Inicial: Detalle De Evolucion

IMG_4245 muestra dificultad para interpretar tiempos, abreviaturas y lista
de etapas. La inspeccion confirma que el detalle compara la edad actual
con requisitos para alcanzar la etapa seleccionada, no con los de su
siguiente evolucion. Se propuso una ficha de progreso, posteriormente
aprobada e implementada en la entrega descrita arriba; sigue pendiente
la validacion fisica. Este reporte no cambia reglas ni sustituye la
aceptacion previa del contraste.
Antes de publicar requisitos definitivos hay que reconciliar catalogo
Python y firmware: Evolution.cpp exige peso 8..14 para Firemon, pero
rookie.json no declara ese campo. El manual explicita el alcance de placa;
la diferencia no se corrige silenciosamente como parte de documentacion.

## Posicion Del Globo Zzz

El usuario confirma que Zzz aparece en placa pero pide que quede encima
del vPet, no separado en la parte superior. Se centra horizontalmente en
el cuadro de 88 px y se situa a 2 px sobre la primera fila visible del
sprite, con limite bajo la barra de navegacion. Sigue la postura al
tumbarse. AssetStore devuelve esa fila durante el dibujo ya existente:
sin otra lectura, escaneo de fondo, buffers, cambios de assets o NVS.
Simulador usa los limites de la mascara de transparencia del mismo frame.

1602 pruebas Python (234.27 s), 213 focalizadas, 185 nativas y build ESP32
aprobados. RAM 56116,
app 1015849 bytes. Vista previa real C++ en
`out/sleep-bubble-position/home-lying.png` y `sleep-gallery.png`.
El usuario autoriza cargar solo firmware ece6506 sin repetir antes la
validacion fisica pendiente de Status. Compilacion fresca y presupuestos
verificados; app escrita solo en 0x10000 y digest coincidente. LittleFS
no se escribe y su digest coincide con los graficos de la carga anterior.
Respaldo critico nuevo en `out/board-backups/20261023-zzz-position/`;
lectura posterior de 24576 bytes de tabla/NVS identica, SHA-256
`1eacf2312d618bb69f24ad3a0a1d1c3e19ba50c4fd201c4eee608dbd563ff287`.
Arranque VPET_READY, manifest 1; heap libre 66144 estable y minimo 60952
en 45 s, cuatro muestras, sin fatal/reinicio, cero eventos de botones.
El usuario confirma el 2026-10-23 que el globo queda bien justo encima
del vPet, tambien al terminar de acostarse. Posicion aceptada en placa.
Esa confirmacion no valida FPS, una noche completa, desaparicion al
despertar ni las cuatro paginas de Status, que siguen pendientes.
Logs y metadatos en `out/sleep-bubble-position/`.

## Indicador De Sueno Zzz

Usuario aprueba un globo fijo Zzz y su carga conservando la partida, sin
repetir antes la validacion fisica pendiente de Status. Se agregan dos
assets pequenos: cola izquierda/derecha y letras sin espejo. Home lo
compone despues de oscurecer el mundo; no aparece en paneles, huevo,
muerto, pausa o viaje y desaparece al despertar. Sin cambios en reglas
de sueno, animo, Arena, calendario, NVS o persistencia.

1596 pruebas Python y 185 nativas aprobadas; build ESP32 y LittleFS
correctos. RAM 56116/327680, app 1015685/4194304; 227 assets,
10891653 bytes de payload. Los 13 iconos anteriores son identicos byte a
byte. Pillow minimo 10.1 por la API de tamano de fuente embebida.
Cargados app (0x10000) y FS (0x410000), ambos digests verificados.
Los 24576 bytes de tabla/NVS son identicos al respaldo fresco, SHA-256
`695011133bba21d31b869b2cc8b99ca3692087a9771cdfa2509a094e0b0949b4`.
Arranque VPET_READY/manifest 1; FS real 11792384/12451840, heap libre
66128 estable, minimo 60980. Cuatro muestras en 45 s, sin fatal/reinicio;
cero eventos de botones: no prueba FPS, una noche ni uso del indicador.
Aceptacion visual del globo y cuatro paginas de Status pendientes.
Evidencia en `out/sleep-bubble/`; respaldo en
`out/board-backups/20261022-sleep-zzz-final/`.

## Entrega Conjunta De Exploracion

El usuario autoriza cargar juntas las tres correcciones: sprite de viaje
ampliado, contraste de Evolucion y salto de menus bloqueados por etapa,
conservando la partida y sin completar antes la validacion pendiente de
las cuatro paginas de Status. Esa aceptacion de Status sigue abierta.
No cambian reglas de viajes, premios, velocidad de animacion ni NVS.

1584 pruebas Python y 185 nativas aprobadas; 215 focalizadas de Exploracion.
Compilacion ESP32 y buildfs correctos: RAM 56116/327680, app 1015489/4194304;
225 assets, 10889361 bytes de payload. Presupuesto logico de assets mas
manifest 10947098/12451840, antes del coste interno de LittleFS. Respaldo critico nuevo en
`out/board-backups/20261022-exploration-sprite44-final/`.
Cargados aplicacion en 0x10000 y LittleFS en 0x410000, con verificacion
independiente de ambos digests. Comparacion posterior de los 24576 bytes
criticos: tabla de particiones y NVS identicos al respaldo, SHA-256
`7a30d88d7a4581c2cff4839b1e76034cba354903c2667f5e78d07ea1dcc918a3`.
Arranque VPET_READY, manifest 1; uso real FS 11784192/12451840 (667648
bytes libres tras overhead). Heap libre 66128 estable, minimo 60932;
BLE ADVERTISING, sin fatal/reinicios en 45 s. No hubo eventos de botones;
no demuestra FPS ni aceptacion visual. Evidencia en `out/exploration-sprite44/`.
El usuario confirma que la escala del sprite y las letras de Evolucion
se ven bien en placa. Esa aceptacion no cierra Status ni el resto de
pruebas fisicas de persistencia y viajes.

## Contraste De Evolucion

Nombre de la etapa actual y NOW/AHORA usan la tinta oscura existente en
vez de verde claro. Solo cambia el color de esos textos; seleccion,
progreso, siluetas, posiciones, reglas y partida intactos. Firmware y sim
corregidos. Veinte casos nuevos verifican cinco etapas en ES/EN, mediante
colores enviados a TFT y pixeles del simulador; 50 comparaciones contra
la revision anterior confirman cambios limitados a las etiquetas.
55 pruebas focalizadas aprobadas y ESP32 compilado: RAM 56116/327680,
app 1015425/4194304. Vista previa en `out/evolution-contrast/after.png`.
Suite general final: 1512 Python aprobadas en 247.33 s; avisos existentes
conservados. Catalogo generado comprobado y diff sin errores de espacios.
Cargado en el paquete de Exploracion descrito arriba, con firmware y
LittleFS verificados y NVS preservada. Usuario confirma que las letras
se leen bien; la autorizacion excepcional no cierra la validacion de Status.
La nota de Mochila queda en este documento;
el catalogo generado se regenera desde su fuente, sin edicion manual.

## Menus Por Etapa

La barra atenua al 50% las actividades bloqueadas por etapa: huevo
Alimentar/Entrenar/Explorar/Batalla/Descanso; Sparkmon Entrenar/Explorar/
Batalla. Firemon y etapas posteriores conservan brillo. No se cambia el
acceso a vistas de consulta ni el marco seleccionado. Tras la confirmacion
visual del usuario, NEXT ahora salta las actividades bloqueadas por etapa;
no salta necesidades temporales como sueno o cansancio.
Home, paneles y Exploracion coinciden con el simulador T-Display y
refrescan la barra al evolucionar. Sin textos ni cambios de reglas/NVS.
1478 Python y 185 nativas aprobadas. Firmware cargado y verificado por
digest, con globos sin textos incluidos; LittleFS/NVS no reescritos.
Arranque VPET_READY, heap libre 66128 estable, minimo 61000, BLE conectado
y sin fatal/reinicio en 45 s. Usuario confirma atenuacion y globos sin
textos; aceptacion fisica del nuevo salto NEXT pendiente.
Revision NEXT: cargada junto al paquete de Exploracion y contraste,
1584 Python y 185 nativas aprobadas; firmware/FS y arranque verificados.
RAM estatica sin aumento; aceptacion fisica de NEXT pendiente.
[Contrato y evidencia](superpowers/plans/2026-10-22-stage-menu-dimming.md).

Reporte de Mochila: el usuario intenta todos los objetos. Pruebas del
handler real App confirman consumo de manzana azul y descuento persistido
al recargar cuando hay animo por recuperar. Los objetos BAT solo funcionan
en Arena; venda requiere lesion y cuidado no se gasta sin efecto ni dormido.
No se han cambiado esas reglas ni identificado aun la condicion concreta
de la partida fisica. [Contrato](adopted-items.md).

## Training: velocidad y Tecnicas

Reporte reabierto el 2026-10-22: vistas previas demasiado rapidas solo en
Training y atasco al pasar por Tecnicas. Reproducidas trece aperturas de
archivos por refresco en Select 7/8-8/8 por doce iconos en una LRU de diez.
Correccion local: footer en buffer existente, una sola apertura caliente
para el retrato y cadencia 90/120 ms solo Training/Tecnicas. Home, Arena,
sesiones, balance, assets, Status y NVS sin cambios. Aceptacion fisica de
la nueva cadencia/NEXT confirmada por el usuario: ambos mejoraron.
1443 Python y 185 nativas aprobadas; RAM estatica sin aumento. Solo
firmware cargado y verificado por digest; VPET_READY, heap libre 66132,
BLE conectado y sin fatal/reinicio en 45 s. Persisten matriz ampliada y
mediciones instrumentadas; [evidencia](training-board-performance.md).

## Descanso: solo iconos

La foto del usuario muestra LOW ENERGY, contador y barra que no queria
conservar. Se eliminan esas tres capas y el fondo negro en ambos renderers.
Poca energia queda solo con gotas; hora de dormir sigue solo con carita.
No cambian reglas de descanso, prioridad, ocultacion, metas internas,
assets, Status, Training, Arena ni NVS.
La primera carga no pudo abrir el puerto y no escribio la placa. Tras
reconectar, se carga junto a menus atenuados: 1478 Python y 185 nativas,
digest de firmware y arranque verificados. Usuario confirma que se ven sin
textos; desaparicion al resolver necesidad sigue pendiente en placa.
[Correccion y evidencia](superpowers/plans/2026-10-22-rest-icon-only.md).

## Simbolos de descanso: entrega anterior

Por solicitud del usuario, POCA ENERGIA conserva nivel/meta y barra pero
usa gotas de cansancio en lugar de rayo. Hora de dormir usa solo una carita
dormida en el globo, sin titulo, hora ni fondo negro de etiqueta. Ambas
variantes conservan el animo bajo y las supresiones existentes. No cambian
recuperacion, horario aprendido, hambre, Status, guardado ni animaciones.

1432 pruebas Python y 185 nativas aprobadas; compilacion ESP32 correcta.
RAM estatica 56108/327680, app 1015085/4194304. Pico/T-Display regenerados:
225 assets, 10789125 bytes de payload. Otros nueve iconos identicos.
Vista previa inspeccionada. Cargado el 2026-10-22 desde la revision 3a9c406:
firmware y LittleFS coinciden por digest independiente. Respaldo critico
nuevo verificado; sin borrar NVS. Arranque VPET_READY, manifest 1, heap libre
66144/minimo inicial 66124; FS 11685888/12451840. Observacion posterior de
45 s: cuatro muestras, heap libre estable en 66144, minimo 61008, BLE
conectado y sin fatal/reinicio. No certifica FPS ni sesiones prolongadas.
El usuario autorizo esta carga sin validacion fisica previa de Status;
esa aceptacion y la legibilidad natural de los nuevos globos siguen abiertas.
[Contrato](mood-cues.md),
[plan y evidencia](superpowers/plans/2026-10-22-rest-symbols.md).

## Claridad del descanso: primera version

Implementadas las explicaciones aprobadas POCA ENERGIA (nivel/meta y barra)
y HORA DE DORMIR (horario preferido/aprendido) en Home, ES/EN. La segunda
tiene prioridad al coincidir; sin calendario valido se conserva energia.
Hambre, alimentacion, consumibles, reglas de sueno, Calls y persistencia
no cambian. Status conserva su distribucion. Los once iconos anteriores
son identicos; se agregan dos globos de energia a los assets reproducibles.

1413 pruebas Python (197 enfocadas) y 185 nativas aprobadas; compilacion ESP32 correcta,
RAM estatica 56108/327680, app 1015213/4194304. Pico/T-Display regenerados,
225 assets, 10789233 bytes de payload; simulador headless 90 frames correcto.
Vista previa aislada inspeccionada. Carga y aceptacion visual en placa
pendientes en esa primera preparacion: no se detecto puerto USB. En ese
momento el ultimo firmware confirmado en placa era Angry, descrito abajo.
[Evidencia historica](superpowers/plans/2026-10-22-rest-cue-clarity.md).
Rayo, bombilla y texto horario se sustituyen por la revision descrita arriba.

## Angry en las cuatro etapas

Las hojas aportadas de Sparkmon, Firemon, Flamemon y Dragfiremon completan
el cuerpo enojado en Home: 25 frames a 90ms, sin reemplazar los globos ni
cambiar reglas de animo, guardado o enums. Cansancio y acciones tienen
prioridad; estados suprimidos no muestran enojo corporal. Status conserva
su retrato y su icono actual. [Contrato](mood-cues.md).

Verificacion local: 1376 pruebas Python, 183 nativas, 163 casos enfocados,
Pico/T-Display regenerados y simulador 90 frames correctos. RAM estatica
56108/327680, app 1014393/4194304; 223 assets, 10786603 bytes de payload.
Recorte lossless de padding en acciones de Home, sin formato nuevo ni
reducir frames/colores, mantiene 12.91% de margen de presupuesto con
manifiesto. Aceptacion visual de Angry en placa separada de estas pruebas.
Cargado el 2026-10-19: firmware y LittleFS coinciden por digest independiente.
Deploy OK y arranque VPET_READY: heap libre 66148/minimo 66088, FS
11677696/12451840, manifest 1, BLE PAIRED/CONNECTED. No se borro NVS;
respaldo nuevo verificado. El espacio usado real baja 266240 bytes frente
a la entrega anterior, aun con los cuatro sprites adicionales.
[Plan y evidencia](superpowers/plans/2026-10-19-angry-sprites.md).

## Rest, pausa y luz apagada

Rest ofrece solo APAGAR/ENCENDER LUZ y VOLVER. Cold se presenta como PAUSAR
CRIANZA en Opciones; la reserva sale del menu sin borrar sus datos. Pausa
congela tambien descanso y margen Call, con guardado/rollback y sin cambiar
schema NVS 3 ni los IDs anteriores. El usuario confirmo fisicamente ambos
menus y detecto que dormir aun dejaba el fondo claro.

Seguimiento: luz apagada oscurece Home a un cuarto de cada canal RGB565,
independientemente del ciclo 18:00-06:00; despertar restaura el brillo.
Menu superior y paneles conservan legibilidad. Sin nuevos assets/framebuffer
ni cambios de cadencia, Training o Status. Pruebas finales: 1324 Python,
183 nativas, simulador headless 90 frames y compilacion ESP32 correctos;
RAM estatica 56108/327680, app 1014233/4194304. El usuario acepta la
correccion de oscuridad en placa: confirma que apagar
oscurece y encender restaura brillo. Noche completa y pausa siguen pendientes.
Cargado el 2026-10-19 sin recargar LittleFS: firmware y FS conservado
coinciden por digest independiente. Arranque VPET_READY, manifest 1,
heap libre 66128/minimo 66108; FS 11943936/12451840, BLE PAIRED/CONNECTED.
Respaldo nuevo verificado; no se borro NVS ni la reserva.
[Contrato y alcance](rest-and-board-validation.md),
[evidencia](superpowers/plans/2026-10-19-rest-and-board-validation.md).

Observacion USB previa al seguimiento de luz: cinco minutos, 29 muestras,
7 entradas, heap libre 66060..66132, minimo historico 43876 bytes, BLE
conectado y sin fatal/regresion de uptime entre muestras. Hubo ciclos de
hasta 927 ms: no se declara FPS, ausencia de fugas ni reconexion BLE.
Siguen pendientes la noche real, necesidades resueltas, equipo 3/4/Arena,
evolucion ganada y stock/recompensas comparados tras reiniciar.

## Entrega anterior: globos y caras de animo

Home muestra comida, descanso/luz, lesion, tristeza o enojo junto al pet.
La marca de enojo depende del animo, no solo del hambre. Status cambia
unicamente el icono de ANIMO por happy/neutral/sad/angry; conserva las
cuatro paginas, barras y valores. Sin nuevos Calls, penalidades, campos
guardados ni cambios de escala/cadencia, Training o Arena.

Validacion local: 1292 pruebas Python y 183 nativas aprobadas; 1536 vectores
Python/C++, harness de Renderer/Panels/AssetStore reales, previews ES/EN,
Pico regenerado y Make Sim 90 frames. Build T-Display correcto: RAM estatica
56100/327680, app 1014749/4194304; 219 assets, 11075765 bytes de payload.
Firmware y LittleFS cargados y verificados por digest independiente el
2026-10-18, sin borrar NVS. Reinicio de 18s: VPET_READY, manifest 1,
heap libre 66572/minimo 66528, FS 11943936/12451840; BLE conectado y sin
fatal. La aceptacion visual fisica de los iconos sigue abierta.
[Contrato](mood-cues.md), [evidencia](superpowers/plans/2026-10-18-mood-bubbles.md).

## Entrega anterior: noche y descanso

Noche 18:00-06:00, cuatro sprites cansados y rutina de
descanso moldeada por ADN/habitos. Amanecer independiente de despertar;
minimo ocho horas nocturnas, recuperacion progresiva y premio unico.
JSON/sleepState v1, snapshots v4 compatibles con v1/v2/v3, schema NVS 3
intacto. 1237 pruebas Python y 180 nativas aprobadas; Make Sim 90 frames,
Pico regenerado y build T-Display correctos. Cargado firmware/LittleFS y
verificados por digest independiente en ambas particiones el 2026-10-18.
Deploy OK: heap libre 66592/minimo 66516; FS 11890688/12451840, manifest 1.
Reinicio observado 18s sin fatal: BLE ADVERTISING/PAIRED/CONNECTED,
VPET_READY. Sin borrar NVS; respaldo nuevo conservado. Falta aceptacion
visual y una noche real; ajustar Fecha/Hora si se perdio el calendario.
[Contrato](sleep-routine.md), [evidencia](superpowers/plans/2026-10-18-sleep-routine.md).

## Entrega de tecnicas anterior a noche/descanso

Tecnicas ampliadas en Python y C++: Firemon equipa 2, Flamemon 3,
Dragfiremon 4. Rafaga (30 poder/12 MP, Champion+, 4 lecciones) e Inferno
(38 poder/18 MP, Ultimate, 6 lecciones) completan el catalogo de cinco.
Aprender/evolucionar no equipa; se conservan IDs y schema NVS 3. Snapshot
interno v3 admite v1/v2; equipo/dominio nuevos sobreviven a reinicios y
recuperacion transaccional. [Contrato vigente](techniques.md).

Validacion final: 1132 pruebas Python y 175 nativas aprobadas, Make Sim
headless de 90 frames y build T-Display correctos. Comparacion pixel a pixel
de TrainingUi/Tecnicas ES/EN con equipo 2/3/4, trazas numericas y recuperacion
de partidas antiguas/nuevas. RAM estatica 56044/327680, flash 1009965/4194304;
204 assets, 10497880 bytes. [Plan y evidencia](superpowers/plans/2026-10-18-technique-expansion.md).

Cargado firmware y LittleFS el 2026-10-18; verificacion USB independiente
con digest matched en ambas particiones, sin borrar NVS. Deploy OK y
VPET_READY: heap libre 66640/minimo 66564, filesystem 11309056/12451840,
manifest 1; BLE ADVERTISING. Falta aceptacion fisica de aprender/equipar
3/4 y usar los nuevos ataques. No se forzo evolucion ni progreso en la placa.

## Entregas anteriores del 2026-10-18

Arena y evolucion automatica conectadas en Python/C++: victorias/derrotas
aportan a batallas de etapa y W/L, sin contar empates ni retiradas. Guardado
atomico de contadores/premios y evolucion al volver a Home; no hay progreso
retroactivo de peleas anteriores. [Plan y validacion](superpowers/plans/2026-10-18-arena-evolution.md).
Validado con 1120 pruebas Python y 174 nativas; Make Sim y build correctos.
Firmware cargado/verificado por USB, VPET_READY con heap 66644/minimo 66576,
sin fatal durante 18s. Aceptacion fisica de evolucion mediante Arena pendiente.
Seguimiento IMG_4004: color RGB565 del escalador corregido; Arena reutiliza
fondo/selector y Exploracion su barra de iconos, sin otro framebuffer.
El usuario acepta la distribucion de Arena; colores y fluidez de esta nueva
correccion requieren comprobacion fisica. Ver el seguimiento en
[Arena](arena-presentation-fixes.md#seguimiento-img_4004-color-y-latencia).
Cargado y verificado por USB: firmware/FS coinciden por digest; arranque
VPET_READY, heap 66512/minimo 66440, BLE conectado, sin fatal en 18s.
Arena corregida en Python/C++: celebracion completa, texto de feedback
retirado, escala propia de combate y cursor persistente entre rondas.
El harness host ejecuta Panels.cpp/AssetStore.cpp reales en 24 escenarios.
[Alcance y pruebas](arena-presentation-fixes.md): 1096 pruebas Python y 173
nativas aprobadas. Cargado el 2026-10-18; firmware/LittleFS coinciden por
digest. Deploy OK, heap libre 66656, minimo 66580; filesystem
11292672/12451840, manifest 1. Aceptacion visual fisica pendiente.

Status ampliado en simulador y firmware: cuarta barra de animo, lesiones
acumuladas /15, rotulos HERIDO/MUERTO y EV por atributo junto a la barra
de combate. [Contrato y verificacion](status-vitals-care-ev.md).
1081 pruebas Python y 172 nativas aprobadas. Cargado el 2026-10-17 con
`Deploy OK`: heap libre 66660, minimo 66616, filesystem 9404416/12451840,
manifest 1. Verificacion USB del 2026-10-18: firmware y LittleFS coinciden
por digest. Arranque VPET_READY, heap libre 66652, minimo 66576;
BLE ADVERTISING/PAIRED/CONNECTED, sin fallo fatal en 18 segundos observados.
La aceptacion fisica anterior no cubre estas nuevas filas.

Flamemon y Dragfiremon tienen Guardia, dano y emociones propias desplegadas.
La entrega de sprites paso 1077 pruebas Python; firmware/LittleFS coinciden
por digest con placa. Heap libre 72504, minimo 72436; filesystem
9404416/12451840; manifest 1. El ultimo arranque registro PAIRED/CONNECTED y
VPET_READY, no una prueba completa de reconexion movil.

El usuario confirmo Training fluido en placa el 2026-10-18; aceptacion
visual de la pantalla probada registrada. El 2026-10-22 se reabre por
cadencia excesiva y atasco especifico en Tecnicas; ver revision arriba.
La nueva cache de diez iconos estaticos y lecturas agrupadas del retrato
reducen E/S en host y se cargaron el 2026-10-17. Falta medir latencia y heap
durante Training real, no solo en el arranque. Ver
[rendimiento de Training](training-board-performance.md).
Validacion local de la cache: 1078 pruebas Python aprobadas; compilacion
T-Display correcta, RAM estatica 56028/327680, flash 1007657/4194304 bytes.
Codigo, sprites, pruebas y roadmap publicados en origin/master: `bdcf027`.
La optimizacion de E/S esta desplegada: firmware y LittleFS coinciden por
digest. Arranque final VPET_READY, heap libre 66660, minimo 66584, filesystem
9404416/12451840 y manifest 1. BLE registro CONNECTED/PAIRED; no certifica
estabilidad prolongada; la fluidez visual se acepta por el reporte del
usuario posterior. Evidencia local en
`out/training-cache-board-deploy/`; respaldo nuevo conservado sin borrar NVS.

Los numeros de exploracion siguientes son su corte previo, no los de la
ultima carga de sprites.

Exploracion portada y cargada a T-Display: nueve iconos, Patio/Jornada/Noche,
tablas ES/EN, retorno anticipado, cobro unico, recibo y Guia en entrenamiento.
El registro expState v1 usa snapshots atomicos v2 compatibles con v1, sin
cambiar schema principal 3 ni enums persistidos. Sin reloj respaldado, perder
el calendario exige ajustar Fecha/Hora antes de enviar o reclamar un viaje.

Evidencia final: 1067 pruebas Python, 172 nativas, 162 vectores numericos
sim/C++, 127 casos de UI y regresiones de App/persistencia. Firmware y LittleFS
verificados por digest en placa; heap libre 72644, minimo 72568, manifest 1.
La aceptacion visual fisica y del viaje en uso real continua abierta. Ese
arranque registro PAIR_FAILED; el arranque de sprites citado arriba lo
supera, sin cerrar la validacion prolongada de conectividad.
Contrato: [Exploracion](exploration.md). Evidencia y hashes:
[port de placa](superpowers/plans/2026-10-16-exploration-board.md).

El roadmap vigente sigue en
[Plan de cierre](superpowers/plans/2026-10-11-delivery-roadmap.md).
Los cortes inferiores son historia, no la lista actual de pendientes.

## Corte historico: 2026-10-11

Este bloque sustituye las afirmaciones de entrega del registro historico inferior.
El indice de pendientes vigente es
[Plan de cierre y siguientes entregas](superpowers/plans/2026-10-11-delivery-roadmap.md).

- Status, entrenamiento temporizado y tecnicas estan implementados en el
  simulador y firmware. La ultima carga de firmware y LittleFS termino con
  `Deploy OK`, `heap_free=109620`, `heap_min=55836`,
  `fs=5722112/12451840`, `manifest=1`.
- START inicia una sesion automatica de 10 segundos; al terminar aplica y guarda
  una vez. El contrato vigente es [Timed Training Contract](training-session.md),
  no el antiguo flujo de repeticiones manuales TRAIN/FINISH.
- El regreso a Home tras 10 segundos de inactividad esta implementado; no
  interrumpe entrenamiento ni combate activos. BACK tiene prioridad sobre NEXT
  en la cola de entrada. Ambos comportamientos requieren aceptacion fisica.
- Evidencia de la ultima ejecucion: 511 pruebas Python aprobadas, compilacion
  T-Display aprobada y prueba ampliada de 466 comparaciones de imagen ES/EN
  entre Python y el renderer C++ de Training/Tecnicas. No son fotografias de
  la placa ni certifican la paridad de todas las pantallas del juego.
- El usuario confirmo una mejora importante de Status. Aun falta confirmar
  en la ultima carga la salida por pulsacion larga, respuesta de NEXT,
  animaciones, ausencia de solapamientos y retorno por inactividad.
- Combate conserva diferencias de presentacion Python/C++: el panel Arena del
  firmware sigue usando una ventana de 1500 ms y la vista anterior. No marcar
  la paridad visual global como terminada.
- `vpet-ui-assets` y `vpet-pixel-art` son propuestas; no estan creadas ni
  instaladas para MiniMax. Exploracion y catalogo de recompensas no estan
  implementados.
- HEAD comprobado: `de63fd0`. Existen cambios locales y archivos nuevos sin
  seguimiento; estas entregas no constituyen un commit ni un push confirmado.

## Registro historico: corte 2026-10-07

Se conserva a continuacion como trazabilidad, NO como lista de pendientes vigente.
Las referencias a ausencia de despliegue, Training solo en simulador o FINALIZAR
manual describen ese corte y quedaron superadas por el estado del 2026-10-11.

Actualizado originalmente el 2026-10-07. El hash del HEAD era
`de63fd0 feat: add practice battles and targeted training` (con cambios
locales posteriores sobre `master`); no se asume un `commit` por omision.

## Confirmado

- El telefono detecta el vPet por BLE cuando el modo `ADVERTISING` esta activo.
- WiFi esta deshabilitado y no aparece en el menu del dispositivo.
- La navegacion de dos botones y las animaciones tienen una respuesta mas
  fluida que las versiones anteriores.
- El simulador y el firmware comparten recursos y reglas principales.
- La intro de arranque existe en ambos entornos, pero aun no se ha cargado a la
  placa despues del ultimo commit.
- `make sim-practice` y el icono de espadas abren directamente el combate
  determinista. `make sim-training` abre entrenamiento y tecnicas en la pesa.
  Ambos comandos comparten un guardado de preview separado de la partida normal.
- En el simulador Firemon tiene seis entrenamientos por atributo con iconos,
  coste de 8 ENE, ganancia de 6 EV y vista antes/despues. No cambia sus IV.
  Aprendizaje y dominio de tecnicas se abren desde la pesa; Guardia usa `block`.
- El motor de practica Python/C++ tiene trazas comparadas y pruebas nativas;
  la vista y persistencia NVS estan integradas en codigo y compiladas, sin
  despliegue ni validacion fisica del flujo nuevo.
- **Balance de entrenamiento v1 (simulador + tests deterministas)**:
  - Menu training: **3 ENE por sesion** (antes 0), **+1 EV en una stat
    elegida (off o spd)**, **cap 8 sesiones por ciclo de cuidado**
    (resetea con `reset_after_evolution`).
  - Dumbbell: sin cambio (8 ENE, +6 EV en cualquiera de 6 stats).
  - Wake-from-sleep / battle / feed: sin cambio (sus caps naturales —
    motion, dp+injury, ciclo overfeed — ya acotan los loops).
  - EV/ENE ratio v1: menu 0.33 EV/ENE, dumbbell 0.75 EV/ENE. El
    dumbbell sigue siendo el camino fuerte para maxar una stat; el
    menu es la sesion diaria barata. 31 pruebas en
    `tests/test_balance_sim.py` validan los 6 stats, energia
    insuficiente, caps, y comparan estrategias rest+dumbbell+menu.
  la vista y persistencia NVS estan integradas en codigo y compiladas, sin
  despliegue ni validacion fisica del flujo nuevo.
- **Sesion de entrenamiento por tandas (simulador, 2026-10-07)**:
  - Reemplaza el ciclo "presionar y el stat cambia" por
    `elegir > entrenar > revisar > confirmar`. Cada ACTION de
    entrenamiento = una repeticion; el costo se reserva y los EV se
    proyectan en paralelo a los valores reales sin mutar el pet.
  - Dominio (`src/core/training.py`): `training_index_for`,
    `batch_block_reason`, `batch_max_reps`, `batch_plan_one_rep`,
    `batch_projected_value`, `batch_apply`, `batch_commit` (snapshot
    pre-apply + rollback), `BatchSaveError`. Politica EV al tope:
    partial last-rep allowed (cabe 1 rep cuando headroom < 6),
    zero-gain reps bloqueadas cuando `pending_ev + real_ev >= 252`.
  - Orquestador (`scripts/training_session.py`): 5 estados
    (A select, B prepare, C session, D result, E error) con foco
    por estado, sub-estados confirm/cancel, save atomico via
    `batch_commit`, retry idempotente. `busy()` durante 1500 ms
    tras una rep bloquea solo ACTION con foco `train`; NEXT nunca
    se bloquea. Un toque = una repeticion.
  - Renderer (`scripts/training_renderer.py`): 7 vistas (select,
    prepare, session, confirm, cancel, result, error) reusando
    `pet_sprite`, `info_icon`, `info_label`, `icon_button`, `text`
    de `practice_renderer.py`. Bandas: header (y=0..19), sprite +
    datos (y=23..110), action buttons (y=115..132). En D muestra
    ANTES/CAMBIO/AHORA solo si el delta no es 0; no inventa `+1
    stat` cuando solo aumento EV.
  - Tests: `test_batched_training.py` (39, contrato transaccional
    y politica EV al tope, frozen pre-renderer) +
    `test_batched_training_ui.py` (57, bounds 240x135, no overlap,
    NEXT/ACTION/BACK, 6 atributos, freeze time, retry idempotente).
  - Previews reproducibles: 12 PNGs en
    `out/practice-preview/training-*.png` (select, select-def,
    prepare, session, session-cap, confirm, result, result-legacy,
    cancel, error, overview 4x2) via `scripts/preview_practice.py`.
  - Suite: 443/443 tests Python pasan en 48.75 s.
    `git diff --check` limpio. `sim.py --training` arranca sin
    errores bajo `SDL_VIDEODRIVER=dummy`.
  - NO firmware/NVS/BLE/WiFi. NO se modifico
    `out/board-backups/`. Plan completo + decisiones en
    `docs/superpowers/plans/2026-10-07-batched-training-session.md`.
- **Localizacion y resultado navegable del entrenamiento (2026-10-07)**:
  - Catalogo i18n (`src/core/i18n.py`): `TRAINING_STRINGS` y
    `STAT_STRINGS` con ES/EN, `tr(pet, key)` con fallback seguro a
    ES para lenguajes no soportados. El renderer no embebe strings
    visibles (verificado por
    `test_renderer_has_no_hardcoded_user_facing_strings` y
    `test_i18n_every_used_key_is_bilingual`).
  - Estado D partido en dos paginas navegables con NEXT:
    `RESULT_PAGE_SUMMARY` (tabla ANTES | +CAMBIO | AHORA con delta
    solo donde hubo cambio) y `RESULT_PAGE_STATS` (6 stats con
    barras compactas, escala documentada `round(ev / 252 * 96)` px,
    stat entrenado resaltado en amarillo). Indicador
    `RESUMEN | STATS` arriba a la derecha. ACTION/BACK vuelven al
    selector; NEXT solo flipea la pagina.
  - Previews bilingues: 16 PNGs nuevos en
    `out/practice-preview/training-{select,select-def,prepare,
    session,session-cap,confirm,result,result-stats}-{es,en}.png`
    mas `training-bilingual-overview.png` (8x2 grid 1920x540).
    Para que las barras del STATS page se vean utiles, el preview
    refleja el EV/ENE/ESF post-apply en el pet antes de capturar;
    el renderer nunca muta.
  - Tests: i18n (ES/EN/fallback/formato/keys faltantes/blacklist),
    dos paginas de D (NEXT toggle, ACTION returns, BACK returns,
    NEXT no avanza el state machine), barras (clamp 0..96,
    monotonia), extremos (EV 0/50/252, zero deltas, freeze time).
  - Suite: pasa completa. `git diff --check` limpio. NO se toco
    firmware, NVS, BLE, WiFi ni `out/board-backups/`. Plan
    actualizado con seccion 11 (catalogo, renderer, dos paginas,
    tests, previews, decisiones).
- **Menu Status T-Display 240x135 (2026-10-07, simulador + tests)**:
  - Direccion visual aprobada: barra superior de 8 iconos, selector
    amarillo, paleta y sprite actuales, mascota a izquierda y datos
    a derecha. Cabecera compacta `STATUS n/4`; filas alineadas con
    iconos, etiquetas y valores legibles.
  - Pagina 1/4 vital: HP de crianza (`stats["hp"]`), alimentacion
    (`stats["h"]`), energia (`stats["e"]`) con barras diferenciadas
    rojo/naranja/cian. El HP de combate (pool derivado de IV+EV)
    vive en la pagina 4/4 junto al codigo DNA para no confundir
    las dos metricas.
  - Pagina 2/4 care: 5 filas claras — EDAD (formato s/m/h/d segun
    magnitud), SOBREAL/OVERFEED, CUIDADO/CARE ERR, ESFUERZO/EFFORT,
    BATALLAS/BATTLES. Sin siglas tipo OF/CM. La primera fila
    acepta texto extra (reloj o llamada) en la segunda linea.
  - Pagina 3/4 battle: PESO/WEIGHT, DP (no renombrado), %VIC/WIN%,
    PROT/PROT, V-D/W-L. `--` cuando no hay encuentros. Layout
    apilado (label arriba, valor abajo) en las 4 fichas estrechas
    para que las etiquetas largas quepan.
  - Pagina 4/4 DNA (obligatoria): codigo completo `DNA: XX-XX-XX-XX`
    visible (fuente 10 px para caber en el strip de 92 px), helice
    rotando suavemente derivada de `now_ms` via `helix_spin`, 6
    stats HP/MP/OFF/DEF/SPD/BRN con barras en escala 0..99
    (`combat_stat`, no EV). El giro no muta ADN, IV, EV ni stats.
    Caso sin ADN con placeholder honesto.
  - Catalogo i18n extendido (`src/core/i18n.py`): claves
    `status.vital.*`, `status.care.*`, `status.battle.*`,
    `status.dna.*`, `status.header` con fallback seguro a ES.
    Helpers `tr_status_dna_label(pet, stat)` y
    `format_age(pet, total_seconds)`.
  - Tests: `tests/test_status_card.py` (10, contrato de filas y
    layout) + `tests/test_status_pages.py` (16, bounds, no-overlap,
    barras diferenciadas, helix rotando, render sin mutar, DNA
    completo, valores estables entre timestamps, i18n bilingue).
  - Previews: 10 PNGs + 1 GIF en `out/status-preview/`:
    `status-{1,2,3,4}-4-{es,en}.png`, `status-overview-{es,en}.png`
    (4x1 grid 1920x270), `status-helix-{es,en}.gif` (24 frames a
    100 ms cubriendo un giro completo de 2400 ms).
  - Suite: 489/489 tests Python pasan. `git diff --check` limpio.
    Smoke test `sim.py --max-frames 3 --training` OK.
  - **Limitacion firmware pendiente**: el layout apilado de las
    paginas 2/4 y 3/4, la fuente 10 px para el codigo DNA y el
    formato de edad adaptativo son features del simulador. El
    port a C++/firmware requiere verificar que la fuente 10 px
    esta disponible en el atlas del T-Display y que el cache de
    glifos cabe en la RAM del sprite. NO se ha desplegado a
    hardware.
- Fase 6 del combate de practica: balance afinado con pruebas deterministas
  (dano minimo 1, dano maximo ~62 con llama y stats maximas, MP no negativo,
  treinta rondas de empate, desobediencia segun vinculo y personalidad,
  compatibilidad con guardados antiguos sin clave `techniques`,
  `_draw_combatant` mostrando `hit` solo al atacante y `hurt` solo al
  defensor que pierde HP). El layout del simulador 240x135 ahora separa
  cuatro bandas: header con HP/MP de doble columna y barras de 46 px,
  feedback band de dos lineas explicitas (`PEDISTE <orden> -> HIZO
  <accion>` con R#X a la derecha, `MOTIVO: <razon real>` con dano de
  ronda `PRACT -X | FIRE -Y` a la derecha — `damage[i]` es el dano
  que fighter `i` inflige al oponente, por lo que `PRACT` recibe
  `damage[0]` y `FIRE` recibe `damage[1]` — color por categoria
  verde/rojo/amarillo/blanco/muted), action selector de 4 iconos con
  status de coste o disponibilidad (`PET DECIDE` / `COSTE N MP` / `SIN
  MP` / `RECARGA N` / `RECUPERA 4 MP` / `FIN BATALLA`) y banner terminal
  con outline de color por resultado. El mensaje generico "PET SUSTITUYO
  ORDEN" se elimino: cada sustitucion muestra la razon real devuelta por
  `choose()` (`SIN MP`, `EN RECARGA`, `PREFIERE DEFENDER`,
  `PREFIERE ATACAR`, `A SU CRITERIO`). 343 pruebas Python + 119 nativas
  C++ pasan; firmware compila; el simulador pinta frames de `hit`/`hurt`
  durante los 1.2 s del impacto, banner de resultado y label "PRACTICA".

## Pendiente de producto

- Definir el contenido descargable: pets, themes, bundles, metadata, licencias
  y limites de almacenamiento.
- Definir los nuevos pets, sus sprites, acciones, estadisticas y evoluciones.
- Implementar el esquema publico `.vpetpack` y su validador.
- Implementar el catalogo web y sus previews.
- Implementar instalacion inicial por USB/Web Serial.
- Implementar posteriormente aprovisionamiento WiFi y descargas HTTPS.
- Diseñar una app movil para estado, BLE y gestion de contenido.

## Pendiente tecnico

- Trasladar a C++ el entrenamiento por atributo y la nueva interfaz de
  pesa/tecnicas/combate con iconos. El firmware conserva el flujo anterior;
  la paridad del motor de combate no implica paridad de estas nuevas pantallas.
- Portar al firmware los frames de impacto (`hit`/`hurt`) y el banner de
  resultado del combate de practica; el simulador ya los muestra, el panel
  T-Display sigue con la vista anterior. El firmware usa 1500 ms para la
  ventana de animacion (`Panels.cpp: <1500>`), el simulador usa 1200 ms
  (`PRACTICE_IMPACT_MS`).
- Ajustar con pruebas de juego los costes y ganancias de entrenamiento.
- Conectar feedback de impacto con `hit`/`hurt` ya disponibles en el
  simulador (`PRACTICE_IMPACT_MS` = 1.2 s). `dodge` tambien existe en assets,
  pero no se usa para insinuar una evasion que el motor aun no calcula.
  Sprites sugeridos nuevos: victoria, derrota y ejercicios especificos.
- Igualar la intro: firmware usa un sprite Firemon fijo; simulador muestra
  texto FIREMON. Aun no usa la mascota guardada. La intro bloquea el arranque
  durante aproximadamente 2.2 segundos y no tiene pruebas dedicadas.
- Corregir divergencia de eclosion: App.cpp y config.py usan 2 segundos;
  el catalogo generado declara 8 segundos. La documentacion anterior decia 8.
- Revisar paridad de Status/DNA, descanso y guardado entre Python y C++.
  Son implementaciones separadas, aunque comparten recursos generados.

- Probar en la placa la intro posterior al commit.
- Confirmar el ciclo BLE `ADVERTISING -> CONNECTED -> ADVERTISING` desde el
  telefono y dejar evidencia serial.
- Añadir pruebas de regresion para la intro y los nuevos paquetes cuando se
  defina el contrato.
- Validar practica en pantalla y botones reales, restauracion NVS y BLE activo
  cuando se autorice el despliegue.
- Separar una configuracion de firmware de produccion con Secure Boot, Flash
  Encryption, OTA firmada y anti-rollback.

La board actual se mantiene como dispositivo de desarrollo. Ningun cambio se
considera validado fisicamente hasta que se cargue de forma explicita y se
pruebe en pantalla, botones y radio.
