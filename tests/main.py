import sys
import pytest

def main():
    # "--trace-config", "-o", "cache-dir=/dev/null"
    sys.exit(pytest.main(["--log-cli-level=INFO"] + sys.argv[1:]))