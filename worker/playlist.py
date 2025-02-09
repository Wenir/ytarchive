import json
import yt_dlp
from pprint import pprint
from pathlib import Path

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

    for key in "url", "title", "id", "channel", "channel_id", "channel_url":
        item[key] = entry[key]

    return item


if __name__ == "__main__":
    config = load_config()
    data = get_flat_playlist(config["SRC_PLAYLIST"])
    data_manager = DataManager(config)

    existing_objects = set(x.key for x in data_manager.get_all_objects())

    for entry in data["entries"]:
        item = format_item(entry)

        key = Key.from_playlist_item(item)

        if key in existing_objects:
            print(f"Item already exists. {item}")
            continue

        data_manager.add_new_object(key, item)

        print(f"Item added. {item}")

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
