"""Allow running as: python -m dspng"""

try:
    from .main import main
except ImportError:
    from dspng.main import main

raise SystemExit(main())
