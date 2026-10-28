"""Versioned, bounded wire envelope for transferring one egg snapshot."""
from dataclasses import dataclass
import struct
import zlib

PROTOCOL_VERSION = 1
MAX_SNAPSHOT_BYTES = 3800
HEADER = struct.Struct("<B16sHI")


@dataclass(frozen=True)
class EggEnvelope:
    token: str
    snapshot: bytes

    def encode(self):
        if (not isinstance(self.token, str) or len(self.token) != 32 or
                any(char not in "0123456789abcdef" for char in self.token)):
            raise ValueError("Invalid egg transfer token")
        if not isinstance(self.snapshot, bytes) or not 1 <= len(self.snapshot) <= MAX_SNAPSHOT_BYTES:
            raise ValueError("Invalid egg snapshot size")
        payload = bytes.fromhex(self.token) + self.snapshot
        checksum = zlib.crc32(payload) & 0xFFFFFFFF
        return HEADER.pack(PROTOCOL_VERSION, bytes.fromhex(self.token), len(self.snapshot), checksum) + self.snapshot

    @classmethod
    def decode(cls, packet):
        if not isinstance(packet, bytes) or len(packet) < HEADER.size:
            raise ValueError("Truncated egg envelope")
        version, token, length, checksum = HEADER.unpack_from(packet)
        snapshot = packet[HEADER.size:]
        if version != PROTOCOL_VERSION or not 1 <= length <= MAX_SNAPSHOT_BYTES or length != len(snapshot):
            raise ValueError("Unsupported or invalid egg envelope")
        if zlib.crc32(token + snapshot) & 0xFFFFFFFF != checksum:
            raise ValueError("Egg envelope checksum mismatch")
        return cls(token.hex(), snapshot)


class EggReceiver:
    """Domain choreography; durable_commit must atomically store egg and receipt."""
    def __init__(self, durable_commit, receipts=()):
        self._durable_commit = durable_commit
        self._receipts = list(receipts)
        self.room_open = False

    def open_room(self):
        self.room_open = True

    def close_room(self):
        self.room_open = False

    def receive(self, packet):
        if not self.room_open:
            raise ValueError("Receive room is closed")
        envelope = EggEnvelope.decode(packet)
        if envelope.token in self._receipts:
            return envelope.token
        if len(self._receipts) >= 27:
            raise ValueError("Transfer receipt capacity reached")
        if not self._durable_commit(envelope.token, envelope.snapshot):
            return None
        self._receipts.append(envelope.token)
        return envelope.token


def remove_sender_copy_after_ack(token, acknowledged, durable_remove):
    if acknowledged != token:
        return False
    return bool(durable_remove(token))
