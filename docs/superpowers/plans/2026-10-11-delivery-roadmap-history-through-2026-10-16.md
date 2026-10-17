# Historico del roadmap anterior al cierre de sprites de 2026-10-16

Este documento conserva el texto anterior, con sus cifras y pendientes
historicos. NO es el roadmap vigente. Consultar
[roadmap actual](2026-10-11-delivery-roadmap.md).

Actualizado: 2026-10-11. Este es el indice vigente; los planes del 5 y 7 de
octubre conservan el historial, no una lista actualizada de entregas pendientes.
Alcance de esta revision: documentacion. No se cambia codigo ni se flashea.

## Entregado con evidencia

- [x] Catalogo adoptado de 40 consumibles sin evolucion/mapas/pesca/venta:
  JSON de desarrollo, header C++, fichas, sprites y funciones de efecto.
- [x] Conectar objetos adoptados a stock persistente, Mochila y selector de
  objetos de Arena en ambos runtimes; implementar adquisicion sin duplicados.
- [x] Conectar Manual a la transaccion de entrenamiento sin acumular Guia.
- [ ] Validar consumibles y journal fisicamente en placa tras autorizacion.

- [x] Status, entrenamiento temporizado y Tecnicas integrados en sim/firmware.
- [x] Sesion de atributo: START, 10 segundos, aplicacion/guardado unico,
  cancelacion sin cobro y reintento transaccional.
- [x] Regreso por inactividad implementado y BACK prioritario en la entrada.
- [x] Firmware y recursos cargados: `Deploy OK`, heap libre 109620 bytes,
  minimo 55836, filesystem 5722112/12451840, manifest 1.
- [x] Ultima suite completa: 511 pruebas Python. Comparacion ampliada posterior:
  466 frames Training/Tecnicas ES/EN. Compilacion T-Display correcta.

Estas cifras corresponden a ejecuciones anteriores de esta conversacion;
no se volvieron a ejecutar durante la actualizacion documental.

## P0: cerrar aceptacion de la placa

- [ ] Probar 20 pulsaciones cortas de NEXT en Status: un cambio por pulsacion.
- [ ] Mantener NEXT durante 2 segundos: volver a Home, sin quedar recorriendo
  paginas; comprobar que soltar el boton no produce una accion residual.
- [ ] Revisar las cuatro paginas en ES/EN: datos legibles, DNA completo,
  animaciones de pet/helice y ausencia de restos del frame anterior.
- [ ] Probar inactividad: reiniciar cuenta con cada boton; volver a Home tras
  10 segundos en menus/resultados. No interrumpir entrenamiento ni combate.
- [ ] Completar, cancelar y repetir entrenamiento; comprobar coste y recompensa
  una sola vez y persistencia tras reiniciar. Verificar tecnicas equipadas tras
  reinicio sin perder el resto de la partida.
- [ ] Guardar fotos/video, identificacion de build y log serial de estas pruebas.
  Si hay fallos, reproducir y crear regresion antes de dar el bloque por cerrado.

Responsable de correcciones/verificacion: Codex. La inspeccion fisica requiere
observacion real o evidencia del usuario; el arranque serial no basta.

## P1: paridad del combate

Auditoria de firmware del 2026-10-15:
[informe y reproducciones](../reviews/2026-10-15-board-audit.md).
Los P1 de intercambio de respaldo/snapshots parciales y el P2 del borrado vacio
tienen correcciones con pruebas de host. La confirmacion ambigua de commit
usa estado Pending y barrera sync. Falta validacion fisica de cortes de energia.
La optimizacion de placa exige mediciones reales de latencia, heap y BLE;
compilar y pasar pruebas de host no la demuestra.

- [ ] Comparar `scripts/practice_renderer.py` con la rama Arena de
  `firmware/t-display/src/Panels.cpp` para los estados esperando, ronda,
  victoria, derrota y empate, con la misma partida y reloj.
