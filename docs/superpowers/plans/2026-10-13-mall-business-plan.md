# Plan del negocio después de la placa

Fecha: 2026-10-13. Esto no autoriza firmware, WiFi, app ni un evento.
Empieza cuando la placa cierre el corte de abajo. Hasta entonces el
índice de desarrollo sigue siendo
[el roadmap del 11 de octubre](2026-10-11-delivery-roadmap.md).

## El negocio

La persona compra el aparato. Entre semana la mascota vive ahí: se
cuida, entrena y explora sola. El teléfono es la casa: la cuenta, la
colección y las descargas. El sábado la marca paga un evento en el
centro comercial. La gente lleva la placa, pelea en un módulo con el
pet en 3D y se lleva un premio. Comprar en la tienda patrocinadora
también deja un ítem o un pet.

El aparato se vende una vez. El sábado se cobra a la marca, no al
jugador. El centro comercial pone el tráfico; la marca pone el premio
y el nombre del evento.

## Dónde estamos

Hoy el producto es una placa de 240×135, dos botones, una línea de
mascota y reglas locales.

| Ya existe | Todavía no existe |
|---|---|
| Status, entrenamiento de 10 s, técnicas, combate de práctica | Aceptación física cerrada (P0) |
| Bluetooth que el teléfono puede ver (`ADVERTISING` / `CONNECTED`) | Pasar una mascota, un guardado o un premio por Bluetooth |
| WiFi apagado a propósito | App, cuenta, catálogo descargable |
| Inventario de seis objetos de kit inicial, sin reposición | Códigos de tienda, tienda, botín que vuelva a entrar |
| Exploración diseñada, no programada | El ciclo de semana que prepara el sábado |
| Paquetes `.vpetpack` descritos, no instalables | Instalar un pet nuevo sin recompilar y flashear |
| Un modelo 3D empezado en Meshy, fuera del producto | Módulo, pelea 3D, recibo, contrato con una marca |

El teléfono ya detecta la placa. No puede leer la partida ni escribir
un premio. Los sprites no viajan por Bluetooth: el documento de
paquetes reserva BLE para comandos cortos. El arte pesado entra por
USB o por un paquete ya instalado.

## Corte de la placa, antes de este plan

El negocio no empieza con el módulo. Empieza cuando la partida de la
placa es una mascota que se puede copiar sin reinterpretarla.

1. Cerrar P0: botones, las cuatro páginas de Status, entrenamiento que
   cobra una vez y sobrevive a un reinicio.
2. Cerrar P1: el combate de la placa y el del simulador usan la misma
   regla y la misma ventana de golpe. El módulo del sábado tiene que
   correr esa regla. Si la placa y la laptop pelean distinto, el
   premio no es legal.
3. Programar la exploración ya diseñada, con los números aprobados.
   Sin ese ciclo, el sábado no tiene una semana detrás.
4. Congelar un retrato de la mascota, versionado: especie, etapa,
   stats, técnicas equipadas, inventario, versión de reglas. Ese
   retrato es lo que el teléfono y el módulo leen. Cambiarlo después
   rompe los premios ya entregados.
5. Catálogo de objetos genérico, con id estable. El anillo visible
   como Amuleto sigue siendo decisión de diseño; el id de guardado
   no cambia.
6. Especies propias. Una marca no patrocina un evento si la mascota
   es el personaje de otro juego.

Salida de este corte: una placa que una persona puede usar toda la
semana y llevar el sábado, aunque el sábado todavía sea en la mesa de
casa.

## Lo que la idea todavía no aguanta

**El premio no puede escribirse dos veces por separado.** Si la laptop
anota el ítem en la app y otra vez en la placa, se duplica. Si solo lo
anota en un lado, quien se va del centro comercial sin abrir el
teléfono sale sin premio, o abre el teléfono y pisa la partida de la
placa. El premio es un recibo con id. La placa lo aplica al terminar
la pelea. El teléfono aplica el mismo id cuando sincroniza. La segunda
vez no suma.

**Bluetooth en un centro comercial es un mal cable.** Hay decenas de
radios en el mismo canal. El evento no puede depender de que la placa
se empareje con una laptop en ese piso. En la casa, Bluetooth sirve.
En el módulo, el pase de pelea sale del teléfono (un código de un solo
uso, válido unos minutos) y el premio vuelve a la placa por un dock
USB en el mismo módulo. La placa sigue siendo lo que la persona
enseña y lo que se lleva puesto.

**La laptop no es el dueño de la mascota.** Renderiza el modelo 3D
que corresponde al id de especie y corre el combate. El modelo de
Meshy vive en esa máquina. La placa sigue en píxeles.

**Un solo pet no llena un evento.** Firemon demuestra el aparato. El
primer sábado patrocinado necesita un roster, aunque sea corto, y un
modelo 3D por especie. El pet de diciembre es la prueba de que una
especie nueva entra como ficha (id, nombres, sprites, evolución,
técnicas, objetos exclusivos) y no como un firmware nuevo.

**El guardado de hoy se puede copiar.** Hay respaldos de placa. Para
un hobby en casa da igual. Para un premio de marca, el módulo tiene
que firmar el recibo y la placa solo acepta un recibo de ese evento,
una vez, para esa partida. Copiar el archivo a otra placa no debe
cobrar el mismo premio otra vez.

