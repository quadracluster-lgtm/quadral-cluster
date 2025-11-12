from __future__ import annotations

import base64
import binascii
from typing import Iterable


HOURS_PER_WEEK = 7 * 24


def _bits_from_bytes(raw: bytes) -> list[int]:
    bits: list[int] = []
    for byte in raw:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def decode_weekly_mask(mask: str | bytes | None) -> list[int]:
    """Decode a weekly availability mask into a list of bits."""

    if mask is None:
        return [0] * HOURS_PER_WEEK

    if isinstance(mask, bytes):
        bits = _bits_from_bytes(mask)
        bits.extend([0] * max(0, HOURS_PER_WEEK - len(bits)))
        return bits[:HOURS_PER_WEEK]

    mask = mask.strip()
    if not mask:
        return [0] * HOURS_PER_WEEK

    if len(mask) == HOURS_PER_WEEK and set(mask) <= {"0", "1"}:
        return [1 if ch == "1" else 0 for ch in mask]

    try:
        decoded = base64.b64decode(mask, validate=True)
    except (binascii.Error, ValueError):
        decoded = b""
    if decoded:
        bits = _bits_from_bytes(decoded)
        bits.extend([0] * max(0, HOURS_PER_WEEK - len(bits)))
        return bits[:HOURS_PER_WEEK]

    try:
        decoded = bytes.fromhex(mask)
    except ValueError:
        decoded = b""
    if decoded:
        bits = _bits_from_bytes(decoded)
        bits.extend([0] * max(0, HOURS_PER_WEEK - len(bits)))
        return bits[:HOURS_PER_WEEK]

    if "," in mask:
        tokens = [token.strip() for token in mask.split(",") if token.strip()]
        values = [1 if token in {"1", "true", "True"} else 0 for token in tokens]
        values.extend([0] * max(0, HOURS_PER_WEEK - len(values)))
        return values[:HOURS_PER_WEEK]

    if set(mask) <= {"0", "1", " "}:
        values = [1 if ch == "1" else 0 for ch in mask if ch in {"0", "1"}]
        values.extend([0] * max(0, HOURS_PER_WEEK - len(values)))
        return values[:HOURS_PER_WEEK]

    return [0] * HOURS_PER_WEEK


def overlap(mask_a: str | bytes | None, mask_b: str | bytes | None) -> float:
    bits_a = decode_weekly_mask(mask_a)
    bits_b = decode_weekly_mask(mask_b)

    total_a = sum(bits_a)
    total_b = sum(bits_b)
    if total_a == 0 and total_b == 0:
        return 0.0

    overlap_hours = sum(1 for bit_a, bit_b in zip(bits_a, bits_b) if bit_a and bit_b)
    denominator = max(total_a, total_b, 1)
    return overlap_hours / denominator


def ensure_mask_length(bits: Iterable[int]) -> str:
    values = list(bits)[:HOURS_PER_WEEK]
    values.extend([0] * max(0, HOURS_PER_WEEK - len(values)))
    return "".join("1" if value else "0" for value in values)


__all__ = ["decode_weekly_mask", "overlap", "ensure_mask_length", "HOURS_PER_WEEK"]
