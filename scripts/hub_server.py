"""Read-only local content workbench; deliberately has no board write transport."""
import argparse
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.content_definitions import load_definition
from core.content import PetDefinition, ROLES


def describe(definition):
    return {'id': definition.document['id'], 'version': definition.document['version'],
            'profile': definition.document['profile'], 'installable': False,
            'stages': [{'role': role, 'name': definition.stage(role)['name'],
                        'actions': list(definition.stage(role)['actions']),
                        'clips': {action: definition.clip(role, action)
                                  for action in definition.stage(role)['actions']}}
                       for role in ROLES]}


def catalog():
    return describe(load_definition())


def validate_payload(payload):
    if not payload or len(payload) > 65536:
        raise ValueError('La definicion debe tener entre 1 byte y 64 KiB.')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Clave JSON duplicada: ' + key)
            result[key] = value
        return result
    try:
        document = json.loads(payload, object_pairs_hook=unique)
        definition = PetDefinition(document)
        return {**describe(definition), 'valid': True, 'assets_verified': False}
    except (TypeError, KeyError, AttributeError, UnicodeError, RecursionError) as exc:
        raise ValueError('Definicion F1 no valida.') from exc


@lru_cache(maxsize=80)
def preview(role, action):
    definition = load_definition()
    if role not in ROLES or action not in definition.stage(role)['actions']:
        raise ValueError('Recurso desconocido.')
    clip = definition.clip(role, action)
    from PIL import Image
    with Image.open(ROOT / 'build-tdisplay' / clip['atlas'].lstrip('/')) as source:
        image = source.convert('RGBA')
        # Prepared paletted atlases reserve index zero, just like the simulator.
        if source.mode == 'P':
            image.putalpha(source.point([0] + [255] * 255, mode='L'))
        output = BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, mime='application/json'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime + ('; charset=utf-8' if mime != 'image/png' else ''))
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlsplit(self.path)
        try:
            if url.path == '/api/catalog':
                return self.reply(200, catalog())
            if url.path == '/api/preview':
                query = parse_qs(url.query)
                return self.reply(200, preview(query.get('role', [''])[0],
                                               query.get('action', [''])[0]), 'image/png')
            files = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'),
                     '/style.css': ('style.css', 'text/css')}
            if url.path not in files:
                return self.reply(404, {'error': 'No encontrado'})
            name, mime = files[url.path]
            return self.reply(200, (ROOT / 'web/hub' / name).read_bytes(), mime)
        except ValueError as exc:
            self.reply(400, {'error': str(exc)})
        except OSError:
            self.reply(503, {'error': 'Recursos no preparados. Ejecuta make build-tdisplay.'})

    def do_POST(self):
        # Reject cross-origin requests; no filesystem or device writes exist here.
        if self.headers.get('Origin') not in (None, 'http://' + self.headers.get('Host', '')):
            return self.reply(403, {'error': 'Origen no permitido'})
        if self.path != '/api/validate':
            return self.reply(404, {'error': 'No encontrado'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                return self.reply(413, {'error': 'Limite: 64 KiB'})
            self.reply(200, validate_payload(self.rfile.read(length)))
        except (ValueError, RecursionError) as exc:
            self.reply(400, {'error': str(exc) or 'JSON no valido'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'vPet Hub: http://127.0.0.1:{args.port}', flush=True)
    server.serve_forever()
