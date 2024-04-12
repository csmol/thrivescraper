import sys
from .thrive import main

rc = 1
try:
    rc = main()
except Exception as e:
    print("Error: %s" % e, file=sys.stderr)
sys.exit(rc)
