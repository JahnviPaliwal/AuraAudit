import json
import time
import os
import pandas as pd
from controller_agent import run_audit
from evaluator import evaluate_audit

def evaluate():
    print("=" * 60)
    print("           AURAAUDIT BATCH RECONCILIATION EVALUATOR           ")
    print("=" * 60)
    
    # 1. Regenerate synthetic batch data
    print("Regenerating synthetic Indian ledger batch data...")
    import generate_data
    generate_data.main()
    print("-" * 60)

    # 2. Check if files exist
    if not os.path.exists("razorpay_ledger.csv") or not os.path.exists("ground_truth.json"):
        print("[ERROR] Ledger CSV or Ground Truth files do not exist.")
        return

    # 3. Timed run of the two-stage compliance audit loop
    print("Executing Two-Stage (Heuristic Rules + Local AI Reasoner) Audit...")
    start_time = time.time()
    audit_results = run_audit()
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 4. Evaluate metrics against ground-truth labels
    eval_report = evaluate_audit(audit_results, ground_truth_path="ground_truth.json")
    
    total_records = len(pd.read_csv('razorpay_ledger.csv'))
    throughput = total_records / execution_time if execution_time > 0 else 0

    # 5. Print out verification summary metrics
    print("\n" + "=" * 60)
    print("                    EVALUATION METRICS REPORT                 ")
    print("=" * 60)
    print(f"  Total Records Processed  : {total_records}")
    print(f"  Execution Time           : {execution_time:.4f} seconds")
    print(f"  Reconciliation Throughput: {throughput:.2f} records/second")
    print("-" * 60)
    print(f"  Reconciliation Match Rate: {eval_report['match_rate'] * 100:.2f}%")
    print(f"  Flagging Precision       : {eval_report['precision'] * 100:.2f}%")
    print(f"  Flagging Recall          : {eval_report['recall'] * 100:.2f}%")
    print(f"  F1 Score                 : {eval_report['f1_score'] * 100:.2f}%")
    print("-" * 60)
    print("  CONFUSION MATRIX SUMMARY:")
    print(f"    - True Positives (Exceptions correctly found) : {eval_report['tp']}")
    print(f"    - True Negatives (Compliant lines verified)  : {eval_report['tn']}")
    print(f"    - False Positives (False alarm exceptions)   : {eval_report['fp']}")
    print(f"    - False Negatives (Missed exceptions)        : {eval_report['fn']}")
    print("-" * 60)
    
    print("  COMPLIANCE CATEGORY BREAKDOWN ACCURACY:")
    print("  %-25s | %-8s | %-8s | %-8s | %-8s" % ("Category Code", "Expected", "Detected", "Correct", "Accuracy"))
    print("-" * 60)
    for cat, stats in eval_report['category_metrics'].items():
        print("  %-25s | %-8d | %-8d | %-8d | %-8.1f%%" % (
            cat, 
            stats['expected_count'], 
            stats['detected_count'], 
            stats['correct_count'], 
            stats['accuracy'] * 100
        ))
        
    print("\n" + "=" * 60)
    print("                 HONEST EXCEPTION DETAIL LOG                 ")
    print("=" * 60)
    for idx, exc in enumerate(audit_results['exceptions'], 1):
        print(f"{idx}. {exc['tx_id']} - {exc['type']}")
        print(f"   Date: {exc['date']} | Amount: Rs. {abs(exc['amount']):,.2f}")
        print(f"   Reason: {exc['details']}")
        print(f"   Confidence Score: {exc.get('confidence', 0.95)*100:.0f}%")
        if exc.get('proposed_adjustment'):
            print(f"   Balancing adjustment: {exc['proposed_adjustment']}")
        print("-" * 60)

if __name__ == "__main__":
    evaluate()
