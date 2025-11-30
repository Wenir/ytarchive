import pytest
import io
import ytarchive_lib.data_manager as dm
import ytarchive_lib.config as config
from conftest import generate_id, check_items, check_warnings


@pytest.fixture(scope="function", autouse=True)
def enable_bucket_cleanup(bucket_cleanup):
    yield


@pytest.fixture(scope="function", autouse=True)
def enable_db_cleanup(db_cleanup):
    yield


def make_item(state=dm.SrcItem.State.NEW):
    return dm.SrcItem(
        provider="youtube",
        id="vROdVsU_K80",
        url="https://www.youtube.com/watch?v=vROdVsU_K80",
        title="The Original Washing Machine Self Destructs",
        channel="Photonicinduction",
        channel_id="UCl9OJE9OpXui-gRsnWjSrlA",
        channel_url="https://www.youtube.com/channel/UCl9OJE9OpXui-gRsnWjSrlA",
        duration=93,
        state=state,
        priority=0,
    )


async def test_add_src_item(data_manager):
    await data_manager.add_src_item(make_item())

    await check_items(data_manager, [make_item()])


async def test_add_src_item_warning(data_manager):
    await data_manager.add_src_item(make_item(state=dm.SrcItem.State.WARNING))
    await data_manager.add_warning(
        dm.Warning(
            provider="youtube",
            id="vROdVsU_K80",
            warning_id="too_long",
            message="Item duration is too long",
        )
    )

    await check_items(data_manager, [make_item(state=dm.SrcItem.State.WARNING)])
    await check_warnings(
        data_manager,
        [
            dm.Warning(
                provider="youtube",
                id="vROdVsU_K80",
                warning_id="too_long",
                message="Item duration is too long",
                state=dm.Warning.State.NEW,
            )
        ],
    )


async def test_mark_as_done(data_manager):
    await data_manager.add_src_item(make_item())

    await data_manager.mark_as_done("youtube", "vROdVsU_K80")

    await check_items(data_manager, [make_item(state=dm.SrcItem.State.DONE)])


def test_upload_file(data_manager):
    test_data = b"test file content for upload" * 1024 * 1024
    file_obj = io.BytesIO(test_data)

    data_manager.upload_file("youtube", "TESTKEY", file_obj)

    returned_file = b"".join(data_manager.download_file("youtube", "TESTKEY"))

    assert returned_file == test_data
