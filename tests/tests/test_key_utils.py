import pytest
import ytarchive_lib.data_manager as dm
import ytarchive_lib.utils as utils


def test_hash_string_deterministic():
    test_string = "test_input_123"
    hash1 = utils.hash_string(test_string)
    hash2 = utils.hash_string(test_string)

    assert hash1 == hash2
    assert len(hash1) == 64


def test_hash_string_different_inputs():
    hash1 = utils.hash_string("input1")
    hash2 = utils.hash_string("input2")

    assert hash1 != hash2