- [ ] Llevar feedback de orden/accion/motivo y dano bidireccional al firmware;
  verificarlo visualmente con la misma partida y reloj. La ventana de impacto
  ya es 1200 ms en sim y placa; la orden historica se conserva al mover cursor.
- [ ] Incluir Guardia y frames hit/hurt derivados del resultado real; no
  insinuar esquiva sin que exista una regla de evasion.
- [ ] Ampliar harness nativo y comparaciones de imagen de Arena en ES/EN,
  sin alterar formulas, progreso ni enums persistidos.
- [ ] Compilar, desplegar con autorizacion y repetir combate con BLE activo;
  medir heap minimo, estabilidad y restauracion NVS.

Salida: paridad demostrada de Arena, no solo del motor numerico.

Revision 2026-10-15: sigue pendiente el harness de imagen para Arena de
`Panels.cpp` en ES/EN. El harness actual compara Training/Tecnicas, no Arena.
Las reacciones de resultado (happy/sad frente a idle en firmware) tampoco
son equivalentes; no marcar P1 cerrado por las pruebas numericas.

## Despues de P1: elemento de la tecnica

Estado: regla cerrada el 2026-10-14 en
[estándar de técnicas](../specs/2026-10-14-technique-standard.md).
Implementada en ambos motores; revisada el 2026-10-15. La evidencia numerica
no cierra por si sola la paridad visual ni la validacion fisica de P1.

- [x] Implementar el elemento de Cyber Sleuth en el mismo cambio para el
  simulador y para el firmware. Misma cuenta en Python y en C++:
  si el elemento de la tecnica le gana al de quien recibe, dano por 3/2;
  si no, el multiplicador queda en 1. Guardia parte despues, minimo 1.
- [x] Firemon es `fire`. Golpe es `neutral`. Guardia no tiene elemento.
  Llama es `fire`.
- [x] Probar los dos lados con la misma partida: agua contra Firemon suma
  la mitad, Llama contra planta suma la mitad, Llama contra agua no
  resta, neutral no dispara el elemento.
- [x] No implementar Vaccine, Data ni Virus en este bloque.

Evidencia: `tests/test_practice.py` y `tests/practice_elements.cpp` comparan
810 combinaciones de elemento atacante/receptor, dano base y Guardia entre
Python y C++; incluyen 27 -> 40 con ventaja, 27 -> 27 sin ventaja y
3 -> 4 -> 2 con Guardia. Las sesiones asignan fuego a las tres etapas de
Firemon y al rival Firemon. No se agregan tecnicas de agua ni una especie
planta: los cruces se ejercitan con combatientes de prueba.

Salida: placa y simulador aplican el mismo multiplicador. Un solo lado
no cuenta como hecho.

## P1: skills y pipeline reproducible para MiniMax

Estado: propuestas, NO creadas ni instaladas.

- [ ] Inspeccionar como MiniMax descubre skills y que herramientas de imagen
  tiene disponibles; no asumir que lee las skills globales de Codex.
- [ ] Crear `vpet-ui-assets`: consultar assets existentes, contrato 240x135,
  variantes ES/EN, estados/extremos, empaquetado y comparacion Python/C++.
- [ ] Crear `vpet-pixel-art`: paleta, transparencia, dimensiones/atlas, pivotes
  estables, fotogramas, nombres y conversion automatica; separar arte de
  referencia de un sprite efectivamente importable.
- [ ] Ubicarlas en una ruta versionable que MiniMax realmente cargue y
  documentar dependencias. Probar con un asset pequeno de extremo a extremo.
- [ ] Mantener decisiones visuales junto a los renderers/tests bajo Codex;
  no delegar Training a MiniMax, conforme a la instruccion del usuario.

Salida: skills leidas por MiniMax y una entrega de ejemplo validada, no solo
archivos SKILL.md presentes. No se ha autorizado una delegacion nueva.

## Alimentacion y peso: implementacion integrada; validacion parcial

