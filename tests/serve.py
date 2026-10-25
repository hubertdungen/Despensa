"""Isolated browser-test server: temporary database, no worker, no retailer requests."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from waitress import serve
from app import create_app

with tempfile.TemporaryDirectory(prefix='despensa-e2e-') as folder:
    serve(create_app(folder, testing=True), host='127.0.0.1', port=38108, threads=4)
