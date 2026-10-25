# Plan Maestro: Genetica, Encuentros Y Aprendizaje

> Para ejecucion por agentes: este es un plan maestro propuesto, no una
> autorizacion para modificar o flashear el firmware. Cada entrega requiere
> su especificacion aprobada y su plan de pruebas antes de implementarse.

**Fecha:** 2026-10-23.
**Estado:** criterios de identidad, sexo, parentesco y herencia conductual
moderada aprobados; resto del programa propuesto para revision. Entregas
posteriores F2a/F2b implementan localmente perfil/migracion y potencial,
no el programa E completo. [Perfil](../../individual-profile.md),
[crecimiento](../../growth-integration.md); sin flasheo ni breeding.
El usuario confirma despues inventario compartido y objetivo de cuatro
mascotas sujeto a presupuesto. Ver [pilotos numericos y breeding](../../product-decisions-2026-10-23.md).
F1 de contenido se implementa localmente en otra entrega, no estas fases E.
**Orden conjunto:** el [programa consolidado](2026-10-23-consolidated-delivery-program.md)
incluye tambien Hub, paquetes e items. Sus fases F0..F9 no reemplazan los
identificadores E0..E6 de los contratos tecnicos de este documento.
**Objetivo:** permitir identidad sexual y breeding, encuentros entre boards,
batallas recordadas, potencial por ADN y aprendizaje de experiencias.
**Arquitectura:** reglas portables y deterministas, un registro transaccional
de experiencias, una politica adaptativa ligera y adaptadores BLE/almacenamiento.
TinyML es un proveedor opcional de decisiones, no el responsable del guardado.
**Stack actual:** ESP32 T-Display clasico, PlatformIO/Arduino C++, NimBLE 2.5.1,
TFT_eSPI, NVS/LittleFS y simulador Python/Pillow/pygame.

**Aclaracion posterior del usuario (2026-10-23):** un paquete recibido por
premio corresponde a otra mascota que nace de huevo, no a cambiar apariencia.
Se requiere roster de individuos/huevos y breeding interno en una board.
Maximos e incubacion de inactivos siguen por definir. Esta aclaracion
sustituye la incubadora de una plaza como supuesto inicial; no la da por
aprobada. Ver [arquitectura](../../architecture.md) y
[paquetes](../../content-packages.md). No se ha implementado esta ampliacion.

## 1. Alcance Y Decisiones De Producto

Requisitos pedidos por el usuario:

| Requisito | Entregas propuestas |
| --- | --- |
| Sexo para implementar breeding | E1 identidad; E5 breeding completo |
| Guardar rivales y aprender de las peleas | E2 experiencias; E4 batalla y ecos |
| Comunicarse con otros vPets/boards | E3 enlace BLE versionado |
| Limites variables por ADN de cada stat | E1 potencial y curva de crecimiento |
| Aprender de entrenamiento, combate y exploracion; evaluar TinyML | E2 aprendizaje local; E6 TinyML opcional |

El usuario confirma que por ahora dispone de UNA placa. Se priorizan las
funciones locales, roster/breeding interno, un par de vPets simulados y un emulador de protocolo en el
computador. Ninguna prueba con un solo dispositivo cierra la validacion
fisica board-a-board ni demuestra interoperabilidad con firmware ajeno.

Criterio de producto aprobado por el usuario (2026-10-23):

- Cada vPet tiene identidad propia, sexo y parentesco, conservados al evolucionar.
- Sexo macho/hembra, distribuido 50/50 al crear un nuevo individuo, sin
  ventajas de combate por sexo.
- Herencia conductual moderada: temperamento y una influencia inicial
  acotada de las tendencias/preferencias aprendidas de ambos padres. La cria
  puede desarrollar otro estilo con sus propias experiencias; no nace como
  copia entrenada. No hereda EV, victorias, dominio de tecnicas ni recuerdos
  completos de combates. Tampoco copia el malestar temporal de los padres.

Esta aprobacion fija el criterio de producto; no autoriza por si sola la
implementacion completa de E1, breeding, migraciones ni despliegue.
Pesos, limites, mezcla y representacion de la herencia conductual requieren
todavia una especificacion y pruebas de balance; no hay porcentaje aprobado.

Reglas de producto restantes propuestas para aprobar:

- El huevo puede mantener el sexo oculto hasta eclosionar.
- El ADN no cambia al evolucionar; identidad, sexo, parentesco y ADN se
  conservan tambien al reiniciar mediante persistencia versionada.
