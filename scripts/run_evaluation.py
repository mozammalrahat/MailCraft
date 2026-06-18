#!/usr/bin/env python3
"""Thin wrapper — prefer `uv run mailcraft-eval`."""

from app.cli.evaluation import main

if __name__ == "__main__":
    raise SystemExit(main())
