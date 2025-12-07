import pytest
import io
import os
import zipfile
import yt_dlp
import ytarchive_lib.download_app as app
import ytarchive_lib.data_manager as dm
import logging
import json
from psycopg.rows import dict_row
from pathlib import Path
from conftest import check_items


@pytest.fixture(scope="function", autouse=True)
def enable_bucket_cleanup(bucket_cleanup):
    yield


@pytest.fixture(scope="function", autouse=True)
def enable_db_cleanup(db_cleanup):
    yield


class MockYoutubeDL:
    def __init__(self, ydl_opts):
        self.ydl_opts = ydl_opts

    def extract_info(self, url, download=True):
        download_folder = self.ydl_opts['paths']['home']
        Path(download_folder).mkdir(parents=True, exist_ok=True)

        video_info = {
            'id': 'y8Kyi0WNg40',
            'title': 'Dramatic Look',
            'ext': 'mp4',
            'duration': 6,
            'channel': 'magnets99',
            'channel_id': 'UCYHyU6eGm4V2qjI_Sz4DO3A',
            'description': 'A dramatic look',
            'chapters': [
                {'start_time': 0, 'end_time': 3, 'title': 'First Half'},
                {'start_time': 3, 'end_time': 6, 'title': 'Second Half'}
            ],
        }

        base_filename = f"{video_info['title']} [{video_info['id']}]"

        video_file = Path(download_folder) / f"{base_filename}.{video_info['ext']}"
        video_file.write_bytes(b"fake video content")

        if self.ydl_opts.get('writeinfojson'):
            info_file = Path(download_folder) / f"{base_filename}.info.json"
            info_file.write_text(json.dumps(video_info))

        if self.ydl_opts.get('writedescription'):
            desc_file = Path(download_folder) / f"{base_filename}.description"
            desc_file.write_text(video_info['description'])

        if self.ydl_opts.get('writethumbnail'):
            thumb_file = Path(download_folder) / f"{base_filename}.jpg"
            thumb_file.write_bytes(b"fake thumbnail")

        return video_info

    def sanitize_info(self, info):
        return info

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


async def test_download(data_manager, monkeypatch, print_bucket, print_db):
    monkeypatch.setattr(yt_dlp, "YoutubeDL", MockYoutubeDL)

    await data_manager.add_src_item(
        dm.SrcItem(
            provider="youtube",
            id="y8Kyi0WNg40",
            url="https://www.youtube.com/watch?v=y8Kyi0WNg40",
            title="Dramatic Look",
            channel="magnets99",
            channel_id="UCYHyU6eGm4V2qjI_Sz4DO3A",
            channel_url="https://www.youtube.com/channel/UCYHyU6eGm4V2qjI_Sz4DO3A",
            duration=6,
            state=dm.SrcItem.State.NEW,
            priority=0,
        )
    )

    await app.amain()

    await check_items(
        data_manager,
        [
            dm.SrcItem(
                provider="youtube",
                id="y8Kyi0WNg40",
                url="https://www.youtube.com/watch?v=y8Kyi0WNg40",
                title="Dramatic Look",
                channel="magnets99",
                channel_id="UCYHyU6eGm4V2qjI_Sz4DO3A",
                channel_url="https://www.youtube.com/channel/UCYHyU6eGm4V2qjI_Sz4DO3A",
                duration=6,
                state=dm.SrcItem.State.DONE,
                priority=0,
            ),
        ],
    )

    archive = b"".join(data_manager.download_file("youtube", "y8Kyi0WNg40"))

    assert archive.startswith(b"PK\x03\x04")  # ZIP file signature

    bio = io.BytesIO(archive)
    with zipfile.ZipFile(bio, "r") as zip_ref:
        filenames = zip_ref.namelist()
        assert len(filenames) == 5

        assert "Dramatic Look [y8Kyi0WNg40].mp4" in filenames
        assert "Dramatic Look [y8Kyi0WNg40].info.json" in filenames
        assert "Dramatic Look [y8Kyi0WNg40].description" in filenames
        assert "Dramatic Look [y8Kyi0WNg40].jpg" in filenames
        assert "src_item.json" in filenames

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

    chapters = json.loads(row['chapters'])
    assert len(chapters) == 2
    assert chapters[0]['title'] == 'First Half'
    assert chapters[1]['title'] == 'Second Half'

    assert row['description'] == "A dramatic look"

    raw_data = json.loads(row['raw_data'])
    assert raw_data['title'] == "Dramatic Look"
    assert raw_data['duration'] == 6
    assert 'chapters' in raw_data