- La experiencia aprende preferencias/tacticas sin reescribir los genes.
  La influencia conductual sobre una cria se calcula por separado segun el
  criterio aprobado; no implica copiar las tablas completas de aprendizaje.
- Breeding interno: dos individuos propios compatibles producen un hijo
  mediante una transaccion local; ambos padres permanecen. No requiere BLE.
- Breeding entre boards: UN huevo en UNA board receptora elegida por ambos
  usuarios. Es otra operacion; no duplica hijos al reintentar la entrega.
- Capacidad de roster/incubadora pendiente de presupuesto y aprobacion.
  No sobrescribir partida activa, huevos ni reserva; assets compartidos
  por definicion/version, sin duplicar un paquete por cada individuo.
- Primera version de breeding dentro de una linea evolutiva compatible.
  Nuevas especies, fusiones y sus sprites requieren entregas posteriores.
- Los ecos guardados permiten practicar offline, pero no son una copia
  exacta del cerebro del rival ni un rival remoto conectado en tiempo real.
- Revisar los limites de EV y stat visible con compatibilidad explicita.
  El usuario pide resolver el bloqueo en 99: no conservarlo como techo de
  producto. La alternativa de valores ampliados y potencial por ADN/etapa
  sigue pendiente de aprobar formula, curva y migracion; no ampliar campos
  numericos ni reinterpretar partidas silenciosamente.

## 2. Punto De Partida Verificado El 2026-10-23

Baseline historico para este plan maestro. F2a/F2b posteriores agregan
perfil individual y crecimiento al codigo local; consultar sus contratos
enlazados arriba para el estado vigente. No describir estas ausencias
originales como estado actual de implementacion.

- `firmware/t-display/platformio.ini`: central BLE y observer desactivados,
  una conexion maxima. No existe hoy escaneo ni cliente para encuentros.
- `BleService.cpp`: servidor HID/DIS/bateria, cifrado sin interfaz de
  autenticacion visual y sin protocolo vPet de juego. No envia teclas.
- `PetState`: ADN de cuatro bytes; seis IV de 0 a 15 y EV de 0 a 252.
  No hay petId persistente independiente, sexo ni parentesco.
- `PracticeBattle.h`: eleccion por puntuaciones, personalidad y vinculo;
  no hay aprendizaje estadistico de decisiones ni rival remoto.
- Ya existen dominio de tecnicas, vinculo, rutina de sueno aprendida,
  registros de cuidados y journals de algunas acciones. No equivalen a
  memoria tactica general ni se deben aplicar sus premios dos veces.
- NVS actual schema 3; snapshots y journals poseen versiones propias.
  No modificar sus valores numericos ni reinterpretar bytes existentes.
- La instalacion Arduino usa ESP-IDF 4.4.7, comprobado en
  `tools/sdk/esp32/include/esp_common/include/esp_idf_version.h` del framework.
- Ultimo registro USB disponible: heap libre 66144 bytes, minimo 60952,
  FS real 11792384/12451840: 659456 bytes libres. Es una observacion de
  45 s, no el peor caso de todos los modos ni una medida actual en vivo.
- La flash de 16 MB no sustituye RAM; no hay PSRAM. Los dos framebuffers
  existentes se conservan; no reservar un tercero para red o aprendizaje.

## 3. Alternativas Y Recomendacion

| Alternativa | Ventaja | Coste/riesgo |
| --- | --- | --- |
| Reglas + estadisticas adaptativas locales | Aprende online, poco consumo, explicable y portable | No es una red neuronal; exige disenar recompensa y evaluar mejoras |
| Red TinyML + adaptacion ligera | Politica base entrenada y personalizacion local | Compatibilidad de toolchain, arena RAM y mantenimiento de modelos |
| Entrenamiento/decisiones externas | Modelos mas grandes | Dependencia de computador/telefono/red; no cumple autonomia total |

Recomendacion: primera alternativa como base independiente; evaluar la
segunda sin bloquear el producto. No introducir WiFi ni una dependencia
de nube. Un vPet puede aprender de verdad con actualizaciones estadisticas
pequenas; no necesita un modelo de lenguaje para tomar mejores decisiones.

## 4. Entregas Y Dependencias

