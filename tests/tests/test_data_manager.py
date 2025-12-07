import pytest
import io
import ytarchive_lib.data_manager as dm
import ytarchive_lib.config as config
from psycopg.rows import dict_row
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


async def test_add_playlist(data_manager):
    playlist = dm.Playlist(url="https://www.youtube.com/playlist?list=PLs6f7LuYcgtn1IeWz1is9AXZd46F4V6qu")

    inserted = await data_manager.add_playlist(playlist)

    assert inserted is True

    playlists = []
    async for p in data_manager.get_playlists():
        playlists.append(p)

    assert playlists == [playlist]


async def test_add_duplicate_playlist(data_manager):
    playlist = dm.Playlist(url="https://www.youtube.com/playlist?list=PLs6f7LuYcgtn1IeWz1is9AXZd46F4V6qu")

    first_insert = await data_manager.add_playlist(playlist)
    assert first_insert is True

    second_insert = await data_manager.add_playlist(playlist)
    assert second_insert is False

    playlists = []
    async for p in data_manager.get_playlists():
        playlists.append(p)

    assert len(playlists) == 1
    assert playlists == [playlist]


async def test_add_multiple_playlists(data_manager):
    playlist1 = dm.Playlist(url="https://www.youtube.com/playlist?list=PLs6f7LuYcgtn1IeWz1is9AXZd46F4V6qu")
    playlist2 = dm.Playlist(url="https://www.youtube.com/playlist?list=PL2222LuYcgtn1IeWz1is9AXZd46F42222")
    playlist3 = dm.Playlist(url="https://www.youtube.com/playlist?list=PL3333LuYcgtn1IeWz1is9AXZd46F43333")

    await data_manager.add_playlist(playlist1)
    await data_manager.add_playlist(playlist2)
    await data_manager.add_playlist(playlist3)

    playlists = []
    async for p in data_manager.get_playlists():
        playlists.append(p)

    assert len(playlists) == 3
    assert set(p.url for p in playlists) == {playlist1.url, playlist2.url, playlist3.url}


async def test_get_playlists_empty(data_manager):
    playlists = []
    async for p in data_manager.get_playlists():
        playlists.append(p)

    assert playlists == []


async def test_get_warnings_empty(data_manager):
    warnings = []
    async for warning, src_item in data_manager.get_warnings():
        warnings.append((warning, src_item))

    assert warnings == []


async def test_get_warnings_basic(data_manager):
    await data_manager.add_src_item(make_item(state=dm.SrcItem.State.WARNING))
    warning = dm.Warning(
        provider="youtube",
        id="vROdVsU_K80",
        warning_id="too_long",
        message="Item duration is too long",
    )
    await data_manager.add_warning(warning)

    warnings = []
    async for w, src_item in data_manager.get_warnings():
        warnings.append((w, src_item))

    assert len(warnings) == 1
    assert warnings[0][0] == warning
    assert warnings[0][1] == make_item(state=dm.SrcItem.State.WARNING)


async def test_get_warnings_multiple(data_manager):
    item1 = dm.SrcItem(
        provider="youtube",
        id="video1",
        url="https://www.youtube.com/watch?v=video1",
        title="Video 1",
        channel="Channel1",
        channel_id="UC123",
        channel_url="https://www.youtube.com/channel/UC123",
        duration=100,
        state=dm.SrcItem.State.WARNING,
        priority=0,
    )
    warning1 = dm.Warning(
        provider="youtube",
        id="video1",
        warning_id="too_long",
        message="Duration too long",
        state=dm.Warning.State.NEW,
    )

    item2 = dm.SrcItem(
        provider="youtube",
        id="video2",
        url="https://www.youtube.com/watch?v=video2",
        title="Video 2",
        channel="Channel2",
        channel_id="UC456",
        channel_url="https://www.youtube.com/channel/UC456",
        duration=200,
        state=dm.SrcItem.State.WARNING,
        priority=0,
    )
    warning2 = dm.Warning(
        provider="youtube",
        id="video2",
        warning_id="unknown_duration",
        message="Duration unknown",
        state=dm.Warning.State.NEW,
    )

    await data_manager.add_src_item(item1)
    await data_manager.add_warning(warning1)
    await data_manager.add_src_item(item2)
    await data_manager.add_warning(warning2)

    warnings = []
    async for w, src_item in data_manager.get_warnings():
        warnings.append((w, src_item))

    assert len(warnings) == 2
    assert warnings[0][0] == warning1
    assert warnings[0][1] == item1
    assert warnings[1][0] == warning2
    assert warnings[1][1] == item2


