import json, os, re
from typing import List, Dict, Any

# -------- CONFIG --------
RAW_PATH   = "results/submission_unchecked-test_case_in_train_and_test-hyperparameter_epoch_step_val-colab.json"
FENCED_PATH = "postprocess/submission_fenced.json"   # intermediate (fenced but unchecked)
FINAL_PATH  = "postprocess/submission.json"          # required final file name

# -------- HELPERS --------
def wrap_in_fence(code: str) -> str:
    """Ensure response is wrapped in ```python fences (auto-close if missing)."""
    code = code.strip()
    if code.startswith("```python"):
        if not code.endswith("```"):
            return f"{code}\n```"   # add missing closing fence
        return code                # already correct
    else:
        return f"```python\n{code}\n```"

def file_format_check(path: str) -> bool:
    """Validate file-level format: name, structure, JSON validity."""
    if os.path.basename(path) != "submission.json":
        print(f"❌ Error: File name must be 'submission.json' (got {os.path.basename(path)})")
        return False
    if not path.lower().endswith(".json"):
        print("❌ Error: File must have .json extension")
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON - {e}")
        return False

    if not isinstance(data, list):
        print("❌ Error: Root must be a list of objects")
        return False

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            print(f"❌ Error: Item {idx} not a dict")
            return False
        if set(item.keys()) != {"id", "response"}:
            print(f"❌ Error: Item {idx} keys = {set(item.keys())}, expected {{'id','response'}}")
            return False
        if not isinstance(item["id"], int):
            print(f"❌ Error: id at {idx} not int")
            return False
        if not isinstance(item["response"], str):
            print(f"❌ Error: response at {idx} not str")
            return False

    print("✅ File format check passed!")
    return True

def item_format_ok(item: Dict[str, Any]) -> bool:
    """Check per-item dict structure and types."""
    return (
        isinstance(item, dict)
        and set(item.keys()) == {"id", "response"}
        and isinstance(item["id"], int)
        and isinstance(item["response"], str)
    )

# -------- STEP 1: POSTPROCESS (wrap fences) --------
with open(RAW_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

for item in raw_data:
    item["response"] = wrap_in_fence(item["response"])

with open(FENCED_PATH, "w", encoding="utf-8") as f:
    json.dump(raw_data, f, ensure_ascii=False, indent=2)

print(f"✍️  Wrote fenced intermediate → {FENCED_PATH}")

# -------- STEP 2: VALIDATION --------
fence_pat = re.compile(r"^```python[\s\S]*```$", re.MULTILINE)

valid_data = []
nf = nm = nb = 0

for item in raw_data:
    vfmt = item_format_ok(item)
    vf   = bool(fence_pat.match(item["response"])) if vfmt else False
    if vfmt: nm += 1
    if vf: nf += 1
    if vfmt and vf: nb += 1

    # Strict policy: blank if invalid
    if not (vfmt and vf):
        valid_data.append({"id": item.get("id", -1), "response": ""})
    else:
        valid_data.append(item)

n = len(raw_data)
den = max(n, 1)
print(f"📊 Stats → Fencing valid: {nf}/{n} ({nf*100/den:.1f}%)")
print(f"📊 Stats → Format  valid: {nm}/{n} ({nm*100/den:.1f}%)")
print(f"📊 Stats → Both    valid: {nb}/{n} ({nb*100/den:.1f}%)")

# -------- STEP 3: SAVE FINAL --------
with open(FINAL_PATH, "w", encoding="utf-8") as f:
    json.dump(valid_data, f, ensure_ascii=False, indent=2)

print(f"✅ Final cleaned file → {FINAL_PATH}")

# -------- STEP 4: FILE CHECK --------
_ = file_format_check(FINAL_PATH)
