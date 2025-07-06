from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from typing import Iterable, Generator


class Crypt:
    def __init__(self, key: bytes, iv: bytes):
        # Validate key size (must be exactly 32 bytes for AES-256)
        if len(key) != 32:
            raise ValueError(f"Invalid key size ({len(key) * 8}) for AES. Must be exactly 256 bits (32 bytes).")

        # Validate IV size (must be exactly 16 bytes for AES-CBC)
        if len(iv) != 16:
            raise ValueError(f"Invalid IV size ({len(iv)}) for CBC. Must be 16 bytes.")

        self.cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        self.pkcs7 = padding.PKCS7(256)

    def encrypt(self, data: Iterable) -> Generator:
        encryptor = self.cipher.encryptor()
        padder = self.pkcs7.padder()

        for chunk in data:
            assert isinstance(chunk, bytes)
            padded_data = padder.update(chunk)
            encrypted_data = encryptor.update(padded_data)
            yield encrypted_data

        yield encryptor.update(padder.finalize())
        yield encryptor.finalize()

    def decrypt(self, data: Iterable) -> Generator:
        decryptor = self.cipher.decryptor()
        unpadder = self.pkcs7.unpadder()

        for chunk in data:
            assert isinstance(chunk, bytes)
            decrypted_data = decryptor.update(chunk)
            unpadded_data = unpadder.update(decrypted_data)
            yield unpadded_data

        yield unpadder.update(decryptor.finalize())
        yield unpadder.finalize()


if __name__ == "__main__":
    key = bytes.fromhex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    iv = bytes.fromhex("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")

    crypt = Crypt(key, iv)

    with open(__file__, "rb") as f:
        encrypted_data = crypt.encrypt(iter(lambda: f.read(1024), b""))

        data = b"".join(encrypted_data)

        decrypted_data = crypt.decrypt([data])

        print(b"".join(decrypted_data).decode())
