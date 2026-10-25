# Programa Consolidado De Entregas vPet

**Fecha:** 2026-10-23.
**Estado:** consolidacion de requisitos y orden recomendado para revision;
no autorizacion global para implementar, migrar, publicar ni flashear.
**Objetivo:** pasar de la linea actual a un dispositivo con contenido
instalable, individuos propios, crecimiento genetico, aprendizaje e intercambio.
**Arquitectura:** motor portable por composicion y definiciones versionadas;
adaptadores de UI, USB, BLE y persistencia separados. No una subclase por pet.
**Stack vigente:** Python/Pillow/pygame y PlatformIO Arduino C++ para la
T-Display clasica 240x135. WiFi permanece deshabilitado.

Actualizacion posterior: el usuario solicita ejecutar F1 y pruebas antes de
cerrar F0 fisico. [Fundamento F1 implementado localmente](../../content-definitions.md),
sin carga ni instalador; la medicion no permite dos lineas del tamano actual.
Inventario compartido confirmado; objetivo de cuatro mascotas sujeto a
presupuesto. [Pilotos numericos y breeding](../../product-decisions-2026-10-23.md)
son propuestas por aprobar, no cambios activos.

Este documento ordena el programa; no sustituye las especificaciones y planes
ejecutables de cada subsistema. Se prepara y aprueba una entrega por vez con
contratos, archivos, pruebas fallidas/implementacion y criterio de aceptacion.
No se inventan interfaces finales mientras balance, capacidad y confianza
siguen abiertos. El [roadmap de calidad](2026-10-11-delivery-roadmap.md)
conserva la matriz detallada de pruebas de la base actual.

## 1. Que Tenemos Hoy

| Area | Estado comprobado en el proyecto |
| --- | --- |
| Linea actual | Huevo, Sparkmon, Firemon, Flamemon y Dragfiremon |
| Motor e interfaz | Firmware OO, core portable, simulador y nueve menus; F1 extrae la definicion y resolver, manteniendo adaptador de arte builtin |
| Crianza | Alimentacion, peso/sobrepeso, necesidades, salud, animo y vinculo |
| Descanso | Dia/noche 18:00-06:00, luces, horario aprendido, tired/angry y globos sin leyendas; Zzz sobre el pet |
| Entrenamiento | Seis stats, sesiones y cinco tecnicas; espacios 2/3/4, aprendizaje y equipo manual separados |
| Arena y evolucion | Combate local y resultados que aportan a evolucion automatica |
| Mochila y exploracion | 40 consumibles, tres rutas, stock, recibos y recuperacion; validacion fisica incompleta |
| Persistencia y radio | NVS y reserva actuales; BLE existente no es protocolo de juego P2P |
| Nueva ficha evolutiva | Implementada y probada localmente; aun no cargada ni aceptada en placa |
| Documentacion | Arquitectura, guia funcional y matriz para video; no hay video de lanzamiento producido |

No confundir implementado, compilado, cargado y aceptado. Ultima carga
registrada: ece6506 (posicion Zzz); no es el binario de la nueva ficha.
La ultima suite local registrada para la ficha tiene 1653 Python/185 nativas;
no se ejecuto de nuevo al redactar este programa.

## 2. Requisitos Y Aprobaciones

| Tema | Decision o requisito | Lo que sigue abierto |
| --- | --- | --- |
| Identidad y sexo | F2a local: ID individual, macho/hembra 50/50, padres y migracion de partida/reserva, sin ventaja de combate por sexo | Visibilidad del sexo, carga y validacion fisica; breeding aun pendiente |
| Herencia conductual | Aprobada: temperamento e influencia moderada de tendencias/preferencias parentales; experiencia propia puede cambiar el estilo | Pesos, mezcla, topes y control entre generaciones |
| No copiar entrenamiento | Aprobado: no heredar EV, victorias, dominio de tecnicas, recuerdos completos ni malestar temporal | Contrato de inicializacion y persistencia del hijo |
| Crecimiento | Requerido: desbloqueo por evolucion y ADN por stat; resolver saturacion en 99 | Formula, escala visible, tipos numericos, curva y migracion; el ejemplo de 280 no esta aprobado como balance |
| Paquetes y huevos | Requerido: otra mascota distinta como huevo de premio; objetivo cuatro mascotas | Viabilidad de arte/registro, plazas de huevos, crianza inactiva y compatibilidad |
| Hub web USB | Direccion solicitada inspirada en TamaPoke: catalogo y carga desde navegador | Contrato USB, navegador objetivo validado, respaldo y despliegue del portal |
| Items externos | Requerido: recibir de personas/proveedores; inventario compartido confirmado | Emisores, migracion de stock, canje, coordinacion de doble gasto y servicio |
| Aprendizaje | Requerido: aprender de entrenamiento, Arena y exploracion | Eventos, recompensas, politica y evaluacion de resultados |
| Breeding y comunicacion | Requeridos: breeding interno, encuentros y rivales recordados; actualmente hay una placa | Reglas de cruce, cooldown, protocolo y segundo dispositivo para validar radio |
| TinyML | Evaluacion solicitada; proveedor opcional de decisiones | Compatibilidad, RAM y beneficio frente a politica ligera; no adopcion aprobada |

