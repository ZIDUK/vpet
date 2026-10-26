# Coleccion, Aprendizaje Y Breeding Local

Fecha: 2026-10-25.
Estado: alcance y reglas iniciales de coleccion aprobados. El usuario confirma
cuatro plazas incluyendo huevos, mochila activa como stock compartido sin
sumar la reserva y huevo fundador local tras confirmacion, sin objetos nuevos.
El contrato de implementacion usa los pilotos acotados descritos abajo;
la aprobacion no equivale a implementacion, migracion ejecutada ni flash.

## Base Inspeccionada

- Entrega publicada F1/F2: `4c6ce16`; aceptacion visual de Status: `e839c3e`.
- `PetProfile` ya aporta identidad, sexo y padres; evolucionar conserva identidad.
- `Pet` y `PetState` contienen cuidado, ADN, EV, tecnicas y resultados propios.
- `SettingsStore` guarda un individuo y reserva NVS con journals recuperables;
  no es un roster y las dos instantaneas incluyen inventarios independientes.
- `SimulatorServices` usa reemplazo atomico de un JSON de una sola mascota.
- Arena AUTO usa puntuaciones fijas. No hay aprendizaje por experiencias.
- LittleFS tenia 647168 bytes libres en el ultimo despliegue verificado;
  no es una lectura actual ni capacidad garantizada de nuevos paquetes.
- Creator tiene cambios locales ajenos a esta entrega; no editarlos ni publicarlos.

## Limites Comunes

Motor OO por composicion y reglas portables Python/C++, sin Arduino/TFT/BLE
en dominio. No cambiar valores numericos de enums ni reinterpretar schema
legacy NVS 3. No modificar reglas de evolucion ni el balance de crecimiento.
Sin WiFi, TinyML, P2P, instalacion de paquetes, premios de proveedor ficticios,
nuevas especies ni fusiones de imagenes. Esta especificacion no autoriza flash.

La entrega se divide en tres subproyectos con pruebas y revision propias:
coleccion/persistencia; experiencias/politica; breeding/incubacion. No activar
breeding antes de que las otras dos partes sean recuperables y evaluadas.

## A. Coleccion E Inventario Compartido

### Individuos Y Plazas

Propuesta: cuatro plazas TOTALES, contando adultos, jovenes y huevos. No son
cuatro adultos mas huevos adicionales ni cuatro paquetes graficos. V1 usa
la definicion builtin instalada; individuos distintos comparten arte, no
identidad, ADN, EV, tecnicas, cuidado, sueno ni experiencia.

Una sola mascota activa. Los inactivos quedan conservados: no envejecen,
no pierden cuidado, no entrenan ni completan viajes o sueno en segundo plano.
No hay progreso apagado. Un cambio se rechaza durante entrenamiento, Arena,
viaje, sueno, journal pendiente o error de almacenamiento. Cambiar mascota
requiere confirmacion y no se implementa como reiniciar una vida.

El ID se asigna al recibir el huevo y no cambia al eclosionar. No borrar,
liberar ni sustituir automaticamente un individuo cuando se llenen las plazas.
No inventar una segunda mascota como efecto secundario de migracion/importacion.

### Inventario

Una mochila de coleccion es la unica autoridad de cantidades y del cursor de
recompensas. Gastos y premios de la mascota activa actualizan esa mochila
en la misma transaccion que su efecto. Cambiar mascota nunca repone stock.
Bonificaciones ya aplicadas a un individuo no se convierten otra vez en items.
Los alimentos ilimitados conservan su comportamiento actual.

Propuesta de migracion: stock ACTIVO como mochila compartida inicial. La
reserva legacy se conserva completa y sin cambios como archivo de recuperacion;
su inventario no se suma ni se reclama automaticamente, porque no existe una
procedencia fiable para distinguir unidades independientes de una copia previa.
El usuario aprobo explicitamente esta politica en la revision del diseno.

### Migracion

Recuperar primero journals legacy. Validar activo y reserva sin generacion de
premios. Identidades distintas se conservan como individuos distintos. Igual
ID/estado se deduplica; igual ID con estados divergentes bloquea migracion y
pide reconciliacion, no asigna otro ID para fingir dos mascotas. Una reserva
sin ID recibe identidad una sola vez como parte de la transaccion candidata.

No escribir el marcador de coleccion hasta validar y confirmar todo el estado.
Si falta espacio, hay formato futuro/corrupto o falla una escritura, conservar
los originales y bloquear nuevas mutaciones. Un reinicio repite la misma
migracion o recupera la coleccion confirmada, nunca suma mochilas nuevamente.