async def test_get_warnings_filtered_by_state(data_manager):
    item1 = dm.SrcItem(
        provider="youtube",
        id="video1",
        url="https://www.youtube.com/watch?v=video1",
        title="Video 1",
        channel="Channel1",
        channel_id="UC123",
        channel_url="https://www.youtube.com/channel/UC123",
        duration=100,
        state=dm.SrcItem.State.WARNING,
        priority=0,
    )
    warning1 = dm.Warning(
        provider="youtube",
        id="video1",
        warning_id="too_long",
        message="Duration too long",
        state=dm.Warning.State.NEW,
    )

    item2 = dm.SrcItem(
        provider="youtube",
        id="video2",
        url="https://www.youtube.com/watch?v=video2",
        title="Video 2",
        channel="Channel2",
        channel_id="UC456",
        channel_url="https://www.youtube.com/channel/UC456",
        duration=200,
        state=dm.SrcItem.State.NEW,
        priority=0,
    )
    warning2 = dm.Warning(
        provider="youtube",
        id="video2",
        warning_id="unknown_duration",
        message="Duration unknown",
        state=dm.Warning.State.OVERRIDDEN,
    )

    await data_manager.add_src_item(item1)
    await data_manager.add_warning(warning1)
    await data_manager.add_src_item(item2)
    await data_manager.add_warning(warning2)

    new_warnings = []
    async for w, src_item in data_manager.get_warnings(state=dm.Warning.State.NEW):
        new_warnings.append((w, src_item))

    assert len(new_warnings) == 1
    assert new_warnings[0][0] == warning1
    assert new_warnings[0][1] == item1

    overridden_warnings = []
    async for w, src_item in data_manager.get_warnings(state=dm.Warning.State.OVERRIDDEN):
        overridden_warnings.append((w, src_item))

    assert len(overridden_warnings) == 1
    assert overridden_warnings[0][0] == warning2
    assert overridden_warnings[0][1] == item2


async def test_clear_warning(data_manager):
    await data_manager.add_src_item(make_item(state=dm.SrcItem.State.WARNING))
    warning = dm.Warning(
        provider="youtube",
        id="vROdVsU_K80",
        warning_id="too_long",
        message="Item duration is too long",
        state=dm.Warning.State.NEW,
    )
    await data_manager.add_warning(warning)

    await check_items(data_manager, [make_item(state=dm.SrcItem.State.WARNING)])
    await check_warnings(data_manager, [warning])

    await data_manager.clear_warning("youtube", "vROdVsU_K80")

    await check_items(data_manager, [make_item(state=dm.SrcItem.State.NEW)])
    await check_warnings(
        data_manager,
        [
            dm.Warning(
                provider="youtube",
                id="vROdVsU_K80",
                warning_id="too_long",
                message="Item duration is too long",
                state=dm.Warning.State.OVERRIDDEN,
            )
        ],
    )


async def test_clear_warning_multiple(data_manager):
    item1 = dm.SrcItem(
        provider="youtube",
        id="video1",
        url="https://www.youtube.com/watch?v=video1",
        title="Video 1",
        channel="Channel1",
        channel_id="UC123",
        channel_url="https://www.youtube.com/channel/UC123",
        duration=100,
        state=dm.SrcItem.State.WARNING,
        priority=0,
    )
    warning1 = dm.Warning(
        provider="youtube",
        id="video1",
        warning_id="too_long",
        message="Duration too long",
        state=dm.Warning.State.NEW,
    )

    item2 = dm.SrcItem(
        provider="youtube",
        id="video2",
        url="https://www.youtube.com/watch?v=video2",
        title="Video 2",
        channel="Channel2",
        channel_id="UC456",
        channel_url="https://www.youtube.com/channel/UC456",
        duration=200,
        state=dm.SrcItem.State.WARNING,
        priority=0,
    )
    warning2 = dm.Warning(
        provider="youtube",
        id="video2",
        warning_id="unknown_duration",
        message="Duration unknown",
        state=dm.Warning.State.NEW,
    )

    await data_manager.add_src_item(item1)
    await data_manager.add_warning(warning1)
    await data_manager.add_src_item(item2)
    await data_manager.add_warning(warning2)

    await data_manager.clear_warning("youtube", "video1")

    expected_items = [
        dm.SrcItem(
            provider="youtube",
            id="video1",
            url="https://www.youtube.com/watch?v=video1",
            title="Video 1",
            channel="Channel1",
            channel_id="UC123",
            channel_url="https://www.youtube.com/channel/UC123",
            duration=100,
            state=dm.SrcItem.State.NEW,
            priority=0,
        ),
        item2,
    ]
    await check_items(data_manager, expected_items)

    expected_warnings = [
        dm.Warning(
            provider="youtube",
            id="video1",
            warning_id="too_long",
            message="Duration too long",
            state=dm.Warning.State.OVERRIDDEN,
        ),
        warning2,
    ]
    await check_warnings(data_manager, expected_warnings)


async def test_clear_warning_does_not_affect_non_warning_items(data_manager):
    await data_manager.add_src_item(make_item(state=dm.SrcItem.State.DONE))
    warning = dm.Warning(
        provider="youtube",
        id="vROdVsU_K80",
        warning_id="too_long",
        message="Item duration is too long",
        state=dm.Warning.State.NEW,
    )
    await data_manager.add_warning(warning)

    await data_manager.clear_warning("youtube", "vROdVsU_K80")

    await check_items(data_manager, [make_item(state=dm.SrcItem.State.DONE)])

    await check_warnings(
        data_manager,
        [
            dm.Warning(
                provider="youtube",
                id="vROdVsU_K80",
                warning_id="too_long",
                message="Item duration is too long",
                state=dm.Warning.State.OVERRIDDEN,
            )
        ],
    )