El usuario pidio evaluar peleas mas largas para usar Mochila. No hay nueva
duracion ni pausa de combate aprobadas: se disena por separado, sin cambiar
la Arena actual como efecto colateral de genetica o Hub.

## 3. Orden Recomendado

### F0. Cerrar La Base Y Su Recuperacion

- [ ] Diagnosticar Mochila con estado real, item, contexto y stock antes/despues;
  distinguir sin efecto, dormido, lesion y objetos exclusivos de Arena. No
  asumir corregido el reporte de que todos los items fallan.
- [ ] Validar Status de cuatro paginas, NEXT/salto de bloqueados, tecnicas
  3/4, evolucion automatica por Arena y consumo/recompensas tras reinicio.
- [ ] Completar noche, pausa/reanudacion, desaparicion de globos y sesiones
  largas con BLE; registrar latencia y memoria, no inferir FPS del host.
- [ ] Compilar revision fresca, respaldar y, con autorizacion vigente,
  cargar/aceptar la nueva ficha evolutiva. Conservar todos los backups.

Salida: version base identificada y matriz de aceptacion, con fallos abiertos
explicitamente registrados. Las autorizaciones excepcionales antiguas de
Status no se reutilizan para otra carga.

### F1. Definiciones Y Presupuesto De Contenido

- [x] Extraer la linea builtin a definiciones/roles y resolver de assets,
  eliminando nombres/rutas/loops concretos de los consumidores del motor.
- [x] Reconciliar las tres reglas automaticas desde JSON sin cambiar balance;
  peso 8..14 tambien en catalogos. Metadata legacy de huevo se conserva.
- [ ] Medir dos paquetes completos, recursos compartidos, staging y rollback;
  decidir compresion/organizacion antes de prometer espacio para otra linea.

Salida: Firemon funciona igual a traves del resolver y un segundo paquete
de prueba ejercita las mismas vistas sin recompilar por criatura.
La ultima medicion de LittleFS deja 659456 bytes libres; no es una medicion
actual ni un presupuesto que garantice otra linea completa.

### F2. Identidad Y Potencial Por ADN

- [x] Piloto F2b aislado: curva por rango/IV, barrido y referencia Python/C++,
  proyecciones de EV y combates host. [Resultados y limites](../../growth-pilot.md).
  No equivale a cerrar identidad, balance aprobado, migracion o integracion.
- [x] F2a local: perfil individual, sexo, parentesco y migracion de partida/reserva
  sin cambiar IDs numericos existentes ni regenerar ADN o perder inventario.
  [Contrato y limites](../../individual-profile.md). Visibilidad de sexo y
  validacion fisica pendientes; no habilita breeding ni roster.
- [x] F2b local: integrar curva genetica por stat/etapa, tipos ampliados,
  consumibles, previews y vistas. [Alcance](../../growth-integration.md).
  BLE de juego futuro debe declarar este perfil/numeros en su version.
- [x] Conservar EV adquiridos y evitar reducciones silenciosas del progreso;
  ganancias nuevas y consumo sin efecto obedecen el limite aprobado.
- [ ] Cargar y aceptar fisicamente caps/boosts/rival y legibilidad de stats
  amplios, con autorizacion y gate de Status vigente. Sin carga en esta entrega.

Salida: evolucion abre margen real y cada stat depende de su ADN; paridad
Python/C++, reglas de combate compatibles y migracion verificadas.
Huevo/Sparkmon no obtienen entrenamiento por este cambio sin otra aprobacion.

### F3. Hub USB De Consulta Y Respaldo

- [ ] Definir identificacion de dispositivo/firmware, capacidades, lectura de
  espacio, estado y respaldo verificado con consentimiento del usuario.
- [ ] Probar permisos de navegador, puerto ocupado, desconexion y version
  incompatible. Primer hito sin instalar paquetes ni modificar inventario.

Salida: conectar, consultar y respaldar desde navegador. Puede prepararse
tras F0, sin esperar breeding; usar binarios propios, no el de TamaPoke.

### F4. Coleccion E Incubadora

- [ ] Verificar objetivo de cuatro mascotas y aprobar plazas de huevos/paquetes
  y politica de inactivos. Inventario compartido ya confirmado; migracion unica.
- [ ] Crear roster versionado: individuo activo, otros individuos y huevos
  comparten recursos por definicion, pero nunca ADN/progreso por accidente.
- [ ] Integrar reserva legacy sin borrarla. Eclosionar conserva el mismo ID;
  cambiar de mascota no duplica stock ni reinicia su vida.

Salida: varios individuos bajo un limite aprobado; una board basta para
probar la modalidad local. Depende de F1 y F2a.

### F5. Instalar Paquetes Y Recibir Premios/Items

- [ ] F5a: validar manifiesto, rutas, dimensiones, bytes, compatibilidad,
  hashes y autorizacion; transferir por bloques, verificar y activar al final.
- [ ] F5b: recibos de proveedor con ID, destinatario, item/huevo y cantidad;
  confirmar stock/premio una sola vez despues de asegurar los recursos.
