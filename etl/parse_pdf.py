import pdfplumber
import json
from pathlib import Path


def extract_tables_from_page(page):
    tables = []
    raw_tables = page.extract_tables()
    if not raw_tables:
        return tables
    for idx, raw in enumerate(raw_tables):
        if not raw or len(raw) < 2:
            continue
        cleaned = [[str(c).strip() if c else "" for c in row] for row in raw]
        headers = cleaned[0]
        rows = cleaned[1:]
        structured = []
        for row in rows:
            if any(row):
                structured.append({headers[i] if i < len(headers) else f"col_{i}": row[i] if i < len(row) else "" for i in range(len(headers))})
        flat = f"[TABLE on page {page.page_number}]\nColumns: {' | '.join(headers)}\n"
        flat += "\n".join(" | ".join(str(v) for v in r.values()) for r in structured)
        tables.append({"table_index": idx, "page": page.page_number, "headers": headers, "rows": structured, "flat_text": flat, "type": "table"})
    return tables


def extract_text_from_page(page):
    bboxes = [t.bbox for t in page.find_tables()]
    words = []
    for w in page.extract_words():
        in_table = any(w["x0"] >= b[0]-2 and w["x1"] <= b[2]+2 and w["top"] >= b[1]-2 and w["bottom"] <= b[3]+2 for b in bboxes)
        if not in_table:
            words.append(w["text"])
    return " ".join(words)


def parse_pdf(pdf_path):
    pages, all_tables = [], []
    with pdfplumber.open(str(pdf_path)) as pdf:
        print(f"[ETL] Parsing {len(pdf.pages)} pages...")
        for page in pdf.pages:
            text = extract_text_from_page(page)
            tables = extract_tables_from_page(page)
            all_tables.extend(tables)
            pages.append({"page_num": page.page_number, "text": text, "tables": tables})
    print(f"[ETL] Done. {len(all_tables)} tables found.")
    return {"source": Path(pdf_path).name, "total_pages": len(pages), "pages": pages, "all_tables": all_tables}


if __name__ == "__main__":
    import sys
    result = parse_pdf(sys.argv[1])
    with open("data/parsed.json", "w") as f:
        json.dump(result, f, indent=2)
