import logging
from ytarchive_lib.download_app import main


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


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