```text
E0 presupuestos y contratos
  -> E1 identidad/sexo/ADN/potencial
     -> E2 experiencias y aprendizaje local
     -> E5a roster, premio/huevo y breeding interno (sin BLE; requiere
        aprobar capacidades, incubacion y compatibilidad de descendientes)
     -> E3 protocolo y enlace BLE
        -> E4 encuentros, memoria de rivales y ecos (tambien requiere E2)
        -> E5b breeding entre boards (tambien requiere E5a)

E6 prueba TinyML: estudiar compatibilidad en E0; integrar solo despues
de E2 y de volver a medir la memoria con el enlace de E3 habilitado.
```

### E0. Presupuestos, Compatibilidad Y Recuperacion

- [ ] Registrar revision, backups y memoria de Home, Training, Arena,
  Exploracion, sueno, guardado y BLE. Medir heap minimo, bloque contiguo
  mayor, stack y latencia de botones; no inferir FPS del maximo de loop.
- [ ] Mantener guardas vigentes: heap al arranque >=64 KiB, minimo >=48 KiB,
  margenes logicos de app/FS >=10%. Ninguna fase puede rebajarlas para pasar.
- [ ] Separar presupuesto real de FS del tamano logico de assets. Reservar
  al menos 256 KiB reales libres y limitar datos nuevos inicialmente a
  128 KiB, incluyendo journals, temporales y checkpoints duplicados.
- [ ] Presupuesto inicial de tablas adaptativas: <=4 KiB RAM; cargar solo
  un rival/registro a la vez. BLE y ML necesitan su propia medicion conjunta.
- [ ] Disenar registro versionado, checksum, checkpoint A/B y recuperacion
  tras corte de energia. Un checksum detecta corrupcion, no autentica al peer.
- [ ] Probar compatibilidad TinyML en un entorno de compilacion separado;
  no actualizar PlatformIO, Arduino, IDF o NimBLE de la partida principal
  simplemente para instalar un runtime ML.

Salida: informe de presupuestos y decisiones de compatibilidad, mas pruebas
de fallos de escritura. Con una board se puede preparar y medir; cualquier
carga requerira autorizacion y el gate de Status o su excepcion especifica.

### E1. Identidad, Sexo Y Potencial Genetico

- [ ] Crear `PetProfile` separado del ADN actual: petId aleatorio de 128 bits,
  sexo, generacion, IDs de padres, version de reglas y metadatos de linea.
  No usar MAC ni los cuatro bytes de ADN como identificador unico.
- [ ] Migracion una sola vez para partidas existentes; conservar ADN, EV,
  inventario, rutina, vida activa y reserva. El perfil viaja con el pet al
  guardar/restaurar/intercambiar, no con la board que lo hospeda.
- [ ] Definir `ProgressionProfile`: rango adulto actual y cantidad de rangos
  adultos de su linea. Debe venir del catalogo, no de nombres de criaturas
  ni del valor numerico persistido de SpeciesId. Huevo/bebe no entrenan.
- [ ] Introducir una unica funcion portable de potencial para todas las
  fuentes: entrenamiento, Arena/cuidado, objetos y Exploracion. La vista
  previa, el consumo real y el recibo deben coincidir.

Formula candidata V1 para calibrar, aun no aprobada como balance final:

Referencia historica del candidato de EV geneticos. Para el siguiente piloto
se recomienda la alternativa de potencial visible 200+8*IV y EV por rango
del documento de decisiones; no activar ni mezclar ambas sin aprobacion.

```text
IV_i: gen de cada stat, entre 0 y 15
m: rango adulto actual / cantidad de rangos adultos de su linea
P_i = 192 + 4 * IV_i
L_i = 6 * floor((P_i * m) / 6)
```

P_i es el potencial individual; L_i es lo desbloqueado en la etapa. Para
una linea de tres rangos adultos:

| IV del stat | Primer rango | Segundo rango | Rango final |
| --- | ---: | ---: | ---: |
| 0 | 60 | 126 | 192 |
| 8 | 72 | 144 | 222 |
| 15 | 84 | 168 | 252 |

Son EV, no el numero visible de Speed o Ataque. Cada stat obtiene su propio
limite y cada nueva evolucion abre margen. La formula implica que no todos
los individuos alcanzan 252 EV: el ADN fija tambien un techo individual.
Esta consecuencia debe aprobarse junto a la formula, no introducirse oculta.
Esta candidata no resuelve por si sola el bloqueo visible en 99. La discusion
posterior propone ampliar ese rango con potencial por etapa y ADN; ejemplo
de 280 meramente ilustrativo, sin balance ni representacion aprobados.

- [ ] Evaluar los 16 IV en todos los rangos y lineas de 2/3/4 etapas:
  monotonia al evolucionar, limites 0..252, paridad exacta Python/C++ y
  crecimiento visible sin saturar todas las formas intermedias en 99.
