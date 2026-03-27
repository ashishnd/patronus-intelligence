import re, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from etl.vector_store import get_index


def search_document(query, top_k=6, filter_type=None):
    return get_index().search(query, top_k=top_k, filter_type=filter_type)


def calculate(expression):
    try:
        safe = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
        safe.update({"abs": abs, "round": round, "pow": pow})
        cleaned = re.sub(r"[^0-9\s\.\+\-\*/\(\)\^%,a-zA-Z_]", "", expression).replace("^", "**")
        result = float(eval(cleaned, {"__builtins__": {}}, safe))
        return {"result": result, "expression": expression, "formatted": f"{result:.6f}"}
    except Exception as e:
        return {"error": str(e)}


def compute_cagr(start_value, end_value, years):
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return {"error": "All inputs must be positive"}
    cagr = (end_value / start_value) ** (1.0 / years) - 1
    return {
        "cagr_decimal": round(cagr, 6),
        "cagr_percent": f"{cagr * 100:.2f}%",
        "formula_used": f"({end_value} / {start_value}) ^ (1 / {years}) - 1",
        "inputs": {"start_value": start_value, "end_value": end_value, "years": years},
    }


def extract_number(text):
    matches = re.findall(r"\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\b", text)
    if not matches:
        return {"error": "No number found"}
    return {"number": float(matches[0].replace(",", "")), "raw": matches[0]}
