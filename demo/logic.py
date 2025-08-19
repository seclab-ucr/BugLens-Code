# logic.py
import csv
import os
import re
import psycopg2

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", 5432)),
    "dbname": os.getenv("PGDATABASE", "lmsuture"),
    "user": os.getenv("PGUSER", "lmsuture_user"),
    "password": os.getenv("PGPASSWORD", "password1"),
}


GROUND_TRUTH_FILE = "ground_truth.csv"

# Example: a flexible list of models you want to compare
MODELS = [
    # "o1",
    "o3-mini",
    # "gpt-4.1",
    # "o3",
    # "deepseek-reasoner",
    # 'gemini-2.5-pro-preview-03-25',
    # "o4-mini",
    # "claude-3-7-sonnet-latest",
    # "deepseek-chat"
    # "openrouter/Friendli/deepseek/deepseek-r1",

      # add more as needed
]

# Excluded IDs
# UPDATE: treat all of them as "not_a_bug" (i.e., false positive)
EXCLUDED_IDS = {
    8, 9, 10, 13, 14, 16, 17,
    20, 21, 22, 23, 24, 25, 26,
    33,
    51, 56, 61, 68, 76, 82, 91, 95,
    102, 106, 110, 115
}

def load_ground_truth(filepath=GROUND_TRUTH_FILE):
    """
    Load CSV: each row => { id: int, FP: "Y"/"N"/"?"/... }
    """
    gt = {}
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_int = int(row["id"])
            gt[case_int] = row["FP"]
    return gt

def fuzzy_map(sanitize_result):
    """
    Convert the raw sanitize_result to either 'not_a_bug' or 'still_a_bug'.
    Here we treat None => 'not_a_bug'.
    """
    if (
        sanitize_result is None or
        sanitize_result in ["not_exploitable", "likely_safe", "eliminated", "not_a_bug"]
    ):
        return "not_a_bug"
    elif sanitize_result in ["still_a_bug", "likely_unsafe", "uncertain"]:
        return "still_a_bug"
    else:
        return sanitize_result  # fallback if you have other statuses

def is_correct(fuzzy_value, ground_truth):
    """
    ground_truth 'N'/'N?' => real bug => correct if fuzzy_value == 'still_a_bug'
    ground_truth 'Y'/'Y?' => false positive => correct if fuzzy_value == 'not_a_bug'
    """
    if ground_truth.startswith("N"):
        return (fuzzy_value == "still_a_bug")
    elif ground_truth.startswith("Y"):
        return (fuzzy_value == "not_a_bug")
    return False  # for skip, ?, etc. we won't count it anyway

def get_data():
    """
    1) Query DB for all models in MODELS.
    2) Merge with ground_truth, skipping excluded or skip/? cases.
    3) Build:
        - rows_for_table: each row has .case_id, .gt, and a dict of results for each model
        - model_stats: { model_name => { missed_bug, mislabel_fp } }
    4) Return (rows_for_table, model_stats, list_of_models)
    """
    ground_truth_map = load_ground_truth()

    # Build a parameterized query for (model IN (...))
    # If you have an unknown number of models, we can do something like:
    placeholders = ", ".join(["%s"] * len(MODELS))
    query = f"""
      SELECT case_id, model, sanitize_result
      FROM cases
      WHERE model IN ({placeholders})
      and case_id like 'msm-sound:%%'
      ORDER BY case_id, model
    """

    # Connect to DB
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(query, tuple(MODELS))  # pass the models as parameters
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # data dict: {case_int => {"case_id_str": <orig case_id>, "models": {model_name => sanitize_result, ...}}}
    data = {}
    for (case_id, model, sanitize_result) in rows:
        match = re.search(r":(\d+)$", case_id)
        if not match:
            continue
        case_int = int(match.group(1))
        if case_int not in data:
            data[case_int] = {
                "case_id_str": case_id,
                "models": {}
            }
        data[case_int]["models"][model] = sanitize_result
    
    # Initialize stats dictionary for each model
    model_stats = {
        m: {"missed_bug": 0, "mislabel_fp": 0}
        for m in MODELS
    }

    rows_for_table = []

    for case_int, info in data.items():
        gt_val = ground_truth_map.get(case_int)
        if case_int in EXCLUDED_IDS:
            gt_val = "Y"  # treat excluded IDs as false positives
        
        if gt_val is None:
            continue
        if gt_val == "skip":
            continue
        if gt_val == "?":
            continue  # uncertain => skip

        row_dict = {
            "case_id": info["case_id_str"],
            "gt": gt_val,
            # We'll store results in a dict keyed by model
            # for the final template to iterate over
            "results": {}
        }

        # For each model in MODELS:
        # 1) get the original sanitize_result
        # 2) fuzzy-map it
        # 3) check correctness
        for m in MODELS:
            orig_result = info["models"].get(m)  # could be None
            fuzz = fuzzy_map(orig_result)
            correct = is_correct(fuzz, gt_val)
            
            # If incorrect => increment missed_bug / mislabel_fp
            if not correct:
                if gt_val.startswith("N") and fuzz == "not_a_bug":
                    model_stats[m]["missed_bug"] += 1
                elif gt_val.startswith("Y") and fuzz == "still_a_bug":
                    model_stats[m]["mislabel_fp"] += 1

            # put in row_dict
            row_dict["results"][m] = {
                "orig": orig_result,
                "correct": correct
            }

        rows_for_table.append(row_dict)

    return rows_for_table, model_stats, MODELS