- [ ] Comparar curvas de stat visible en un informe antes de activar el
  nuevo balance: la formula actual ya puede saturar Flamemon en 99.
  Cambiar solo el cap de EV no resuelve esa saturacion.
- [ ] No truncar EV antiguos. Si exceden L_i, conservarlos y bloquear nuevas
  ganancias hasta abrir capacidad; no consumir objetos sin efecto. La
  aplicacion retroactiva de la curva visible requiere un plan de migracion
  aprobado que no reduzca silenciosamente los valores actuales. Identificar
  aparte los legacy ya saturados: preservar su 99 no deja margen bajo 99.
- [ ] Mostrar limite actual y potencial total en Training/Status sin agregar
  textos explicativos ni leyendas nuevas a los globos de Home.

Salida: identidad estable y potencial por ADN probado. La curva/migracion
se aprueba a partir del informe de balance, antes de cambiar la partida.

### E2. Experiencias, Humor Y Aprendizaje Local

- [ ] Definir `ExperienceEvent` compacto y versionado: ID, tipo, contexto,
  accion, resultado y recompensa. Usar secuencia monotona persistida, no
  fecha editable como identificador o defensa contra repeticiones.
- [ ] Capturar entrenamientos confirmados, combates resueltos, rondas
  relevantes y recibos cobrados de Exploracion; no frames de animacion.
- [ ] Aplicar efectos y aprendizaje una sola vez mediante journal y ultimo
  evento aplicado. Cancelar una sesion o recuperar un journal no duplica EV,
  dominio, vinculo ni actualizaciones de politica.
- [ ] Retener inicialmente 256 eventos de hasta 32 bytes y resumen aprendido
  persistente. Al rotar el historial se conserva el aprendizaje agregado;
  no se promete guardar indefinidamente cada detalle de toda su vida.
- [ ] Separar necesidades fisicas, emocion temporal y temperamento. Alegria,
  frustracion, interes y aburrimiento deben tener causas y decaimiento
  gradual; no cambiar arbitrariamente cada frame ni convertirse en dano
  permanente. No alterar hambre/salud/evolucion por ML sin una regla explicita.
- [ ] Implementar una politica de puntuaciones adaptativas, inspirada en un
  contextual bandit: tres tablas (combate/entrenamiento/exploracion), hasta
  32 contextos y 8 acciones por tabla, media de recompensa y contador en
  enteros de 16 bits: 3072 bytes antes de metadatos. Objetivo total <=4 KiB.
- [ ] Mantener una politica inicial por reglas y una mascara de acciones
  legales. Nunca usar MP inexistente, tecnicas bloqueadas, entrenar lesionado
  o gastar objetos/enviar viajes sin las decisiones del usuario.
- [ ] Separar predisposicion heredada y experiencia propia. Inicializar la
  cria con un sesgo acotado, sin copiar contadores de experiencia ni asumir
  que acciones bloqueadas estan aprendidas. Definir limites y decaimiento
  para que entrenamiento/combate/exploracion propios puedan cambiar el estilo.
- [ ] Usar recompensas propias de cada dominio: eficiencia y supervivencia
  en combate; progreso real y fatiga en entrenamiento; rendimiento y estado
  al volver de Exploracion. La media aprendida no debe ser otro premio EV.
- [ ] Entrenar con simulaciones y evaluar semillas no usadas al ajustar:
  mejora frente a politica fija, cero acciones ilegales, ausencia de bucles
  de Guardia y capacidad de adaptarse al cambiar el rival. Comparar ablations
  con aprendizaje desactivado y recompensa alterada.
- [ ] Guardar al terminar experiencias/checkpoints acotados, no cada frame.
  Un error de flash conserva o recupera el ultimo estado valido, sin inventar
  una experiencia que no quedo confirmada.

Ejemplos esperados, sujetos a evaluacion: conservar MP cuando sus tecnicas
caras rinden mal, responder a un rival defensivo, mostrar interes por rutas
que dieron buen resultado y reconocer rutinas repetidas de entrenamiento.
La eleccion de entrenamiento/ruta sigue bajo control del usuario; se aprende
afinidad y reaccion, no se inicia una accion costosa por cuenta propia.

### E3. Enlace Entre vPets

- [ ] Crear protocolo de juego propio sobre GATT, version/capacidades y UUID
  de servicio propios; HID y DIS actuales no transportan las partidas.
