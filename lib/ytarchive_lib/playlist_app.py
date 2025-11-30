import json
import yt_dlp
import datetime
import logging
import asyncio
from pprint import pprint
from pathlib import Path

import ytarchive_lib.notify as notify
from ytarchive_lib.config import load_config
from ytarchive_lib.data_manager import DataManager, SrcItem, Warning


def get_flat_playlist(playlist_url):
    ydl_opts = {
        'extract_flat': True,  # This option tells yt-dlp to extract only the video URLs, without downloading the videos.
        'dump_single_json': True  # Get the output in a single JSON format.
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(playlist_url, download=False)

    return info_dict


def make_item(entry):
    return SrcItem(
        provider="youtube",
        id=entry["id"],
        url=entry["url"],
        title=entry["title"],
        channel=entry["channel"],
        channel_id=entry["channel_id"],
        channel_url=entry["channel_url"],
        duration=entry["duration"]
    )


def detect_warnings(item: SrcItem):
    if item.duration is None:
        return Warning(
            provider=item.provider,
            id=item.id,
            warning_id="unknown_duration",
            message=f"Item duration is unknown: {item.title}, {item.url}"
        )

    if item.duration > 600:
        return Warning(
            provider=item.provider,
            id=item.id,
            warning_id="too_long",
            message=f"Item duration is too long: {item.duration} seconds, {item.title}, {item.url}"
        )

    return None


async def amain():
    config = load_config()
    #data = {"entries": [{
    #    "id": "vROdVsU_K80",
    #    "url": "https://www.youtube.com/watch?v=vROdVsU_K80",
    #    "title": "The Original Washing Machine Self Destructs",
    #    "channel": "Photonicinduction",
    #    "channel_id": "UCl9OJE9OpXui-gRsnWjSrlA",
    #    "channel_url": "https://www.youtube.com/channel/UCl9OJE9OpXui-gRsnWjSrlA",
    #    "duration": 93
    #}]}
    data = get_flat_playlist(config["SRC_PLAYLIST"])

    async with await DataManager.create(config) as data_manager:
        warnings = []

        async def process_entry(entry):
            item = make_item(entry)

            warning = detect_warnings(item)
            if warning:
                item.state = SrcItem.State.WARNING

            added = await data_manager.add_src_item(item)

            if not added:
                return

            if warning:
                await data_manager.add_warning(warning)
                warnings.append(warning.message)

            logging.info(f"Item added. {item=}, {warning=}")

        await asyncio.gather(*[process_entry(entry) for entry in data["entries"]])

        logging.info("Done")

    if warnings:
        message = "\n".join(warnings)
        notify.send_message(message, config, with_notification=False)

def main():
    asyncio.run(amain())