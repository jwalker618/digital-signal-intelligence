"""Enable ``python -m seed`` to dispatch to the CLI."""
from seed.cli import main
import sys

if __name__ == "__main__":
    sys.exit(main())
