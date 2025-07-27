import pytest
import logging
import itertools
import cryptography.exceptions
from ytarchive_lib.crypt_v2 import Crypt


@pytest.fixture
def test_key():
    return bytes.fromhex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

@pytest.fixture
def crypt(test_key):
    return Crypt(test_key)

def byte_generator():
    value = 0
    while True:
        yield bytes([value])
        value = (value + 1) % 256


@pytest.mark.parametrize("sizes", itertools.product(range(0, 10), range(0, 3), range(0, 3)))
def test_get_prefix(crypt, sizes):
    gen = byte_generator()
    def n_bytes(n):
        return b''.join(next(gen) for _ in range(n))

    data = [n_bytes(size) for size in sizes]

    joined = b"".join(data)

    if len(joined) < 8:
        with pytest.raises(ValueError, match="Not enough data to read 8 bytes"):
            crypt._get_prefix(8, data)

    else:
        prefix, rest = crypt._get_prefix(8, data)

        assert len(prefix) == 8
        assert prefix == joined[:8]

        assert joined[8:] == b"".join(rest)


def test_get_prefix_two_calls(crypt):
    def gen():
        yield b"123456"
        yield b"7890"
        raise ValueError("End of data")

    prefix, rest = crypt._get_prefix(8, gen())

    assert len(prefix) == 8
    assert prefix == b"12345678"

    assert next(rest) == b"90"
    with pytest.raises(ValueError, match="End of data"):
        next(rest)


@pytest.mark.parametrize("sizes", itertools.product(range(0, 3), range(0, 3), range(0, 3), range(0, 10)))
def test_get_suffix(crypt, sizes):
    gen = byte_generator()
    def n_bytes(n):
        return b''.join(next(gen) for _ in range(n))

    data = [n_bytes(size) for size in sizes]

    joined = b"".join(data)

    if len(joined) < 8:
        with pytest.raises(ValueError, match="Not enough data to read 8 bytes"):
            result = crypt._get_suffix(8, data)
            joined_result = b"".join(result.rest)

    else:
        result = crypt._get_suffix(8, data)
        res = list(result.rest)
        joined_result = b"".join(res)

        assert joined_result == joined[:-8]
        assert result.suffix == joined[-8:]
        logging.error(f"Suffix: {result.suffix}, Length: {len(result.suffix)}, Expected: {joined}, jouned_result: {joined_result}")
        logging.error(f"res: {res}")
        #assert sizes != (2, 2, 2, 7)


def test_encrypt_decrypt_roundtrip(crypt):
    original_data = b"Hello, World! This is a test message."

    encrypted_chunks = list(crypt.encrypt([original_data]))
    encrypted_data = b"".join(encrypted_chunks)

    decrypted_chunks = list(crypt.decrypt([encrypted_data]))
    decrypted_data = b"".join(decrypted_chunks)

    assert decrypted_data == original_data


