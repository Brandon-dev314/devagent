"""
Script de ingesta.
"""
import argparse
import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(env_path)

from app.rag.ingestion import IngestionPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ingest")


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into DevAgent RAG")
    parser.add_argument("--file", type=str, help="Path to a specific file")
    parser.add_argument("--dir", type=str, default="docs/source", help="Directory to ingest")
    parser.add_argument("--extensions", nargs="+", default=[".md", ".txt"])
    args = parser.parse_args()

    pipeline = IngestionPipeline()

    logger.info("Ensuring Qdrant collection exists...")
    pipeline.ensure_collection()

    if args.file:
        logger.info("Ingesting single file: %s", args.file)
        result = pipeline.ingest_file(args.file)
        print(f"\n{'='*50}")
        print(f"Source:  {result.source}")
        print(f"Status:  {result.status}")
        print(f"Chunks:  {result.chunks_created}")
        if result.message:
            print(f"Message: {result.message}")
    else:
        logger.info("Ingesting directory: %s", args.dir)
        results = pipeline.ingest_directory(args.dir, args.extensions)

        print(f"\n{'='*50}")
        print("INGESTION RESULTS")
        print(f"{'='*50}")
        for r in results:
            status_icon = "OK" if r.status == "success" else "FAIL"
            print(f"  [{status_icon}] {r.source} -> {r.chunks_created} chunks")

        total = sum(r.chunks_created for r in results)
        print(f"{'='*50}")
        print(f"Total: {total} chunks from {len(results)} files")


if __name__ == "__main__":
    main()