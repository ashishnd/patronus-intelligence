import json, os, sys, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from agent.agent import get_agent

TEST_QUERIES = [
    {"id": "test_1", "name": "Verification Challenge",   "query": "What is the total number of jobs reported, and where exactly is this stated?"},
    {"id": "test_2", "name": "Data Synthesis Challenge", "query": "Compare the concentration of 'Pure-Play' cybersecurity firms in the South-West against the National Average."},
    {"id": "test_3", "name": "Forecasting Challenge",    "query": "Based on our 2022 baseline and the stated 2030 job target, what is the required compound annual growth rate (CAGR) to hit that goal?"},
]

def run():
    if not Path("data/index.json").exists():
        print("ERROR: data/index.json not found.")
        print("Run first: python etl/ingest.py data/cyber_ireland_2022.pdf")
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    agent = get_agent(api_key=api_key)
    results, traces = [], []

    print("\n" + "="*60)
    print("  PATRONUS — 3 Evaluation Test Queries")
    print("="*60)

    for i, test in enumerate(TEST_QUERIES):
        print(f"\n{'─'*60}")
        print(f"  {test['id'].upper()}: {test['name']}")
        print(f"  Query: {test['query']}")
        print(f"{'─'*60}")

        start = time.time()
        result = agent.run(test["query"])
        elapsed = round(time.time() - start, 2)

        print(f"\n  ✅ Answer ({elapsed}s):")
        for line in result["answer"].split("\n"):
            print(f"     {line}")
        if result.get("citations"):
            print(f"\n  📄 Citations: {result['citations']}")
        print(f"\n  🔍 Trace: {result.get('trace_file', 'N/A')}")

        results.append({
            "test_id": test["id"],
            "name": test["name"],
            "query": test["query"],
            "answer": result["answer"],
            "citations": result.get("citations", []),
            "iterations": result.get("iterations", 1),
            "duration_seconds": elapsed,
            "trace_file": result.get("trace_file", "")
        })
        traces.append(result.get("trace", {}))

        # Pause between tests to avoid rate limits
        if i < len(TEST_QUERIES) - 1:
            print("\n  ⏳ Waiting 5s before next test...")
            time.sleep(5)

    Path("logs").mkdir(exist_ok=True)
    combined = {
        "run_timestamp": datetime.utcnow().isoformat(),
        "total_tests": len(results),
        "results": results,
        "traces": traces
    }
    with open("logs/test_run_combined.json", "w") as f:
        json.dump(combined, f, indent=2)

    print("\n" + "="*60)
    print("  All tests complete! Log: logs/test_run_combined.json")
    print("="*60 + "\n")

if __name__ == "__main__":
    run()