### Almacenamiento

Propuesta: repositorio de coleccion en LittleFS, separado de assets y del core,
con dos generaciones verificables, version, secuencia, longitud y checksum.
Limite inicial de 64 KiB por generacion y reserva operativa de 192 KiB que
incluye ambas generaciones y escrituras temporales. Estos limites son gates
de implementacion, no presupuestos fisicos ya comprobados.

Preparar el candidato sin cambiar el activo, verificar lectura/checksum y
confirmar el marcador durable al final. La generacion previa valida sigue
disponible para recuperacion. No usar guardar cuatro PetState completos mas
tablas de aprendizaje en NVS como ampliacion directa de los namespaces actuales.

Solo se conserva en RAM el estado necesario de la mascota activa; las demas
se cargan al consultar/cambiar. Medir pico de heap, pila, latencia y escrituras.
Actualizar LittleFS completa despues de esta migracion destruiria la coleccion:
el flujo de deploy debe bloquearlo sin respaldo/restauracion verificados de
los datos de usuario. No considerar suficiente el respaldo legacy de NVS.

### Interfaz

Entrada Coleccion en Opciones, sin cambiar las nueve opciones de Home ni
Status. Lista compacta con retrato existente, forma, sexo, activo/huevo y
plazas ocupadas; detalle para activar o elegir padres y confirmacion separada.
NEXT recorre, ACTION elige, BACK cancela. Ninguna apertura de panel guarda,
consume, concede premios o modifica genes. No agregar leyendas a globos de Home.
Definir y revisar el layout 240x135 antes de editar sus renderers.

## B. Experiencias Y Comportamiento Adaptativo

### Estado E Integracion

Separar cuatro conceptos: cuidado fisico existente; emocion pasajera;
predisposicion/temperamento heredado; politica aprendida durante esta vida.
No modificar genes, EV ni condiciones de evolucion al actualizar una politica.

Evento versionado con secuencia monotona por individuo, dominio, contexto,
accion legal, resultado y recompensa acotada. No usar fecha editable o frame
como identificador. Emitir solo al confirmar entrenamiento, resultado de
combate o cobro de viaje. Sesiones canceladas no generan experiencia.
La aplicacion del evento, su efecto existente y su ultimo numero confirmado
deben persistirse juntos. Recuperar/reintentar no aprende ni recompensa dos veces.

Piloto: tres tablas, hasta 32 contextos y ocho acciones por dominio. Media
de recompensa con signo y contador uint16: 3072 bytes antes de metadatos.
Historial circular de hasta 256 eventos de como maximo 32 bytes cada uno;
rotarlo no borra el resumen aprendido ni permite repetir eventos viejos.
Limite propuesto de 12 KiB serializados por individuo para aprendizaje e historial.

### Decisiones Y Personalidad

La politica fija es fallback. Comparar solo acciones legales: tecnica aprendida
y equipada, MP, cooldown y condiciones actuales. AUTO puede usar preferencia
aprendida; una orden explicita conserva las reglas de obediencia actuales.
No lanzar viajes, entrenamiento, gastos, reproduccion ni envios automaticamente.
Preferencias de entrenamiento/exploracion se muestran en su panel, sin elegir
ni gastar por el usuario. No anadir un control que parezca operativo sin efecto.

Recompensa de combate: eficiencia/supervivencia; de entrenamiento: progreso
real/fatiga; de exploracion: rendimiento y estado al volver. No otorgar EV,
items ni curacion adicional por el mero hecho de aprender. Emociones con
causa y decaimiento gradual, sin alternar humor al azar en cada frame ni
cambiar retrospectivamente el humor guardado al renderizar.

La implementacion fijara contextos y recompensas por dominio en su contrato
ejecutable y los evaluara con semillas reservadas, antes de activar AUTO
adaptativo. No afirmar inteligencia mejorada por variar animaciones.

## C. Breeding Interno

### Elegibilidad Propuesta

Consentimiento explicito del propietario; dos IDs distintos, macho/hembra,
de la misma linea instalada y adultos (rookie/champion/ultimate). Ambos vivos,
sin lesion, despiertos, sin viaje, pausa o sesion activa. Salud >=80, hambre
>=60, energia >=70 y animo >=60 en los dos. No cobrar items ni consumir padres.

Bloquear padres/hijos, hermanos y relaciones detectables en dos generaciones
conocidas. Guardar referencias/ascendencia necesarias en el registro del hijo.
Ascendencia desconocida no se inventa ni equivale a genealogia verificada infinita.

