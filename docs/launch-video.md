# Preparacion Del Video De Lanzamiento

Solicitado por el usuario el 2026-10-23. Documento de preparacion, no video
producido, guion comercial aprobado ni certificacion de lanzamiento.
La [guia funcional](product-guide.md) explica cada opcion; el
[roadmap](superpowers/plans/2026-10-11-delivery-roadmap.md) conserva los pendientes.

## Regla Editorial

Mostrar funciones de la version elegida para lanzamiento y sus resultados
reales. Separar simulacion, hardware, demostracion acelerada y propuestas.
Una captura o un firmware compilado no demuestra persistencia, radio o
autonomia nocturna. No anunciar breeding, P2P, TinyML o app movil
mientras sigan en propuesta. F2a ya guarda sexo/identidad/parentesco localmente,
pero no tiene indicador visual ni validacion en placa: no filmarlo como
opcion disponible. [Contrato](individual-profile.md).
No emplear EVOLVE como prueba de evolucion ganada.

La direccion de contenido es recibir otra mascota como huevo de premio,
con vida propia y breeding interno; no una skin. Capacidad de paquetes,
mascotas y huevos sigue abierta. No mostrar descarga/premio/incubadora como
disponibles ni anunciar cuantos caben hasta implementar y medir ese flujo.

F1 aporta definiciones y resolver probados localmente, no una nueva opcion
descargable. Objetivo solicitado de cuatro mascotas e inventario compartido
confirmado; aun no implementados como coleccion. No mostrar el fixture de
arte reutilizado como otra mascota comercial ni el Hub como disponible.
[Alcance F1](content-definitions.md), [decisiones](product-decisions-2026-10-23.md).

F2b ya integra [stats >99 y caps por etapa](growth-integration.md) en codigo
local. No mostrarlos como funciones de la placa hasta cargar y aceptar esa
revision. La pausa de Mochila y la coleccion siguen pendientes; el piloto
solo mide y no despliega ni cambia configuracion al ejecutarse.

Estructura recomendada: video promocional breve que recorra las nueve
opciones y tutorial por capitulos con controles, condiciones y excepciones.
Duracion, locucion, musica, formato y nombres finales quedan por aprobar.

## Matriz De Tomas

Las aceptaciones indicadas se refieren al uso previo del usuario, no a
material audiovisual disponible. TODAS las tomas finales siguen por grabar.

| Capitulo | Que explicar | Toma y evidencia necesarias | Estado o precaucion |
| --- | --- | --- | --- |
| Inicio / controles | Huevo, crecimiento y dos botones | Arranque real, NEXT/ACTION/BACK y etapas en una partida de demo identificada | Aceleracion o cortes de tiempo deben rotularse; no alterar la partida personal |
| Status | Cuatro paginas; salud, energia, animo, cuidado y ADN/EV | Recorrer ES/EN, sano/herido, valores legibles a tamano real | Aceptacion fisica de las cuatro paginas pendiente |
| Alimentar | Carne/Proteina, saciedad y peso | Antes/despues y rechazo por limite de ciclo | No decir alimentacion sin limites; falta prueba fisica de persistencia |
| Training | Seis atributos y recompensa al completar | Preparacion, 10 s reales, resultado y cancelacion sin cobro | Fluidez mejorada aceptada; falta matriz ampliada y persistencia fisica |
| Tecnicas | Aprender, equipar y usar 2/3/4 espacios | Tres etapas, equipo conservado, tecnica en Arena | Equipo ampliado pendiente de aceptacion fisica completa |
| Exploracion | Patio/Jornada/Noche, regreso y premios | Salida, viaje, regreso anticipado, recibo y reinicio sin segundo cobro | Escala del sprite aceptada; viajes/reinicios pendientes |
| Arena | AUTO/tecnicas/Guardia, bolsa, resultado | Accion legible, consumo BAT valido, stock antes/despues y resultado guardado | Bolsa no pausa; duracion ampliada no aprobada ni implementada |
| Descanso | Gotas, carita dormida, apagar luz y Zzz | Necesidad -> descanso -> recuperacion -> despertar, sin textos en globos | Luz y posicion Zzz aceptadas; desaparicion, noche real y reinicio pendientes |
| Mochila | Stock y diferencias entre BAT/cuidado/permanentes | Un ejemplo valido por familia y un rechazo sin gasto | Reporte del usuario de objetos que no se consumen sigue sin cerrar en su partida |
| Evolucion | Arbol, condiciones y automatico | Dos paginas de requisitos, tiempo restante, evolucion sin EVOLVE y guardado posterior | Nueva ficha aprobada e implementada localmente; falta carga y aceptacion fisica. Arena/evolucion fisica pendiente |
| Opciones | BLE, idioma, sonido, guardar/cargar, reloj, pausa y volver | Cambios reales y pausa/reanudacion; explicar diferencia con dormir | No prometer audio sin hardware probado; decidir si EVOLVE sale de la version comercial |
| BLE | Anunciar y conectar un telefono | OFF -> ADVERTISING -> CONNECTED -> desconexion -> ADVERTISING | No equivale a comunicacion de juego con otra board; ciclo sostenido pendiente |

