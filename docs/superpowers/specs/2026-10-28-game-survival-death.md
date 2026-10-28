# SPEC-GAME-SURVIVAL-001: Supervivencia Y Muerte Por Descuido

## Estado Y Aprobacion

Estado: scope-approved, 2026-10-28, por solicitud explicita del usuario de
implementar hambre, cansancio y lesiones. Piloto: gracia de 12 horas de cuidado
activo continuo en hambre=0 o energia=0; rescate al subir el stat por encima de
cero; sueño, pausa/frio, huevo y exploracion suspenden los relojes. La regla
existente por lesiones (15 lesiones o 6 horas continuas herido) no cambia.

## Problema

La mascota puede entrar en hambre o energia cero y emitir llamadas de cuidado,
pero esos estados no causan muerte por si solos. Las lesiones ya tienen una
regla de muerte, aunque el jugador necesita entender y recuperar esos estados.
Sin reglas explicitas y durables, hambre, agotamiento y heridas pueden sentirse
inconsistentes o letales sin aviso suficiente.

## Objetivo

Especificar una supervivencia gradual, legible y recuperable antes del estado
terminal: hambre prolongada, agotamiento prolongado y lesion grave no atendida
pueden causar muerte solo despues de una ventana de gracia aprobada. La UI debe
avisar y ofrecer acciones de recuperacion; los plazos deben sobrevivir reinicios
sin doble conteo.

## Alcance

Reglas portables de dominio Python/C++17, llamadas de cuidado, descanso,
recuperacion de lesiones, persistencia del estado y presentacion del estado
critico/muerte en las superficies existentes del juego.

## Exclusiones

No cambia breeding, ADN, reglas de combate, balance de stats ni comportamiento
de huevos. No cambia enum numerico ni permite revivir. El plazo de 12 horas es
un valor piloto conservador, configurable en el core, pendiente de balance de
jugabilidad tras validar el uso real.

## Requisitos

### REQ-GAME-SURVIVAL-001

El dominio debe dar 12 horas de cuidado activo continuo en hambre=0 o energia=0;
alimentar o restaurar energia por encima de cero reinicia su reloj. Sueño,
Pause Pet/frio y exploracion suspenden los relojes; el huevo nunca los acumula.
Los temporizadores persisten con defaults cero para partidas antiguas y no
cuentan tiempo offline. Llegar a cero no mata de inmediato. Se conserva la muerte
actual por 15 lesiones acumuladas o 6 horas continuas herido, curable con
Medkit antes del limite.

## Criterios De Aceptacion

### AC-GAME-SURVIVAL-001

Con stats en cero, el primer tick no mata; 12h menos 1ms no mata y el ultimo ms
si; alimentar/restaurar energia a 1 resetea el timer correspondiente. Sleeping,
cold/pause, away y egg no avanzan los relojes. Guardar/cargar mantiene los ms
restantes, y un save viejo sin claves nuevas empieza en cero. La muerte por
lesion conserva sus limites previos. Tests Python y C++ deben probar estos casos.

## Contratos Y Compatibilidad

El firmware usa `hunCritMs` y `eneCritMs` saturados a 43,200,000; la ausencia de
las claves en saves actuales/viejos significa cero. No se cambia schema ni se
reinterpreta una clave. `tick` recibe elapsed de cuidado activo; App no lo llama
durante away/frio y el core lo suspende durante sueño/huevo. Death se guarda por
el campo existente. La lesion mantiene su contador previo aun durante sueño;
sólo los temporizadores nuevos de hambre/energia se pausan al dormir. Cualquier
aviso UI nuevo requiere diseno propio, no se inventa aqui.

## Errores Y Recuperacion

Ante save pendiente/fallido, bloquear nuevas mutaciones que pudieran duplicar
una muerte o perder una recuperacion, pero ofrecer salida/reintento segun el
contrato global de guardado. Valores corruptos negativos normalizan a cero y
valores superiores al limite saturan al limite; no se suman tiempos offline.
Los huevos no son sujetos a estas reglas.

## Riesgos

La muerte permanente puede destruir progreso y reducir confianza si la UI no
avisa con tiempo. El estado de lesion actual ya acumula seis horas y 15 lesiones,
por lo que cambiarlo requiere compatibilidad y migracion cuidadosas.

## Verificacion

El plan separado registra pruebas de limites, recuperacion, reinicio, pausa,
sueño, huevo, overflow y persistencia Python/C++. La implementacion y compilacion
no sustituyen la aceptacion fisica ni autorizan por si solas el flash.

## Preguntas Pendientes

- La muerte es terminal en la vida activa actual; la gestion de una vida muerta
  en Coleccion y cualquier resurreccion quedan fuera de esta implementacion.
- El umbral de 12h es piloto inicial; ajustar balance despues de pruebas con
  jugadores, sin cambiar el contrato de persistencia.
