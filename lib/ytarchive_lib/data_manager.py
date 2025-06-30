import json
import boto3
from botocore.exceptions import ClientError
from to_file_like_obj import to_file_like_obj
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
from typing import BinaryIO

from .crypt import Crypt
from .utils import hash_string


@dataclass(frozen=True)
class Key:
    key: str

    @classmethod
    def from_id(cls, id):
        return cls(hash_string(id))

    @classmethod
    def from_playlist_item(cls, item):
        return cls.from_id(item["id"])


@dataclass
class Object:
    key: Key
    types: set[str]


class DataManager:
    def __init__(self, config):
        self.s3 = self._create_s3_client(config)
        self.bucket = self.s3.Bucket(config["BUCKET_NAME"])
        self.cryptor = Crypt(
            bytes.fromhex(config["DATA_KEY"]),
            bytes.fromhex(config["DATA_IV"]),
        )

        self.NEW = "new"
        self.ALL = "all"
        self.DONE = "done"
        self.WARNING = "warning"

    def get_objects(self):
        result = {}

        for obj in self.bucket.objects.all():
            path = Path(obj.key)

            obj_type = path.parts[0]
            key = Key(path.parts[1])

            if key.key not in result:
                result[key.key] = Object(key, set())

            result[key.key].types.add(obj_type)

        return result.values()

    def get_objects_by_type(self, type):
        result = []

        for obj in self.get_objects():
            if type in obj.types:
                result.append(obj)

        return result

    def get_all_objects(self):
        return self.get_objects_by_type("all")

    def get_new_objects(self):
        return self.get_objects_by_type("new")

    def add_new_object(self, key: Key, metadata: dict):
        body = b"".join(self.cryptor.encrypt([json.dumps(metadata).encode()]))

        self.bucket.put_object(
            Key=f"{self.NEW}/{key.key}",
            Body=body,
        )
        self.bucket.put_object(
            Key=f"{self.ALL}/{key.key}",
            Body=body,
        )

    def add_warning(self, key: Key, metadata: dict):
        body = b"".join(self.cryptor.encrypt([json.dumps(metadata).encode()]))

        self.bucket.put_object(
            Key=f"{self.WARNING}/{key.key}",
            Body=body,
        )

    def mark_as_done(self, key: Key):
        obj = self.bucket.Object(f"{self.NEW}/{key.key}")
        obj.delete()

    def load_metadata(self, key: Key):
        obj = self.bucket.Object(f"{self.ALL}/{key.key}")
        encrypted = obj.get()["Body"].read()
        return json.loads(b"".join(self.cryptor.decrypt([encrypted])).decode())

    def upload_file(self, key: Key, file: BinaryIO):
        def gen():
            while chunk := file.read(1024):
                yield chunk

        encrypted = to_file_like_obj(self.cryptor.encrypt(gen()))

        obj = self.bucket.Object(f"{self.DONE}/{key.key}")

        res = obj.upload_fileobj(encrypted, ExtraArgs={"Tagging": "archive=true"})
        print(f"Uploaded to bucket with status {res}")

        res = obj.wait_until_exists()
        print(f"Wait status {res}")

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
