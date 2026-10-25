import json
import pytest
from scripts.hub_server import catalog, validate_payload, preview


def test_catalog_has_real_stages():
    data = catalog()
    assert data['id'] == 'vpet.firemon'
    assert len(data['stages']) == 5
    assert data['installable'] is False


def test_validation_is_metadata_only():
    from scripts.content_definitions import load_definition
    result = validate_payload(json.dumps(load_definition().document).encode())
    assert result['valid']
    assert result['assets_verified'] is False
    assert result['installable'] is False


@pytest.mark.parametrize('payload', [b'{}', b'{', b'x' * 65537,
                                    b'{"schema":1,"schema":1}'])
def test_bad_import(payload):
    with pytest.raises(ValueError):
        validate_payload(payload)


def test_preview_and_restricted_lookup():
    assert preview('rookie', 'idle').startswith(b'\x89PNG')
    with pytest.raises(ValueError):
        preview('../secret', 'idle')


def test_preview_preserves_index_zero_transparency():
    from io import BytesIO
    from PIL import Image
    with Image.open(BytesIO(preview('ultimate', 'idle'))) as image:
        assert image.getpixel((0, 0))[3] == 0
        assert image.getchannel('A').getbbox() is not None
