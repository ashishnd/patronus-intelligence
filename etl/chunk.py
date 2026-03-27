import json, re

TARGET = 1600
OVERLAP = 320


def chunk_text(text, page_num, source):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 50:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = start + TARGET
        if end < len(text):
            for sep in [". ", ".\n", "\n\n"]:
                b = text.rfind(sep, start + TARGET // 2, end)
                if b > 0:
                    end = b + 1
                    break
        chunk = text[start:end].strip()
        if len(chunk) > 30:
            chunks.append({"chunk_id": f"text_p{page_num}_{len(chunks)}", "type": "text", "page": page_num, "source": source, "content": chunk})
        start = end - OVERLAP
        if start <= 0 or start >= len(text) - 50:
            break
    return chunks


def table_to_chunk(table, source):
    page = table["page"]
    content = f"[TABLE on page {page}]\nColumns: {', '.join(h for h in table['headers'] if h)}\n\n{table['flat_text']}"
    return {"chunk_id": f"table_p{page}_{table['table_index']}", "type": "table", "page": page, "source": source, "content": content}


def build_chunks(parsed):
    source = parsed.get("source", "Cyber Ireland 2022")
    chunks = []
    for page in parsed["pages"]:
        chunks.extend(chunk_text(page["text"], page["page_num"], source))
        for table in page["tables"]:
            chunks.append(table_to_chunk(table, source))
    print(f"[Chunk] {len(chunks)} chunks ({sum(1 for c in chunks if c['type']=='text')} text, {sum(1 for c in chunks if c['type']=='table')} table)")
    return chunks


if __name__ == "__main__":
    with open("data/parsed.json") as f:
        parsed = json.load(f)
    chunks = build_chunks(parsed)
    with open("data/chunks.json", "w") as f:
        json.dump(chunks, f, indent=2)