- [ ] Modo Encuentro explicito: una conexion activa. Buscar/Unirse habilita
  observer/central; Esperar actua como periferico. Pausar conexion de telefono
  mientras se usa otro peer, con aviso y decision del usuario.
- [ ] Conservar el ciclo actual de telefono y la propiedad de callbacks.
  Liberar cliente/servidor/escaneo y medir el retorno a Home sin fugas.
- [ ] Mensajes con version, sesion, secuencia, tipo, longitud y limites.
  Fragmentar para el MTU minimo negociado; reintentos/ACK y timeouts
  acotados. No depender de conseguir un MTU grande.
- [ ] Callbacks solo validan/copiar a colas acotadas. Guardar, decidir y
  dibujar desde la tarea de App, sin bloqueos de animacion por escaneo.
- [ ] Confirmacion en ambas pantallas y asociacion BLE autenticada cuando
  el modo de entrada lo permita; verificar la capacidad real con dos botones.
  El cifrado Just Works actual no da proteccion MITM por si solo.
- [ ] Rechazar versiones/rulesets incompatibles, secuencias repetidas,
  longitudes excesivas, stats fuera de rango y tecnicas inexistentes. Nunca
  aceptar rutas de archivos, codigo, modelos ML o pesos ejecutables del peer.
- [ ] Definir la confianza: protocolo autentica una sesion con un companero,
  no prueba que su firmware sea honesto. Sin servidor/atestacion no prometer
  un ranking resistente a placas modificadas.
- [ ] Crear emulador de protocolo en Python con enlace en memoria y fallos
  reproducibles. Bleak en el Mac puede ejercitar la board como servidor;
  no asumir que Bleak tambien emula un servidor GATT. El rol central de la
  board necesita un periferico compatible para su prueba de radio.

Salida con una board: contratos y simulaciones, mas una parte de la radio
si se autoriza. Aceptacion completa exige dos boards o un segundo periferico
compatible comprobado. Una board de otro proyecto no funciona solo por tener BLE.

### E4. Batallas Compartidas, Rivales Guardados Y Ecos

- [ ] Extraer resolucion determinista de ronda con las dos decisiones
  explicitas. Conservar el wrapper de Arena actual; no modificar sin
  aprobacion la duracion de pelea/pausa de Mochila discutida previamente.
- [ ] Intercambiar snapshot consentido del rival: petId, especie/rango,
  reglas, stats efectivos, elemento, tecnicas y dominio relevante. No
  enviar toda su partida, parentesco o identificadores personales por defecto.
- [ ] Acordar snapshot, hash de reglas, battleId y semilla de sesion. Validar
  cada accion y comprobar hash del estado por ronda; una divergencia detiene
  la pelea sin aplicar un resultado unilateral inventado.
- [ ] Coordinar semillas/decisiones sin ventaja de elegir despues de conocer
  la orden remota; propuesta commit/reveal acotada para decisiones de ronda.
  Un coordinador de sesion no puede imponer HP ni recompensas arbitrarios.
- [ ] Resultado con recibo bilateral y journal local antes de otorgar premio.
  Desconexion deja resultado pendiente hasta reconciliar; no forzar empate
  ni repetir premios al reiniciar o reconectar.
- [ ] Guardar hasta 8 rivales y 32 trazas de hasta 30 rondas; cargar solo
  una al practicar. No reservar memoria para todo el archivo de combates.
- [ ] Diferenciar Replay (reproducir lo ocurrido) de Eco (simular otra pelea
  con snapshot y tendencias observadas). Un Eco no reproduce exactamente
  decisiones futuras ni el cerebro privado de la otra mascota.
- [ ] Separar premios: Arena actual conserva su contrato; P2P confirmado
  aporta progreso acordado una sola vez; Eco es practica con aprendizaje
  limitado, sin victorias oficiales, EV ni stock infinitos para evolucionar.
- [ ] Probar desconexion antes/durante/despues de confirmar, reinicio de
  cada lado, duplicados, versiones distintas y corrupcion de ronda.

### E5. Breeding E Incubadora

- [ ] Dividir entrega en roster/premios/huevos, breeding interno y despues
  breeding entre boards. La modalidad interna con dos mascotas propias
  se puede validar en una board; no bloquearla por falta de un segundo peer.
- [ ] Separar paquete compartido, definicion e individuo. Premio crea huevo
  unico; eclosion conserva ID y nunca sustituye otra mascota. Fijar limites
  de paquetes/mascotas/huevos e incubacion fuera de foco mediante presupuesto
  medido. No heredar por accidente la vieja propuesta de una sola plaza.
