# F1: Definiciones De Contenido Y Pruebas

**Estado:** fundamento implementado y probado localmente; sin autorizacion
nueva de carga. Roster, genetica, breeding y balance no se implementan aqui.
**Objetivo:** extraer nombres, recursos, frames y loops a una definicion
versionada sustituible, conservando comportamiento y guardado de la linea actual.
**Arquitectura:** `PetDefinition` portable y resolver por rol/accion/contexto;
JSON builtin validado genera tablas C++ y Python. Adaptadores graficos usan
la misma definicion. Un segundo contenido de prueba verifica sustitucion.

## Contrato De Esta Entrega

- Cinco roles de juego existentes, con enums numericos conservados. El rol
  no es identidad individual ni especie universal de futuros paquetes.
- Cada contexto (Home, Training, Arena, Exploracion y retrato) resuelve
  recursos y metadatos; fallback explicito, sin seleccionar otra mascota.
- Duracion visual no modifica premios, cooldowns o costes de las sesiones.
- Sin plugins ejecutables, heap por frame, nuevo framebuffer ni I/O de red.
- Definiciones alternativas se inyectan para pruebas/preparacion, no hay
  instalador de paquetes externos ni seleccion persistida aun.
- Validacion de fuentes y arte antes de generar: rutas, roles, frames,
  duraciones y limites. No aceptar un manifiesto que apunte a archivos ausentes.
- Informe de bytes de contenido compartido, segundo paquete y margen de
  staging; no inferir capacidad de la particion total ni prometer cuatro lineas.

## Tareas

- [x] Pruebas fallidas de resolucion, rechazo y generacion reproducible.
- [x] Definicion builtin, resolver Python y tablas C++ generadas verificables.
- [x] Integrar Motion y consumidores de presentacion sin cambiar layouts.
- [x] Conectar el pipeline y corregir metadatos de peso del catalogo sin
  cambiar reglas de evolucion vigentes.
- [x] Segundo contenido de prueba: nombres, rutas y tiempos distintos;
  resolver todas las vistas y probar que no cambia partida ni recompensas.
- [x] Presupuesto conservador de dos contenidos; rechazo de capacidad en
  pruebas locales. No equivale a recuperacion de una instalacion en placa.
- [x] Ejecutar Python, nativas, build ESP32 y comparaciones visuales existentes.
- [x] Documentar resultados, limites y trabajo que queda para F4/F5.
- [ ] Antes de F5: optimizar/medir dos lineas de arte independientes y su
  staging/recuperacion reales. El presupuesto actual no cabe, no se da por cerrado.

## Evidencia Local

- Red inicial: diez fallos por APIs inexistentes; tambien se comprobaron fallos
  previos a la integracion de Motion y Panels, y al rechazo de JSON/rutas
  conflictivas. Despues de implementar, pasan 34 pruebas especificas de F1.
- 680 vectores de clips: dos definiciones, cinco roles, cuatro contextos y
  17 acciones. Siete vistas reales en Python y siete en C++, sin mutar partida.
  El arte alternativo de prueba deriva de sprites existentes; no representa
  una segunda mascota comercial terminada.
- Suite Python completa: 1.687 pruebas aprobadas en 255,05 s. Una primera
  ejecucion detecto un fixture de Exploracion sin viaje; se corrigio y se
  repitio la suite completa. Pruebas nativas: 185 aprobadas en 1,29 s.
- ESP32: compilacion final aprobada; RAM 56.052/327.680 bytes, aplicacion
  1.030.989/4.194.304 bytes. RAM estatica 64 bytes menor que la base local
  anterior; esto no mide el pico de heap durante una sesion larga.
- `make build-tdisplay`: 227 assets, 10.891.653 bytes de payload.
- Presupuesto conservador: 32.752.237 bytes requeridos frente a 12.451.840
  de capacidad de filesystem. Los 4 KiB por individuo y una segunda linea
  igual de pesada son supuestos, no mediciones del futuro roster.
- Galeria inspeccionada: `out/f1-content-evidence/content-views0/gallery.png`.
  Demuestra resolucion por definicion, no paridad exacta de estado/idioma entre
  ambas columnas. El stub TFT registra texto ordinario sin dibujarlo. Las
  suites dedicadas de paridad visual existentes tambien pasaron.
- Sin acceso USB, flasheo, cambios NVS, WiFi ni publicacion. F1 no cambia
  reglas de juego, premios, balance ni duracion de combate.

## Decisiones De Producto Recibidas En Esta Revision

- Inventario compartido entre individuos: confirmado. Una futura migracion
  consolida el stock una sola vez, no suma copias de cada snapshot del pet.
- Objetivo solicitado: hasta cuatro mascotas. Se evaluara contra presupuesto;
  no esta implementado ni garantizado. Recomendar contar cada huevo entre las
  cuatro plazas para que eclosionar no requiera una quinta plaza inesperada;
  esa politica de huevos sigue pendiente de aprobacion.
- Potencial: proponer un piloto de curva normalizada por rango adulto e IV,
  probar todos los IV y comparar rendimiento antes de fijar cifras. No cambiar
  el techo 99 ni EV en F1. Propuesta de F2, no balance aprobado.
- Breeding propuesto: dos adultos compatibles, saludables, despiertos y con
  identidades distintas; sin padres/hijos/hermanos. Hijo nuevo con ID propio,
  cada IV elegido de uno de los padres y mutacion pequena acotada por aprobar.
  Combinar temperamento y un sesgo moderado de tendencias, no copiar progreso.
  Conservar padres; huevo y cooldown se confirman una sola vez. Compatibilidad
  visual de linea, tiempos y mutaciones se aprueban antes de implementar.
- Combate propuesto: primero pausa de decision al abrir Mochila, para que el
  usuario pueda elegir sin recibir dano mientras navega; limitar el uso de
  objetos por turno y definir coste de accion. Evaluar despues objetivo de
  45-90 s, no imponer espera fija ni inflar HP arbitrariamente. Propuesta por
  aprobar; F1 conserva duracion y reglas actuales.
