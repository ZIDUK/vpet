"""Host side of the consult-only USB link. No install and no save mutation."""

PROTOCOL = 1
STATUS_FIELDS = (
    'protocol', 'heap_free', 'heap_min', 'flash', 'fs_used', 'fs_total', 'manifest',
)


class HubLinkError(ValueError):
    pass


def parse_reply(line):
    """Return a status dict, an error code, or None for unrelated board logs."""
    text = line.strip()
    if text == 'HUB ERR' or text.startswith('HUB ERR '):
        fields = _fields(text[len('HUB ERR '):])
        code = fields.get('code')
        if not code:
            raise HubLinkError('Respuesta de error sin codigo.')
        return {'ok': False, 'code': code}
    if not text.startswith('HUB STATUS '):
        return None
    fields = _fields(text[len('HUB STATUS '):])
    missing = [name for name in STATUS_FIELDS if name not in fields]
    if missing:
        raise HubLinkError('Faltan campos: ' + ', '.join(missing))
    try:
        protocol = int(fields['protocol'])
        numbers = {name: int(fields[name]) for name in STATUS_FIELDS if name != 'manifest' and name != 'protocol'}
    except ValueError as error:
        raise HubLinkError('Campo numerico invalido.') from error
    if protocol != PROTOCOL:
        raise HubLinkError('Protocolo incompatible: ' + str(protocol))
    if any(value < 0 for value in numbers.values()) or numbers['fs_used'] > numbers['fs_total']:
        raise HubLinkError('Capacidad incoherente.')
    if not fields['manifest'] or any(c.isspace() for c in fields['manifest']):
        raise HubLinkError('Manifiesto ausente.')
    return {'ok': True, 'protocol': protocol, 'manifest': fields['manifest'], **numbers}


def _fields(body):
    result = {}
    for part in body.split():
        if '=' not in part:
            raise HubLinkError('Campo sin valor: ' + part)
        key, value = part.split('=', 1)
        if key in result:
            raise HubLinkError('Campo duplicado: ' + key)
        result[key] = value
    return result
