import pytest
import yaml
import argparse
from pathlib import Path
import ytarchive_lib.warnings_app as app
import ytarchive_lib.data_manager as dm
from conftest import check_items, check_warnings


@pytest.fixture(scope="function", autouse=True)
def enable_db_cleanup(db_cleanup):
    yield


def make_warning_item(id: str, channel: str, duration: int):
    return dm.SrcItem(
        provider="youtube",
        id=id,
        url=f"https://www.youtube.com/watch?v={id}",
        title=f"Video {id}",
        channel=channel,
        channel_id=f"UC{id}",
        channel_url=f"https://www.youtube.com/channel/UC{id}",
        duration=duration,
        state=dm.SrcItem.State.WARNING,
        priority=0,
    )


def make_warning(id: str, warning_id: str, message: str, state=dm.Warning.State.NEW):
    return dm.Warning(
        provider="youtube",
        id=id,
        warning_id=warning_id,
        message=message,
        state=state,
    )


async def test_list_warnings_empty(data_manager, capsys):
    args = argparse.Namespace(new=False)
    await app.list_warnings(args)

    captured = capsys.readouterr()
    assert captured.out == ""


async def test_list_warnings_basic(data_manager, capsys):
    # Add item with warning
    item = make_warning_item("video1", "Channel1", 100)
    warning = make_warning("video1", "too_long", "Duration too long")

    await data_manager.add_src_item(item)
    await data_manager.add_warning(warning)

    # List warnings
    args = argparse.Namespace(new=False)
    await app.list_warnings(args)

    captured = capsys.readouterr()
    assert "video1" in captured.out
    assert "too_long" in captured.out
    assert "Duration too long" in captured.out
    assert "Channel1" in captured.out


async def test_list_warnings_with_new_filter(data_manager, capsys):
    # Add warnings with different states
    item1 = make_warning_item("video1", "Channel1", 100)
    warning1 = make_warning("video1", "too_long", "Duration too long", dm.Warning.State.NEW)

    item2 = make_warning_item("video2", "Channel2", 200)
    warning2 = make_warning("video2", "too_long", "Duration too long", dm.Warning.State.OVERRIDDEN)

    await data_manager.add_src_item(item1)
    await data_manager.add_warning(warning1)
    await data_manager.add_src_item(item2)
    await data_manager.add_warning(warning2)

    # List only NEW warnings
    args = argparse.Namespace(new=True)
    await app.list_warnings(args)

    captured = capsys.readouterr()
    assert "video1" in captured.out
    assert "video2" not in captured.out


async def test_export_warnings_empty(data_manager, tmp_path):
    output_file = tmp_path / "warnings.yml"
    args = argparse.Namespace(output=str(output_file), new=False)

    await app.export_warnings(args)

    assert output_file.exists()
    with open(output_file, 'r') as f:
        data = yaml.safe_load(f)

    assert data == []


async def test_export_warnings_basic(data_manager, tmp_path):
    # Add item with warning
    item = make_warning_item("video1", "Channel1", 100)
    warning = make_warning("video1", "too_long", "Duration too long")

    await data_manager.add_src_item(item)
    await data_manager.add_warning(warning)

    # Export warnings
    output_file = tmp_path / "warnings.yml"
    args = argparse.Namespace(output=str(output_file), new=False)
    await app.export_warnings(args)

    assert output_file.exists()
    with open(output_file, 'r') as f:
        data = yaml.safe_load(f)

    assert len(data) == 1
    assert data[0]['id'] == 'video1'
    assert data[0]['provider'] == 'youtube'
    assert data[0]['warning_id'] == 'too_long'
    assert data[0]['message'] == 'Duration too long'
    assert data[0]['clear'] is False
    assert data[0]['item_state'] == 'warning'
    assert data[0]['channel'] == 'Channel1'
    assert data[0]['duration'] == 100


async def test_export_warnings_multiple(data_manager, tmp_path):
    # Add multiple items with warnings
    item1 = make_warning_item("video1", "Channel1", 100)
    warning1 = make_warning("video1", "too_long", "Duration too long")

    item2 = make_warning_item("video2", "Channel2", 200)
    warning2 = make_warning("video2", "unknown_duration", "Duration unknown")

    await data_manager.add_src_item(item1)
    await data_manager.add_warning(warning1)
    await data_manager.add_src_item(item2)
    await data_manager.add_warning(warning2)

    # Export warnings
    output_file = tmp_path / "warnings.yml"
    args = argparse.Namespace(output=str(output_file), new=False)
    await app.export_warnings(args)

    assert output_file.exists()
    with open(output_file, 'r') as f:
        data = yaml.safe_load(f)

    assert len(data) == 2
    assert data[0]['id'] == 'video1'
    assert data[1]['id'] == 'video2'


