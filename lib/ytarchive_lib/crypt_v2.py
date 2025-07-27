from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes, hmac
from typing import Iterable, Generator
from dataclasses import dataclass, field
import secrets


class Crypt:
    def __init__(self, key: bytes):
        # Validate key size (must be exactly 32 bytes for AES-256)
        if len(key) != 32:
            raise ValueError(f"Invalid key size ({len(key) * 8}) for AES. Must be exactly 256 bits (32 bytes).")

        self.algorithm = algorithms.AES(key)

    def encrypt(self, data: Iterable) -> Generator:
        nonce = secrets.token_bytes(16)

        yield b"V2:"

        yield nonce

        encryptor = Cipher(self.algorithm, modes.GCM(nonce)).encryptor()
        for chunk in data:
            assert isinstance(chunk, bytes)
            yield encryptor.update(chunk)

        yield encryptor.finalize()

        tag = encryptor.tag
        assert len(tag) == 16, f"Invalid tag size ({len(tag)}). Must be 16 bytes."

        yield tag

    def decrypt(self, data: Iterable) -> Generator:
        version, rest = self._get_prefix(3, data)
        if version != b"V2:":
            raise ValueError(f"Unsupported version: {version.decode()}")

        nonce, rest = self._get_prefix(16, rest)

        suffix = self._get_suffix(16, rest)

        decryptor = Cipher(self.algorithm, modes.GCM(nonce)).decryptor()

        for chunk in suffix.rest:
            assert isinstance(chunk, bytes)
            yield decryptor.update(chunk)

        yield decryptor.finalize_with_tag(suffix.suffix)

    def _get_prefix(self, size: int, data: Iterable[bytes]) -> tuple[bytes, Generator]:
        buffer = b""
        it = iter(data)

        while len(buffer) < size:
            try:
                chunk = next(it)
            except StopIteration:
                raise ValueError(f"Not enough data to read {size} bytes")
            assert isinstance(chunk, bytes)
            buffer += chunk

        prefix, remainder = buffer[:size], buffer[size:]

        def rest():
            if remainder:
                yield remainder

            yield from it

        return prefix, rest()


    def _get_suffix(self, size: int, data: Iterable[bytes]):
        @dataclass
        class Result:
            rest: Generator = None
            suffix: bytes = b""
            window: list[bytes] = field(default_factory=list)

        result = Result()

        def take_prefix():
            total = 0

            for i in range(len(result.window) - 1, -1, -1):
                total += len(result.window[i])
                if total > size:
                    prefix = result.window[:i]
                    del result.window[:i]
                    return prefix

            return []

        def process_stream():
            for chunk in data:
                assert isinstance(chunk, bytes)

                result.window.append(chunk)
                yield from iter(take_prefix())

            result.suffix = b"".join(result.window)
            if len(result.suffix) > size:
                tmp = result.suffix
                result.suffix = result.suffix[-size:]
                yield tmp[:-size]

            if len(result.suffix) < size:
                raise ValueError(f"Not enough data to read {size} bytes")

        result.rest = process_stream()
        return result


if __name__ == "__main__":
    key = bytes.fromhex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    iv = bytes.fromhex("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")

    crypt = Crypt(key, iv)

    with open(__file__, "rb") as f:
        encrypted_data = crypt.encrypt(iter(lambda: f.read(1024), b""))

        data = b"".join(encrypted_data)

        decrypted_data = crypt.decrypt([data])

        print(b"".join(decrypted_data).decode())
