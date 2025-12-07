import os
import logging
import json
import yt_dlp
import random
import shutil
import zipfile
import asyncio
from pathlib import Path
from dataclasses import asdict
from pprint import pprint

from ytarchive_lib.config import load_config
from ytarchive_lib.data_manager import DataManager, SrcItem, VideoMetadata

DOWNLOAD_FOLDER = "/tmp/ytarchive"


def download(url):
    if shutil.which("ffmpeg") is None:
        raise Exception("FFmpeg is not installed or not found in PATH. This operation requires FFmpeg.")

    shutil.rmtree(DOWNLOAD_FOLDER, ignore_errors=True)

    ydl_opts = {
        'allsubtitles': True,
        'extract_flat': 'discard_in_playlist',
        'fragment_retries': 10,
        'ignoreerrors': False,
        'paths': {'home': DOWNLOAD_FOLDER},
        'postprocessors': [
            {
                'key': 'FFmpegConcat',
                'only_multi_video': True,
                'when': 'playlist'
            }
        ],
        'retries': 10,
        'writeannotations': True,
        'writedescription': True,
        'writeinfojson': True,
        'writesubtitles': True,
        'writethumbnail': True,
        'outtmpl': '%(title).150B [%(id)s].%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        #ydl.download([url])
        info = ydl.extract_info(url)

        info = ydl.sanitize_info(info)
        #pprint(info)

        return info


def archive_files(archive_path):
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(DOWNLOAD_FOLDER):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.relpath(file_path, DOWNLOAD_FOLDER))


async def get_possible_items(data_manager):
    new_items = []
    async for item in data_manager.get_src_items_by_state(SrcItem.State.NEW):
        new_items.append(item)

    logging.info(f"Found {len(new_items)} NEW items")

    if new_items:
        priority = new_items[0].priority
        new_items = [item for item in new_items if item.priority == priority]

    logging.info(f"Found {len(new_items)} prioritized items")
    return new_items


async def amain():
    config = load_config()

    async with await DataManager.create(config) as data_manager:
        new_items = await get_possible_items(data_manager)

        if not new_items:
            logging.info("No items to download")
            return

        selected_item = random.choice(new_items)
        logging.info(f"Selected item: {selected_item}")

        info = download(selected_item.url)

        video_metadata = VideoMetadata(
            provider=selected_item.provider,
            id=selected_item.id,
            chapters=json.dumps(info.get('chapters', [])),
            description=info.get('description', ""),
            raw_data=json.dumps(info),
        )
        await data_manager.add_video_metadata(video_metadata)
        logging.info(f"Stored video metadata for: {selected_item.title}")

        with open(Path(DOWNLOAD_FOLDER) / "src_item.json", "w") as f:
            json.dump(asdict(selected_item), f, default=str)

        archive = "/tmp/.files.zip"
        archive_files(archive)

        with open(archive, "rb") as f:
            data_manager.upload_file(selected_item.provider, selected_item.id, f)

        await data_manager.mark_as_done(selected_item.provider, selected_item.id)

        logging.info(f"Successfully processed item: {selected_item.title}")


def main():
    asyncio.run(amain())