Piloto de cooldown: 24 horas de funcionamiento acumulado por padre. El reloj
de reproduccion avanza mientras la coleccion esta encendida y no pausada,
sin evolucion, hambre ni aprendizaje de fondo. Checkpoints conservadores;
adelantar fecha o reiniciar no acelera el reloj. Restaurar un respaldo antiguo
no ofrece proteccion anti-trampa absoluta: documentar ese limite.

### Hijo E Incubacion

ID y sexo independientes del potencial genetico. Cada uno de los seis IV
elige un padre con mascara que use al menos un locus de cada uno. Mutacion
piloto: 1/32 por locus, -1/+1 acotado a 0..15, con semilla persistida. El
cuarto byte de ADN que afecta rasgos no debe quedar implicito: heredar sus
dos nibbles por el mismo mecanismo, sin confundirlo con IV adicionales.
ADN coincidente es posible entre padres similares; no confundir ID unico
con promesa de genoma necesariamente diferente.

Temperamento: media acotada parental. Sesgo de preferencias: propuesta de
25% de la tendencia parental normalizada, limitado al rango inicial acordado,
sin copiar contadores, historial, dominio, victorias, EV ni malestar temporal.
La experiencia propia debe poder superar y revertir este sesgo. Evaluar
generaciones sucesivas para evitar amplificacion no acotada.

El huevo ocupa una de las cuatro plazas desde la confirmacion del cruce.
Incubacion piloto de 30 minutos encendido con el huevo activo; sin progreso
apagado o inactivo. El huevo inicial legacy conserva su duracion actual.
Reiniciar/reanudar conserva tiempo acumulado, ADN e identidad; eclosionar no
vuelve a lanzar dados ni acredita la mochila inicial de otro fundador.

Transaccion unica: breedingId, padres, version de reglas, semilla, sesgo
parental fijado, ID/genoma del huevo, plaza y cooldowns. Comprobar plaza antes
de preparar; confirmar solo tras guardar el candidato valido. Reintentar
devuelve el mismo hijo o recupera el pendiente, no vuelve a evaluar padres
ni crea otro huevo con una semilla nueva.

### Origen Del Segundo Individuo

Migrar la reserva permite conservar un segundo individuo si ya existe. Si
solo hay uno, no prometer breeding inmediatamente utilizable ni crear una
mascota de premio falsa. Decision aprobada: permitir un huevo fundador local
SOLO tras una orden explicita del usuario, con ID nuevo y mochila inicial
vacia. No presentarlo como premio de proveedor ni como paquete instalado.

## Descomposicion Y Pruebas De Aceptacion

1. Coleccion: contratos y codec estrictos; cuatro plazas; mismo ID no se
   clona; stock compartido; rechazo de cambio durante sesiones; migracion
   activo/reserva; cortes antes/despues de cada escritura; corrupcion y
   futuro bloquean sin reemplazar origen; capacidad llena no borra datos.
2. Aprendizaje: tablas/contextos/recompensas y limites documentados; eventos
   confirmados exactamente una vez; recuperacion/cancelacion; paridad Python/C++;
   saturacion de contadores; historial circular; cero acciones ilegales;
   aprendizaje desactivado como control y adaptacion ante cambio de rival.
3. Breeding: salud/edad/sexo/linea/parentesco; reserva de plaza; mismos padres
   y semilla dan mismo hijo; limites IV y mezcla de ambos; herencia moderada;
   experiencia del hijo parte de cero; cooldown/fecha/reinicio; incubacion;
   multigeneracion; corte en cada fase no duplica hijos ni mochila.
4. UI: sim y firmware 240x135, lista/detalle/confirmacion/cancelacion y
   mensajes de error; abrir vistas no muta estado; ausencia de recortes.
5. Integracion: suite Python, nativas, build fresco ESP32, presupuesto de
   RAM/flash y archivos. No confundir pruebas host con persistencia fisica.
6. Despliegue posterior solo autorizado: respaldar NVS Y coleccion, firmware
   actual y hashes, arranque, comprobar IDs/progreso/mochila y reinicio real.

## Revision De La Especificacion

No cambia Creator, no usa una subclase por especie, no concede stock al nacer
ni aprende de eventos no confirmados. La reserva no se destruye. El inventario
legacy y el origen de un segundo fundador fueron aprobados explicitamente.
Los tres subproyectos necesitan planes ejecutables separados con interfaces,
pruebas RED/GREEN y revision; este documento no declara su implementacion.
