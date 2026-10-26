# Guia De Funciones Del Producto

## Ampliacion 2026-10-25

Opciones incorpora Coleccion: cuatro plazas totales con huevos incluidos,
un individuo activo, mochila compartida y confirmaciones para migrar,
crear fundador, activar mascota o cruzar padres aptos. No concede items.
El simulador incluye Preferencias aprendidas por individuo y herencia
conductual moderada. [Reglas y guion de video](collection-learning-breeding.md).
El firmware tambien registra experiencias y usa AUTO aprendido despues de
activar Coleccion; la consulta de Preferencias aun es solo del simulador.
Esta ampliacion ya esta flasheada, con arranque, digests y BLE comprobados;
la aceptacion visual y las sesiones prolongadas siguen pendientes. Ver
[registro de entrega](superpowers/plans/2026-10-25-collection-board-delivery.md).

Corte documental: 2026-10-25. Borrador de manual para la T-Display 240x135,
basado en el codigo y los contratos actuales; no es una certificacion de
lanzamiento. Base versionada inspeccionada: `f733c60`, mas la ficha evolutiva
implementada despues, F1/F2 y la entrega de coleccion/aprendizaje.
El [estado vigente](project-status.md) y el
[roadmap](superpowers/plans/2026-10-11-delivery-roadmap.md) separan
implementacion, carga USB y aceptacion fisica. Pico es una plataforma legacy.

## Controles Y Disponibilidad

Revision visual 2026-10-26: Coleccion muestra cuatro plazas con sus criaturas,
marca de activa y sexo M/F. Una plaza vacia o el comando Huevo abre una
confirmacion; no crea un individuo al seleccionarla. La ficha permite activar,
elegir padre, consultar preferencias y volver. En el cruce primero se fija un
padre y luego la pareja elegible; ambos son visibles antes de confirmar.
La bienvenida "Activar coleccion" reemplaza el termino tecnico "Migrar".
En firmware la bienvenida abre una confirmacion predeterminada en Cancelar.
No activar ni crear huevos solo para grabar un video sin explicar ese efecto.
Preferencias en placa muestra la politica de la mascota activa; los individuos
en reserva no cargan otra politica para esta consulta. El simulador conserva
la consulta de todas las politicas. La carga y aceptacion visual se registran
por separado en el estado del proyecto.

El [perfil individual F2a](individual-profile.md) ya implementado localmente
guarda ID, sexo y padres desde huevo, y los conserva al evolucionar.
El perfil no agrega ventajas de combate por sexo. La entrega posterior
incorpora Coleccion y breeding local; no confundirlo con enlace entre boards.

- Izquierdo corto: NEXT. Derecho corto: ACTION.
- Izquierdo mantenido dos segundos: BACK. En Opciones se sale seleccionando
  VOLVER; el hold no cierra ese menu.
- Los menus bloqueados por etapa se ven atenuados y NEXT los salta. El
  cansancio o el sueno pueden impedir una accion, pero no equivalen a un
  bloqueo permanente por etapa.
- Huevo no come, entrena, explora, batalla ni descansa. Sparkmon ya puede
  comer y descansar; entrenamiento, viajes y Arena se habilitan desde Firemon.

Orden de los nueve iconos, verificado en Navigation/App de T-Display; no
usar los indices del menu Pico para describir esta barra.

## Las Nueve Opciones

