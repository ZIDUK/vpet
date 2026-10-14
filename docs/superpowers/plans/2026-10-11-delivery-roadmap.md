# Plan de cierre y siguientes entregas

Actualizado: 2026-10-11. Este es el indice vigente; los planes del 5 y 7 de
octubre conservan el historial, no una lista actualizada de entregas pendientes.
Alcance de esta revision: documentacion. No se cambia codigo ni se flashea.

## Entregado con evidencia

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

- [ ] Comparar `scripts/practice_renderer.py` con la rama Arena de
  `firmware/t-display/src/Panels.cpp` para los estados esperando, ronda,
  victoria, derrota y empate, con la misma partida y reloj.
- [ ] Llevar feedback de orden/accion/motivo y dano bidireccional al firmware;
  igualar la ventana de impacto, actualmente 1200 ms en sim y 1500 ms en placa.
- [ ] Incluir Guardia y frames hit/hurt derivados del resultado real; no
  insinuar esquiva sin que exista una regla de evasion.
- [ ] Ampliar harness nativo y comparaciones de imagen de Arena en ES/EN,
  sin alterar formulas, progreso ni enums persistidos.
- [ ] Compilar, desplegar con autorizacion y repetir combate con BLE activo;
  medir heap minimo, estabilidad y restauracion NVS.

Salida: paridad demostrada de Arena, no solo del motor numerico.

## Despues de P1: elemento de la tecnica

Estado: regla cerrada el 2026-10-14 en
[estándar de técnicas](../specs/2026-10-14-technique-standard.md).
No implementada. No entra dentro de los pendientes de arriba: ese
bloque iguala el combate actual y no cambia la formula.

- [ ] Implementar el elemento de Cyber Sleuth en el mismo cambio para el
  simulador y para el firmware. Misma cuenta en Python y en C++:
  si el elemento de la tecnica le gana al de quien recibe, dano por 3/2;
  si no, el multiplicador queda en 1. Guardia parte despues, minimo 1.
- [ ] Firemon es `fire`. Golpe es `neutral`. Guardia no tiene elemento.
  Llama es `fire`.
- [ ] Probar los dos lados con la misma partida: agua contra Firemon suma
  la mitad, Llama contra planta suma la mitad, Llama contra agua no
  resta, neutral no dispara el elemento.
- [ ] No implementar Vaccine, Data ni Virus en este bloque.

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

Actualizacion: 2026-10-14. Python pasa 554 pruebas; el core C++ de nutricion y
persistencia pasa chequeo sintactico. El runner PlatformIO no inicia por
permisos de `~/.platformio`, y la placa aun no se valida con el build final.
Plan y pendientes en
[alimentacion, peso, combate y evolucion](2026-10-14-feeding-weight-combat-evolution.md).

- [ ] Validar el balance propuesto: comida ilimitada sin EV, ciclo metabolico,
  peso saludable por etapa y modificadores acotados de combate.
- [ ] Implementar reglas Python/C++, migracion compatible y consumo recuperable.
- [ ] Integrar Alimentar con exactamente carne/proteina ilimitadas, mochila,
  stats efectivos y requisito de evolucion. Alimentar no descuenta inventario.
- [ ] Definir en trabajo separado filete/champinon como mejoras de stats de
  mochila: objetivo, magnitud, duracion, topes y origen. No entran en Alimentar.
- [ ] Verificar paridad, guardado, animaciones por especie y comportamiento fisico.

El plan contiene tareas, archivos, contratos y criterios de terminado. Las
cifras son propuestas para medir, no un balance ya validado. Los efectos de
los objetos actuales siguen documentados como implementados hasta completar
la migracion; esta entrada no cambia el estado de P0/P1.

## P2: exploracion y recompensas

Estado: en diseño (2026-10-11). No hay funcionalidad implementada.
Los requerimientos vivos están en
[exploración](../specs/2026-10-11-exploration-design.md).
El inventario actual, sus efectos y su adquisicion estan en
[catalogo de objetos](../../items-and-rewards.md); el botin de exploracion
sigue siendo propuesta.
Ya quedó el icono nuevo, la salida larga, el jugador de semana corta
con combate el sábado, el piso **C**, el coste **A**, el retorno
**B**, la etapa mínima, los relojes, el puesto del icono y las
cantidades: Jornada +2 EV (tope 8/semana), Noche +2 de dominio
(tope 4/semana) o el aprendizaje de Llama. El 2026-10-14 quedaron el
Patio (+25 o +10 ENE, sin objeto), la Guía de la Jornada (+1 EV en la
próxima sesión, una sola) y la especie siguiente de elemento planta.
Siguen abiertos el formato en bytes del guardado, el nombre y el poder
de la técnica de planta, y filete/champiñón. No cambiar economía ni
guardado hasta implementar ese formato.

- [ ] Definir entrada del menu superior, destinos, duracion, coste, requisitos,
  retorno anticipado, actividad offline y comportamiento ante reinicio.
- [ ] Presentar rutas con propositos distintos (materiales, cuidado, aprendizaje)
  y riesgos/recompensas comprensibles; valores concretos requieren aprobacion.
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

Salida de esta fase: propuesta aprobada y catalogo versionado. Exploracion no
debe desplazar el cierre de errores/paridad de la placa.

## P2: entrega versionada

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
