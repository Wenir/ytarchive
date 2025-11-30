import logging
from ytarchive_lib.playlist_app import main


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


if __name__ == "__main__":
    main()

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
