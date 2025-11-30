import pytest
import copy
import os
import json
import yt_dlp
import ytarchive_lib.playlist_app as app
import ytarchive_lib.data_manager as dm
import ytarchive_lib.notify as notify
import logging
from conftest import check_items


@pytest.fixture(scope="function", autouse=True)
def enable_bucket_cleanup(bucket_cleanup):
    yield


@pytest.fixture(scope="function", autouse=True)
def enable_db_cleanup(db_cleanup):
    yield


MOCK_PLAYLIST_DATA = {
    "entries": [
        {
            "id": "vROdVsU_K80",
            "url": "https://www.youtube.com/watch?v=vROdVsU_K80",
            "title": "The Original Washing Machine Self Destructs",
            "channel": "Photonicinduction",
            "channel_id": "UCl9OJE9OpXui-gRsnWjSrlA",
            "channel_url": "https://www.youtube.com/channel/UCl9OJE9OpXui-gRsnWjSrlA",
            "duration": 93
        },
        {
            "id": "ey_UIU8E_Go",
            "url": "https://www.youtube.com/watch?v=ey_UIU8E_Go",
            "title": "[Deleted video]",
            "channel": None,
            "channel_id": None,
            "channel_url": None,
            "duration": None
        },
        {
            "id": "y8Kyi0WNg40",
            "url": "https://www.youtube.com/watch?v=y8Kyi0WNg40",
            "title": "Dramatic Look",
            "channel": "magnets99",
            "channel_id": "UCYHyU6eGm4V2qjI_Sz4DO3A",
            "channel_url": "https://www.youtube.com/channel/UCYHyU6eGm4V2qjI_Sz4DO3A",
            "duration": 6
        }
    ]
}


def mock_youtube_dl(data):
    class MockYoutubeDL:
        def __init__(self, ydl_opts):
            self.ydl_opts = ydl_opts

        def extract_info(self, url, download=False):
            assert url == os.environ["TESTS_SRC_PLAYLIST"]
            return data

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockYoutubeDL


class MockNotify:
    def __init__(self):
        self.calls = []

    def send_message(self, message, config, with_notification=False):
        self.calls.append({
            'message': message,
            'with_notification': with_notification
        })
        logging.info(f"Mock notification called: {message} (with_notification={with_notification})")


async def test_from_scratch(data_manager, monkeypatch):
    mock_notify = MockNotify()
    monkeypatch.setattr(notify, "send_message", mock_notify.send_message)
    monkeypatch.setattr(yt_dlp, "YoutubeDL", mock_youtube_dl(MOCK_PLAYLIST_DATA))

    await app.amain()

    assert mock_notify.calls == [
        {
            'message': 'Item duration is unknown: [Deleted video], https://www.youtube.com/watch?v=ey_UIU8E_Go',
            'with_notification': False,
        },
    ]

    await check_items(
        data_manager,
        [
            dm.SrcItem(
                provider="youtube",
                id="vROdVsU_K80",
                url="https://www.youtube.com/watch?v=vROdVsU_K80",
                title="The Original Washing Machine Self Destructs",
                channel="Photonicinduction",
                channel_id="UCl9OJE9OpXui-gRsnWjSrlA",
                channel_url="https://www.youtube.com/channel/UCl9OJE9OpXui-gRsnWjSrlA",
                duration=93,
                state=dm.SrcItem.State.NEW,
                priority=0,
            ),
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
            ),
            dm.SrcItem(
                provider="youtube",
                id="ey_UIU8E_Go",
                url="https://www.youtube.com/watch?v=ey_UIU8E_Go",
                title="[Deleted video]",
                channel=None,
                channel_id=None,
                channel_url=None,
                duration=None,
                state=dm.SrcItem.State.WARNING,
                priority=0,
            ),
        ],
    )