async def test_export_warnings_with_new_filter(data_manager, tmp_path):
    # Add warnings with different states
    item1 = make_warning_item("video1", "Channel1", 100)
    warning1 = make_warning("video1", "too_long", "Duration too long", dm.Warning.State.NEW)

    item2 = make_warning_item("video2", "Channel2", 200)
    warning2 = make_warning("video2", "too_long", "Duration too long", dm.Warning.State.OVERRIDDEN)

    await data_manager.add_src_item(item1)
    await data_manager.add_warning(warning1)
    await data_manager.add_src_item(item2)
    await data_manager.add_warning(warning2)

    # Export only NEW warnings
    output_file = tmp_path / "warnings.yml"
    args = argparse.Namespace(output=str(output_file), new=True)
    await app.export_warnings(args)

    assert output_file.exists()
    with open(output_file, 'r') as f:
        data = yaml.safe_load(f)

    assert len(data) == 1
    assert data[0]['id'] == 'video1'


async def test_clear_warnings_no_file(data_manager, tmp_path, capsys):
    # Try to clear from non-existent file
    input_file = tmp_path / "nonexistent.yml"
    args = argparse.Namespace(input=str(input_file))

    await app.clear_warnings(args)

    captured = capsys.readouterr()
    assert "not found" in captured.out.lower() or "not found" in captured.err.lower()


async def test_clear_warnings_empty_file(data_manager, tmp_path, capsys):
    # Create empty YAML file
    input_file = tmp_path / "warnings.yml"
    with open(input_file, 'w') as f:
        yaml.dump([], f)

    args = argparse.Namespace(input=str(input_file))
    await app.clear_warnings(args)

    captured = capsys.readouterr()
    assert "No warnings" in captured.out


async def test_clear_warnings_none_marked(data_manager, tmp_path, capsys):
    # Add item with warning
    item = make_warning_item("video1", "Channel1", 100)
    warning = make_warning("video1", "too_long", "Duration too long")

    await data_manager.add_src_item(item)
    await data_manager.add_warning(warning)

    # Create YAML with clear=False
    input_file = tmp_path / "warnings.yml"
    with open(input_file, 'w') as f:
        yaml.dump([{
            'id': 'video1',
            'provider': 'youtube',
            'warning_id': 'too_long',
            'message': 'Duration too long',
            'clear': False,
        }], f)

    args = argparse.Namespace(input=str(input_file))
    await app.clear_warnings(args)

    captured = capsys.readouterr()
    assert "No warnings marked" in captured.out

    # Verify warning is still NEW
    await check_warnings(data_manager, [warning])


async def test_clear_warnings_basic(data_manager, tmp_path):
    # Add item with warning
    item = make_warning_item("video1", "Channel1", 100)
    warning = make_warning("video1", "too_long", "Duration too long")

    await data_manager.add_src_item(item)
    await data_manager.add_warning(warning)

    # Create YAML with clear=True
    input_file = tmp_path / "warnings.yml"
    with open(input_file, 'w') as f:
        yaml.dump([{
            'id': 'video1',
            'provider': 'youtube',
            'warning_id': 'too_long',
            'message': 'Duration too long',
            'clear': True,
        }], f)

    args = argparse.Namespace(input=str(input_file))
    await app.clear_warnings(args)

    # Verify item is now NEW
    await check_items(data_manager, [
        dm.SrcItem(
            provider="youtube",
            id="video1",
            url="https://www.youtube.com/watch?v=video1",
            title="Video video1",
            channel="Channel1",
            channel_id="UCvideo1",
            channel_url="https://www.youtube.com/channel/UCvideo1",
            duration=100,
            state=dm.SrcItem.State.NEW,
            priority=0,
        )
    ])

    # Verify warning is OVERRIDDEN
    await check_warnings(data_manager, [
        dm.Warning(
            provider="youtube",
            id="video1",
            warning_id="too_long",
            message="Duration too long",
            state=dm.Warning.State.OVERRIDDEN,
        )
    ])


