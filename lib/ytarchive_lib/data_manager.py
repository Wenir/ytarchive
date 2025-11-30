import json
import boto3
from botocore.exceptions import ClientError
from to_file_like_obj import to_file_like_obj
from enum import StrEnum, auto
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
from typing import BinaryIO
import contextlib
import psycopg

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

    async def get_src_items_by_state(self, state: SrcItem.State):
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("""
                SELECT provider, id, url, title, channel, channel_id, channel_url, duration, state, priority
                FROM src_items
                WHERE state = %s
                ORDER BY priority DESC;
            """, (str(state),))

            async for row in cursor:
                yield SrcItem(
                    provider=row[0],
                    id=row[1],
                    url=row[2],
                    title=row[3],
                    channel=row[4],
                    channel_id=row[5],
                    channel_url=row[6],
                    duration=row[7],
                    state=SrcItem.State(row[8]),
                    priority=row[9],
                )

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

    def upload_file(self, provider: str, id: str, file: BinaryIO):
        def gen():
            while chunk := file.read(1024):
                yield chunk

        encrypted = to_file_like_obj(self.cryptor.encrypt(gen()))

        key = hash_string(f"{provider}:{id}")

        obj = self.bucket.Object(f"archive/{key}")

        res = obj.upload_fileobj(encrypted, ExtraArgs={"Tagging": "archive=true"})
        print(f"Uploaded to bucket with status {res}")

        res = obj.wait_until_exists()
        print(f"Wait status {res}")

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
