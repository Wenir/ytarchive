import ytarchive_lib.data_manager as dm
import ytarchive_lib.config as config
import os
import logging
import pytest


@pytest.fixture(scope="module", autouse=True)
def autofixture():
    os.environ["BUCKET_NAME"] = os.environ["TESTS_BUCKET_NAME"]


def test_one():
    data_manager = dm.DataManager(config.load_config())

    logging.info(data_manager.add_new_object(dm.Key.from_id("test_item2"), {"meta": "data", "int": 123}))

    logging.info(data_manager.get_objects())