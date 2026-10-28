import pytest

from core.egg_transfer import EggEnvelope, EggReceiver, remove_sender_copy_after_ack


TOKEN = "00000001000000020000000300000004"


def test_room_state_and_disconnect_resume():
    durable = []
    receiver = EggReceiver(lambda token, body: durable.append((token, body)) or True)
    envelope = EggEnvelope(TOKEN, b"valid egg snapshot")
    packet = envelope.encode()
    with pytest.raises(ValueError):
        receiver.receive(packet)
    receiver.open_room()
    receiver.close_room()
    with pytest.raises(ValueError):
        receiver.receive(packet)
    receiver.open_room()
    assert receiver.receive(packet) == TOKEN
    receiver.close_room()
    resumed = EggReceiver(lambda token, body: durable.append((token, body)) or True, [TOKEN])
    resumed.open_room()
    assert resumed.receive(packet) == TOKEN
    assert durable == [(TOKEN, b"valid egg snapshot")]


def test_transfer_commit_ack_and_retry_exactly_once():
    durable = []
    writes = []
    receiver = EggReceiver(lambda token, body: durable.append((token, body)) or True)
    packet = EggEnvelope(TOKEN, b"egg").encode()
    receiver.open_room()
    ack = receiver.receive(packet)
    assert ack == TOKEN and len(durable) == 1
    assert remove_sender_copy_after_ack(TOKEN, "", lambda value: writes.append(value)) is False
    assert writes == []
    assert remove_sender_copy_after_ack(TOKEN, ack, lambda value: writes.append(value) or True) is True
    assert writes == [TOKEN]
    assert receiver.receive(packet) == TOKEN
    assert len(durable) == 1


def test_envelope_rejects_corruption_and_receipt_full_without_mutation():
    packet = bytearray(EggEnvelope(TOKEN, b"egg").encode())
    packet[-1] ^= 1
    with pytest.raises(ValueError, match="checksum"):
        EggEnvelope.decode(bytes(packet))
    durable = []
    receiver = EggReceiver(lambda token, body: durable.append(token) or True,
                           ["%032x" % value for value in range(1, 28)])
    receiver.open_room()
    with pytest.raises(ValueError, match="capacity"):
        receiver.receive(EggEnvelope(TOKEN, b"egg").encode())
    assert durable == []


def test_failed_durable_commit_does_not_create_receipt_or_ack():
    receiver = EggReceiver(lambda token, body: False)
    receiver.open_room()
    packet = EggEnvelope(TOKEN, b"egg").encode()
    assert receiver.receive(packet) is None