## Ficha Por Funcion Y Por Grabacion

Para cada fila conservar:

- Funcion, idioma y etiquetas exactas de la version elegida.
- Condiciones de entrada y partida de demostracion separada.
- Secuencia de botones y resultado esperado; rechazo/cancelacion si aplica.
- Efectos sobre recursos, stock, aprendizaje, evolucion y persistencia.
- Commit de codigo, digest de firmware y digest de LittleFS de la placa.
- Fecha, board, evidencia local antes/despues y persona que acepta la toma.
- Si se acelera el tiempo, se usa simulador o se edita una espera, indicarlo.
- Identificador de toma y texto de locucion revisado contra el contrato.

Los originales se guardan localmente en una carpeta de grabacion dedicada
bajo `out/`; el indice editorial y las decisiones aprobadas se versionan
en docs. No subir dumps, partidas personales, MAC, identificadores BLE,
credenciales o respaldos a Git. Conservar `out/board-backups/` intacto.
No mostrar datos identificables de dispositivos/usuarios sin consentimiento.

## Criterios Antes De Publicar

- [ ] Elegir version candidata y confirmar que app y recursos de la placa
  corresponden a esa version. Esta tarea documental no ejecuta un despliegue.
- [ ] Cerrar la aceptacion de las cuatro paginas de Status y casos de
  sueno, objetos, viajes, evolucion y estabilidad enumerados en el roadmap.
- [x] Aprobar e implementar el detalle de Evolucion; preview de produccion
  en [contrato](evolution-progress.md). No es una funcion ya cargada en placa.
- [ ] Cargar con autorizacion y aceptar fisicamente la ficha antes de grabar
  su version final. Un render C++ no sustituye esa toma.
- [ ] Resolver el reporte de Mochila con un caso reproducible en placa.
- [ ] Reconciliar diferencias de catalogo/firmware y nombres ES/EN antes
  de escribir umbrales o capacidades en locucion.
- [ ] Si se incluye contenido descargable, validar mismo firmware con dos
  paquetes, nacimiento de otra mascota y capacidad/recuperacion documentadas;
  no usar un cambio de assets recompilado para aparentar plug and play.
- [ ] Revisar herramientas de desarrollo visibles, especialmente EVOLVE;
  cualquier ocultacion/eliminacion necesita su propia decision y pruebas.
- [ ] Grabar las nueve opciones y subopciones con texto legible y botones
  reales; revisar que el montaje no sugiera funciones o tiempos inexistentes.
- [ ] Completar guion, locucion, edicion, permisos de musica/arte y revision
  de nombres/marcas antes de distribucion comercial.
- [ ] Aprobar manual y video contra el mismo commit/version, dejando
  propuestas futuras fuera de las afirmaciones de disponibilidad.

## Actualizacion Continua

Todo cambio de opcion actualiza guia, contratos y esta matriz. Si cambia
la version de lanzamiento, revisar que tomas quedan invalidas y regrabar
las afectadas. No marcar una toma completada por tener un preview o un log USB.
