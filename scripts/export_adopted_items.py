"""Generate adopted catalog JSON, board metadata, docs and original sprites."""
import argparse
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
from core.adopted_items import ITEMS, VERSION, STARTER_STOCK, item_name, item_blurb
from scripts.adopted_item_icons import render


def markdown():
    lines = ['# Catalogo adoptado de consumibles vPet', '',
             'Aprobado el 2026-10-15. Fuente: `src/core/adopted_items.py`.',
             'Esta lista sustituye la propuesta de importar los 81 objetos sin filtrar.', '',
             '## Reglas', '',
             '- Carne y Proteina siguen ilimitadas exclusivamente en Alimentar.',
             '- HP/MP porcentuales se calculan sobre el maximo del luchador, no sobre salud de cuidado.',
             '- Recuperacion: 20/50/90/100%; redondeo hacia abajo, minimo 1, sin superar el maximo.',
             '- No resucita, no consume con recurso lleno y no cura fuera de combate.',
             '- Discos: 20% o 40% sobre atributo inicial del combate; no acumulan, tope 99.',
             '- Un disco fuerte sustituye a uno debil; nunca se multiplica un bono anterior.',
             '- Chips: +4 EV; alimentos de atributo: +2 EV; tope 252 por atributo, sin alterar IV.',
             '- Venda cura lesion; Medicina cura lesion y recupera 20 de salud de cuidado.',
             '- Manual: +1 EV en la siguiente sesion completada; no se acumula con Guia.', '',
             '## Disponibilidad real', '',
             'Catalogo, sprites, Mochila, bolsa de Arena y stock persistente integrados en sim y firmware.',
             'La compilacion no equivale a validacion fisica: esta entrega no flashea la placa.',
             'Las partidas conservan sus objetos legacy; no se reinterpretan ni renumeran.',
             'No hay SQLite. JSON es un recurso de desarrollo; la placa usa constantes y LittleFS.', '',
             '## Adquisicion y consumo', '',
             '- Kit inicial una sola vez al crear/migrar el registro: 2 recuperadores pequenos, 2 discos MP pequenos, 1 venda, 1 disco OFF y 1 manzana azul.',
             '- Una victoria de practica entrega 1 objeto, recorriendo este catalogo en orden, excluyendo comida ilimitada y stacks llenos.',
             '- El cursor de recompensas se guarda con el stock. Derrota, empate, retirada y ticks repetidos del resultado no dan objetos.',
             '- Limite 99 por objeto; Manual maximo 1. Reiniciar a huevo conserva stock y cursor; no repone el kit.',
             '- Mochila permite cuidado, curacion de lesion y EV permanentes. Los objetos BAT solo se usan en Arena.',
             '- Arena mantiene el reloj automatico al abrir la bolsa. No consume si el recurso esta lleno, el bono no mejora el actual o termino la pelea.',
             '- Manual abre Entrenamiento sin gastarse: consume 1 al completar y guardar una sesion con hueco de EV. Guia antigua tiene prioridad; no se suman ambos bonos.',
             '- Cancelacion o fallo de guardado conserva stock y efecto anterior. Premio de batalla con fallo de guardado permite Reintentar, sin duplicar el premio.', '',
             '## Persistencia', '',
             'Sim: `adopted_items` version 1, cantidades por ID y cursor, dentro del JSON reemplazado atomicamente.',
             'ESP32: `adoptBag` y journal `itemTx` en NVS. Rechazo restaura el efecto; confirmacion pendiente',
             'conserva el modelo y bloquea nuevas acciones hasta sincronizar y recuperar el journal;',
             'un reinicio aplica los valores finales de forma idempotente antes de cargar la partida.',
             'El schema principal sigue en 3 y no cambia ningun enum/indice antiguo. Registros desconocidos se rechazan en la placa sin borrar la partida.', '',
             '## Objetos adoptados', '',
             '| ID | Nombre | Referencia original | Categoria | Efectos vPet | Duracion | Sprite |',
             '|---|---|---|---|---|---|---|']
    for i in ITEMS:
        effects = '; '.join('%s:%s %s%d' % (e['kind'], e['target'], '+' if e['amount'] > 0 else '', e['amount']) for e in i['effects'])
        lines.append('| `%s` | %s | %s | %s | %s | %s | [PNG](../%s) |' %
                     (i['id'], i['name'], i['reference'], i['category'], effects, i['duration'], i['sprite']))
    lines += ['', '## Excluidos', '',
              'Todas las fichas de evolucion; llaves, pruebas de misiones, pesca, herramientas de mapa y objetos de venta.',
              'Tambien coma, estados de combate inexistentes, disciplina, cansancio y longevidad.',
              'Los chips DV y alimentos de efectos vagos/riesgosos no se adoptan sin una regla concreta.', '',
              '## Compatibilidad', '',
              'El catalogo anterior de siete entradas es la capa de compatibilidad de partidas, no el catalogo futuro.',
              'Tonico, Estrella, Amuleto y Botiquin no se convierten automaticamente a objetos nuevos.',
              'Guia y Manual representan la misma mejora; su migracion debe evitar duplicar recompensas.', '',
              '## Generacion', '',
              '`.venv-platformio/bin/python scripts/export_adopted_items.py`',
              'Usar `--check` para verificar JSON, documentacion, header y pixeles.', '']
    return '\n'.join(lines)