| Opcion / icono | Que permite hacer | Resultado o restriccion importante | Contrato |
| --- | --- | --- | --- |
| Status / ficha con corazon | Consultar vitales, cuidado, combate y ADN en cuatro paginas | Es consulta, no cura ni entrena. La aceptacion fisica completa de las cuatro paginas sigue pendiente | [Status](status-vitals-care-ev.md) |
| Alimentar / carne | Dar Carne o Proteina | Son ilimitadas en este menu, pero existen limites de saciedad y por ciclo; no significa comer infinitamente seguido | [Alimentos](items-and-rewards.md) |
| Training / pesa | Entrenar ataque, defensa, velocidad, HP, MP, mente; aprender y equipar tecnicas | Atributos: 10 s, 8 energia y hasta 6 EV por sesion completada. Cancelar no premia ni cobra. HP de combate no es curacion de salud | [Sesion](training-session.md), [tecnicas](techniques.md) |
| Exploracion / brujula | Elegir Patio, Jornada o Noche y reclamar el regreso | Necesita reloj fiable. Premios limitados; regresar antes puede reducirlos. Cerrar el panel no cancela el viaje | [Exploracion](exploration.md) |
| Arena / espadas | Combatir contra el rival interno con tecnicas equipadas y bolsa | La bolsa NO pausa actualmente el combate. Resultados decisivos guardados contribuyen a evolucion; abrir o retirarse no cuenta | [Arena y evolucion](superpowers/plans/2026-10-18-arena-evolution.md), [objetos](adopted-items.md) |
| Descanso / foco | Apagar o encender luz; volver | Apagar inicia descanso, encender lo interrumpe. Abrir Rest no lo inicia. No contiene Backup ni Cold | [Descanso](sleep-routine.md), [Rest](rest-and-board-validation.md) |
| Mochila / bolsa | Consultar existencias y usar objetos permitidos | Los BAT se usan en Arena; sin efecto util, dormido o sin stock no se consumen. Manual/Guia se gastan al completar entrenamiento valido | [Catalogo activo](adopted-items.md), [compatibilidad](items-and-rewards.md) |
| Evolucion / libro | Consultar arbol y progreso hacia la siguiente evolucion | Ficha cargada con F1/F2: tiempo restante, requisitos actuales/objetivos y paginas con NEXT. ACTION/BACK vuelve al arbol; aceptacion especifica pendiente | [Detalle](evolution-progress.md) |
| Opciones / engrane | Bluetooth, idioma, sonido, guardar/cargar, fecha/hora, EVOLVE, pausar crianza, Coleccion y volver | EVOLVE de desarrollo queda bloqueado al activar Coleccion. Pausar crianza no es dormir | Seccion siguiente y [conectividad](connectivity.md) |

## Opciones Del Engrane

| Ajuste | Comportamiento actual | Limite que debe explicarse |
| --- | --- | --- |
| Bluetooth | Activa anuncio BLE y muestra OFF/ADVERTISING/CONNECTED/ERROR | No implementa batallas, breeding ni transferencia entre vPets |
| Idioma | Alterna ES/EN | Grabar ambos idiomas si se muestran en material comercial |
| Sonido | Alterna la preferencia guardable | No prometer altavoz o audio audible sin hardware y prueba especifica |
| Guardar | Solicita guardar el estado actual | No crea una copia exportable para el usuario |
| Cargar | Lee la partida persistida | No confundir con reiniciar vida ni con importar otra mascota |
| Fecha / Hora | Ajusta el calendario del juego | Tras perder el reloj sin alimentacion puede requerir ajuste; no hay RTC respaldado |
| EVOLVE | En modo legacy fuerza formas para desarrollo; bloqueado con Coleccion activa | No usar para aparentar evolucion automatica ni reiniciar individuos de la coleccion |
| Pausar crianza | Congela crianza y avance del descanso hasta reanudar | No recupera energia ni reemplaza una siesta |
| Coleccion | Migrar con confirmacion, consultar cuatro plazas, crear fundador, activar mascota y cruzar adultos aptos | Un huevo ocupa una plaza; no instala paquetes, no regala objetos y congela individuos inactivos |
| Volver | Sale de Opciones | Es la salida de este menu, no el hold BACK |

## Como Leer Las Senales

- Comida: alimentar cuando pueda comer. Puede necesitar varias raciones;
  el globo no representa una cantidad de objetos concreta.
- Gotas: poca energia/cansancio. Descanso -> APAGAR LUZ; no pausar crianza.
- Carita dormida: horario preferido de dormir; apagar la luz para acostarlo.
- Zzz: esta dormido; se coloca encima del sprite. No indica hambre o lesion.
- Lesion: usar cuidado/curacion compatible. Salud de crianza y HP de Arena
  son recursos distintos; un recuperador BAT no cura una lesion en Home.
- Tristeza/enojo: expresa animo bajo segun las reglas actuales. Atender una
  necesidad no garantiza que todas las otras necesidades desaparezcan.

Se muestra una necesidad prioritaria, no todas simultaneamente. Resolverla
puede revelar la siguiente. Los avisos de descanso no llevan textos,
contadores ni barras en Home. [Contrato de senales](mood-cues.md).