Actualizacion: 2026-10-14. Python pasa 555 pruebas, incluida navegacion real
automatizada del simulador para Status, Alimentar, Mochila y persistencia de
items; tambien se verificaron previews de Training/Battle. El core C++ de
nutricion y persistencia pasa chequeo sintactico. El runner PlatformIO no inicia
por permisos de `~/.platformio`, y la placa aun no se valida con el build final.
Plan y pendientes en
[alimentacion, peso, combate y evolucion](2026-10-14-feeding-weight-combat-evolution.md).

- [ ] Cerrar aceptacion de balance: comida ilimitada sin EV, ciclo metabolico,
  peso saludable por etapa y modificadores acotados de combate.
- [x] Implementar reglas Python/C++, migracion compatible y consumo recuperable.
- [x] Integrar Alimentar con exactamente carne/proteina ilimitadas, mochila,
  stats efectivos y requisito de evolucion. Alimentar no descuenta inventario.
- [ ] Definir en trabajo separado filete/champinon como mejoras de stats de
  mochila: objetivo, magnitud, duracion, topes y origen. No entran en Alimentar.
- [x] Verificar rutas de simulador, persistencia en mochila, paridad y
  animaciones renderizadas; la aceptacion fisica sigue pendiente.

El plan contiene tareas, archivos, contratos y criterios de terminado. Las
cifras son propuestas para medir, no un balance ya validado. Los efectos de
los objetos actuales siguen documentados como implementados hasta completar
la migracion; esta entrada no cambia el estado de P0/P1.

## P2: exploracion y recompensas

Actualizacion 2026-10-16: port a firmware autorizado e implementado. Incluye
barra de nueve iconos, motor portable, tablas ES/EN, Guia, recibo unico y
snapshot NVS v2 compatible con v1. Ver [plan del port](2026-10-16-exploration-board.md)
y [contrato de placa](../../exploration.md). Sin RTC respaldado, perder el
calendario requiere ajuste manual; no se certifica progreso sin alimentacion.
El texto inferior conserva el corte del simulador. La aceptacion fisica visual
continua separada de build, pruebas de host y verificacion serial.

Estado: ciclo completo implementado en Make Sim (2026-10-14), por autorizacion
del usuario. La placa sigue pendiente. El contrato de guardado JSON, el flujo
y las decisiones de balance estan en [Exploracion en Make Sim](../../exploration.md).
La suite completa de esta entrega pasa 634 pruebas Python, incluido el flujo
de teclas pygame Jornada -> reclamar -> Guia -> entrenamiento con +7 EV.
Los requerimientos vivos están en
[exploración](../specs/2026-10-11-exploration-design.md).
El inventario actual, sus efectos y su adquisicion estan en
[catalogo de objetos](../../items-and-rewards.md); el botin de exploracion
sigue pendiente en firmware; Patio/Jornada/Noche y Guia ya funcionan en sim.
Ya quedó el icono nuevo, la salida larga, el jugador de semana corta
con combate el sábado, el piso **C**, el coste **A**, el retorno
**B**, la etapa mínima, los relojes, el puesto del icono y las
cantidades: Jornada +2 EV (tope 8/semana), Noche +2 de dominio
(tope 4/semana) o el aprendizaje de Llama. El 2026-10-14 quedaron el
Patio (+25 o +10 ENE, sin objeto), la Guía de la Jornada (+1 EV en la
próxima sesión, una sola) y la especie siguiente de elemento planta.
Siguen abiertos el formato en bytes del guardado, el nombre y el poder
de la técnica de planta, y filete/champiñón. El formato NVS se implementara
al portar a placa; el simulador usa guardado JSON atomico y versionado.

- [x] Implementar en sim entrada del menu superior, destinos, duracion, coste, requisitos,
  retorno anticipado, actividad offline y comportamiento ante reinicio.
- [x] Presentar rutas de energia, EV y tecnica, con confirmacion, tiempo restante,
  retorno anticipado, preview de recompensa y recibo guardado, en ES/EN.