def test_reject_modified_message(crypt):
    original_data = b"Hello, World! This is a test message."

    encrypted_chunks = list(crypt.encrypt([original_data]))
    encrypted_data = b"".join(encrypted_chunks)

    # Add byte in the middle
    encrypted_data = encrypted_data[:len(encrypted_data)//2] + b'\x00' + encrypted_data[len(encrypted_data)//2:]

    with pytest.raises(cryptography.exceptions.InvalidTag):
        list(crypt.decrypt([encrypted_data]))

def test_encrypt_same_result_different_chunk_sizes(crypt):
    original_data = b"This is a test message that will be split into different chunk sizes to verify encryption consistency."

    encrypted_single = b"".join(crypt.encrypt([original_data]))

    chunk_size = 5
    small_chunks = [original_data[i:i+chunk_size] for i in range(0, len(original_data), chunk_size)]
    encrypted_small_chunks = b"".join(crypt.encrypt(small_chunks))

    chunk_size = 20
    medium_chunks = [original_data[i:i+chunk_size] for i in range(0, len(original_data), chunk_size)]
    encrypted_medium_chunks = b"".join(crypt.encrypt(medium_chunks))

    decrypted_single = b"".join(crypt.decrypt([encrypted_single]))
    decrypted_small_chunks = b"".join(crypt.decrypt([encrypted_small_chunks]))
    decrypted_medium_chunks = b"".join(crypt.decrypt([encrypted_medium_chunks]))

    assert decrypted_single == original_data
    assert decrypted_small_chunks == original_data
    assert decrypted_medium_chunks == original_data

def test_encrypt_decrypt_multiple_chunks(crypt):
    original_chunks = [b"First chunk", b"Second chunk", b"Third chunk"]
    original_data = b"".join(original_chunks)

    encrypted_chunks = list(crypt.encrypt(original_chunks))
    encrypted_data = b"".join(encrypted_chunks)

    decrypted_chunks = list(crypt.decrypt([encrypted_data]))
    decrypted_data = b"".join(decrypted_chunks)

    assert decrypted_data == original_data

def test_encrypt_decrypt_empty_data(crypt):
    original_data = b""

    encrypted_chunks = list(crypt.encrypt([original_data]))
    encrypted_data = b"".join(encrypted_chunks)

    decrypted_chunks = list(crypt.decrypt([encrypted_data]))
    decrypted_data = b"".join(decrypted_chunks)

    assert decrypted_data == original_data

def test_encrypt_decrypt_large_data(crypt):
    original_data = b"A" * 10000

    encrypted_chunks = list(crypt.encrypt([original_data]))
    encrypted_data = b"".join(encrypted_chunks)

    decrypted_chunks = list(crypt.decrypt([encrypted_data]))
    decrypted_data = b"".join(decrypted_chunks)

    assert decrypted_data == original_data

def test_encrypt_output_different_from_input(crypt):
    original_data = b"Test data for encryption"

    encrypted_chunks = list(crypt.encrypt([original_data]))
    encrypted_data = b"".join(encrypted_chunks)

    assert encrypted_data != original_data
    assert len(encrypted_data) > len(original_data)

def test_different_keys_produce_different_outputs():
    key1 = bytes.fromhex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    key2 = bytes.fromhex("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")

    crypt1 = Crypt(key1)
    crypt2 = Crypt(key2)

    original_data = b"Test data"

    encrypted_data1 = b"".join(crypt1.encrypt([original_data]))
    encrypted_data2 = b"".join(crypt2.encrypt([original_data]))

    assert encrypted_data1 != encrypted_data2

def test_encrypt_non_bytes_raises_assertion_error(crypt):
    with pytest.raises(AssertionError):
        list(crypt.encrypt(["not bytes"]))

def test_decrypt_non_bytes_raises_assertion_error(crypt):
    with pytest.raises(AssertionError):
        list(crypt.decrypt(["not bytes"]))

def test_partial_decryption_chunks(crypt):
    original_data = b"Test partial decryption with multiple chunks"

    encrypted_chunks = list(crypt.encrypt([original_data]))
    encrypted_data = b"".join(encrypted_chunks)

    # Split encrypted data into chunks for decryption
    chunk_size = 8
    encrypted_chunks = [encrypted_data[i:i+chunk_size] for i in range(0, len(encrypted_data), chunk_size)]

    decrypted_chunks = list(crypt.decrypt(encrypted_chunks))
    decrypted_data = b"".join(decrypted_chunks)

    assert decrypted_data == original_data

def test_generator_behavior(crypt):
    original_data = b"Test generator behavior"

    # Test that encrypt returns a generator
    encrypted_gen = crypt.encrypt([original_data])
    assert hasattr(encrypted_gen, '__iter__')
    assert hasattr(encrypted_gen, '__next__')

    # Test that decrypt returns a generator
    encrypted_data = b"".join(encrypted_gen)
    decrypted_gen = crypt.decrypt([encrypted_data])
    assert hasattr(decrypted_gen, '__iter__')
    assert hasattr(decrypted_gen, '__next__')

def test_invalid_key_sizes():
    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"a" * 15)

    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"a" * 31)

    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"a" * 33)

    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"")

    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"a" * 16)

    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"a" * 24)
