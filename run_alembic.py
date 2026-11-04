import sys
from alembic.config import CommandLine

try:
    args = sys.argv[1:] if len(sys.argv) > 1 else ["upgrade", "head"]
    CommandLine().main(argv=args)
    print("ALEMBIC_SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()

