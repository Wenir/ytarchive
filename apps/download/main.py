import os
import json
import yt_dlp
import random
import shutil
import zipfile
from pprint import pprint
from pathlib import Path


from ytarchive_lib.config import load_config
from ytarchive_lib.data_manager import DataManager, Key

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

        return info


def archive_files(archive_path):
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(DOWNLOAD_FOLDER):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.relpath(file_path, DOWNLOAD_FOLDER))


def get_possible_objects(data_manager):
    new_objects = data_manager.get_new_objects()
    filtered = list(filter(lambda x: data_manager.WARNING not in x.types, new_objects))

    print(f"Unprocessed objects: {len(new_objects)}, objects with warnings: {len(new_objects) - len(filtered)}")

    return filtered


def main():
    config = load_config()
    data_manager = DataManager(config)

    new_objects = get_possible_objects(data_manager)

    if not new_objects:
        return

    selected_object = random.choice(new_objects)
    print(f"Selected object: {selected_object}")

    item = data_manager.load_metadata(selected_object.key)
    print(f"Item: {item}")

    download(item["url"])

    with open(Path(DOWNLOAD_FOLDER) / "playlist_item.json", "w") as f:
        json.dump(item, f)

    arhive = ".files.zip"
    archive_files(arhive)
    with open(arhive, "rb") as f:
        data_manager.upload_file(selected_object.key, f)

    data_manager.mark_as_done(selected_object.key)


if __name__ == "__main__":
    main()

    #download("https://www.youtube.com/watch?v=MV9KPhbpAjI")

    # keys = ["url", "title", "id", "channel", "channel_id", "channel_url"]


    #for entry in data["entries"]:
    #    item = {}
    #    for key in "url", "title", "id", "channel", "channel_id", "channel_url":
    #        item[key] = entry[key]

    #    if item["id"] in existing_objects:
    #        print(f"Item already exists. {item}")
    #        continue

    #    bucket.put_object(Key=f"all/{item['id']}", Body=json.dumps(item))
    #    bucket.put_object(Key=f"new/{item['id']}", Body=json.dumps(item))

    #    print(f"Item added. {item}")