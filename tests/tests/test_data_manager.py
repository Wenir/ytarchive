

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