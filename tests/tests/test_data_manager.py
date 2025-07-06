
import pytest
import ytarchive_lib.data_manager as dm
import ytarchive_lib.config as config
from conftest import generate_id


def test_add():
    data_manager = dm.DataManager(config.load_config())

    item_id = generate_id()

    key = dm.Key.from_id(item_id)
    metadata = {"meta": "data", "int": 123}

    assert len(data_manager.get_objects()) == 0

    data_manager.add_new_object(key, metadata)

    stored_meta = data_manager.load_metadata(key)

    assert metadata == stored_meta
    assert len(data_manager.get_objects()) == 1


def test_get_objects_empty(data_manager):
    objects = list(data_manager.get_objects())
    assert objects == []


def test_get_objects_by_type(data_manager):
    key1 = dm.Key.from_id(generate_id())
    key2 = dm.Key.from_id(generate_id())

    data_manager.add_new_object(key1, {"test": "data1"})
    data_manager.add_warning(key2, {"test": "data2", "warning": "too_long"})

    all_objects = data_manager.get_all_objects()
    assert len(all_objects) == 1
    assert all_objects[0].key == key1

    new_objects = data_manager.get_new_objects()
    assert len(new_objects) == 1
    assert new_objects[0].key == key1

    warning_objects = data_manager.get_objects_by_type("warning")
    assert len(warning_objects) == 1
    assert warning_objects[0].key == key2


def test_add_warning(data_manager):
    key = dm.Key.from_id(generate_id())
    warning_metadata = {
        "id": "test_id",
        "title": "Long Video",
        "duration": 3600,
        "warning": "too_long"
    }

    data_manager.add_warning(key, warning_metadata)

    warning_objects = data_manager.get_objects_by_type("warning")
    assert len(warning_objects) == 1
    assert warning_objects[0].key == key
    assert "warning" in warning_objects[0].types


def test_mark_as_done(data_manager):
    key = dm.Key.from_id(generate_id())
    metadata = {"test": "data"}

    data_manager.add_new_object(key, metadata)
    assert len(data_manager.get_new_objects()) == 1

    data_manager.mark_as_done(key)

    assert len(data_manager.get_new_objects()) == 0
    assert len(data_manager.get_all_objects()) == 1


def test_load_metadata_nonexistent(data_manager):
    key = dm.Key.from_id(generate_id())

    with pytest.raises(Exception):
        data_manager.load_metadata(key)


def test_encryption_roundtrip(data_manager):
    key = dm.Key.from_id(generate_id())
    original_metadata = {
        "complex": "data",
        "with": ["arrays", "and", "objects"],
        "nested": {"structure": True},
        "unicode": "🎬📺",
        "numbers": 42
    }

    data_manager.add_new_object(key, original_metadata)
    retrieved_metadata = data_manager.load_metadata(key)

    assert original_metadata == retrieved_metadata


def test_object_types_tracking(data_manager):
    key = dm.Key.from_id(generate_id())
    metadata = {"test": "data"}

    data_manager.add_new_object(key, metadata)

    objects = list(data_manager.get_objects())
    assert len(objects) == 1

    obj = objects[0]
    assert obj.key == key
    assert "new" in obj.types
    assert "all" in obj.types
    assert len(obj.types) == 2

    data_manager.add_warning(key, {**metadata, "warning": "test"})

    objects = list(data_manager.get_objects())
    assert len(objects) == 1

    obj = objects[0]
    assert "new" in obj.types
    assert "all" in obj.types
    assert "warning" in obj.types
    assert len(obj.types) == 3


def test_upload_file_mock(data_manager):
    import io

    key = dm.Key.from_id(generate_id())
    test_data = b"test file content for upload"
    file_obj = io.BytesIO(test_data)

    data_manager.upload_file(key, file_obj)


def test_multiple_objects_same_key(data_manager):
    key = dm.Key.from_id(generate_id())

    data_manager.add_new_object(key, {"type": "new"})
    data_manager.add_warning(key, {"type": "warning"})

    objects = list(data_manager.get_objects())
    assert len(objects) == 1

    obj = objects[0]
    assert obj.key == key
    assert "new" in obj.types
    assert "all" in obj.types
    assert "warning" in obj.types


def test_empty_metadata(data_manager):
    key = dm.Key.from_id(generate_id())
    empty_metadata = {}

    data_manager.add_new_object(key, empty_metadata)
    retrieved = data_manager.load_metadata(key)

    assert retrieved == empty_metadata


def test_large_metadata(data_manager):
    key = dm.Key.from_id(generate_id())
    large_metadata = {
        "description": "A" * 10000,
        "entries": [f"entry_{i}" for i in range(1000)],
        "nested": {f"key_{i}": f"value_{i}" for i in range(100)}
    }

    data_manager.add_new_object(key, large_metadata)
    retrieved = data_manager.load_metadata(key)

    assert retrieved == large_metadata