async def test_add_video_metadata(data_manager):
    metadata = dm.VideoMetadata(
        provider="youtube",
        id="y8Kyi0WNg40",
        chapters='[{"start_time": 0, "end_time": 10, "title": "Chapter 1"}]',
        description="Test video description",
        raw_data='{"title": "Test Video", "duration": 120}'
    )

    inserted = await data_manager.add_video_metadata(metadata)
    assert inserted is True

    # Verify the metadata was stored
    async with data_manager.db.connection.cursor(row_factory=dict_row) as cursor:
        await cursor.execute("""
            SELECT provider, id, chapters, description, raw_data
            FROM video_metadata
            WHERE provider = %s AND id = %s
        """, ("youtube", "y8Kyi0WNg40"))
        row = await cursor.fetchone()

    assert row is not None
    assert row['provider'] == "youtube"
    assert row['id'] == "y8Kyi0WNg40"
    assert row['chapters'] == '[{"start_time": 0, "end_time": 10, "title": "Chapter 1"}]'
    assert row['description'] == "Test video description"
    assert row['raw_data'] == '{"title": "Test Video", "duration": 120}'


async def test_add_video_metadata_update(data_manager):
    metadata1 = dm.VideoMetadata(
        provider="youtube",
        id="y8Kyi0WNg40",
        chapters='[{"start_time": 0, "end_time": 10, "title": "Chapter 1"}]',
        description="Original description",
        raw_data='{"title": "Original", "duration": 120}'
    )

    first_insert = await data_manager.add_video_metadata(metadata1)
    assert first_insert is True

    # Update with new metadata
    metadata2 = dm.VideoMetadata(
        provider="youtube",
        id="y8Kyi0WNg40",
        chapters='[{"start_time": 0, "end_time": 20, "title": "Updated Chapter"}]',
        description="Updated description",
        raw_data='{"title": "Updated", "duration": 240}'
    )

    second_insert = await data_manager.add_video_metadata(metadata2)
    assert second_insert is True

    # Verify only one record exists with updated values
    async with data_manager.db.connection.cursor(row_factory=dict_row) as cursor:
        await cursor.execute("""
            SELECT provider, id, chapters, description, raw_data
            FROM video_metadata
        """)
        rows = await cursor.fetchall()

    assert len(rows) == 1
    assert rows[0]['chapters'] == '[{"start_time": 0, "end_time": 20, "title": "Updated Chapter"}]'
    assert rows[0]['description'] == "Updated description"
    assert rows[0]['raw_data'] == '{"title": "Updated", "duration": 240}'


async def test_add_video_metadata_multiple(data_manager):
    metadata1 = dm.VideoMetadata(
        provider="youtube",
        id="video1",
        chapters='[]',
        description="Description 1",
        raw_data='{"title": "Video 1"}'
    )

    metadata2 = dm.VideoMetadata(
        provider="youtube",
        id="video2",
        chapters='[{"start_time": 0, "end_time": 30, "title": "Intro"}]',
        description="Description 2",
        raw_data='{"title": "Video 2"}'
    )

    metadata3 = dm.VideoMetadata(
        provider="vimeo",
        id="video1",
        chapters='[]',
        description="Description 3",
        raw_data='{"title": "Video 3"}'
    )

    await data_manager.add_video_metadata(metadata1)
    await data_manager.add_video_metadata(metadata2)
    await data_manager.add_video_metadata(metadata3)

    # Verify all three records exist
    async with data_manager.db.connection.cursor(row_factory=dict_row) as cursor:
        await cursor.execute("""
            SELECT provider, id, description
            FROM video_metadata
            ORDER BY provider, id
        """)
        rows = await cursor.fetchall()

    assert len(rows) == 3
    assert rows[0]['provider'] == "vimeo"
    assert rows[0]['id'] == "video1"
    assert rows[1]['provider'] == "youtube"
    assert rows[1]['id'] == "video1"
    assert rows[2]['provider'] == "youtube"
    assert rows[2]['id'] == "video2"


async def test_add_video_metadata_empty_fields(data_manager):
    metadata = dm.VideoMetadata(
        provider="youtube",
        id="empty_test",
        chapters="",
        description="",
        raw_data='{"minimal": "data"}'
    )

    inserted = await data_manager.add_video_metadata(metadata)
    assert inserted is True

    # Verify empty strings are stored correctly
    async with data_manager.db.connection.cursor(row_factory=dict_row) as cursor:
        await cursor.execute("""
            SELECT chapters, description
            FROM video_metadata
            WHERE provider = %s AND id = %s
        """, ("youtube", "empty_test"))
        row = await cursor.fetchone()

    assert row is not None
    assert row['chapters'] == ""
    assert row['description'] == ""
