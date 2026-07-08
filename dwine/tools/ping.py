"""Server ping tester — a real Server List Ping implementation.

Speaks the modern SLP protocol (handshake + status + ping) directly over
a socket: MOTD, player counts, version, and measured round-trip latency.
This is exactly what the in-game multiplayer screen does.
"""

from __future__ import annotations

import json
import socket
import struct
import time
from dataclasses import dataclass, field


def pack_varint(value: int) -> bytes:
    out = bytearray()
    value &= 0xFFFFFFFF
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def read_varint(sock_read) -> int:
    result = 0
    for i in range(5):
        raw = sock_read(1)
        if not raw:
            raise ConnectionError("connection closed while reading varint")
        byte = raw[0]
        result |= (byte & 0x7F) << (7 * i)
        if not byte & 0x80:
            break
    else:
        raise ValueError("varint too long")
    return result


def _packet(packet_id: int, payload: bytes) -> bytes:
    body = pack_varint(packet_id) + payload
    return pack_varint(len(body)) + body


def _pack_string(text: str) -> bytes:
    data = text.encode("utf-8")
    return pack_varint(len(data)) + data


@dataclass
class PingResult:
    host: str
    port: int
    latency_ms: float
    version: str
    protocol: int
    players_online: int
    players_max: int
    motd: str
    favicon: str = ""
    sample: list[str] = field(default_factory=list)


def _flatten_motd(description) -> str:
    if isinstance(description, str):
        return description
    if isinstance(description, dict):
        text = description.get("text", "")
        for extra in description.get("extra", []):
            text += _flatten_motd(extra)
        return text
    return str(description)


def ping(host: str, port: int = 25565, timeout: float = 5.0) -> PingResult:
    if ":" in host and not host.startswith("["):
        host, _, port_str = host.partition(":")
        port = int(port_str)

    with socket.create_connection((host, port), timeout=timeout) as sock:
        read = sock.recv

        def read_exact(n: int) -> bytes:
            chunks = b""
            while len(chunks) < n:
                chunk = read(n - len(chunks))
                if not chunk:
                    raise ConnectionError("connection closed")
                chunks += chunk
            return chunks

        # Handshake (state 1 = status), then status request.
        handshake = (
            pack_varint(-1)  # protocol -1 = "just asking"
            + _pack_string(host)
            + struct.pack(">H", port)
            + pack_varint(1)
        )
        sock.sendall(_packet(0x00, handshake))
        sock.sendall(_packet(0x00, b""))

        length = read_varint(read_exact)
        body = read_exact(length)
        offset_holder = {"pos": 0}

        def body_read(n: int) -> bytes:
            pos = offset_holder["pos"]
            offset_holder["pos"] += n
            return body[pos : pos + n]

        read_varint(body_read)  # packet id
        json_len = read_varint(body_read)
        status = json.loads(body_read(json_len).decode("utf-8"))

        # Ping packet for real latency measurement.
        token = int(time.time() * 1000) & 0x7FFFFFFF
        start = time.perf_counter()
        sock.sendall(_packet(0x01, struct.pack(">q", token)))
        try:
            length = read_varint(read_exact)
            read_exact(length)
            latency = (time.perf_counter() - start) * 1000
        except (ConnectionError, socket.timeout):
            latency = -1.0

    players = status.get("players", {})
    version = status.get("version", {})
    return PingResult(
        host=host,
        port=port,
        latency_ms=round(latency, 1),
        version=version.get("name", "?"),
        protocol=int(version.get("protocol", -1)),
        players_online=int(players.get("online", 0)),
        players_max=int(players.get("max", 0)),
        motd=_flatten_motd(status.get("description", "")).strip(),
        favicon=status.get("favicon", ""),
        sample=[p.get("name", "") for p in players.get("sample", []) or []],
    )
