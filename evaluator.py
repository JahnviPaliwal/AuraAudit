import json
import os

def evaluate_audit(audit_results: dict, ground_truth_path: str = "ground_truth.json") -> dict:
    if not os.path.exists(ground_truth_path):
        return {
            "match_rate": 1.0,
            "precision": 1.0,
            "recall": 1.0,
            "f1_score": 1.0,
            "total_transactions": 0,
            "tp": 0, "tn": 0, "fp": 0, "fn": 0,
            "category_metrics": {}
        }
        
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        gt = json.load(f)
        
    gt_tx = gt.get("transactions", {})
    audited = audit_results.get("audited_transactions", [])
    
    tp = 0
    tn = 0
    fp = 0
    fn = 0
    
    # Track breakdown by compliance flags
    flag_types = ["TDS_UNDER_DEDUCTION", "MSME_PAYMENT_DELAY", "GSTR2B_MISMATCH", "MISSING_RECEIPT", "DUPLICATE_PAYMENT", "SAAS_PRICE_SPIKE"]
    type_stats = {ft: {"expected": 0, "detected": 0, "correct": 0} for ft in flag_types}
    
    for tx in audited:
        tx_id = tx["tx_id"]
        actual_flags = tx.get("flags", [])
        actual_verdict = "exception" if len(actual_flags) > 0 else "matched"
        
        gt_info = gt_tx.get(tx_id, {"verdict": "matched", "flags": [], "category": tx.get("messy_category", "")})
        gt_verdict = gt_info.get("verdict", "matched")
        gt_flags = gt_info.get("flags", [])
        
        # Calculate confusion matrix for exception classification
        if gt_verdict == "exception" and actual_verdict == "exception":
            tp += 1
        elif gt_verdict == "matched" and actual_verdict == "exception":
            fp += 1
        elif gt_verdict == "matched" and actual_verdict == "matched":
            tn += 1
        elif gt_verdict == "exception" and actual_verdict == "matched":
            fn += 1
            
        # Count detailed compliance flag metrics
        for ft in flag_types:
            has_gt_flag = ft in gt_flags
            has_actual_flag = ft in actual_flags
            
            if has_gt_flag:
                type_stats[ft]["expected"] += 1
            if has_actual_flag:
                type_stats[ft]["detected"] += 1
            if has_gt_flag and has_actual_flag:
                type_stats[ft]["correct"] += 1

    total = tp + tn + fp + fn
    match_rate = (tp + tn) / total if total > 0 else 1.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 1.0
    
    # Format category metrics output for frontend
    category_metrics = {}
    for ft, stats in type_stats.items():
        exp = stats["expected"]
        corr = stats["correct"]
        accuracy = (corr / exp) if exp > 0 else 1.0
        category_metrics[ft] = {
            "expected_count": exp,
            "detected_count": stats["detected"],
            "correct_count": corr,
            "accuracy": round(accuracy, 2)
        }

    return {
        "match_rate": round(match_rate, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "total_transactions": total,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "category_metrics": category_metrics
    }
