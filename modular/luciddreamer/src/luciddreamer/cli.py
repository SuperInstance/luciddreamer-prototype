"""
LucidDreamer.AI CLI — command-line interface for the meta-package.

Usage:
    luciddreamer serve [--audio-dir DIR] [--port PORT]
    luciddreamer ingest [--source DIR]
    luciddreamer status
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="luciddreamer",
        description="LucidDreamer.AI — multi-agent dream radio station",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start the streaming server")
    serve_parser.add_argument("--audio-dir", "-a", default="./audio", help="Audio directory")
    serve_parser.add_argument("--port", "-p", type=int, default=8420, help="HTTP port")

    # ingest
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents into the knowledge base")
    ingest_parser.add_argument("--source", "-s", default="./docs", help="Source directory")

    # status
    subparsers.add_parser("status", help="Show module status")

    args = parser.parse_args()

    if args.command == "serve":
        serve(args)
    elif args.command == "ingest":
        ingest(args)
    elif args.command == "status":
        status()
    else:
        parser.print_help()


def serve(args):
    """Start the streaming server."""
    try:
        from streamer.stream_server import main as stream_main
    except ImportError:
        print("Streamer not installed. Run: pip install superinstance-streamer")
        sys.exit(1)

    # Patch sys.argv for the stream server's argparse
    sys.argv = ["stream_server", "--audio-dir", args.audio_dir, "--port", str(args.port)]
    stream_main()


def ingest(args):
    """Ingest documents into the knowledge base."""
    try:
        from knowledge_base.build_knowledge_base import main as kb_main
    except ImportError:
        print("Knowledge base not installed. Run: pip install superinstance-knowledge-base")
        sys.exit(1)

    kb_main()


def status():
    """Show module status."""
    from luciddreamer import LucidDreamer

    ld = LucidDreamer(enable_streamer=False)  # don't need audio dir
    print("LucidDreamer.AI Module Status")
    print("=" * 40)
    for module, state in ld.status().items():
        icon = "✓" if state == "active" else "○"
        print(f"  {icon} {module}: {state}")


if __name__ == "__main__":
    main()
