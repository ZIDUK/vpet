# Combate de practica: plan de implementacion

**Objetivo:** Firemon contra un rival de practica, con golpe, llama y guardia,
HP/MP separados de crianza, orden del jugador y decision explicable del pet.
**Arquitectura:** motor determinista portable Python/C++, progreso independiente
del encuentro, UI de dos botones en el simulador. Se conserva combate legado
para las demas especies. No hay cargas a la board en este trabajo.
**Stack:** Python/Pillow/pygame; C++ portable/PlatformIO. Sin TinyML inicialmente.

## Contrato v1

- IV/EV existentes alimentan HP/MP/OFF/DEF/SPD/BRN (1..99).
- HP max = 40 + HP*2; MP max = 10 + MP. Distancia fija corta (1).
- Golpe: potencia 12, coste 0, alcance 1, enfriamiento 0.
- Llama: potencia 24, coste 8, alcance 2, enfriamiento 1 ronda completa.
- Guardia: coste 0, reduce dano a la mitad esa ronda y recupera 4 MP.
- Dano = max(1, potencia + OFF/3 + dominio/20 - DEF/4), enteros.
- Velocidad define orden; empate alterna por ronda. Guardia se prepara antes
  de los ataques. Si cae un actor, no ejecuta su ataque.
- 30 rondas como limite: empate. Sin heridas, consumo de DP ni victorias
  oficiales en practica; no acelera requisitos de evolucion.
- Orden invalida se rechaza; una orden conocida sin MP o en enfriamiento puede
  sustituirse por otra valida con motivo visible.
- Personalidad deriva de DNA[3] modulo 3. Vinculo 0..100 pesa en obediencia.
- Progreso: golpe y guardia conocidos; llama tras 2 entrenamientos de tecnica.
  Dos tecnicas equipadas, nunca cero. Dominio 0..100, +1 por uso al completar
  encuentro; entrenar cuesta 4 energia y suma 5 dominio. Abandonar no premia.
- Guardado antiguo sin progreso recibe defaults; progreso persiste al evolucionar
  y se borra al iniciar nueva vida. Los previews usan un JSON separado; el
  adaptador firmware guarda progreso en claves NVS opcionales.

## Fases y archivos

1. Contrato y motor: `src/core/practice.py`,
   `firmware/t-display/lib/vpet_core/src/vpet/PracticeBattle.h`.
   Probar damage, cooldown, MP, muerte, empate y determinismo en
   `tests/test_practice.py`; comparar trazas Python/C++ con compilador nativo.
2. Tecnicas/progreso: `src/core/techniques.py`, `src/core/pet.py`.
   Serializar progreso versionado y sanitizar saves; preservar IV/EV.
3. Encuentro: integrar ronda y resultado unico en `scripts/practice_session.py`.
   No invocar `finish_battle` ni contabilizar resultados de practica como oficiales.
4. UI: `scripts/practice_renderer.py`, `scripts/sim.py`. Espadas abre la batalla
   directamente; Pesa abre entrenamiento/tecnicas. NEXT selecciona, ACTION
   confirma; resultado requiere
   confirmacion. Pausar crianza/evolucion durante sesion. Capturas a 240x135.
5. Autonomia: puntuar acciones con personalidad, vinculo, HP, MP, cooldown;
   mostrar motivo de sustitucion. Casos repetibles con distinta personalidad.
6. Balance/firmware: compilar motor en firmware y ejecutar encuentros por lotes.
   Adaptar UI y persistencia NVS despues de revisar el prototipo; medir BLE/heap
   en hardware solo cuando el usuario solicite despliegue.

## Verificacion

```sh
.venv-platformio/bin/python -m pytest tests/test_practice.py -q
.venv-platformio/bin/python -m pytest -q
.venv-platformio/bin/pio run -d firmware/t-display
SDL_VIDEODRIVER=dummy .venv-platformio/bin/python scripts/sim.py --profile tdisplay --build-dir build-tdisplay --practice --max-frames 60
```

## Seguimiento

- [x] Fases 1-3: contrato, progreso y motor local.
- [x] Fases 4-5: UI y autonomia local.
- [x] Fase 6 parcial: 24 encuentros deterministas comparados Python/C++ y compilacion.
- [ ] Fase 6: ajuste de balance con pruebas de juego.
- [x] Fase 6: UI/persistencia firmware conectada y compilada; 119 pruebas nativas.
- [ ] Fase 6: BLE/heap y aceptacion fisica tras autorizacion.

Las etapas nuevas, rival definitivo, aprendizaje por observacion y TinyML quedan
fuera de v1. El rival usa el sprite Firemon espejado y se identifica PRACTICA.

## Estado de la entrega local

El motor C++ esta conectado a App/Panels y NVS mediante PracticeSession y
PracticeProgress. La practica pausa el tick de cria durante la sesion.
No se ha desplegado firmware. Las cifras de RAM del compilador no validan el
heap con BLE activo. El alcance es metadata: la arena v1 mantiene distancia 1.
Los encuentros son por rondas a demanda, sin movimiento tactico ni TinyML.
En el simulador se muestran las animaciones existentes de golpe/llama y `block`
para guardia. El renderer firmware conserva la vista anterior.

El aprendizaje por etapas posteriores a Firemon y los efectos de estado quedan
pendientes de diseno. El progreso se persiste en JSON y en claves NVS tech*;
los IV/EV existentes se conservan, no se vuelven a sortear durante combate.

Para revisar cuatro pantallas reproducibles sin tocar partidas:
`.venv-platformio/bin/python scripts/preview_practice.py`.

## Revision UX del 2026-10-06 (simulador)

- [x] Iconos junto a vida, MP, atributos, vinculo y datos de tecnicas.
- [x] La pesa abre seis atributos y una entrada a aprendizaje/dominio de tecnicas.
- [x] Espadas abre directamente la batalla con las tecnicas equipadas. No hay
  menu de preparacion. Consultar/equipar queda en Pesa > Tecnicas; retirarse o
  confirmar el resultado devuelve a Home con las espadas seleccionadas.
- [x] Entrenamiento por atributo: 8 ENE, 6 EV, tope 252; IV intactos. HP maximo
  sube 2 y los otros valores 1 por sesion completa. Si se alcanza el tope, la
  ganancia se limita. No cura HP ni aumenta ENE de crianza.
- [x] Cada sesion suma al contador, aumenta esfuerzo 8 y animo 3 (maximo 100),
  y reduce peso 1 (minimo 0). Estas sesiones no desbloquean Llama: sus lecciones
  separadas cuestan 4 ENE cada una y se abren en Pesa > Tecnicas.
- [x] `make sim-training` y previews reproducibles de entrenamiento y bloqueo.
- [ ] Portar reglas de entrenamiento y nuevos layouts/iconos a C++; comparar
  trazas antes de afirmar paridad. No se ha desplegado a hardware.
- [ ] Validar balance, feedback de impacto y nuevos sprites de victoria/derrota.

Los sprites `hit`, `hurt` y `dodge` ya existen en los assets. El siguiente paso
visual recomendado es recibir impacto; evasion necesita primero reglas reales.