async def test_add_missing(data_manager, monkeypatch):
    mock_notify = MockNotify()
    monkeypatch.setattr(notify, "send_message", mock_notify.send_message)
    monkeypatch.setattr(yt_dlp, "YoutubeDL", mock_youtube_dl(MOCK_PLAYLIST_DATA))

    await data_manager.add_src_item(
        dm.SrcItem(
            provider="youtube",
            id="vROdVsU_K80",
            url="https://www.youtube.com/watch?v=vROdVsU_K80",
            title="The Original Washing Machine Self Destructs",
            channel="Photonicinduction",
            channel_id="UCl9OJE9OpXui-gRsnWjSrlA",
            channel_url="https://www.youtube.com/channel/UCl9OJE9OpXui-gRsnWjSrlA",
            duration=93,
            state=dm.SrcItem.State.DONE,
            priority=0,
        )
    )
    await data_manager.add_src_item(
        dm.SrcItem(
            provider="youtube",
            id="ey_UIU8E_Go",
            url="https://www.youtube.com/watch?v=ey_UIU8E_Go",
            title="[Deleted video]",
            channel=None,
            channel_id=None,
            channel_url=None,
            duration=None,
            state=dm.SrcItem.State.WARNING,
            priority=0,
        )
    )
    #await data_manager.add_warning(
    #    dm.Warning(
    #        provider="youtube",
    #        id="ey_UIU8E_Go",
    #        warning_id="unknown_duration",
    #        message="Item duration is unknown: [Deleted video], https://www.youtube.com/watch?v=ey_UIU8E_Go",
    #        state=dm.Warning.State.NEW,
    #    )
    #)

    await app.amain()

    assert mock_notify.calls == []

    await check_items(
        data_manager,
        [
            dm.SrcItem(
                provider="youtube",
                id="vROdVsU_K80",
                url="https://www.youtube.com/watch?v=vROdVsU_K80",
                title="The Original Washing Machine Self Destructs",
                channel="Photonicinduction",
                channel_id="UCl9OJE9OpXui-gRsnWjSrlA",
                channel_url="https://www.youtube.com/channel/UCl9OJE9OpXui-gRsnWjSrlA",
                duration=93,
                state=dm.SrcItem.State.DONE,
                priority=0,
            ),
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
            ),
            dm.SrcItem(
                provider="youtube",
                id="ey_UIU8E_Go",
                url="https://www.youtube.com/watch?v=ey_UIU8E_Go",
                title="[Deleted video]",
                channel=None,
                channel_id=None,
                channel_url=None,
                duration=None,
                state=dm.SrcItem.State.WARNING,
                priority=0,
            ),
        ],
    )


async def test_add_legacy_done(data_manager, monkeypatch, print_bucket, print_db):
    data = copy.deepcopy(MOCK_PLAYLIST_DATA)
    data["entries"] = [data["entries"][0]]

    mock_notify = MockNotify()
    monkeypatch.setattr(notify, "send_message", mock_notify.send_message)
    monkeypatch.setattr(yt_dlp, "YoutubeDL", mock_youtube_dl(data))

    await data_manager.add_src_item(
        dm.SrcItem(
            provider="youtube",
            id="vROdVsU_K80",
            url="https://www.youtube.com/watch?v=vROdVsU_K80",
            title="The Original Washing Machine Self Destructs",
            channel="Photonicinduction",
            channel_id="UCl9OJE9OpXui-gRsnWjSrlA",
            channel_url="https://www.youtube.com/channel/UCl9OJE9OpXui-gRsnWjSrlA",
            duration=93,
            state=dm.SrcItem.State.LEGACY_DONE,
            priority=0,
        )
    )

    await app.amain()

    assert mock_notify.calls == []

    await check_items(
        data_manager,
        [
            dm.SrcItem(
                provider="youtube",
                id="vROdVsU_K80",
                url="https://www.youtube.com/watch?v=vROdVsU_K80",
                title="The Original Washing Machine Self Destructs",
                channel="Photonicinduction",
                channel_id="UCl9OJE9OpXui-gRsnWjSrlA",
                channel_url="https://www.youtube.com/channel/UCl9OJE9OpXui-gRsnWjSrlA",
                duration=93,
                state=dm.SrcItem.State.LEGACY_DONE,
                priority=0,
            ),
        ],
    )


async def test_add_warning_too_long(data_manager, monkeypatch, print_bucket, print_db):
    data = copy.deepcopy(MOCK_PLAYLIST_DATA)
    data["entries"] = [data["entries"][0]]
    data["entries"][0]["duration"] = 7000  # too long

    mock_notify = MockNotify()
    monkeypatch.setattr(notify, "send_message", mock_notify.send_message)
    monkeypatch.setattr(yt_dlp, "YoutubeDL", mock_youtube_dl(data))

    await app.amain()

    assert mock_notify.calls == [
        {
            'message': 'Item duration is too long: 7000 seconds, The Original Washing Machine Self Destructs, https://www.youtube.com/watch?v=vROdVsU_K80',
            'with_notification': False,
        },
    ]

    await check_items(
        data_manager,
        [
            dm.SrcItem(
                provider="youtube",
                id="vROdVsU_K80",
                url="https://www.youtube.com/watch?v=vROdVsU_K80",
                title="The Original Washing Machine Self Destructs",
                channel="Photonicinduction",
                channel_id="UCl9OJE9OpXui-gRsnWjSrlA",
                channel_url="https://www.youtube.com/channel/UCl9OJE9OpXui-gRsnWjSrlA",
                duration=7000,
                state=dm.SrcItem.State.WARNING,
                priority=0,
            ),
        ],
    )


