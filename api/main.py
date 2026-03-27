import json, os, sys, time, uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent.agent import get_agent

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
_agent = None

def get_or_create_agent():
    global _agent
    if _agent is None:
        _agent = get_agent(api_key=os.environ.get("OPENAI_API_KEY"))
    return _agent

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Patronus Intelligence API", "endpoints": {"POST /query": "Submit a query", "GET /logs": "List traces"}})

@app.route("/query", methods=["POST"])
def query():
    start = time.time()
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    body = request.get_json()
    if not body or "query" not in body:
        return jsonify({"error": "Missing 'query' field"}), 400
    query_text = str(body["query"]).strip()
    if not query_text:
        return jsonify({"error": "Query cannot be empty"}), 400

    request_id = str(uuid.uuid4())[:8]
    print(f"\n[API] {request_id}: {query_text[:80]}")

    try:
        result = get_or_create_agent().run(query_text)
        resp = {
            "request_id": request_id,
            "query": query_text,
            "answer": result.get("answer", ""),
            "citations": result.get("citations", []),
            "iterations": result.get("iterations", 1),
            "trace_file": result.get("trace_file", ""),
            "duration_seconds": round(time.time() - start, 2),
        }
        if body.get("include_trace"):
            resp["trace"] = result.get("trace", {})
        return jsonify(resp)
    except Exception as e:
        return jsonify({"request_id": request_id, "error": str(e)}), 500

@app.route("/logs", methods=["GET"])
def list_logs():
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return jsonify({"logs": [], "count": 0})
    files = sorted(logs_dir.glob("trace_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    logs = []
    for f in files[:20]:
        try:
            data = json.load(open(f))
            logs.append({"file": f.name, "trace_id": data.get("trace_id"), "query": data.get("query","")[:80], "duration_seconds": data.get("duration_seconds"), "steps": data.get("total_steps")})
        except Exception:
            pass
    return jsonify({"logs": logs, "count": len(logs)})

@app.route("/logs/<trace_id>", methods=["GET"])
def get_log(trace_id):
    matches = list(Path("logs").glob(f"trace_{trace_id}*.json"))
    if not matches:
        return jsonify({"error": "Not found"}), 404
    return jsonify(json.load(open(matches[0])))

if __name__ == "__main__":
    key_set = bool(os.environ.get("OPENAI_API_KEY"))
    print("=" * 50)
    print("  Patronus Intelligence API")
    print(f"  Model   : gpt-4o-mini")
    print(f"  API Key : {'SET ✓' if key_set else 'NOT SET (fallback mode)'}")
    print("  URL     : http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