- [ ] Primera version: dos individuos adultos de sexo compatible, sanos,
  despiertos, de linea compatible, en dos identidades distintas y con
  consentimiento del propietario para breeding interno o de ambos usuarios
  entre boards. Sin auto-breeding ni sustitucion de padres.
- [ ] Cooldown propuesto V1: 24 h de tiempo encendido acumulado por padre,
  con checkpoints persistentes conservadores. No acreditar tiempo apagado
  sin un reloj confiable; ajustar la fecha no adelanta este contador.
  Probar reinicios y restauraciones sin saltar ni reiniciar el cooldown.
- [ ] Bloquear parentesco directo conocido (padres/hijos/hermanos); guardar
  hasta dos generaciones. Es una restriccion acotada, no genealogia infinita.
- [ ] Cada uno de los seis IV proviene de uno de los dos padres; propuesta
  inicial de mutacion pequena: probabilidad 1/32 por gen, cambio -1/+1,
  limitado a 0..15. Usar semilla de breeding acordada y reproducible.
- [ ] Sexo del hijo se sortea independientemente; no vincularlo a mejores
  IV. No copiar EV, victorias, dominio ni recuerdos completos de padres.
- [ ] Herencia conductual moderada aprobada: mezclar temperamento y un
  resumen acotado de tendencias/preferencias parentales, no sus tablas de
  experiencia, eventos, tecnicas dominadas ni emocion temporal. Especificar
  pesos y topes antes de implementarlo; evitar amplificacion ilimitada entre
  generaciones y mantener capacidad de aprender un estilo opuesto.
- [ ] Fijar la influencia parental al preparar el breeding y conservar el
  resultado en su recibo versionado. Reintentos no recalculan la personalidad
  segun cambios posteriores de los padres ni duplican experiencia del hijo.
- [ ] Transaccion con breedingId, padres, reglas, destino e ID del hijo;
  fases preparar/confirmar/entregar y recibos persistentes. Cortes de energia
  pueden dejar una entrega pendiente, resuelta al reconectar, no un segundo huevo.
- [ ] En breeding interno usar una transaccion local para padres/cooldown/hijo
  y semilla persistida. No requiere confirmacion de otro dispositivo. Definir
  compatibilidad de lineas y contenido del hijo antes de aceptar el cruce;
  no prometer fusiones con sprites inexistentes.
- [ ] Mantener marcas de secuencia/recibos suficientes para impedir reenvios
  tras rotar el historial. No prometer atomicidad instantanea entre dos
  dispositivos desconectados ni resistencia a un peer que borre su propia flash.
- [ ] Con capacidad llena, conservar premio pendiente o rechazar antes de
  aceptar segun politica aprobada. Elegir mascota activa no borra ni clona
  al adulto. El usuario confirma inventario compartido: migracion unica de
  reserva/stock requiere contrato explicito y pruebas contra duplicados.
- [ ] Tests de herencia, parentesco, saturacion de genes, migracion, doble
  confirmacion, incubadora llena, retries y cortes en cada escritura.
- [ ] Probar padres de estilos iguales/opuestos, multiples generaciones y
  cambio posterior de estilo de la cria. Verificar contadores propios nuevos,
  cero EV/victorias/dominio heredados, ausencia de recuerdos copiados y mismo
  resultado tras retry/reinicio, con paridad Python/C++.

### E6. TinyML Opcional Y Comparacion Con La Politica Ligera

- [ ] Evaluar TensorFlow Lite Micro/LiteRT Micro como candidato principal
  para inferencia de una red int8 pequena; ESP-DL como alternativa. No
  instalar la version actual de Espressif en IDF 4.4.7 como si fuera compatible.
- [ ] Resolver primero el spike de toolchain: version compatible fijada y
  mantenible o migracion de IDF/Arduino por separado con regresiones completas.
  Comprobar tambien el estandar C++ requerido en ese entorno aislado.
  Si no hay ruta sostenible, conservar politica ligera y posponer este runtime.
- [ ] Modelo piloto tabular, no imagen/audio/LLM: aproximadamente 12 entradas
  de estado/contexto y hasta 5 puntuaciones de tecnicas, una capa pequena.
  Datos de simulacion y encuentros consentidos, separados por pet/rival/semilla
  para no medir memorizacion como generalizacion.
