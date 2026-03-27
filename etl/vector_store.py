import json, math, re
from pathlib import Path

STOPWORDS = {"a","an","the","and","or","but","in","on","at","to","for","of","with","is","are","was","were","be","been","have","has","had","do","does","did","will","would","could","should","this","that","it","its","we","our","they","their","by","from","as","about","into"}

def tokenize(text):
    tokens = re.sub(r"[^\w\s]", " ", text.lower()).split()
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


class TFIDFIndex:
    def __init__(self):
        self.chunks = []
        self.tf = []
        self.idf = {}

    def build(self, chunks):
        self.chunks = chunks
        N = len(chunks)
        df = {}
        self.tf = []
        for chunk in chunks:
            tokens = tokenize(chunk["content"])
            freq = {}
            for t in tokens:
                freq[t] = freq.get(t, 0) + 1
            total = len(tokens) or 1
            tf_doc = {t: c / total for t, c in freq.items()}
            self.tf.append(tf_doc)
            for t in freq:
                df[t] = df.get(t, 0) + 1
        self.idf = {t: math.log((N + 1) / (cnt + 1)) + 1.0 for t, cnt in df.items()}
        print(f"[Store] Index built: {len(chunks)} chunks, vocab {len(self.idf)}")

    def search(self, query, top_k=6, filter_type=None):
        tokens = tokenize(query)
        results = []
        for i, chunk in enumerate(self.chunks):
            if filter_type and chunk.get("type") != filter_type:
                continue
            score = sum(self.tf[i].get(t, 0) * self.idf.get(t, 0) for t in tokens)
            if score > 0:
                results.append({"chunk": chunk, "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        return [{"chunk_id": r["chunk"]["chunk_id"], "type": r["chunk"]["type"], "page": r["chunk"]["page"], "content": r["chunk"]["content"], "score": round(r["score"], 4)} for r in results[:top_k]]

    def save(self, path):
        with open(path, "w") as f:
            json.dump({"chunks": self.chunks, "tf": self.tf, "idf": self.idf}, f)
        print(f"[Store] Saved → {path}")

    def load(self, path):
        with open(path) as f:
            data = json.load(f)
        self.chunks = data["chunks"]
        self.tf = data["tf"]
        self.idf = data["idf"]
        print(f"[Store] Loaded {len(self.chunks)} chunks from {path}")


_index = None

def get_index(path="data/index.json"):
    global _index
    if _index is None:
        if not Path(path).exists():
            raise RuntimeError(f"Index not found at {path}. Run: python etl/ingest.py data/cyber_ireland_2022.pdf")
        _index = TFIDFIndex()
        _index.load(path)
    return _index
