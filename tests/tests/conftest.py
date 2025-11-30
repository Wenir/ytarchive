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


@pytest.fixture(scope="session", autouse=False)
def resources_lock(tmp_path_factory):
    lock = TestBucketLock(tmp_path_factory)
    with lock.lock():
        yield lock


@pytest.fixture(scope="module", autouse=True)
def autofixture():
    os.environ["BUCKET_NAME"] = os.environ["TESTS_BUCKET_NAME"]
    os.environ["DB_ACCESS"] = os.environ["TESTS_DB_ACCESS"]
    os.environ["SRC_PLAYLIST"] = os.environ["TESTS_SRC_PLAYLIST"]


@pytest.fixture(scope="function", autouse=False)
async def data_manager(resources_lock):
    assert "main" not in os.environ["BUCKET_NAME"]
    assert "main" not in os.environ["DB_ACCESS"]

    async with await dm.DataManager.create(config.load_config()) as data_manager:
        yield data_manager


def delete_all(data_manager):
    assert "main" not in os.environ["BUCKET_NAME"]

    all_objects = data_manager.bucket.objects.all()
    if not list(all_objects):
        logging.info("nothing to delete")
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


async def delete_all_db(data_manager):
    assert "main" not in os.environ["DB_ACCESS"]

    async with data_manager.db.connection.cursor() as cursor:
        # Get all tables in public schema
        await cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)
        tables = await cursor.fetchall()

        if not tables:
            logging.info("no tables found in database")
            return

        # Delete all records from each table
        for (table_name,) in tables:
            logging.info(f"deleting all records from table {table_name}")
            await cursor.execute(f"DELETE FROM {table_name}")
            deleted_count = cursor.rowcount
            logging.info(f"deleted {deleted_count} rows from {table_name}")

        await data_manager.db.connection.commit()
        logging.info("database cleaned")


@pytest.fixture(scope="function")
def bucket_cleanup(data_manager, resources_lock):
    delete_all(data_manager)

    yield

    delete_all(data_manager)


@pytest.fixture(scope="function")
async def db_cleanup(data_manager, resources_lock):
    await delete_all_db(data_manager)

    yield

    await delete_all_db(data_manager)



def generate_id():
    return shortuuid.uuid()


async def check_items(data_manager, expected):
    async def get_items_by_state(state):
        items = []
        async for item in data_manager.get_src_items_by_state(state):
            items.append(item)

        return items

    actual_items = {}
    expected_items = {}

    for state in dm.SrcItem.State:
        expected_items[state] = [item for item in expected if item.state == state]
        actual_items[state] = await get_items_by_state(state)

    assert actual_items == expected_items


async def check_warnings(data_manager, expected):
    async with data_manager.db.connection.cursor() as cursor:
        await cursor.execute("""
            SELECT provider, id, warning_id, message, state
            FROM warnings
            ORDER BY provider, id, warning_id;
        """)

        actual_warnings = []
        async for row in cursor:
            actual_warnings.append(
                dm.Warning(
                    provider=row[0],
                    id=row[1],
                    warning_id=row[2],
                    message=row[3],
                    state=dm.Warning.State(row[4]),
                )
            )

    assert actual_warnings == expected


@pytest.fixture
def print_bucket(data_manager):
    yield

    logging.info("bucket contents:")

    objects = list(data_manager.bucket.objects.all())

    logging.info("bucket contents:")
    logging.info(objects)


@pytest.fixture
async def print_db(data_manager):
    yield

    logging.info("database contents:")

    async with data_manager.db.connection.cursor() as cursor:
        await cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = await cursor.fetchall()

        if not tables:
            logging.info("No tables found in database")
        else:
            for (table_name,) in tables:
                await cursor.execute(f"SELECT * FROM {table_name}")
                rows = await cursor.fetchall()

                logging.info(f"\n{table_name.upper()} table: {len(rows)} records")
                if rows:
                    columns = [desc[0] for desc in cursor.description]
                    logging.info(f"Columns: {', '.join(columns)}")
                    for row in rows:
                        logging.info(f"  {dict(zip(columns, row))}")
                else:
                    logging.info("  (empty)")