- [ ] Entrenar/convertir la red en el computador. Inferencia en board; la
  personalizacion online vive en tablas propias. TFLM no aporta entrenamiento
  en dispositivo como funcionalidad estandar.
- [ ] Objetivos exploratorios, no consumo garantizado: pesos <=16 KiB en
  flash y arena <=8 KiB RAM. Medir arena REAL, bloque contiguo y el resto
  del interprete; una red diminuta no garantiza runtime diminuto.
- [ ] Inferir al decidir, no al dibujar. Objetivo p95 <=5 ms por decision,
  sin regresion perceptible de NEXT y con guardas de heap intactas mientras
  BLE esta habilitado. Rechazar integracion si falla el presupuesto.
- [ ] Comparar contra politica E2 con mismos rivales/semillas y coste de
  memoria/latencia. Adoptar solo si aporta mejora fuera del conjunto de
  entrenamiento; sino la ausencia de red no elimina el aprendizaje local.
- [ ] Modelo versionado con schema de entradas y hash de reglas, distribuido
  por el flujo de firmware verificado, no recibido del rival. Un digest
  no prueba autoria; firma de firmware/secure boot requiere un diseno aparte
  y no se presume habilitada. Si no carga, no hay memoria o falla una
  inferencia, volver a la politica ligera sin interrumpir cuidado,
  guardado ni batalla.

## 5. Mapa De Archivos Para Las Especificaciones De Cada Entrega

Rutas nuevas son propuestas de propiedad, no modulos que ya existan.

| Area | Existente | Nuevos modulos previstos |
| --- | --- | --- |
| Identidad y genetica | `src/core/dna.py`, `PetState.h/.cpp`, `src/data/digimon/*.json` | `src/core/pet_profile.py`, `src/core/potential.py`, `vpet/PetProfile.h`, `vpet/Potential.h` |
| Persistencia | `SettingsStore.h/.cpp`, `NvsKeyValueStore` | `vpet/ExperienceStore.h`, adaptador LittleFS versionado y tests de fallo |
| Aprendizaje/afecto | `PracticeProgress.h`, `SleepRoutine.h`, `cues.py` | `src/core/experience.py`, `src/core/adaptive_policy.py`, `vpet/Experience.h`, `vpet/AdaptivePolicy.h`, `vpet/Affect.h` |
| Comunicacion | `BleService.h/.cpp`, `platformio.ini` | `vpet/PeerProtocol.h`, `vpet/PeerSession.h`, adaptador `PeerService`, `scripts/peer_emulator.py` |
| Encuentros/ecos | `PracticeBattle.h`, `PracticeSession.h`, `practice.py` | `vpet/PeerBattleSession.h`, `vpet/OpponentArchive.h`, equivalentes Python |
| Breeding | ADN y guardado existentes | `src/core/breeding.py`, `vpet/Breeding.h`, `vpet/Nursery.h` |
| ML opcional | No existe | entorno PIO separado, `scripts/ml/`, adaptador `TinyPolicy` y fixtures de paridad |
| UI/integracion | `App.cpp`, `Panels.cpp`, `Navigation`, `scripts/sim_renderer.py` | vistas de encuentro, rival e incubadora, sin nuevo framebuffer |

Prefijo `vpet/` significa `firmware/t-display/lib/vpet_core/src/vpet/`.
Adaptadores de radio/flash/modelo viven fuera del core, bajo `src/` e
`include/vpet/` de firmware. El core no depende de NimBLE, TFT ni TFLM.
Coordinar dominio de Status con su propietario; no mezclar refactor de
layout de Status con la primera entrega de identidad.

## 6. Contratos Entre Modulos

- `PetProfile`: identidad individual; se guarda con la mascota y su reserva.
- `Potential(profile, genome, stat)`: calcula limites; nunca modifica ADN
  o inventario al consultar una pantalla.
- `ExperienceReducer(event, learnedState)`: aplica un evento confirmado una
  vez; no inicia acciones de usuario ni vuelve a otorgar recompensas del core.
- `Policy(context, legalActions, learnedState)`: sugiere accion legal; no
  dibuja, hace I/O ni altera persistencia durante inferencia.
- `PeerProtocol`: bytes no confiables a mensajes validados, con capacidades
  y versiones; no escribe directamente PetState desde callbacks.
- `OpponentSnapshot`: datos consentidos y congelados, nunca punteros o
  instrucciones remotas. `BattleReceipt` permite reconciliar el resultado.
- `BreedingReceipt`: hijo/destino/parentesco/semilla ya acordados; reintentar
  entrega conserva breedingId e ID del hijo, no genera un hijo nuevo.