- [ ] Definir confianza y coordinacion de canje antes de prometer proteccion
  contra doble gasto entre boards o restauracion de un respaldo antiguo.
- [ ] Probar capacidad llena, replay, corte/reinicio en cada escritura y
  reanudacion ligada a dispositivo/contenido, sin borrar NVS ni toda LittleFS.

Salida: Hub entrega un huevo nuevo y unidades de items autorizadas sin
reemplazar la mascota actual. Depende de F1/F3/F4 y modelo de confianza.
Regalos de unidades propias entre usuarios requieren tambien F8.

### F6. Experiencia Y Comportamiento Adaptativo

- [ ] Registrar experiencias confirmadas una sola vez; separar necesidades,
  emocion temporal, temperamento, predisposicion y experiencia propia.
- [ ] Implementar primero politica ligera acotada para combate, entrenamiento
  y exploracion; respetar acciones legales y decisiones del usuario.
- [ ] Evaluar adaptacion a cambios, diferencias individuales y coste de RAM;
  no confundir variar animaciones con aprender ni duplicar recompensas.

Salida: comportamiento cambia por experiencias medibles y persiste, sin
alterar genes ni ejecutar acciones de gasto no autorizadas.

### F7. Breeding Interno

- [ ] Aprobar compatibilidad de padres/lineas, parentesco permitido, cooldown,
  herencia genetica y mezcla conductual limitada.
- [ ] Crear hijo/huevo con identidad propia; fijar predisposicion parental
  en recibo reproducible. No copiar EV, victorias, dominio o recuerdos.
- [ ] Probar generaciones sucesivas, aprendizaje de un estilo contrario,
  incubadora llena y cortes sin duplicar hijos ni consumir dos cooldowns.

Salida: dos individuos propios pueden criar en una sola placa. Depende de
F2a/F4/F6 y contratos aprobados; no requiere BLE ni otra placa.

### F8. Encuentros, Rivales Y Regalos Entre Usuarios

- [ ] Protocolo BLE versionado con consentimiento, capacidades y mensajes
  validados; no asumir que BLE HID actual ya sirve para el juego.
- [ ] Batallas acordadas, resultados reconciliables, snapshots consentidos y
  ecos offline, distintos de replays y de una copia exacta del rival.
- [ ] Transferencia de items coordina debito/credito con recibos recuperables;
  desconexion no crea unidades. Breeding externo reutiliza F7 con acuerdo
  bilateral de destino e hijo unico.
- [ ] Usar emulador y dos pets simulados mientras solo haya una placa;
  validar ambos roles de radio con un segundo peer compatible antes de cerrar.

Salida: interoperabilidad real comprobada entre versiones compatibles, con
politica de premios y seguridad explicitamente limitada al protocolo probado.

### F9. TinyML Opcional Y Lanzamiento

- [ ] Comparar una politica pequena de inferencia con F6; adoptar solo si
  mejora comportamiento con memoria/latencia medidas y toolchain sostenible.
- [ ] Mantener fallback por reglas; no introducir nube, WiFi ni LLM en board.
- [ ] Cerrar manual, arquitectura, catalogo, version y tomas del video sobre
  la misma entrega aceptada; no anunciar funciones de fases no terminadas.

TinyML puede descartarse sin impedir aprendizaje ni lanzamiento. Manual y
matriz audiovisual se mantienen en TODAS las fases, no solo en F9.

## 4. Proceso De Cada Entrega

1. Aprobar especificacion y preparar plan ejecutable propio del subsistema.
2. Escribir pruebas de contrato que fallen y luego implementacion minima.
3. Verificar Python/C++, pixeles cuando aplique y fallos de persistencia.
4. Actualizar arquitectura, guia, estado, roadmap y matriz de video.
5. Compilar y registrar revision/evidencia. Carga solo autorizada con backup,
   digest y aceptacion fisica; nunca confundir compilacion con funcionamiento.
6. Revisar diff, commit de esa entrega y push al destino autorizado, sin
   partidas, secretos ni respaldos. Conservar cambios ajenos.

Comandos de implementacion, no ejecutados por esta consolidacion documental:

```sh
.venv-platformio/bin/python -m pytest -q
.venv-platformio/bin/pio test -d firmware/t-display -e native
.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay
git diff --check
```

## 5. Referencias Y Proximo Hito

El usuario priorizo F1 local y pruebas. Siguiente hito: resolver presupuesto
de contenido y revisar pilotos F2; F0 fisico (Mochila, ficha/Status, noche y
persistencia) sigue abierto y no se cierra por tests de F1. Preparar F3 de
consulta/respaldo por separado; no arrancar todos los subsistemas a la vez.

- [Arquitectura](../../architecture.md).
- [Paquetes, Hub e items externos](../../content-packages.md).
- [Genetica, aprendizaje y encuentros: contratos propuestos](2026-10-23-social-genetics-learning-program.md).
- [Estado y evidencia](../../project-status.md).
- [Guia de opciones](../../product-guide.md).
- [Matriz audiovisual](../../launch-video.md).
