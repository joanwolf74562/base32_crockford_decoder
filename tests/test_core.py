import unittest

from base32_crockford_decoder import encode, decode, encode_bytes, decode_bytes


class TestEncode(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(encode(0), "0")

    def test_basic_values(self):
        self.assertEqual(encode(1), "1")
        self.assertEqual(encode(31), "Z")
        self.assertEqual(encode(32), "10")
        self.assertEqual(encode(33), "11")

    def test_known_vector(self):
        # 1234567 in Crockford Base32
        self.assertEqual(encode(1234567), "15NM7")

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            encode(-1)

    def test_bool_rejected(self):
        with self.assertRaises(TypeError):
            encode(True)


class TestDecode(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(decode("0"), 0)

    def test_roundtrip(self):
        for n in [0, 1, 31, 32, 33, 1234567, 2**40]:
            self.assertEqual(decode(encode(n)), n)

    def test_case_insensitive(self):
        self.assertEqual(decode("15nm7"), 1234567)
        self.assertEqual(decode("15NM7"), 1234567)

    def test_ambiguous_chars_normalised(self):
        # O -> 0, I/L -> 1
        self.assertEqual(decode("O"), 0)
        self.assertEqual(decode("I"), 1)
        self.assertEqual(decode("l"), 1)

    def test_whitespace_stripped(self):
        self.assertEqual(decode("  15NM7 \n"), 1234567)

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            decode("")

    def test_invalid_symbol_rejected(self):
        with self.assertRaises(ValueError):
            decode("15NM7!")

    def test_known_vector(self):
        self.assertEqual(decode("15NM7"), 1234567)


class TestChecksum(unittest.TestCase):
    def test_encode_appends_check(self):
        # 0 % 37 == 0 -> check symbol '0'
        self.assertEqual(encode(0, checksum=True), "00")
        # 1 % 37 == 1 -> '1'
        self.assertEqual(encode(1, checksum=True), "11")

    def test_roundtrip_with_checksum(self):
        for n in [0, 1, 32, 1234567, 2**40]:
            s = encode(n, checksum=True)
            self.assertEqual(decode(s, checksum=True), n)

    def test_bad_checksum_rejected(self):
        s = encode(1234567, checksum=True)
        tampered = s[:-1] + ("0" if s[-1] != "0" else "1")
        with self.assertRaises(ValueError):
            decode(tampered, checksum=True)

    def test_check_symbol_high_values(self):
        # value 32 -> '*' per Crockford's check table
        self.assertEqual(encode(32, checksum=True), "10*")
        self.assertEqual(decode("10*", checksum=True), 32)


class TestBytes(unittest.TestCase):
    def test_bytes_roundtrip(self):
        for b in [b"\x00", b"\x01", b"\xff", b"\x01\x00", b"hello world"]:
            self.assertEqual(decode_bytes(encode_bytes(b)), b)

    def test_empty_bytes_is_zero(self):
        self.assertEqual(encode_bytes(b""), "0")
        self.assertEqual(decode_bytes(encode_bytes(b"")), b"\x00")

    def test_bytearray_accepted(self):
        self.assertEqual(encode_bytes(bytearray(b"\x01")), "1")

    def test_memoryview_accepted(self):
        self.assertEqual(encode_bytes(memoryview(b"\x01")), "1")


if __name__ == "__main__":
    unittest.main()
