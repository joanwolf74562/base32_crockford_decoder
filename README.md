Encodes and decodes integers and byte sequences using Douglas Crockford's Base32 variant, designed for human transcription: case-insensitive and free of ambiguous characters (0/O, 1/I/L).

```python
from base32_crockford_decoder import encode, decode, encode_bytes, decode_bytes

encode(1234567)              # -> "15NM7"
decode("15nm7")              # -> 1234567 (case-insensitive)
encode(1234567, checksum=True)   # -> "15NM7S" (appends a check symbol)
decode("15NM7S", checksum=True)  # -> 1234567
encode_bytes(b"hi")         # -> "5P"
decode_bytes("5P")          # -> b"hi"
```

## Why this exists

When humans copy identifiers by hand or read them over the phone, standard Base32/Base64 alphabets cause transcription errors: `0` vs `O`, `1` vs `I` vs `l`. Crockford's variant removes those ambiguities, normalises case, and offers an optional check symbol that catches single-character mistakes. This library provides a focused, dependency-free implementation for Python.

Trade-off made: only non-negative integers are supported. Crockford's spec allows a leading `-` for negative numbers, but conflating text-level sign markers with numeric semantics is a common source of bugs, so `encode` rejects negatives with `ValueError`. If you need signed values, track the sign at a higher layer.

## Awkward edges

- `decode` is **strict**: unknown characters (`!`, `@`, whitespace-only input) raise `ValueError` rather than being silently dropped. The point of a transcription alphabet is that every character carries meaning.
- When `checksum=True`, the check symbol may be `*`, `~`, or `$` (for mod-37 values 32–36). These are outside the data alphabet, so a check digit is never confused with a data digit.
- `decode_bytes` returns `b'\x00'` for a decoded zero, not `b''`, so the output length is stable.
- Input is whitespace-trimmed before decoding; leading/trailing spaces are tolerated, embedded whitespace is not.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

