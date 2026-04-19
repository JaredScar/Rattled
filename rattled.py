#!/usr/bin/env python
#
# Rattled Programming Language — root-level launcher
#
# Run from the repo root:
#   python rattled.py <file.ry>
#   python rattled.py <file.ry> --emit-python
#   python rattled.py <file.ry> --check
#   python rattled.py                        (REPL)
#
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'interpreter'))

from main import main

if __name__ == '__main__':
    main()
