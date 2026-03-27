import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.parse_pdf import parse_pdf
from etl.chunk import build_chunks
from etl.vector_store import TFIDFIndex


def run(pdf_path):
    Path("data").mkdir(exist_ok=True)

    print("\n=== STEP 1: Parsing PDF ===")
    parsed = parse_pdf(pdf_path)
    with open("data/parsed.json", "w") as f:
        json.dump(parsed, f, indent=2)

    print("\n=== STEP 2: Chunking ===")
    chunks = build_chunks(parsed)
    with open("data/chunks.json", "w") as f:
        json.dump(chunks, f, indent=2)

    print("\n=== STEP 3: Building Index ===")
    idx = TFIDFIndex()
    idx.build(chunks)
    idx.save("data/index.json")

    print(f"\n=== DONE === Pages: {parsed['total_pages']}, Tables: {len(parsed['all_tables'])}, Chunks: {len(chunks)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python etl/ingest.py data/cyber_ireland_2022.pdf")
        sys.exit(1)
    if not Path(sys.argv[1]).exists():
        print(f"File not found: {sys.argv[1]}")
        sys.exit(1)
    run(sys.argv[1])
