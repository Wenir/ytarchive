import os
import pytest
import logging
import ytarchive_lib.data_manager as dm
import ytarchive_lib.config as config
import shortuuid


@pytest.fixture(scope="module", autouse=True)
def autofixture():
    os.environ["BUCKET_NAME"] = os.environ["TESTS_BUCKET_NAME"]


@pytest.fixture(scope="function", autouse=False)
def data_manager():
    assert "main" not in os.environ["BUCKET_NAME"]

    return dm.DataManager(config.load_config())


def delete_all(data_manager):
    assert "main" not in os.environ["BUCKET_NAME"]

    all_objects = data_manager.bucket.objects.all()
    if not list(all_objects):
        logging.info("nothing to delete")
        logging.info(data_manager.get_objects())
        return

    response = data_manager.bucket.delete_objects(
        Delete={
            'Objects': [
                {
                    'Key': x.key,
                } for x in all_objects
            ],
            'Quiet': False
        },
    )

    logging.info(f"{response}")
    logging.info(data_manager.get_objects())


@pytest.fixture(scope="function", autouse=True)
def cleanup(data_manager):
    delete_all(data_manager)

    yield

    delete_all(data_manager)



def generate_id():
    return shortuuid.uuid()

