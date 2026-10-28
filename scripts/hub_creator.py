"""Bounded local authoring export. No installation, rewards or individual state."""
import base64
import binascii
from io import BytesIO
import json
import re
import zipfile

from PIL import Image, UnidentifiedImageError

from scripts.content_definitions import load_definition
from core.content import ACTIONS, ROLES, PetDefinition

MAX_BODY = 24 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_FILE = 4 * 1024 * 1024


def _integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{label}: {low}..{high}')
    return value


def _text(source, key, maximum, pattern=None):
    value = source.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'{key}: obligatorio, maximo {maximum} caracteres')
    if pattern and not re.fullmatch(pattern, value):
        raise ValueError(f'{key}: formato no valido')
    return value


def _png(asset, budget):
    if not isinstance(asset, dict) or not isinstance(asset.get('data'), str):
        raise ValueError('Falta el PNG')
    encoded = asset['data']
    if len(encoded) > (MAX_FILE + 2) // 3 * 4:
        raise ValueError('PNG mayor de 4 MiB')
    try:
        raw = base64.b64decode(encoded, validate=True)
        budget[0] += len(raw)
        if not raw or len(raw) > MAX_FILE or budget[0] > MAX_TOTAL:
            raise ValueError('Limite: 4 MiB por PNG, 16 MiB en total')
        with Image.open(BytesIO(raw)) as image:
            if image.format != 'PNG' or getattr(image, 'n_frames', 1) != 1:
                raise ValueError('Se requiere PNG estatico, no APNG')
            if max(image.size) > 4096 or image.width * image.height > 8 * 1024 * 1024:
                raise ValueError('PNG demasiado grande: maximo 4096px y 8 megapixeles')
            image.verify()
        with Image.open(BytesIO(raw)) as image:
            return image.convert('RGBA'), raw
    except (binascii.Error, OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError('PNG no valido') from exc


def _fit_frames(frames, size):
    bounds = [frame.getchannel('A').point(lambda a: 255 if a >= 128 else 0).getbbox()
              for frame in frames]
    if any(box is None for box in bounds):
        raise ValueError('Hay cuadros completamente transparentes')
    box = (min(b[0] for b in bounds), min(b[1] for b in bounds),
           max(b[2] for b in bounds), max(b[3] for b in bounds))
    scale = min((size-4)/(box[2]-box[0]), (size-4)/(box[3]-box[1]))
    dimensions = (max(1, round((box[2]-box[0])*scale)),
                  max(1, round((box[3]-box[1])*scale)))
    results = []
    for frame in frames:
        result = Image.new('RGBA', (size, size))
        crop = frame.crop(box).resize(dimensions, Image.Resampling.NEAREST)
        result.alpha_composite(crop, ((size-dimensions[0])//2, size-2-dimensions[1]))
        results.append(result)
    return results


def _bmp(image, transparent=True):
    if transparent:
        quantized = image.convert('RGB').quantize(colors=255, dither=Image.Dither.NONE)
        palette = quantized.getpalette()
        indexed = Image.new('P', image.size)
        indexed.putpalette(([0, 0, 0] + palette[:765]))
        colors = quantized.tobytes()
        alpha = image.getchannel('A').tobytes()
        indexed.frombytes(bytes(0 if a < 128 else c+1 for c, a in zip(colors, alpha)))
        image = indexed
    else:
        image = image.convert('RGB')
    out = BytesIO()
    image.save(out, 'BMP')
    return out.getvalue()


def _build(document):
    errors, warnings, outputs, budget = [], [], {}, [0]
    if not isinstance(document, dict) or document.get('schema') != 1:
        return {'valid': False, 'errors': ['Proyecto de autor no valido'], 'warnings': []}, {}
    identity = document.get('identity', {})
    if not isinstance(identity, dict):
        identity = {}
    try:
        package_id = _text(identity, 'id', 40, r'[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+')
        version = _text(identity, 'version', 20, r'\d+\.\d+\.\d+')
        for field, maximum in [('name', 60), ('author', 100), ('license', 80), ('description', 1000)]:
            _text(identity, field, maximum)
    except ValueError as exc:
        return {'valid': False, 'errors': [str(exc)], 'warnings': []}, {}
    content = {'schema': 1, 'id': package_id, 'version': version, 'profile': 'tdisplay-240x135',
               'background': '/Background/day.bmp', 'background_night': '/Background/night.bmp',
               'background_asset': '/backgrounds/day.vpa',
               'background_night_asset': '/backgrounds/night.vpa', 'stages': {}}
    inputs = document.get('stages', {})
    if not isinstance(inputs, dict) or set(inputs) != set(ROLES):
        return {'valid': False, 'errors': ['Se requieren las cinco etapas'], 'warnings': []}, {}

    def resource(asset, key):
        image, raw = _png(asset, budget)
        outputs['sources/' + key + '.png'] = raw
        return image

    builtin = load_definition()
    for role in ROLES:
        try:
            source = inputs[role]
            if not isinstance(source, dict):
                raise ValueError('Etapa no valida')
            name = _text(source, 'name', 12, r'[A-Za-z0-9 _-]+')
            short = _text(source, 'short_name', 12, r'[A-Za-z0-9 _-]+')
            stage = {'name': name, 'short_name': short, 'battle_name': name,
                     'stem': role, 'atlas_root': 'pets/' + role,
                     'home_root': '/animations/' + role, 'portrait': '/portraits/' + role + '.bmp',
                     'portrait_asset': '/portraits/' + role + '.vpa',
                     'training_prefix': '/training/' + role, 'battle_prefix': '/battle/' + role,
                     'exploration_prefix': '/exploration/' + role,
                     'actions': {}, 'aliases': {}, 'training_actions': ['idle'], 'battle_actions': []}
            content['stages'][role] = stage
            clips = source.get('actions', {})
            if not isinstance(clips, dict) or set(clips) - set(ACTIONS):
                raise ValueError('Acciones no validas')
            for action, spec in clips.items():
                if not isinstance(spec, dict):
                    raise ValueError(action + ': configuracion no valida')
                if spec.get('use') != 'upload':
                    continue
                try:
                    image = resource(spec.get('asset'), role + '-' + action)
                    columns = _integer(spec.get('columns'), 1, 64, 'Columnas')
                    rows = _integer(spec.get('rows'), 1, 64, 'Filas')
                    count = _integer(spec.get('frames'), 1, 64, 'Cuadros')
                    interval = _integer(spec.get('interval_ms'), 10, 1000, 'Intervalo')
                    if image.width % columns or image.height % rows or count > columns * rows:
                        raise ValueError('La cuadricula no coincide con el PNG/cuadros')
                    cell = image.width // columns
                    if cell != image.height // rows or cell > 512:
                        raise ValueError('Celdas cuadradas, maximo 512px por lado')
                    frames = [image.crop(((i % columns)*cell, (i // columns)*cell,
                                          (i % columns+1)*cell, (i // columns+1)*cell))
                              for i in range(count)]
                    normalized = _fit_frames(frames, 88)
                    strip = Image.new('RGBA', (88*count, 88))
                    for index, frame in enumerate(normalized):
                        strip.alpha_composite(frame, (88*index, 0))
                    clip = {'frames': count, 'interval_ms': interval}
                    if 'loop' in spec:
                        loop = spec['loop']
                        if not isinstance(loop, list) or len(loop) != 2:
                            raise ValueError('Bucle no valido')
                        first = _integer(loop[0], 0, count-1, 'Inicio de bucle')
                        last = _integer(loop[1], first, count-1, 'Fin de bucle')
                        clip['loop'] = [first, last]
                    stage['actions'][action] = clip
                    outputs[f'prepared/pets/{role}/{role}_{action}_atlas.bmp'] = _bmp(strip)
                    if image.getchannel('A').getextrema()[0] == 255:
                        warnings.append(f'{role}/{action}: PNG opaco; su fondo tambien se mostrara')
                except ValueError as exc:
                    errors.append(f'{role}/{action}: {exc}')
            if 'idle' not in stage['actions']:
                errors.append(role + ': falta la animacion propia de reposo')
            for action in ACTIONS:
                if action in stage['actions']:
                    continue
                spec = clips.get(action, {})
                target = spec.get('use', 'idle') if isinstance(spec, dict) else 'idle'
                if target not in stage['actions'] and not (target == 'idle' and 'idle' not in stage['actions']):
                    errors.append(f'{role}/{action}: reutilizacion sin animacion propia de destino')
                stage['aliases'][action] = target
            # Exploration's current F1 contract reads a concrete walk clip.
            if role != 'egg' and 'walk' not in stage['actions']:
                target = stage['aliases'].get('walk')
                if target in stage['actions']:
                    stage['actions']['walk'] = dict(stage['actions'][target])
                    stage['aliases'].pop('walk')
                    outputs[f'prepared/pets/{role}/{role}_walk_atlas.bmp'] = outputs[
                        f'prepared/pets/{role}/{role}_{target}_atlas.bmp']
            stage['training_actions'] = [a for a in builtin.stage(role)['training_actions']
                                         if a in stage['actions']]
            stage['battle_actions'] = [a for a in builtin.stage(role)['battle_actions']
                                       if a in stage['actions']]
            try:
                portrait = resource(source.get('portrait'), role + '-portrait')
                if portrait.width != portrait.height or portrait.width > 512:
                    raise ValueError('Retrato cuadrado de hasta 512px, no hoja de sprites')
                outputs['prepared' + stage['portrait']] = _bmp(_fit_frames([portrait], 40)[0])
            except ValueError as exc:
                errors.append(f'{role}/retrato: {exc}')
        except (ValueError, TypeError) as exc:
            errors.append(f'{role}: {exc}')
    resources = document.get('resources', {})
    if not isinstance(resources, dict):
        resources = {}
    for key in ['day', 'night']:
        try:
            if key == 'night' and resources.get('reuse_day') is True:
                if 'prepared/Background/day.bmp' not in outputs:
                    raise ValueError('Falta fondo de dia')
                outputs['prepared/Background/night.bmp'] = outputs['prepared/Background/day.bmp']
                continue
            image = resource(resources.get(key), 'background-' + key)
            if image.size != (240, 135) or image.getchannel('A').getextrema()[0] != 255:
                raise ValueError('Fondo PNG opaco de 240x135px')
            outputs[f'prepared/Background/{key}.bmp'] = _bmp(image, False)
        except ValueError as exc:
            errors.append('Fondo ' + key + ': ' + str(exc))
    if resources.get('cover'):
        try:
            resource(resources['cover'], 'cover')
        except ValueError as exc:
            errors.append('Portada: ' + str(exc))
    if not errors:
        try:
            PetDefinition(content)
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append('Definicion generada: ' + str(exc))
    report = {'valid': not errors, 'errors': errors, 'warnings': warnings, 'installable': False,
              'definition': content if not errors else None, 'source_bytes': budget[0],
              'prepared_bytes': sum(len(v) for k, v in outputs.items() if k.startswith('prepared/')),
              'file_count': len(outputs)}
    return report, outputs


def inspect_project(document):
    return _build(document)[0]


def export_project(document):
    report, files = _build(document)
    if not report['valid']:
        raise ValueError('; '.join(report['errors']))
    files['content.json'] = json.dumps(report['definition'], indent=2).encode()
    layouts = {role: {action: {key: value for key, value in spec.items() if key != 'asset'}
                      for action, spec in document['stages'][role]['actions'].items()}
               for role in ROLES}
    files['project.json'] = json.dumps({'schema': 1, 'kind': 'vpet-author-project',
        'identity': document['identity'], 'installable': False,
        'source_layouts': layouts, 'warnings': report['warnings']}, ensure_ascii=False, indent=2).encode()
    files['README.txt'] = (b'vPet authoring project, not an installable package.\n'
        b'content.json: internal F1 definition. prepared/: normalized source for the host build.\n'
        b'sources/: original PNGs. Publication, signing, VPA build and USB installation are separate.\n')
    out = BytesIO()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in sorted(files.items()):
            archive.writestr(name, payload)
    return out.getvalue()
