import json
import time
import os
import pandas as pd
from controller_agent import run_reconciliation

def evaluate():
    print("=" * 60)
    print("                  RECONCILIATION EVALUATOR                   ")
    print("=" * 60)
    
    # 1. Regenerate data to ensure consistency
    print("Regenerating synthetic ledger data...")
    import generate_data
    generate_data.main()
    print("-" * 60)

    # 2. Load ground truth
    with open('ground_truth.json', 'r') as f:
        gt = json.load(f)
        
    gt_matches = gt['matched_pairs']
    gt_exceptions = gt['exceptions']
    
    print(f"Ground Truth loaded:")
    print(f"  Expected Matches: {len(gt_matches)}")
    print(f"  Expected Exceptions: {len(gt_exceptions)}")
    print("-" * 60)

    # 3. Time the execution of the agent
    start_time = time.time()
    results = run_reconciliation()
    end_time = time.time()
    
    agent_matches = results['matched_pairs']
    agent_exceptions = results['exceptions']
    
    execution_time = end_time - start_time
    total_records = len(pd.read_csv('usa_ledger.csv')) + len(pd.read_csv('uk_ledger.csv'))
    throughput = total_records / execution_time if execution_time > 0 else 0
    
    print("Agent Finished Processing:")
    print(f"  Records Processed: {total_records}")
    print(f"  Execution Time: {execution_time:.4f} seconds")
    print(f"  Throughput: {throughput:.2f} records/sec")
    print("-" * 60)

    # 4. Evaluate Matches
    # Set of true matched pairs (tuple of us_id, uk_id)
    true_match_set = {(m['us_tx_id'], m['uk_tx_id']) for m in gt_matches}
    agent_match_set = {(m['us_tx_id'], m['uk_tx_id']) for m in agent_matches}
    
    correct_matches = agent_match_set.intersection(true_match_set)
    false_pos_matches = agent_match_set - true_match_set
    missed_matches = true_match_set - agent_match_set
    
    match_accuracy = len(correct_matches) / len(true_match_set) if len(true_match_set) > 0 else 1.0
    
    print(f"MATCH PERFORMANCE:")
    print(f"  Correct Matches: {len(correct_matches)} / {len(true_match_set)} ({match_accuracy*100:.1f}%)")
    if false_pos_matches:
        print(f"  [WARNING] False Positive Matches: {false_pos_matches}")
    if missed_matches:
        print(f"  [WARNING] Missed Matches: {missed_matches}")
    print("-" * 60)

    # 5. Evaluate Exceptions
    # Helper to check if exception matches a ground truth exception
    def is_matching_exception(agent_exc, gt_exc):
        # Match on type and at least one transaction ID matching
        type_match = agent_exc['type'] == gt_exc['type']
        us_match = (agent_exc['us_tx_id'] == gt_exc['us_tx_id']) if gt_exc['us_tx_id'] else (agent_exc['us_tx_id'] is None or agent_exc['us_tx_id'] == "")
        uk_match = (agent_exc['uk_tx_id'] == gt_exc['uk_tx_id']) if gt_exc['uk_tx_id'] else (agent_exc['uk_tx_id'] is None or agent_exc['uk_tx_id'] == "")
        return type_match and us_match and uk_match

    matched_gt_exceptions = []
    unmatched_gt_exceptions = list(gt_exceptions)
    false_alarm_exceptions = []
    
    for ae in agent_exceptions:
        found_match = False
        for ge in list(unmatched_gt_exceptions):
            if is_matching_exception(ae, ge):
                matched_gt_exceptions.append(ge)
                unmatched_gt_exceptions.remove(ge)
                found_match = True
                break
        if not found_match:
            # Check if it was supposed to be a normal match, or it's a completely false alarm
            # Note: normal operations records (non-intercompany) are not matched and are not exceptions, they shouldn't trigger intercompany exceptions.
            false_alarm_exceptions.append(ae)
            
    recall_exceptions = len(matched_gt_exceptions) / len(gt_exceptions) if len(gt_exceptions) > 0 else 1.0
    precision_exceptions = len(matched_gt_exceptions) / (len(matched_gt_exceptions) + len(false_alarm_exceptions)) if (len(matched_gt_exceptions) + len(false_alarm_exceptions)) > 0 else 1.0
    
    print(f"EXCEPTION DETECTION PERFORMANCE:")
    print(f"  True Exceptions Detected: {len(matched_gt_exceptions)} / {len(gt_exceptions)} (Recall: {recall_exceptions*100:.1f}%)")
    print(f"  Precision: {precision_exceptions*100:.1f}%")
    
    if unmatched_gt_exceptions:
        print(f"  [ERROR] Missed Exceptions:")
        for me in unmatched_gt_exceptions:
            print(f"    - Type: {me['type']}, US ID: {me['us_tx_id']}, UK ID: {me['uk_tx_id']}, Ref: {me['ref_id']}")
            
    if false_alarm_exceptions:
        print(f"  [WARNING] False Positive Exceptions (False Alarms):")
        for fe in false_alarm_exceptions:
            print(f"    - Type: {fe['type']}, US ID: {fe['us_tx_id']}, UK ID: {fe['uk_tx_id']}, Ref: {fe['ref_id']}")
            
    print("=" * 60)
    print("                 DETAILED EXCEPTION REPORT                   ")
    print("=" * 60)
    for idx, ae in enumerate(agent_exceptions, 1):
        ref_str = f" [Ref: {ae['ref_id']}]" if ae['ref_id'] else ""
        print(f"{idx}. {ae['type']}{ref_str}")
        print(f"   Date: {ae['date']}")
        print(f"   US Tx: {ae['us_tx_id']} (${ae['us_amount'] if ae['us_amount'] is not None else 'N/A'} USD)")
        print(f"   UK Tx: {ae['uk_tx_id']} (£{ae['uk_amount'] if ae['uk_amount'] is not None else 'N/A'} GBP)")
        print(f"   Details: {ae['details']}")
        print(f"   Proposed Adjustment: {ae['proposed_adjustment']}")
        print("-" * 60)

if __name__ == "__main__":
    evaluate()
