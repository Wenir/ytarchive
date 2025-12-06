import logging
from ytarchive_lib.warnings_app import main


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


if __name__ == "__main__":
    main()
