import json
import boto3
import logging
from botocore.exceptions import ClientError
from to_file_like_obj import to_file_like_obj
from enum import StrEnum, auto
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
from typing import BinaryIO
import contextlib
import psycopg
from psycopg.rows import dict_row

from .crypt_v2 import Crypt
from .utils import hash_string
from .db import DB


@dataclass
class SrcItem:
    class State(StrEnum):
        NEW = auto()
        DONE = auto()
        WARNING = auto()
        LEGACY_DONE = auto()

    provider: str
    id: str
    url: str
    title: str
    channel: str
    channel_id: str
    channel_url: str
    duration: int
    state: State = State.NEW
    priority: int = 0

    @classmethod
    async def setup_db(cls, connection: psycopg.Connection):
        async with connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS src_items (
                    provider     TEXT NOT NULL,
                    id           TEXT NOT NULL,
                    url          TEXT,
                    title        TEXT,
                    channel      TEXT,
                    channel_id   TEXT,
                    channel_url  TEXT,
                    duration     INTEGER,
                    state        TEXT DEFAULT 'new',
                    priority     INTEGER,
                    PRIMARY KEY (provider, id)
                );
            """)
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_src_items_state ON src_items(state);
            """)
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_src_items_priority ON src_items(priority);
            """)
            await connection.commit()


@dataclass
class Warning:
    class State(StrEnum):
        NEW = auto()
        OVERRIDDEN = auto()

    provider: str
    id: str
    warning_id: str
    message: str
    state: State = State.NEW

    @classmethod
    async def setup_db(cls, connection: psycopg.Connection):
        async with connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    provider     TEXT NOT NULL,
                    id           TEXT NOT NULL,
                    warning_id   TEXT,
                    message      TEXT,
                    state        TEXT DEFAULT 'new',
                    PRIMARY KEY (provider, id)
                );
            """)
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_warnings_state ON warnings(state);
            """)
            await connection.commit()


@dataclass
class Playlist:
    url: str

    @classmethod
    async def setup_db(cls, connection: psycopg.Connection):
        async with connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    url          TEXT NOT NULL,
                    PRIMARY KEY (url)
                );
            """)
            await connection.commit()


