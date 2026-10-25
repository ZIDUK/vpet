# Decisiones De Producto: Crecimiento, Coleccion Y Breeding

Revision: 2026-10-23. El usuario solicita implementar F1 y probarla.
Este documento no autoriza activar las propuestas numericas de F2/F4/F7
ni cambiar Arena en esta entrega.

Actualizacion 2026-10-24: el usuario autoriza continuar con la integracion
recomendada de F2b. Curva 200+8*IV, caps 84/168/252, tipos/boosts y rival
por rango integrados en codigo local. [Reglas actuales](growth-integration.md).
No autoriza flasheo; numeros de breeding, plazas de huevos y cadencia/pausa
de combate siguen propuestas separadas. El texto original de piloto se
conserva abajo como antecedente, no como estado vigente de implementacion.

Continuacion F2a 2026-10-24: [perfil individual](individual-profile.md)
implementado localmente en sim/ESP32, con migracion y pruebas, sin carga.
Sexo M/F equiprobable, padres desconocidos para fundadores y conservacion
al evolucionar; no habilita breeding, roster ni visibilidad nueva en Status.

## Confirmado Y Objetivo De Capacidad

- Inventario COMPARTIDO entre individuos. El stock no se copia al cambiar
  mascota, eclosionar, recibir un paquete ni criar.
- Objetivo solicitado: hasta CUATRO mascotas en el dispositivo. No hay roster
  implementado ni capacidad fisica garantizada para cuatro lineas de arte.
- Recomendacion por aprobar: cuatro plazas de individuos incluyendo huevos,
  una mascota activa y el resto aparcadas. Eclosionar cambia la fase del mismo
  registro; no ocupa otra plaza. Si se desean huevos aparte, requiere otro
  limite y presupuesto explicitos, no asumir una incubadora ilimitada.
- Actualizacion de inventario: migracion unica y transaccional, sin sumar
  copias legacy de snapshots/reserva. Definir una fuente de stock autoritativa
  antes de migrar; no elegir el mayor stock por item ni sumar partidas.

Cuatro individuos de una linea comparten los mismos recursos. Cuatro lineas
distintas requieren otros paquetes. El presupuesto de F1 separa arte, cuatro
registros provisionados, journals, staging y reserva. No son equivalentes.

## Piloto De Crecimiento Recomendado Para F2

Propuesta inicial para medir y ajustar, NO balance aprobado ni codigo activo:

El [piloto aislado F2b](growth-pilot.md) ya permite medir esta curva. Sus
resultados no la activan: registra compatibilidad matematica, costes y los
bloqueos de tipos, potenciadores y rival fijo que deben resolverse primero.

```text
IV_i = gen del stat i (0..15)
P_i = 200 + 8 * IV_i
r = rango adulto actual, comenzando en 1
R = numero de rangos adultos compatibles de la linea
CapStat_i = floor(P_i * r / R + 0.5)
CapEV = 6 * floor((252 * r / R) / 6)
BaseStat_i = floor((10 + 3 * IV_i) * (1 + 0.2 * (r - 1)) + 0.5)
Stat_i = BaseStat_i + floor((CapStat_i - BaseStat_i) * min(EV_i, CapEV) / CapEV)
```

La propuesta se calibra primero con el perfil actual de tres rangos adultos:
Firemon, Flamemon y Dragfiremon. No habilita entrenar huevo/Sparkmon.
Las identidades/nombres no entran en la formula. Otras topologias necesitan
su perfil soportado; no asumir cualquier numero de etapas arbitrario.

| IV del stat | Firemon: cap | Flamemon: cap | Dragfiremon: cap |
| --- | ---: | ---: | ---: |
| 0 | 67 | 133 | 200 |
| 8 | 88 | 176 | 264 |
| 10 | 93 | 187 | 280 |
| 15 | 107 | 213 | 320 |

CapEV seria 84/168/252. El ADN determina el potencial visible; no se castiga
dos veces al gen bajo reduciendo tambien sus oportunidades totales de EV.
Es una alternativa al candidato anterior de EV geneticos 192+4*IV, no deben
mezclarse ambas formulas sin revisar balance. 280 sigue siendo un ejemplo de
un individuo IV10, no un techo universal.

