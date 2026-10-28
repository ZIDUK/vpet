import pytest

from scripts.hub_link import PROTOCOL, HubLinkError, parse_reply


def status(**overrides):
    fields = {
        'protocol': PROTOCOL, 'heap_free': 66000, 'heap_min': 60000,
        'flash': 16777216, 'fs_used': 1400000, 'fs_total': 3145728,
        'manifest': 'vpet-assets-1',
    }
    fields.update(overrides)
    body = ' '.join(f'{key}={value}' for key, value in fields.items())
    return f'HUB STATUS {body}'


def test_status_reports_capacity_without_touching_a_save():
    reply = parse_reply(status())
    assert reply['ok'] is True
    assert reply['flash'] == 16777216
    assert reply['fs_total'] - reply['fs_used'] == 3145728 - 1400000


def test_board_logs_are_not_a_consult_reply():
    assert parse_reply('VPET_READY heap_free=1 heap_min=1 flash=1 fs_used=0 fs_total=1 manifest=x') is None


@pytest.mark.parametrize('line', [
    'HUB STATUS protocol=2 heap_free=1 heap_min=1 flash=1 fs_used=0 fs_total=1 manifest=a',
    'HUB STATUS protocol=1 heap_free=1 heap_min=1 flash=1 fs_used=2 fs_total=1 manifest=a',
    'HUB STATUS protocol=1 heap_min=1 flash=1 fs_used=0 fs_total=1 manifest=a',
    'HUB STATUS protocol=1 heap_free=1 heap_min=1 flash=1 fs_used=0 fs_total=1 manifest=a manifest=b',
    'HUB STATUS protocol=x heap_free=1 heap_min=1 flash=1 fs_used=0 fs_total=1 manifest=a',
])
def test_incompatible_or_incoherent_status_is_rejected(line):
    with pytest.raises(HubLinkError):
        parse_reply(line)


def test_install_and_backup_stay_closed():
    assert parse_reply('HUB ERR code=UNSUPPORTED') == {'ok': False, 'code': 'UNSUPPORTED'}
    with pytest.raises(HubLinkError):
        parse_reply('HUB ERR')
