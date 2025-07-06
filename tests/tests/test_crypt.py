import pytest
from ytarchive_lib.crypt import Crypt


@pytest.fixture
def test_key():
    return bytes.fromhex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

@pytest.fixture
def test_iv():
    return bytes.fromhex("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")

@pytest.fixture
def crypt(test_key, test_iv):
    return Crypt(test_key, test_iv)

def test_encrypt_decrypt_roundtrip(crypt):
    original_data = b"Hello, World! This is a test message."

    encrypted_chunks = list(crypt.encrypt([original_data]))
    encrypted_data = b"".join(encrypted_chunks)

    decrypted_chunks = list(crypt.decrypt([encrypted_data]))
    decrypted_data = b"".join(decrypted_chunks)

    assert decrypted_data == original_data

def test_encrypt_same_result_different_chunk_sizes(crypt):
    original_data = b"This is a test message that will be split into different chunk sizes to verify encryption consistency."

    encrypted_single = b"".join(crypt.encrypt([original_data]))

    chunk_size = 5
    small_chunks = [original_data[i:i+chunk_size] for i in range(0, len(original_data), chunk_size)]
    encrypted_small_chunks = b"".join(crypt.encrypt(small_chunks))

    chunk_size = 20
    medium_chunks = [original_data[i:i+chunk_size] for i in range(0, len(original_data), chunk_size)]
    encrypted_medium_chunks = b"".join(crypt.encrypt(medium_chunks))

    assert encrypted_single == encrypted_small_chunks
    assert encrypted_single == encrypted_medium_chunks
    assert encrypted_small_chunks == encrypted_medium_chunks

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

def test_same_input_produces_same_output(crypt):
    original_data = b"Deterministic test"

    encrypted_chunks1 = list(crypt.encrypt([original_data]))
    encrypted_data1 = b"".join(encrypted_chunks1)

    encrypted_chunks2 = list(crypt.encrypt([original_data]))
    encrypted_data2 = b"".join(encrypted_chunks2)

    assert encrypted_data1 == encrypted_data2

def test_different_keys_produce_different_outputs(test_iv):
    key1 = bytes.fromhex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    key2 = bytes.fromhex("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")

    crypt1 = Crypt(key1, test_iv)
    crypt2 = Crypt(key2, test_iv)

    original_data = b"Test data"

    encrypted_data1 = b"".join(crypt1.encrypt([original_data]))
    encrypted_data2 = b"".join(crypt2.encrypt([original_data]))

    assert encrypted_data1 != encrypted_data2

def test_different_ivs_produce_different_outputs(test_key):
    iv1 = bytes.fromhex("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
    iv2 = bytes.fromhex("cccccccccccccccccccccccccccccccc")

    crypt1 = Crypt(test_key, iv1)
    crypt2 = Crypt(test_key, iv2)

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

def test_invalid_key_sizes(test_iv):
    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"a" * 15, test_iv)

    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"a" * 31, test_iv)

    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"a" * 33, test_iv)

    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"", test_iv)

    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"a" * 16, test_iv)

    with pytest.raises(ValueError, match="Invalid key size.*Must be exactly 256 bits"):
        Crypt(b"a" * 24, test_iv)

def test_invalid_iv_sizes(test_key):
    with pytest.raises(ValueError, match="Invalid IV size.*Must be 16 bytes"):
        Crypt(test_key, b"a" * 15)

    with pytest.raises(ValueError, match="Invalid IV size.*Must be 16 bytes"):
        Crypt(test_key, b"a" * 17)

    with pytest.raises(ValueError, match="Invalid IV size.*Must be 16 bytes"):
        Crypt(test_key, b"")

    with pytest.raises(ValueError, match="Invalid IV size.*Must be 16 bytes"):
        Crypt(test_key, b"a" * 8)

    with pytest.raises(ValueError, match="Invalid IV size.*Must be 16 bytes"):
        Crypt(test_key, b"a" * 32)