## Descanso, Noche Y Habitos

Con calendario valido, el escenario cambia a noche a las 18:00 y a dia a
las 06:00. El escenario nocturno no acuesta por si solo al vPet: el usuario
apaga la luz. Luz apagada oscurece escenario y pet independientemente del reloj.

La siesta diurna dura 30 minutos. Dormir recupera +1 energia cada cinco
minutos encendido; no hay recuperacion acreditada con la placa apagada.
La noche dura al menos ocho horas y hasta las proximas 06:00 si es mayor.
Una noche completa tiene premio unico; interrumpir no lo entrega.

El ADN establece una preferencia inicial y varias noches consistentes
pueden desplazarla gradualmente entre 18:00 y 23:00. Esto ya es habito de
sueno, no aprendizaje general por TinyML. La validacion de una noche real,
recuperacion y reinicio sigue abierta. [Reglas completas](sleep-routine.md).

## Tecnicas, ADN Y Evolucion

- Equipables: Firemon 2, Flamemon 3, Dragfiremon 4. Aprender no equipa
  automaticamente; los espacios nuevos quedan vacios al evolucionar.
- Catalogo: Golpe, Llama, Guardia, Rafaga e Inferno, con requisitos propios
  de etapa y lecciones. HP/MP de combate no son salud/energia de crianza.
- ADN/IV identifican potencial innato; EV es entrenamiento acumulado. La
  revision local F2b permite 84/168/252 EV por atributo en Firemon/Flamemon/
  Dragfiremon; cada gen define su techo visible, ya sin saturacion universal
  en 99. Los EV legacy superiores se conservan. [Reglas](growth-integration.md).
  Cargada con F1/F2; Status aceptado por el usuario. El balance completo
  durante una vida real sigue pendiente de comprobar.
- La evolucion normal requiere edad en la etapa y condiciones reales.
  Firemon pide 24 h, hambre/energia/animo >=55, salud >=75 y peso 8..14
  en firmware. Flamemon pide 36 h, 15 resultados decisivos en esa forma y
  al menos 60% de victorias acumuladas sobre victorias+derrotas.
- Sparkmon pide 12 h 10 min y como maximo un error de cuidado. El reloj
  acelerado del simulador no es la duracion real de la placa.
- La comprobacion automatica no debe interrumpir Arena ni una animacion
  activa. EVOLVE del engrane no acredita que esas condiciones se cumplieron.

Fuentes de condiciones: `Evolution.cpp` y EVOLUTION_REGISTRY en config.py;
ambos runtimes incluyen peso de Firemon 8..14. Los JSON de catalogo/generados
no enumeran todos esos mismos campos: reconciliar esa duplicacion antes
de usarlos como contrato publico, sin cambiar reglas al editar el manual.

## Lo Que Todavia No Se Debe Anunciar Como Disponible

- Enlaces de juego entre boards y rivales guardados siguen pendientes.
  Sexo, potencial por ADN, breeding local y aprendizaje acotado ya existen;
  no equivalen a inteligencia general ni a aprendizaje TinyML.
- TinyML, app movil e instalacion de paquetes de comunidad: no disponibles.
- Otra mascota de premio debe nacer como huevo con su propia vida, no cambiar
  la apariencia del pet actual. El instalador y los premios externos siguen
  pendientes; la coleccion local admite cuatro individuos contando huevos.
  [Arquitectura](architecture.md), [paquetes y huevos](content-packages.md).
- Combate mas largo o pausado al abrir bolsa: sugerencia, no comportamiento actual.
- Nueva ficha de Evolucion: cargada; aceptacion fisica especifica pendiente.
- Funcionamiento sin fallos durante noches/sesiones prolongadas, reconexion
  BLE sostenida o ausencia de duplicados bajo cortes reales: no certificados.

## Mantenimiento

Cada cambio funcional actualiza esta guia, su contrato, estado y roadmap.
Una version final del manual debe fijar commit, firmware y recursos grabados,
idioma y evidencia fisica. La [matriz audiovisual](launch-video.md) indica
que falta capturar; no es un video ya producido ni una aprobacion de lanzamiento.
