import os
import pytest
import logging
import ytarchive_lib.data_manager as dm
import ytarchive_lib.config as config
import shortuuid
import contextlib
from filelock import FileLock


class TestBucketLock:
    def __init__(self, tmp_path_factory, name: str = "main", timeout: float = 30.0):
        run_uid = os.environ.get('PYTEST_XDIST_TESTRUNUID')
        directory = tmp_path_factory.getbasetemp()
        if run_uid:
            directory = directory.parent
        else:
            run_uid = "local"
        filename = f"rpp_shared_data.{run_uid}.{name}.json"

        self.shared_file = directory / filename
        self.lock_file = self.shared_file.parent / (self.shared_file.name + '.lock')


    @contextlib.contextmanager
    def lock(self):
        with FileLock(self.lock_file) as lock:
            yield lock


@pytest.fixture(scope="module", autouse=True)
def autofixture():
    os.environ["BUCKET_NAME"] = os.environ["TESTS_BUCKET_NAME"]
    os.environ["DB_ACCESS"] = os.environ["TESTS_DB_ACCESS"]


@pytest.fixture(scope="function", autouse=False)
def data_manager():
    assert "main" not in os.environ["BUCKET_NAME"]
    assert "main" not in os.environ["DB_ACCESS"]

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


@pytest.fixture(scope="function")
def bucket_cleanup(data_manager, tmp_path_factory):
    with TestBucketLock(tmp_path_factory).lock():
        delete_all(data_manager)

        yield

        delete_all(data_manager)



def generate_id():
    return shortuuid.uuid()