def header():
    q = json.dumps
    lines = ['// Generated by scripts/export_adopted_items.py.', '#pragma once',
             '#include <stdint.h>', 'namespace vpet { namespace adopted {',
             'struct Effect { const char* kind; const char* target; int16_t amount; };',
             'struct Item { const char* id; const char* name; const char* category;',
             '    const char* duration; const char* sprite; bool unlimited;',
             '    Effect effects[4]; uint8_t effectCount;',
             '    const char* nameEn; const char* blurbEs; const char* blurbEn; uint8_t stackMax; uint8_t initialStock; };',
             'static constexpr Item kItems[] = {']
    for item in ITEMS:
        effects = ['{%s,%s,%d}' % (q(e['kind']), q(e['target']), e['amount']) for e in item['effects']]
        effects += ['{nullptr,nullptr,0}'] * (4 - len(effects))
        lines.append('{%s,%s,%s,%s,%s,%s,{%s},%d,%s,%s,%s,%d,%d},' % (
            q(item['id']), q(item['name']), q(item['category']), q(item['duration']),
            q('/ui/items/' + item['id'] + '.vpa'), 'true' if item['unlimited'] else 'false',
            ','.join(effects), len(item['effects']), q(item_name(item)),
            q(item_blurb(item, True)), q(item_blurb(item)), item['stack_max'], STARTER_STOCK.get(item['id'], 0)))
    return '\n'.join(lines + ['};', 'static constexpr uint8_t kCount = sizeof(kItems)/sizeof(kItems[0]);', '} }', ''])


def export(root=ROOT, check=False):
    root = Path(root)
    outputs = {
        'assets/data/items.json': json.dumps({'version': VERSION, 'items': ITEMS}, indent=2) + '\n',
        'docs/adopted-items.md': markdown(),
        'firmware/t-display/lib/vpet_core/src/vpet/AdoptedItems.generated.h': header(),
    }
    for name, text in outputs.items():
        path = root / name
        if check:
            if not path.exists() or path.read_text() != text:
                raise ValueError('Outdated artifact: ' + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    for item in ITEMS:
        path, image = root / item['sprite'], render(item)
        if check:
            with Image.open(path) as actual:
                if actual.mode != 'RGBA' or actual.size != image.size or actual.tobytes() != image.tobytes():
                    raise ValueError('Outdated sprite: ' + item['id'])
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            image.save(path)
    if not check:
        gallery = Image.new('RGB', (640, ((len(ITEMS) + 7) // 8) * 90), '#10161a')
        d = ImageDraw.Draw(gallery)
        for idx, item in enumerate(ITEMS):
            x, y = idx % 8 * 80, idx // 8 * 90
            icon = render(item).resize((48, 48), Image.Resampling.NEAREST)
            gallery.paste(icon, (x + 16, y + 3), icon)
            name = item['id'].replace('_', '\n')
            d.multiline_text((x + 3, y + 53), name, fill='#eaeedb', spacing=0)
        path = root / 'out/item-catalog/adopted.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        gallery.save(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    export(check=parser.parse_args().check)
    print('%d adopted items; no evolution, map or fishing items.' % len(ITEMS))