- [ ] Para el botin futuro, llenar la ficha ya documentada en
  [estándar de catálogo](../specs/2026-10-14-item-catalog-standard.md):
  ID estable, categoria, rareza, icono, ES/EN, stack maximo, efecto tipado,
  objetivo, magnitud, duracion, limites y origen. El esquema está escrito;
  falta el objeto concreto de cada ruta.
- [ ] Proponer familias: alimento, recuperacion, material, manual de tecnica y
  cosmetico. Distinguir recuperacion temporal de EV permanente; no cambiar IV
  ni regalar stats ilimitados. Identificar usos reales antes de crear materiales.
- [ ] Definir inventario lleno, recompensa duplicada, caps, probabilidades,
  tablas por destino y guardado atomico de salida/regreso/reclamacion unica.
- [ ] Aprobar alcance y balance; despues escribir plan implementable del motor
  portable, persistencia compatible y pruebas deterministas Python/C++.

Entregado en sim: topes semanales, reclamacion unica, migracion de partidas,
fallo/reintento atomico y Guia consumida con el entrenamiento completado.
La mochila actual no tiene capacidad general: se conserva el limite de una
Guia sin inventar una bolsa de tres tipos (tres es la ventana visible).

Pendientes reales de la fase: motor C++, reloj de placa, formato/transacciones
NVS y pruebas de paridad y hardware. Filete, champinon, disco de pelea, especie
planta y su tecnica siguen en trabajo separado. Exploracion no cierra P0/P1.

## P2: entrega versionada

Actualizacion de catalogo (2026-10-14): siete objetos oficiales con los doce
campos, descripciones ES/EN y sprites PNG. La fuente `core.item_catalog`
genera documentacion y metadata C++; el Amuleto conserva `ring`/`ItemRing`.
Los objetos de evolucion estan excluidos. Filete, champinon y discos no se
agregan al inventario activo hasta cerrar sus propias reglas.

Validacion del catalogo: 642 pruebas Python, 161 casos nativos C++, compilacion
T-Display correcta, verificacion de artefactos generados y 14 pantallas ES/EN
inspeccionadas. El ultimo ajuste de etiquetas paso 68 regresiones enfocadas.
No se flasheo la placa en esta entrega.

- [ ] Revisar el diff y archivos nuevos, separando trabajo previo del usuario.
- [ ] Seleccionar codigo, tests, assets fuente y documentos necesarios; no
  incluir backups de placa, partidas ni secretos. Nunca borrar board-backups.
- [ ] Preparar commits coherentes y publicar cuando se acuerde la entrega.
  HEAD comprobado: `de63fd0`; cambios actuales aun sin commit.

## Backlog previo a revalidar

- Intro y tiempo de eclosion: confirmar divergencias historicas antes de corregir.
- Paridad de descanso/guardado y resto de menus fuera de Training/Tecnicas.
- Ciclo BLE telefono: ADVERTISING -> CONNECTED -> ADVERTISING con evidencia.
- Nuevas especies/evoluciones, paquetes `.vpetpack`, catalogo y app movil.
  El camino de negocio posterior a la placa (casa en el telefono, recibo,
  modulo 3D y sabado patrocinado) esta en
  [plan del negocio](2026-10-13-mall-business-plan.md). No adelanta P0 ni P1.
- Provisionamiento WiFi/HTTPS y seguridad de produccion requieren alcance y
  autorizacion separados. No habilitar WiFi como parte de estos pendientes.

## Comandos de validacion al cambiar codigo

```sh
.venv-platformio/bin/python -m pytest -q
.venv-platformio/bin/pio test -d firmware/t-display -e native
make build-tdisplay
.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay
git diff --check
```

Usar pruebas nativas cuando cambie el core C++; regenerar assets, nunca editar
build-tdisplay o LittleFS manualmente. El despliegue es una etapa separada de
la aceptacion fisica y no convierte estos checks en prueba visual de la placa.