## 7. Estrategia De Pruebas Y Entrega

Cada fase produce primero pruebas fallidas de su contrato, luego implementacion,
paridad Python/C++ y pruebas adversariales. Pasar tests locales no equivale a
aceptacion visual, radio, dos boards ni cortes reales de alimentacion.

Comandos existentes a conservar al implementar:

```sh
.venv-platformio/bin/python -m pytest -q
.venv-platformio/bin/pio test -d firmware/t-display -e native
.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay
```

- [ ] Probar restauracion de partida actual, reserva, inventario, rutinas y
  datos heredados antes de cada cambio de schema; rechazar version desconocida
  sin resetear silenciosamente la mascota.
- [ ] Testear generacion completa de potencial: todos los IV, topes,
  bonificaciones, compras/uso, viajes, evolucion y datos legacy sobre el cap.
- [ ] Repetir cada evento/paquete/recibo y cortar cada escritura simulada;
  no duplicar premios, hijos ni aprendizaje. Llenar almacenamiento y probar
  corrupcion, perdida y recuperacion del ultimo checkpoint.
- [ ] Comparar aprendizaje activado/desactivado, adaptacion a cambios y
  calidad del comportamiento; registrar limites, no solo victorias favorables.
- [ ] En placa autorizada: observar memoria, fragmentacion, input y
  reconexion durante sesiones prolongadas; no reabrir el gate de Status
  como aprobado por probar otra funcion.
- [ ] Con dos boards: ambas versiones compatibles, aceptar/rechazar
  encuentro, desconexion, reanudacion, doble entrega, poderes distintos y
  cada rol central/periferico. Mantener esta casilla abierta con una board.
- [ ] Entregar una fase por vez con commit/revision, respaldo, verificacion
  de digest, NVS conservada y criterios de vuelta a la version anterior.
  Nunca borrar `out/board-backups/` ni incluir partidas/logs en el push.

No se dan fechas de terminacion sin cerrar balance, spike ML y disponibilidad
del segundo peer. Antes de ampliar, cerrar F0 del programa consolidado. En
este subsistema empezar despues por E0+E1 en subfases: identidad/migracion y
luego potencial/curva, con revision entre ambas.

## 8. Fuentes Tecnicas Consultadas

Verificadas el 2026-10-23; documentacion externa puede evolucionar.

- [LiteRT for Microcontrollers](https://developers.google.com/edge/litert/microcontrollers/overview):
  inferencia C++ en microcontroladores y ESP32; entrenamiento en dispositivo
  no soportado por el runtime estandar. No confundir el peso del modelo con
  todo el coste de memoria del interprete.
- [esp-tflite-micro](https://github.com/espressif/esp-tflite-micro): componente
  para ESP-IDF; politica actual soporta IDF 5.1 y superiores, no 5.0 o anteriores.
- [ESP-DL, Getting Started](https://docs.espressif.com/projects/esp-dl/en/latest/getting_started/readme.html):
  IDF 5.3+, ESP32 clasico mediante operadores C y configuracion adicional;
  ejemplos orientados a S3/P4. No es una integracion directa con el IDF actual.
- [NimBLE-Arduino, cliente](https://h2zero.github.io/NimBLE-Arduino/class_nim_b_l_e_client.html):
  conexion, descubrimiento GATT, MTU, seguridad y ciclo de vida del cliente.

Referencias locales: `firmware/t-display/platformio.ini`, `BleService.cpp`,
`PetState.cpp`, `PracticeBattle.h`, `PracticeProgress.h`, `SettingsStore.h`,
`src/core/dna.py`, `out/sleep-bubble-position/board-runtime.json`,
`firmware/t-display/partitions.csv`.

## 9. Revision De Este Plan

- [x] Cubiertos los cinco requisitos del usuario y la disponibilidad de una placa.
- [x] Separados hechos actuales, propuestas de balance y funciones no implementadas.
- [x] Distinguidos ADN heredable, memoria aprendida y modelo de inferencia.
- [x] Conservados schema/enum/partida actuales como restriccion de migracion.
- [x] Incluidos limites de memoria, toolchain, fallos, duplicados y aceptacion fisica.
- [x] Breeding y P2P requieren consentimiento; no se promete atomicidad magica
  entre dispositivos desconectados ni confianza en firmware ajeno.
- [ ] Usuario revisa reglas propuestas y aprueba la primera subfase antes de ejecutar.
