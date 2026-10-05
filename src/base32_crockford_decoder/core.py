"""Core implementation of Crockford Base32.

Crockford Base32 is designed for human transcription: case-insensitive, no
ambiguous characters (0/O, 1/I/L), and an optional check symbol that catches
single-character errors.

Design decisions taken here (documented so callers know what they get):

1. Only non-negative integers are accepted by ``encode``. Negative values are
   a programming error and raise ``ValueError`` rather than being mapped onto
   a sign symbol, because the sign handling in the spec is a convenience for
   the *text* layer and conflating it with numeric semantics invites bugs.

2. ``decode`` is strict: it rejects unknown symbols (``*``, ``~``, ``$``)
   rather than silently ignoring them, because the whole point of a
   transcription alphabet is that every character carries meaning.

3. Check symbols are purely optional and off by default. When requested, they
   use Crockford's specified modulus-37 table including the non-alphabet
   symbols ``*~$`` for values 32-36.
"""


_SYMBOLS = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_VALUE = {c: i for i, c in enumerate(_SYMBOLS)}
# Normalisation map for visually ambiguous characters.
_NORMALISE = {
    "o": "0", "O": "0",
    "i": "1", "I": "1",
    "l": "1", "L": "1",
}
# Check-symbol table per Crockford. Values 32-36 use symbols outside the
# data alphabet so a check digit is never confused with a data digit.
_CHECK_SYMBOLS = _SYMBOLS + "*~$"
_CHECK_VALUE = {c: i for i, c in enumerate(_CHECK_SYMBOLS)}


def _normalise_char(ch: str) -> str:
    return _NORMALISE.get(ch, ch).upper()


def encode(number: int, checksum: bool = False) -> str:
    """Encode a non-negative integer to a Crockford Base32 string.

    The empty string is the canonical encoding of zero's *absence*? No —
    zero is encoded as ``"0"`` so round-tripping is total. The empty string
    would be ambiguous with "nothing was passed".
    """
    if not isinstance(number, int) or isinstance(number, bool):
        raise TypeError("encode() requires an int")
    if number < 0:
        raise ValueError("encode() requires a non-negative integer")

    if number == 0:
        body = "0"
    else:
        digits = []
        n = number
        while n > 0:
            digits.append(_SYMBOLS[n % 32])
            n //= 32
        body = "".join(reversed(digits))

    if not checksum:
        return body
    return body + _CHECK_SYMBOLS[number % 37]


def decode(encoded: str, checksum: bool = False) -> int:
    """Decode a Crockford Base32 string to a non-negative integer.

    Raises ``ValueError`` on empty input, unknown symbols, or (when
    ``checksum`` is true) a mismatched check symbol.
    """
    if not isinstance(encoded, str):
        raise TypeError("decode() requires a str")

    s = encoded.strip()
    if s == "":
        raise ValueError("empty input is not a valid encoding")

    chars = [_normalise_char(c) for c in s]

    if checksum:
        if len(chars) < 2:
            raise ValueError("checksum requested but input has no check symbol")
        body_chars = chars[:-1]
        check_char = chars[-1]
        if check_char not in _CHECK_VALUE:
            raise ValueError(f"invalid check symbol: {chars[-1]!r}")
    else:
        body_chars = chars
        check_char = None

    value = 0
    for c in body_chars:
        if c not in _VALUE:
            raise ValueError(f"invalid symbol: {c!r}")
        value = value * 32 + _VALUE[c]

    if check_char is not None:
        expected = _CHECK_SYMBOLS[value % 37]
        if check_char != expected:
            raise ValueError(
                f"checksum mismatch: expected {expected!r}, got {check_char!r}"
            )

    return value


def encode_bytes(data: bytes, checksum: bool = False) -> str:
    """Encode a byte sequence.

    The bytes are interpreted as a big-endian unsigned integer (empty bytes
    == 0). This is the simplest total mapping and matches how most byte-to-
    text encodings present their input.
    """
    if isinstance(data, (bytearray, memoryview)):
        data = bytes(data)
    if not isinstance(data, bytes):
        raise TypeError("encode_bytes() requires bytes-like input")
    return encode(int.from_bytes(data, "big"), checksum=checksum)


def decode_bytes(encoded: str, checksum: bool = False) -> bytes:
    """Decode to a minimal big-endian byte representation.

    Zero is returned as ``b'\\x00'`` rather than ``b''`` so that
    ``len(decode_bytes(encode_bytes(b'\\x00')))`` is stable. ``b''`` would
    be a valid but surprising representation of zero.
    """
    value = decode(encoded, checksum=checksum)
    if value == 0:
        return b"\x00"
    length = (value.bit_length() + 7) // 8
    return value.to_bytes(length, "big")
