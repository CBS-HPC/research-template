from __future__ import annotations

import os
from .compat import PROJECT_ROOT
from .normalize import create_or_update_dmp_from_schema

def main() -> None:
    os.chdir(PROJECT_ROOT)
    create_or_update_dmp_from_schema()

if __name__ == "__main__":
    main()
