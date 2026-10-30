#!/usr/bin/env python3
"""Root launcher for Shopify Connector server.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to sys.path
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from shopify_connector.server import run_server


def main():
    parser = argparse.ArgumentParser(description="Shopify Connector Standalone Workstation Server")
    parser.add_argument("--port", type=int, default=8113, help="Port to bind (default: 8113)")
    parser.add_argument("--host", default=None, help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--public-dir", default=None, help="Public directory path")
    args = parser.parse_args()
    run_server(port=args.port, public_dir=args.public_dir, host=args.host)


if __name__ == "__main__":
    main()
