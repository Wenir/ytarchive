import os
import argparse
from ytarchive_lib.crypt import Crypt


def parse_args():
    parser = argparse.ArgumentParser(description="Decrypt data")

    parser.add_argument("file", type=argparse.FileType("rb"), help="File to decrypt")
    parser.add_argument("output", type=argparse.FileType("wb"), help="Output file")

    return parser.parse_args()


def main():
    key = bytes.fromhex(os.environ["TF_VAR_data_key"])
    iv = bytes.fromhex(os.environ["TF_VAR_data_iv"])

    crypt = Crypt(key, iv)
    args = parse_args()

    with args.file as f:
        def gen():
            while chunk := f.read(1024):
                yield chunk

        decrypted_data = crypt.decrypt(gen())

        for chunk in decrypted_data:
            args.output.write(chunk)


if __name__ == "__main__":
    main()