@dataclass
class VideoMetadata:
    provider: str
    id: str
    chapters: str
    description: str
    raw_data: str

    @classmethod
    async def setup_db(cls, connection: psycopg.Connection):
        async with connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_metadata (
                    provider     TEXT NOT NULL,
                    id           TEXT NOT NULL,
                    chapters     TEXT,
                    description  TEXT,
                    raw_data     TEXT,
                    PRIMARY KEY (provider, id)
                );
            """)
            await connection.commit()


class DataManager:
    @classmethod
    async def create(cls, config):
        self = cls()

        self.s3 = self._create_s3_client(config)
        self.bucket = self.s3.Bucket(config["BUCKET_NAME"])
        self.cryptor = Crypt(
            bytes.fromhex(config["DATA_KEY"]),
            #bytes.fromhex(config["DATA_IV"]),
        )
        self.async_exit_stack = contextlib.AsyncExitStack()
        self.db = await DB.create(config["DB_ACCESS"])

        return self

    async def __aenter__(self):
        await self.async_exit_stack.enter_async_context(self.db)
        await self._init()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.async_exit_stack.aclose()

    async def _init(self):
        await SrcItem.setup_db(self.db.connection)
        await Warning.setup_db(self.db.connection)
        await Playlist.setup_db(self.db.connection)
        await VideoMetadata.setup_db(self.db.connection)

    async def add_src_item(self, item: SrcItem):
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("""
                    INSERT INTO src_items (provider, id, url, title, channel, channel_id, channel_url, duration, state, priority)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (provider, id) DO NOTHING
                    RETURNING 1;
                """, (
                    item.provider,
                    item.id,
                    item.url,
                    item.title,
                    item.channel,
                    item.channel_id,
                    item.channel_url,
                    item.duration,
                    str(item.state),
                    item.priority,
                )
            )

            inserted = await cursor.fetchone()
            await self.db.connection.commit()
            return inserted is not None

    async def add_warning(self, warning: Warning):
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO warnings (provider, id, warning_id, message, state)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (provider, id) DO NOTHING
                RETURNING 1;
            """, (
                warning.provider,
                warning.id,
                warning.warning_id,
                warning.message,
                str(warning.state),
            ))

            inserted = await cursor.fetchone()
            await self.db.connection.commit()
            return inserted is not None

    async def add_playlist(self, playlist: Playlist):
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO playlists (url)
                VALUES (%s)
                ON CONFLICT (url) DO NOTHING
                RETURNING 1;
            """, (playlist.url,))

            inserted = await cursor.fetchone()
            await self.db.connection.commit()
            return inserted is not None

    async def add_video_metadata(self, metadata: VideoMetadata):
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO video_metadata (provider, id, chapters, description, raw_data)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (provider, id) DO UPDATE
                SET chapters = EXCLUDED.chapters,
                    description = EXCLUDED.description,
                    raw_data = EXCLUDED.raw_data
                RETURNING 1;
            """, (
                metadata.provider,
                metadata.id,
                metadata.chapters,
                metadata.description,
                metadata.raw_data,
            ))

            inserted = await cursor.fetchone()
            await self.db.connection.commit()
            return inserted is not None

    async def get_playlists(self):
        async with self.db.connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute("""
                SELECT url FROM playlists;
            """)

            async for row in cursor:
                yield Playlist(url=row['url'])

    async def get_src_items_by_state(self, state: SrcItem.State):
        async with self.db.connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute("""
                SELECT provider, id, url, title, channel, channel_id, channel_url, duration, state, priority
                FROM src_items
                WHERE state = %s
                ORDER BY priority DESC;
            """, (str(state),))

            async for row in cursor:
                yield self._create_src_item(row)

    async def mark_as_done(self, provider: str, id: str):
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("""
                UPDATE src_items
                SET state = %s
                WHERE provider = %s AND id = %s;
            """, (
                str(SrcItem.State.DONE),
                provider,
                id,
            ))

            await self.db.connection.commit()

    async def get_warnings(self, state: Warning.State = None):
        """Get warnings with associated src_item data"""
        async with self.db.connection.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT
                    w.provider as w_provider, w.id as w_id, w.warning_id, w.message, w.state as w_state,
                    s.provider, s.id, s.url, s.title, s.channel, s.channel_id, s.channel_url,
                    s.duration, s.state, s.priority
                FROM warnings as w
                LEFT JOIN src_items as s ON w.provider = s.provider AND w.id = s.id
            """
            params = []

            if state is not None:
                query += " WHERE w.state = %s"
                params.append(str(state))

            query += " ORDER BY w.provider, w.id"

            await cursor.execute(query, params)

            async for row in cursor:
                warning = Warning(
                    provider=row['w_provider'],
                    id=row['w_id'],
                    warning_id=row['warning_id'],
                    message=row['message'],
                    state=Warning.State(row['w_state']),
                )

                src_item = None
                if row['url'] is not None:
                    src_item = self._create_src_item(row)

                yield (warning, src_item)

    async def clear_warning(self, provider: str, id: str):
        """Clear a warning by marking src_item as NEW and warning as OVERRIDDEN"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("""
                UPDATE src_items
                SET state = %s
                WHERE provider = %s AND id = %s AND state = %s;
            """, (
                str(SrcItem.State.NEW),
                provider,
                id,
                str(SrcItem.State.WARNING),
            ))

            await cursor.execute("""
                UPDATE warnings
                SET state = %s
                WHERE provider = %s AND id = %s;
            """, (
                str(Warning.State.OVERRIDDEN),
                provider,
                id,
            ))

            await self.db.connection.commit()

    def upload_file(self, provider: str, id: str, file: BinaryIO):
        def gen():
            while chunk := file.read(1024):
                yield chunk

        encrypted = to_file_like_obj(self.cryptor.encrypt(gen()))

        key = hash_string(f"{provider}:{id}")
        logging.info(f"Uploading file to archive/{key}")

        obj = self.bucket.Object(f"archive/{key}")

        res = obj.upload_fileobj(
            encrypted,
            ExtraArgs={"Tagging": "archive=true"},
            Config=boto3.s3.transfer.TransferConfig(
                multipart_chunksize=128 * 1024 * 1024,
                #multipart_threshold=128 * 1024 * 1024,
            ),
        )
        logging.info(f"Uploaded to bucket with status {res}")

        res = obj.wait_until_exists()
        logging.info(f"Wait status {res}")

    def download_file(self, provider: str, id: str) -> BinaryIO:
        key = hash_string(f"{provider}:{id}")

        obj = self.bucket.Object(f"archive/{key}")

        resp = obj.get()
        body = resp["Body"]

        return self.cryptor.decrypt(body.iter_chunks(chunk_size=1024 * 1024))

    def _create_s3_client(self, config):
        session = boto3.Session(
            region_name=config["REGION"],
            aws_access_key_id=config["ACCESS_KEY"],
            aws_secret_access_key=config["SECRET_KEY"],
        )

        resource = session.resource(
            's3',
            endpoint_url=config["API_ENDPOINT"],
        )

        return resource

    def _create_src_item(self, row) -> SrcItem:
        return SrcItem(
            provider=row['provider'],
            id=row['id'],
            url=row['url'],
            title=row['title'],
            channel=row['channel'],
            channel_id=row['channel_id'],
            channel_url=row['channel_url'],
            duration=row['duration'],
            state=SrcItem.State(row['state']),
            priority=row['priority'],
        )
