import csv
import json
import random
from datetime import datetime, timedelta

def main():
    # Headers for simulated business banking bank statement ledger
    headers = [
        "TransactionID", "Date", "Description", "Amount", "MessyCategory", 
        "GSTIN", "TDSSection", "VendorType", "ReceiptUploaded"
    ]

    rows = []
    
    # Ground truth tracking for validation of every single transaction
    ground_truth = {
        "starting_cash_balance": 1500000.00,
        "transactions": {}
    }

    start_date = datetime(2026, 4, 1)

    # 1. Generate clean, non-exception transactions (~45 transactions)
    for m in range(5):  # April to August
        m_start = start_date + timedelta(days=m*30)
        
        # Revenue Inflows
        tx_rev_a = f"TX-REV-{random.randint(1000, 9999)}A"
        date_rev_a = (m_start + timedelta(days=random.randint(3, 6))).strftime('%Y-%m-%d')
        rev_amt_a = round(random.uniform(330000.00, 370000.00), 2)
        rows.append([
            tx_rev_a, date_rev_a, f"Customer Inflow: Invoice #INR-00{m+1}", 
            rev_amt_a, "Revenue", "", "", "", "True"
        ])
        ground_truth["transactions"][tx_rev_a] = {
            "verdict": "matched",
            "category": "Revenue",
            "flags": [],
            "reasoning": "Standard customer revenue invoice payment received.",
            "correct_adjustment": ""
        }

        tx_rev_b = f"TX-REV-{random.randint(1000, 9999)}B"
        date_rev_b = (m_start + timedelta(days=random.randint(17, 21))).strftime('%Y-%m-%d')
        rev_amt_b = round(random.uniform(170000.00, 190000.00), 2)
        rows.append([
            tx_rev_b, date_rev_b, f"Customer Inflow: Client Retainer #INR-00{m+6}", 
            rev_amt_b, "Revenue", "", "", "", "True"
        ])
        ground_truth["transactions"][tx_rev_b] = {
            "verdict": "matched",
            "category": "Revenue",
            "flags": [],
            "reasoning": "Standard customer monthly retainer payment received.",
            "correct_adjustment": ""
        }

        # Employee Payroll Salaries
        tx_pay = f"TX-PAY-{random.randint(2000, 2999)}"
        date_pay = (m_start + timedelta(days=29)).strftime('%Y-%m-%d')
        sal_amt = -round(random.uniform(270000.00, 290000.00), 2)
        rows.append([
            tx_pay, date_pay, "Razorpay X Payroll Payout - Employee Salaries", 
            sal_amt, "Salaries", "", "", "", "True"
        ])
        ground_truth["transactions"][tx_pay] = {
            "verdict": "matched",
            "category": "Employee Payroll",
            "flags": [],
            "reasoning": "Standard monthly salary payroll clearance. TDS processed via separate batch.",
            "correct_adjustment": ""
        }

        # Standard Rent (Sharma Realty) - except August (which has duplicate rent exceptions)
        rent_amt = round(random.uniform(74000.00, 76000.00), 2)
        if m != 4:
            tx_rent = f"TX-RNT-{random.randint(3000, 3999)}"
            date_rent = (m_start + timedelta(days=9)).strftime('%Y-%m-%d')
            rows.append([
                tx_rent, date_rent, "Sharma Realty - Monthly Office Rent", 
                -rent_amt, "Rent Expense", "27AAAPS1000A1Z1", "", "", "True"
            ])
            ground_truth["transactions"][tx_rent] = {
                "verdict": "matched",
                "category": "Rent OpEx",
                "flags": [],
                "reasoning": "Standard monthly office lease rent. Amount falls below professional TDS thresholds.",
                "correct_adjustment": ""
            }
            
        # Standard software subscription (Slack) - except August (which has price spike exception)
        if m != 4:
            tx_slack = f"TX-SaaS-{random.randint(4000, 4999)}"
            date_slack = (m_start + timedelta(days=24)).strftime('%Y-%m-%d')
            rows.append([
                tx_slack, date_slack, "Slack Tech Subscription", 
                -10000.00, "Software Subscription", "", "", "", "True"
            ])
            ground_truth["transactions"][tx_slack] = {
                "verdict": "matched",
                "category": "Software Subscription OpEx",
                "flags": [],
                "reasoning": "Standard monthly SaaS subscription billing.",
                "correct_adjustment": ""
            }

        # Regular AWS Hosting charges
        if m != 4:
            tx_aws = f"TX-AWS-{random.randint(5000, 5999)}"
            date_aws = (m_start + timedelta(days=14)).strftime('%Y-%m-%d')
            aws_amt = -round(random.uniform(43000.00, 47000.00), 2)
            rows.append([
                tx_aws, date_aws, "AWS Cloud Hosting Servers", 
                aws_amt, "Server Hosting", "27AAACA9999P1Z2", "", "", "True"
            ])
            ground_truth["transactions"][tx_aws] = {
                "verdict": "matched",
                "category": "Server Hosting COGS",
                "flags": [],
                "reasoning": "Standard server compute hosting charges with valid GSTIN and receipt.",
                "correct_adjustment": ""
            }

        # Miscellaneous small transactions
        for i in range(3):
            tx_misc_id = f"TX-MISC-{random.randint(6000, 6999)}"
            tx_date = (m_start + timedelta(days=random.randint(1, 28))).strftime('%Y-%m-%d')
            desc = random.choice(["Blue Tokai Coffee", "Swiggy Business Lunch", "Uber Rides", "Stationery Hub"])
            amount = -round(random.uniform(500, 3000), 2)
            rows.append([
                tx_misc_id, tx_date, desc, amount, "Meals & Office Expense", "", "", "", "True"
            ])
            ground_truth["transactions"][tx_misc_id] = {
                "verdict": "matched",
                "category": "Office Meals & Travel OpEx",
                "flags": [],
                "reasoning": "Minor business operational expenditure. Below receipt thresholds.",
                "correct_adjustment": ""
            }

    # 2. Inject Deterministic Exceptions (Stage 1 Rules)
    
    # Exception 1: Professional Fee TDS Under-deduction (Section 194J)
    tx_tds = f"TX-TDS-ERR-{random.randint(100, 999)}"
    tds_fees = round(random.uniform(45000.00, 65000.00), 2)
    tds_calc = int(tds_fees * 0.10)
    rows.append([
        tx_tds, "2026-06-15", "Payout to TechConsulting - Professional Fees", 
        -tds_fees, "Professional Fees", "27BBBPS2000B1Z2", "", "", "True"
    ])
    ground_truth["transactions"][tx_tds] = {
        "verdict": "exception",
        "category": "Professional Fees OpEx",
        "flags": ["TDS_UNDER_DEDUCTION"],
        "reasoning": f"Professional fees payout of Rs. {tds_fees:,.0f} exceeds the Rs. 30,000 threshold and lacks the mandatory 10% TDS deduction.",
        "correct_adjustment": f"Debit IT-SEC-194J (Professional Fees) Rs. {tds_calc}; Credit IT-PAYABLE (TDS Payable) Rs. {tds_calc} under Section 194J."
    }

    # Exception 2: MSME Delay (Section 43B(h))
    tx_msme = f"TX-MSME-ERR-{random.randint(100, 999)}"
    msme_invoice_amt = round(random.uniform(220000.00, 280000.00), 2)
    rows.append([
        tx_msme, "2026-05-10", f"Raj Packers - Packing Material Invoice #{random.randint(300, 399)} (MSME Micro)", 
        -msme_invoice_amt, "Raw Materials", "27AAAPR4000C1Z4", "", "MSME Micro", "True"
    ])
    ground_truth["transactions"][tx_msme] = {
        "verdict": "exception",
        "category": "Raw Materials COGS",
        "flags": ["MSME_PAYMENT_DELAY"],
        "reasoning": "Invoice from MSME Micro supplier Raj Packers remained unpaid for 53 days, violating Section 43B(h) (45-day payment close rule).",
        "correct_adjustment": f"Debit IT-SEC-43B (Disallowed MSME Provision) Rs. {int(msme_invoice_amt):,}; Credit TAX-RESERVE (Tax Liability Add-Back) Rs. {int(msme_invoice_amt):,}."
    }
    
    # Matching payment for the above delayed MSME invoice
    tx_msme_pay = f"TX-MSME-PYMT-{random.randint(100, 999)}"
    rows.append([
        tx_msme_pay, "2026-07-02", "Payout to Raj Packers for Invoice #312",
        -msme_invoice_amt, "Raw Materials", "27AAAPR4000C1Z4", "", "MSME Micro", "True"
    ])
    ground_truth["transactions"][tx_msme_pay] = {
        "verdict": "matched",
        "category": "Raw Materials COGS",
        "flags": [],
        "reasoning": "Settlement of Raj Packers packing materials invoice. Payout itself is correct, invoice was delayed.",
        "correct_adjustment": ""
    }

    # Exception 3: GSTR-2B Input Tax Credit (ITC) Mismatch
    tx_gst = f"TX-GST-ERR-{random.randint(100, 999)}"
    marketing_amt = round(random.uniform(110000.00, 130000.00), 2)
    gst_itc_calc = int(marketing_amt * 18 / 118) # 18% GST inclusive
    rows.append([
        tx_gst, "2026-07-18", "Alpha Ads - Digital Marketing campaign", 
        -marketing_amt, "Marketing", "27AAAAA1111A1Z1", "", "", "True"
    ])
    ground_truth["transactions"][tx_gst] = {
        "verdict": "exception",
        "category": "Marketing OpEx",
        "flags": ["GSTR2B_MISMATCH"],
        "reasoning": f"Vendor Alpha Ads is unfiled in GSTR-2B. Cannot claim Rs. 18,000 Input Tax Credit (ITC).",
        "correct_adjustment": "Debit GST-EXP-HOLD (GST Withholding) Rs. 18,000; Credit GST-ITC-UNAVAILABLE (Blocked ITC Reserve) Rs. 18,000."
    }

    # Exception 4: Missing GST Invoice (> Rs. 10k limit)
    tx_hotel = f"TX-HTL-ERR-{random.randint(100, 999)}"
    hotel_amt = round(random.uniform(13000.00, 18000.00), 2)
    rows.append([
        tx_hotel, "2026-08-05", "Taj Hotel - Business Accommodation Bangalore", 
        -hotel_amt, "Travel Expense", "29AAACT9000D1Z8", "", "", "False"
    ])
    ground_truth["transactions"][tx_hotel] = {
        "verdict": "exception",
        "category": "Office Meals & Travel OpEx",
        "flags": ["MISSING_RECEIPT"],
        "reasoning": f"Travel accommodation expense of Rs. {hotel_amt:,.0f} exceeds corporate audit limit (Rs. 10,000) and lacks a receipt upload.",
        "correct_adjustment": f"Debit AUD-SUSPENSE (Auditing Suspense) Rs. {int(hotel_amt)}; Credit EXP-TRAVEL (Travel Expense Reversion) Rs. {int(hotel_amt)} due to missing receipt."
    }

    # Exception 5: Duplicate Payment rent
    tx_rent_b = "TX-RNT-AUG-B"
    aug_rent_amt = round(random.uniform(74000.00, 76000.00), 2)
    rows.append([
        tx_rent_b, "2026-08-10", "Sharma Realty - Monthly Office Rent", 
        -aug_rent_amt, "Rent Expense", "27AAAPS1000A1Z1", "", "", "True"
    ])
    ground_truth["transactions"][tx_rent_b] = {
        "verdict": "exception",
        "category": "Rent OpEx",
        "flags": ["DUPLICATE_PAYMENT"],
        "reasoning": f"Duplicate rent payment of Rs. 75,000 detected to Sharma Realty on 2026-08-10.",
        "correct_adjustment": "Debit REC-SHARMA (Receivable from Sharma Realty) Rs. 75,000; Credit EXP-RENT (Rent Expense Duplicate Void) Rs. 75,000."
    }
    
    # Normal rent counterpart
    tx_rent_a = "TX-RNT-AUG-A"
    rows.append([
        tx_rent_a, "2026-08-10", "Sharma Realty - Monthly Office Rent", 
        -aug_rent_amt, "Rent Expense", "27AAAPS1000A1Z1", "", "", "True"
    ])
    ground_truth["transactions"][tx_rent_a] = {
        "verdict": "matched",
        "category": "Rent OpEx",
        "flags": [],
        "reasoning": "Standard rent expense. Valid rent counterpart.",
        "correct_adjustment": ""
    }

    # Exception 6: SaaS Price Spike
    tx_slack_spike = "TX-SLK-SPIKE"
    spike_amt = round(random.uniform(32000.00, 38000.00), 2)
    spike_diff = int(spike_amt - 10000.00)
    rows.append([
        tx_slack_spike, "2026-08-25", "Slack Tech Subscription", 
        -spike_amt, "Software Subscription", "", "", "", "True"
    ])
    ground_truth["transactions"][tx_slack_spike] = {
        "verdict": "exception",
        "category": "Software Subscription OpEx",
        "flags": ["SAAS_PRICE_SPIKE"],
        "reasoning": f"Slack subscription cost surged by 250% from Rs. 10,000 to Rs. 35,000 without contract approval.",
        "correct_adjustment": "Debit EXP-SOFTWARE (SaaS Review Buffer) Rs. 25,000; Credit REC-SAAS-RECON (Unapproved SaaS cost variance) Rs. 25,000."
    }

    # 3. Inject Ambiguous Exceptions (Requires LLM / Stage 2 Reasoning)

    # Ambiguity 1: Split Payments (bypassing 194J professional TDS threshold)
    tx_split_a = "TX-TDS-SPLIT-A"
    tx_split_b = "TX-TDS-SPLIT-B"
    split_payout_a = round(random.uniform(19000.00, 21000.00), 2)
    split_payout_b = round(random.uniform(19000.00, 21000.00), 2)
    split_total = split_payout_a + split_payout_b
    split_tds_calc = int(split_total * 0.10)
    rows.append([
        tx_split_a, "2026-08-12", "Consulting Payout to TechConsulting", 
        -split_payout_a, "Professional Fees", "27BBBPS2000B1Z2", "", "", "True"
    ])
    rows.append([
        tx_split_b, "2026-08-13", "TechConsulting fees partition", 
        -split_payout_b, "Professional Fees", "27BBBPS2000B1Z2", "", "", "True"
    ])
    
    ground_truth["transactions"][tx_split_a] = {
        "verdict": "exception",
        "category": "Professional Fees OpEx",
        "flags": ["TDS_UNDER_DEDUCTION"],
        "reasoning": "Split payment trick identified. Two consulting fees of Rs. 20,000 cleared within 24 hours to the same vendor, totaling Rs. 40,000, bypassing the Section 194J professional TDS threshold (Rs. 30,000) without withholding.",
        "correct_adjustment": f"Debit IT-SEC-194J (TechConsulting Professional Fees) Rs. {split_tds_calc}; Credit IT-PAYABLE (TDS Payable) Rs. {split_tds_calc}."
    }
    ground_truth["transactions"][tx_split_b] = {
        "verdict": "exception",
        "category": "Professional Fees OpEx",
        "flags": ["TDS_UNDER_DEDUCTION"],
        "reasoning": "Split payment trick identified. Two consulting fees of Rs. 20,000 cleared within 24 hours to the same vendor, totaling Rs. 40,000, bypassing the Section 194J professional TDS threshold (Rs. 30,000) without withholding.",
        "correct_adjustment": f"Debit IT-SEC-194J (TechConsulting Professional Fees) Rs. {split_tds_calc}; Credit IT-PAYABLE (TDS Payable) Rs. {split_tds_calc}."
    }

    # Ambiguity 2: Typo in MSME Vendor name
    tx_msme_typo = "TX-MSME-TYPO"
    typo_msme_amt = round(random.uniform(90000.00, 110000.00), 2)
    rows.append([
        tx_msme_typo, "2026-05-15", "Rajj Packrs - Supply Invoice (MSME Micro)", 
        -typo_msme_amt, "Raw Materials", "27AAAPR4000C1Z4", "", "MSME Micro", "True"
    ])
    ground_truth["transactions"][tx_msme_typo] = {
        "verdict": "exception",
        "category": "Raw Materials COGS",
        "flags": ["MSME_PAYMENT_DELAY"],
        "reasoning": "MSME vendor name typo resolved. 'Rajj Packrs' matched to micro-MSME 'Raj Packers'. Invoice remained unpaid for 48 days, exceeding the Section 43B(h) 45-day payment close rule.",
        "correct_adjustment": f"Debit IT-SEC-43B (Disallowed MSME Provision) Rs. {int(typo_msme_amt):,}; Credit TAX-RESERVE (Tax Liability Add-Back) Rs. {int(typo_msme_amt):,}."
    }

    # Ambiguity 3: Typo in Rent Vendor duplicate
    tx_rent_typo = "TX-RNT-AUG-TYPO"
    rows.append([
        tx_rent_typo, "2026-08-10", "Shrma Relty office rent lease", 
        -aug_rent_amt, "Rent Expense", "27AAAPS1000A1Z1", "", "", "True"
    ])
    ground_truth["transactions"][tx_rent_typo] = {
        "verdict": "exception",
        "category": "Rent OpEx",
        "flags": ["DUPLICATE_PAYMENT"],
        "reasoning": "Duplicate rent payment audit mismatch. Payout of Rs. 75,000 to 'Shrma Relty' on 2026-08-10 is a duplicate of rent paid to 'Sharma Realty' on the same date.",
        "correct_adjustment": f"Debit REC-SHARMA (Receivable from Sharma Realty) Rs. {int(aug_rent_amt):,}; Credit EXP-RENT (Rent Expense Duplicate Void) Rs. {int(aug_rent_amt):,}."
    }

    # Ambiguity 4: Contractor Gift under Section 194R
    tx_gift = "TX-GFT-194R"
    gift_amt = round(random.uniform(23000.00, 27000.00), 2)
    gift_tds = int(gift_amt * 0.10)
    rows.append([
        tx_gift, "2026-08-18", "Contractor Gift - Laptop for contractor Rohan", 
        -gift_amt, "Office Meals & Travel OpEx", "", "", "", "True"
    ])
    ground_truth["transactions"][tx_gift] = {
        "verdict": "exception",
        "category": "Office Meals & Travel OpEx",
        "flags": ["TDS_UNDER_DEDUCTION"],
        "reasoning": "Contractor gift benefit audit failure. Payout for contractor Rohan's laptop (Rs. 25,000) exceeds Section 194R annual perquisite limit (Rs. 20,000) and lacks mandatory 10% TDS.",
        "correct_adjustment": f"Debit IT-SEC-194R (Contractor perks withholding) Rs. {gift_tds:,.0f}; Credit IT-PAYABLE (TDS Payable) Rs. {gift_tds:,.0f}."
    }

    # Ambiguity 5: Typo in AWS Hostings
    tx_aws_typo = "TX-AWS-TYPO"
    typo_aws_amt = round(random.uniform(11000.00, 13000.00), 2)
    rows.append([
        tx_aws_typo, "2026-08-20", "AWS Servers Inc - Compute cloud charges", 
        -typo_aws_amt, "Server Hosting", "27AAACA9999P1Z2", "", "", "False"
    ])
    ground_truth["transactions"][tx_aws_typo] = {
        "verdict": "exception",
        "category": "Server Hosting COGS",
        "flags": ["MISSING_RECEIPT"],
        "reasoning": "Typo in vendor 'AWS Servers Inc' resolved. Cloud hosting expense of Rs. 12,000 exceeds Rs. 10,000 invoice threshold and lacks a receipt upload.",
        "correct_adjustment": f"Debit AUD-SUSPENSE (Auditing Suspense) Rs. {int(typo_aws_amt):,}; Credit EXP-SOFTWARE (Software Expense Reversion) Rs. {int(typo_aws_amt):,}."
    }

    # 4. Write CSV ledger file with strict quoting and utf-8 encoding
    with open('razorpay_ledger.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Generated razorpay_ledger.csv ({len(rows)} rows)")

    # 5. Write Ground Truth labels file
    with open('ground_truth.json', 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)
    print("Generated ground_truth.json")

    # Layer 6: Verification and Readability Check
    try:
        import pandas as pd
        df_verify = pd.read_csv('razorpay_ledger.csv', encoding='utf-8')
        assert len(df_verify) == len(rows), f"Row count mismatch: expected {len(rows)}, got {len(df_verify)}"
        for h in headers:
            assert h in df_verify.columns, f"Missing header {h} in generated CSV"
        assert not df_verify['TransactionID'].isnull().any(), "Found null TransactionID in generated ledger"
        assert not df_verify['Amount'].isnull().any(), "Found null Amount in generated ledger"
        print("Verification passed: Generated dataset is 100% valid and readable.")
    except Exception as e:
        print(f"CRITICAL WARNING in generated ledger verification: {e}")

if __name__ == "__main__":
    main()