**Quien opera el sábado es parte del producto.** Hace falta guion de
fila, qué hacer si el dock falla, cuántas peleas caben por hora y
quién entrega el premio si el sistema se cae. Sin eso, el firmware
correcto igual produce un evento malo.

**El código de la tienda es el mismo recibo, con otro origen.** Un QR
impreso en un ticket se fotografía y se reutiliza. El código es de un
solo uso, atado al ticket, y cae en la cuenta del teléfono. De ahí el
jugador lo manda a la placa. El cajero no programa el aparato.

**Los premios ligados a una compra tienen reglas locales.** Antes de
que una marca pague, hace falta la revisión legal del país del centro
comercial: promoción, menores, datos de la cuenta y qué se considera
un sorteo.

## Papeles que no se mezclan

| Pieza | Dueño de | No hace |
|---|---|---|
| Placa | La mascota que se entrena y viaja | Render 3D, cuenta, catálogo web |
| Teléfono | Cuenta, colección, descarga, pase del sábado | La pelea oficial ni el archivo 3D |
| Módulo | Pantalla, combate con las reglas de la placa, recibo firmado | Guardar la partida como si fuera la casa |
| Tienda | Un código de un solo uso | Escribir en la placa |
| Marca | Paga el sábado y define el premio de ese día | Tocar stats, IV o el tope de progreso |

## Fases, en orden

Cada fase tiene una salida comprobable. No se abre la siguiente para
tapar un hueco de la anterior.

### 1. Retrato portable

Contrato de la partida: ids estables, versión, tamaño máximo que quepa
en un comando corto y en un dock USB. Prueba: exportar en la placa,
importar en el simulador, obtener los mismos stats y técnicas.

Sin app y sin módulo. Si este retrato cambia cada semana, el resto del
plan se reescribe.

### 2. Casa en el teléfono

Cuenta de una persona, una colección, ver la placa que ya anuncia por
Bluetooth, traer el retrato y devolverlo. El arte pesado sigue
instalándose por USB. La app no descarga sprites por Bluetooth.

Salida: en casa, el teléfono muestra la misma mascota que la placa y
puede devolverla sin perder el progreso de la semana.

### 3. Segunda especie

Una ficha completa: id, nombres, sprites de la placa, técnicas propias,
objetos exclusivos que solo esa especie usa, y un GLB para la arena.
Los objetos genéricos siguen sirviendo a todas.

Salida: las dos especies pelean con la misma regla. Cambiar de pet no
exige un firmware distinto. Este es el ensayo del pet de diciembre.

### 4. Recibo

Un id, un origen (`evento` o `tienda`), un premio (ítem o pet), la
partida a la que pertenece y una firma. Aplicarlo dos veces no cambia
nada. Aplicarlo en la placa y luego en el teléfono deja los dos lados
iguales.

Salida: una laptop de prueba firma un recibo, la placa lo guarda, el
simulador de la cuenta lo acepta una sola vez.

### 5. Módulo de mesa

Una laptop con los GLB, la regla de combate de la placa, un dock USB y
el pase de un solo uso. Diez a veinte personas conocidas. Sin marca y
sin centro comercial.

Se mide: peleas terminadas, premios que llegaron a la placa, premios
que la cuenta no duplicó, cuántas veces el Bluetooth del lugar habría
fallado si hubiera sido el camino principal.

Salida: un sábado de mentira en una mesa, con premio real en la placa.

### 6. Una tienda, un producto

Una marca, un producto, códigos de un solo uso. El código entra en la
cuenta. El jugador manda el premio a la placa con el mismo recibo de
la fase 4.

Salida: comprar no toca la placa; el premio llega igual.

### 7. Piloto pagado, local chico

Una marca, un local, un módulo, un roster corto, un guion de fila y un
plan si el dock falla. El premio de ese día está definido por escrito
antes de abrir.

Salida: cifra de asistencia, peleas completas, códigos cobrados y
fallos de entrega. Con eso se decide si un centro comercial es
posible. Sin esa cifra, no se promete un piso.

### 8. Sábado de centro comercial

Varios módulos solo si el piloto mostró que uno solo se llena. Cada
módulo tiene sus GLB, el mismo motor y el mismo tipo de recibo. La
marca aparece en la pantalla y en el premio del día. La placa se va
con el premio puesto. La cuenta lo refleja al sincronizar.

Salida: un evento repetible el sábado siguiente sin cambiar las reglas
de la mascota.

## Fuera de este camino

- Render 3D dentro de la placa.
- WiFi en el aparato para que el módulo funcione.
- Que la laptop conserve la partida maestra.
- Mercado abierto de mascotas de terceros antes de tener un roster
  propio y un evento que ya funcionó.
- Códigos reutilizables impresos en un póster.

## Primer trabajo cuando la placa cierre

Escribir el retrato portable (fase 1) y acordar que el módulo lee el
pase del teléfono y devuelve el premio por dock USB. Las fases 2 y 4
salen de ese contrato. El modelo de Meshy entra en la fase 3, como el
archivo de la arena de esa especie, no como el guardado.