EXAMPLE_DATA = json.loads("""
{
    "id": "PLs6f7LuYcgtn1IeWz1is9AXZd46F4V6qu",
    "title": "test_archive",
    "availability": "unlisted",
    "channel_follower_count": null,
    "description": "",
    "tags": [],
    "thumbnails": [
        {
            "url": "https://i.ytimg.com/vi/vROdVsU_K80/hqdefault.jpg?sqp=-oaymwEWCKgBEF5IWvKriqkDCQgBFQAAiEIYAQ==&rs=AOn4CLBHaONKKRvTqepGWINuHYIRGP8heQ",
            "height": 94,
            "width": 168,
            "id": "0",
            "resolution": "168x94"
        },
        {
            "url": "https://i.ytimg.com/vi/vROdVsU_K80/hqdefault.jpg?sqp=-oaymwEWCMQBEG5IWvKriqkDCQgBFQAAiEIYAQ==&rs=AOn4CLDn1UsteHH_OU0bfHWBOnU0EC5PlQ",
            "height": 110,
            "width": 196,
            "id": "1",
            "resolution": "196x110"
        },
        {
            "url": "https://i.ytimg.com/vi/vROdVsU_K80/hqdefault.jpg?sqp=-oaymwEXCPYBEIoBSFryq4qpAwkIARUAAIhCGAE=&rs=AOn4CLAHDzbfMPKTF665GNsT0rHXyu8J8Q",
            "height": 138,
            "width": 246,
            "id": "2",
            "resolution": "246x138"
        },
        {
            "url": "https://i.ytimg.com/vi/vROdVsU_K80/hqdefault.jpg?sqp=-oaymwEXCNACELwBSFryq4qpAwkIARUAAIhCGAE=&rs=AOn4CLDWksQluJORFHh_duGZyFW3togwYw",
            "height": 188,
            "width": 336,
            "id": "3",
            "resolution": "336x188"
        }
    ],
    "modified_date": "20251130",
    "view_count": null,
    "playlist_count": 3,
    "channel": "Wenir",
    "channel_id": "UC5aH0RlX9IpzaPHu7L3qGWA",
    "uploader_id": "@WenirR",
    "uploader": "Wenir",
    "channel_url": "https://www.youtube.com/channel/UC5aH0RlX9IpzaPHu7L3qGWA",
    "uploader_url": "https://www.youtube.com/@WenirR",
    "_type": "playlist",
    "entries": [
        {
            "_type": "url",
            "ie_key": "Youtube",
            "id": "vROdVsU_K80",
            "url": "https://www.youtube.com/watch?v=vROdVsU_K80",
            "title": "The Original Washing Machine Self Destructs",
            "description": null,
            "duration": 93,
            "channel_id": "UCl9OJE9OpXui-gRsnWjSrlA",
            "channel": "Photonicinduction",
            "channel_url": "https://www.youtube.com/channel/UCl9OJE9OpXui-gRsnWjSrlA",
            "uploader": "Photonicinduction",
            "uploader_id": "@Photonicinduction",
            "uploader_url": "https://www.youtube.com/@Photonicinduction",
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/vROdVsU_K80/hqdefault.jpg?sqp=-oaymwEbCKgBEF5IVfKriqkDDggBFQAAiEIYAXABwAEG&rs=AOn4CLCeC3cY9JKc51bd3us-1bdl0vHsEw",
                    "height": 94,
                    "width": 168
                },
                {
                    "url": "https://i.ytimg.com/vi/vROdVsU_K80/hqdefault.jpg?sqp=-oaymwEbCMQBEG5IVfKriqkDDggBFQAAiEIYAXABwAEG&rs=AOn4CLA73fPDFwtuyGdb8rrk3uGYdwnUig",
                    "height": 110,
                    "width": 196
                },
                {
                    "url": "https://i.ytimg.com/vi/vROdVsU_K80/hqdefault.jpg?sqp=-oaymwEcCPYBEIoBSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLCIWCbKZRsKAFUAFoQ7y7Mvj63ITg",
                    "height": 138,
                    "width": 246
                },
                {
                    "url": "https://i.ytimg.com/vi/vROdVsU_K80/hqdefault.jpg?sqp=-oaymwEcCNACELwBSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLDKNFGGlxNECN4nuYOo_iTlYnvl1Q",
                    "height": 188,
                    "width": 336
                }
            ],
            "timestamp": null,
            "release_timestamp": null,
            "availability": null,
            "view_count": 5400000,
            "live_status": null,
            "channel_is_verified": null,
            "__x_forwarded_for_ip": null
        },
        {
            "_type": "url",
            "ie_key": "Youtube",
            "id": "ey_UIU8E_Go",
            "url": "https://www.youtube.com/watch?v=ey_UIU8E_Go",
            "title": "[Deleted video]",
            "description": null,
            "duration": null,
            "channel_id": null,
            "channel": null,
            "channel_url": null,
            "uploader": null,
            "uploader_id": null,
            "uploader_url": null,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/img/no_thumbnail.jpg",
                    "height": 90,
                    "width": 120
                },
                {
                    "url": "https://i.ytimg.com/img/no_thumbnail.jpg",
                    "height": 180,
                    "width": 320
                },
                {
                    "url": "https://i.ytimg.com/img/no_thumbnail.jpg",
                    "height": 360,
                    "width": 480
                }
            ],
            "timestamp": null,
            "release_timestamp": null,
            "availability": null,
            "view_count": null,
            "live_status": null,
            "channel_is_verified": null,
            "__x_forwarded_for_ip": null
        },
        {
            "_type": "url",
            "ie_key": "Youtube",
            "id": "y8Kyi0WNg40",
            "url": "https://www.youtube.com/watch?v=y8Kyi0WNg40",
            "title": "Dramatic Look",
            "description": null,
            "duration": 6,
            "channel_id": "UCYHyU6eGm4V2qjI_Sz4DO3A",
            "channel": "magnets99",
            "channel_url": "https://www.youtube.com/channel/UCYHyU6eGm4V2qjI_Sz4DO3A",
            "uploader": "magnets99",
            "uploader_id": "@magnets9999",
            "uploader_url": "https://www.youtube.com/@magnets9999",
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/y8Kyi0WNg40/hqdefault.jpg?sqp=-oaymwE1CKgBEF5IVfKriqkDKAgBFQAAiEIYAXABwAEG8AEB-AG-AoAC8AGKAgwIABABGEMgTShyMA8=&rs=AOn4CLDPt4iqAPggAVHcZ35JzQdNOOpOYg",
                    "height": 94,
                    "width": 168
                },
                {
                    "url": "https://i.ytimg.com/vi/y8Kyi0WNg40/hqdefault.jpg?sqp=-oaymwE1CMQBEG5IVfKriqkDKAgBFQAAiEIYAXABwAEG8AEB-AG-AoAC8AGKAgwIABABGEMgTShyMA8=&rs=AOn4CLD0v9YCKfTjcuXcWyfwO4Dk4uk6uQ",
                    "height": 110,
                    "width": 196
                },
                {
                    "url": "https://i.ytimg.com/vi/y8Kyi0WNg40/hqdefault.jpg?sqp=-oaymwE2CPYBEIoBSFXyq4qpAygIARUAAIhCGAFwAcABBvABAfgBvgKAAvABigIMCAAQARhDIE0ocjAP&rs=AOn4CLC8KsOgAXggZQqzWq8ml5evS6fM4g",
                    "height": 138,
                    "width": 246
                },
                {
                    "url": "https://i.ytimg.com/vi/y8Kyi0WNg40/hqdefault.jpg?sqp=-oaymwE2CNACELwBSFXyq4qpAygIARUAAIhCGAFwAcABBvABAfgBvgKAAvABigIMCAAQARhDIE0ocjAP&rs=AOn4CLCVsqQubR3uVClok2XpPHScx2mRDg",
                    "height": 188,
                    "width": 336
                }
            ],
            "timestamp": null,
            "release_timestamp": null,
            "availability": null,
            "view_count": 47000000,
            "live_status": null,
            "channel_is_verified": null,
            "__x_forwarded_for_ip": null
        }
    ],
    "extractor_key": "YoutubeTab",
    "extractor": "youtube:tab",
    "webpage_url": "https://www.youtube.com/playlist?list=PLs6f7LuYcgtn1IeWz1is9AXZd46F4V6qu",
    "original_url": "https://www.youtube.com/playlist?list=PLs6f7LuYcgtn1IeWz1is9AXZd46F4V6qu",
    "webpage_url_basename": "playlist",
    "webpage_url_domain": "youtube.com",
    "release_year": null,
    "epoch": 1764523449
}""")
