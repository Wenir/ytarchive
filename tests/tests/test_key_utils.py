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


def test_key_from_id_deterministic():
    test_id = "video_id_123"

    key1 = dm.Key.from_id(test_id)
    key2 = dm.Key.from_id(test_id)

    assert key1 == key2
    assert key1.key == key2.key


def test_key_from_playlist_item_required_fields():
    playlist_item = {
        "id": "abc123",
        "title": "Test Video",
        "url": "https://youtube.com/watch?v=abc123",
        "channel": "Test Channel"
    }

    key = dm.Key.from_playlist_item(playlist_item)
    expected_key = dm.Key.from_id("abc123")

    assert key == expected_key


def test_key_from_playlist_item_missing_id():
    playlist_item = {
        "title": "Test Video",
        "url": "https://youtube.com/watch?v=abc123"
    }

    with pytest.raises(KeyError):
        dm.Key.from_playlist_item(playlist_item)


def test_key_from_id_edge_cases():
    test_cases = [
        "",
        " ",
        "a" * 1000,
    ]

    for test_input in test_cases:
        key = dm.Key.from_id(test_input)
        assert isinstance(key, dm.Key)
        assert len(key.key) == 64
        assert isinstance(key.key, str)