async def test_clear_warnings_multiple_selective(data_manager, tmp_path):
    # Add multiple items with warnings
    item1 = make_warning_item("video1", "Channel1", 100)
    warning1 = make_warning("video1", "too_long", "Duration too long")

    item2 = make_warning_item("video2", "Channel2", 200)
    warning2 = make_warning("video2", "unknown_duration", "Duration unknown")

    item3 = make_warning_item("video3", "Channel3", 300)
    warning3 = make_warning("video3", "too_long", "Duration too long")

    await data_manager.add_src_item(item1)
    await data_manager.add_warning(warning1)
    await data_manager.add_src_item(item2)
    await data_manager.add_warning(warning2)
    await data_manager.add_src_item(item3)
    await data_manager.add_warning(warning3)

    # Create YAML with selective clear
    input_file = tmp_path / "warnings.yml"
    with open(input_file, 'w') as f:
        yaml.dump([
            {
                'id': 'video1',
                'provider': 'youtube',
                'warning_id': 'too_long',
                'message': 'Duration too long',
                'clear': True,  # Clear this one
            },
            {
                'id': 'video2',
                'provider': 'youtube',
                'warning_id': 'unknown_duration',
                'message': 'Duration unknown',
                'clear': False,  # Don't clear
            },
            {
                'id': 'video3',
                'provider': 'youtube',
                'warning_id': 'too_long',
                'message': 'Duration too long',
                'clear': True,  # Clear this one
            },
        ], f)

    args = argparse.Namespace(input=str(input_file))
    await app.clear_warnings(args)

    # Verify video1 and video3 are NEW, video2 is still WARNING
    await check_items(data_manager, [
        dm.SrcItem(
            provider="youtube",
            id="video1",
            url="https://www.youtube.com/watch?v=video1",
            title="Video video1",
            channel="Channel1",
            channel_id="UCvideo1",
            channel_url="https://www.youtube.com/channel/UCvideo1",
            duration=100,
            state=dm.SrcItem.State.NEW,
            priority=0,
        ),
        dm.SrcItem(
            provider="youtube",
            id="video2",
            url="https://www.youtube.com/watch?v=video2",
            title="Video video2",
            channel="Channel2",
            channel_id="UCvideo2",
            channel_url="https://www.youtube.com/channel/UCvideo2",
            duration=200,
            state=dm.SrcItem.State.WARNING,
            priority=0,
        ),
        dm.SrcItem(
            provider="youtube",
            id="video3",
            url="https://www.youtube.com/watch?v=video3",
            title="Video video3",
            channel="Channel3",
            channel_id="UCvideo3",
            channel_url="https://www.youtube.com/channel/UCvideo3",
            duration=300,
            state=dm.SrcItem.State.NEW,
            priority=0,
        ),
    ])

    # Verify warnings
    await check_warnings(data_manager, [
        dm.Warning(
            provider="youtube",
            id="video1",
            warning_id="too_long",
            message="Duration too long",
            state=dm.Warning.State.OVERRIDDEN,
        ),
        dm.Warning(
            provider="youtube",
            id="video2",
            warning_id="unknown_duration",
            message="Duration unknown",
            state=dm.Warning.State.NEW,
        ),
        dm.Warning(
            provider="youtube",
            id="video3",
            warning_id="too_long",
            message="Duration too long",
            state=dm.Warning.State.OVERRIDDEN,
        ),
    ])


async def test_export_then_clear_workflow(data_manager, tmp_path):
    """Test the complete workflow: export -> edit -> clear"""
    # Add items with warnings
    item1 = make_warning_item("video1", "Channel1", 100)
    warning1 = make_warning("video1", "too_long", "Duration too long")

    item2 = make_warning_item("video2", "Channel2", 200)
    warning2 = make_warning("video2", "unknown_duration", "Duration unknown")

    await data_manager.add_src_item(item1)
    await data_manager.add_warning(warning1)
    await data_manager.add_src_item(item2)
    await data_manager.add_warning(warning2)

    # Step 1: Export warnings
    output_file = tmp_path / "warnings.yml"
    export_args = argparse.Namespace(output=str(output_file), new=False)
    await app.export_warnings(export_args)

    # Step 2: Edit the file (mark video1 for clearing)
    with open(output_file, 'r') as f:
        data = yaml.safe_load(f)

    for item in data:
        if item['id'] == 'video1':
            item['clear'] = True

    with open(output_file, 'w') as f:
        yaml.dump(data, f)

    # Step 3: Clear marked warnings
    clear_args = argparse.Namespace(input=str(output_file))
    await app.clear_warnings(clear_args)

    # Verify only video1 was cleared
    await check_items(data_manager, [
        dm.SrcItem(
            provider="youtube",
            id="video1",
            url="https://www.youtube.com/watch?v=video1",
            title="Video video1",
            channel="Channel1",
            channel_id="UCvideo1",
            channel_url="https://www.youtube.com/channel/UCvideo1",
            duration=100,
            state=dm.SrcItem.State.NEW,
            priority=0,
        ),
        dm.SrcItem(
            provider="youtube",
            id="video2",
            url="https://www.youtube.com/watch?v=video2",
            title="Video video2",
            channel="Channel2",
            channel_id="UCvideo2",
            channel_url="https://www.youtube.com/channel/UCvideo2",
            duration=200,
            state=dm.SrcItem.State.WARNING,
            priority=0,
        ),
    ])
