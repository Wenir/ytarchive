import json
import yt_dlp
import datetime
from pprint import pprint
from pathlib import Path

import notify
from config import load_config
from data_manager import DataManager, Key


def get_flat_playlist(playlist_url):
    ydl_opts = {
        'extract_flat': True,  # This option tells yt-dlp to extract only the video URLs, without downloading the videos.
        'dump_single_json': True  # Get the output in a single JSON format.
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(playlist_url, download=False)

    return info_dict


def format_item(entry):
    item = {}

    for key in "url", "title", "id", "channel", "channel_id", "channel_url", "duration":
        item[key] = entry[key]

    return item


def add_warning(key, item):
    duration = item["duration"]

    if duration is None:
        item["warning"] = "unknown_duration"

        return f"Item duration is unknown.\n{item}"

    elif duration > 600:
        duration = datetime.timedelta(seconds=item["duration"])
        item["warning"] = "too_long"

        return f"Item duration is too long.\n{duration}, {item["title"]}, {item["url"]}"


if __name__ == "__main__":
    config = load_config()
    data = get_flat_playlist(config["SRC_PLAYLIST"])
    data_manager = DataManager(config)

    existing_objects = set(x.key for x in data_manager.get_all_objects())

    warnings = []
    already_exists = 0

    for entry in data["entries"]:
        item = format_item(entry)

        key = Key.from_playlist_item(item)

        if key in existing_objects:
            already_exists += 1
            continue

        warning = add_warning(key, item)
        if warning:
            warnings.append(warning)
            data_manager.add_warning(key, item)

        data_manager.add_new_object(key, item)

        print(f"Item added. {item}")

    print(f"Done, already exists: {already_exists}")

    if warnings:
        message = "\n".join(warnings)
        notify.send_message(message, config, with_notification=False)


    #  'entries': [{'__x_forwarded_for_ip': None,
    #          '_type': 'url',
    #          'availability': None,
    #          'channel': 'aaa',
    #          'channel_id': 'aaaaaaaaaa-bbbbbbbbbbbbb',
    #          'channel_is_verified': None,
    #          'channel_url': 'https://www.youtube.com/channel/aaaaaaaaaa-bbbbbbbbbbbbb',
    #          'description': None,
    #          'duration': 203,
    #          'id': 'vvvvvv',
    #          'ie_key': 'Youtube',
    #          'live_status': None,
    #          'release_timestamp': None,
    #          'thumbnails': [{'height': 94,
    #                          'url': 'https://i.ytimg.com/vi//hqdefault.jpg?sqp=-',
    #                          'width': 168},
    #                         {'height': 110,
    #                          'url': 'https://i.ytimg.com/vi//hqdefault.jpg?sqp=-',
    #                          'width': 196},
    #                         {'height': 138,
    #                          'url': 'https://i.ytimg.com/vi//hqdefault.jpg?sqp=-',
    #                          'width': 246},
    #                         {'height': 188,
    #                          'url': 'https://i.ytimg.com/vi//hqdefault.jpg?sqp=-',
    #                          'width': 336}],
    #          'timestamp': None,
    #          'title': 'title',
    #          'uploader': 'author',
    #          'uploader_id': None,
    #          'uploader_url': None,
    #          'url': 'https://www.youtube.com/watch?v=uuuu-llllll',
    #          'view_count': 123},
