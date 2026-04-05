"""Shadowpay CLI entry point."""

from src.cli.app import create_app

app = create_app()

if __name__ == "__main__":
    app()
