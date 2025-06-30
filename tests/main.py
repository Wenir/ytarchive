import sys
import pytest

def main():
    # "--trace-config", "-o", "cache-dir=/dev/null"
    sys.exit(pytest.main([] + sys.argv[1:]))