Conservar los EV legacy aunque excedan el cap de etapa y bloquear solo nuevas
ganancias mientras no quede espacio. Antes de adoptar la curva, comparar
todos los IV/EV con el estado actual, probar monotonia entre etapas, ausencia
de reduccion silenciosa, caps parciales y efectos de objetos. Probar rivales
y encuentros fuertes/debiles para medir cuanto dura entrenar/maximizar y
cuanto dura pelear. Los factores 200/8/0.2 se revisan con esos resultados.

Stats de combate ampliados requieren uint16_t y operaciones intermedias
suficientemente anchas; revisar HP/MP temporales, dano, curacion, mensajes,
snapshots y UI. Hambre/salud/energia de cuidado siguen 0..100. No ampliar
simplemente una etiqueta ni reinterpretar NVS sin migracion aprobada.

## Reglas Iniciales De Breeding Recomendadas

Todo lo numerico siguiente es candidato de F7, no implementado en F1:

1. Dos individuos adultos, de sexo compatible, con ID distinto, sanos,
   despiertos y presentes. El usuario confirma ambos padres.
2. Primera entrega solo dentro de una linea compatible cuyo arte del hijo
   ya existe. No fusionar imagenes ni crear un huevo con especie irresoluble.
3. Bloquear padres/hijos/hermanos conocidos; guardar parentesco de alcance
   definido, sin prometer detectar ancestros ilimitados.
4. Umbrales piloto de cuidado: salud >=80, hambre >=60, energia >=70 y
   animo >=60; sin lesion, muerte, viaje ni pausa de crianza.
5. Cada uno de los seis IV se toma de uno de los padres. Elegir una mascara
   que use al menos un gen de cada padre; pequena mutacion propuesta de
   1/32 por gen, -1/+1 acotado a 0..15. No copiar el ADN de un unico padre.
6. El hijo tiene ID unico y un genoma recombinado, mas temperamento/herencia
   conductual moderada aprobada. Si los padres comparten genes, algunos o
   todos los valores pueden coincidir: identidad unica no implica ADN unico.
7. No heredar EV, victorias, tecnicas dominadas ni recuerdos completos.
   El hijo aprende su propio estilo y no nace con el malestar temporal parental.
8. Los padres permanecen. Cooldown piloto: 24 horas encendido acumuladas por
   padre; cambiar fecha o reiniciar no lo evita. Sin credito de tiempo apagado
   mientras no haya reloj confiable.
9. Incubacion piloto del huevo de breeding: 30 minutos encendido en incubadora,
   distinta del huevo inicial rapido. La politica para huevos inactivos debe
   aprobarse con F4 antes de activar este contador.
10. Confirmar hijo, genoma, plazas y cooldown en una transaccion con breedingId
    y semilla persistida. Reintentar conserva el mismo huevo/genoma, nunca
    vuelve a cobrar ni genera otro hijo. Si no hay plaza, no iniciar el cruce.

## Peleas E Items: Primera Mejora Recomendada

Propuesta para Arena LOCAL, separada de F1:

- Pausar avance de combate al abrir Mochila. Guardar tiempo restante para que
  abrir/cerrar repetidamente no reinicie ni adelante rondas o efectos temporales.
- Consumir un item valido ocupa una accion del jugador, en lugar de ataque.
  El rival puede responder al resolver esa ronda; no otorgar objeto y ataque
  gratis juntos. Item sin efecto/stock o menu cancelado no consume turno/stock.
- Un objeto por accion y confirmacion persistida antes de continuar; fallos
  de guardado no aplican otra curacion, buff ni consumo al reintentar.
- Probar cadencia de 2500 ms por ronda en lugar de 1450 ms y objetivo de
  45-90 s para encuentros parejos. No garantizar ese tiempo para todos los
  enfrentamientos ni rellenarlo con esperas o HP arbitrarios. Medir tambien
  casos extremos, empates y bucles de curacion antes de fijar duracion.
- Encuentros P2P necesitan reglas de pausa/tiempo acordadas por ambos; no
  permitir que un participante pause unilateralmente al rival sin limite.

Siguiente decision: aprobar o ajustar los pilotos anteriores despues de
revisar el presupuesto de F1. El inventario compartido ya esta confirmado;
formula, plazas de huevos, numeros de breeding y cadencia son recomendaciones.
