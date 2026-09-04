from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
import json
import os
import io
import re
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Try local imports first
try:
    from controller_agent import run_audit, run_forecast, get_active_groq_model
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from controller_agent import run_audit, run_forecast, get_active_groq_model

try:
    import generate_data
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import generate_data

try:
    import runs_db
    import evaluator
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import runs_db
    import evaluator

app = FastAPI(title="Razorpay X Smart Controller API")

# Enable CORS for Next.js dev server proxying
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScenarioRequest(BaseModel):
    new_hires_count: int = 0
    new_hires_salary: float = 0.0
    new_hires_start_month: int = 0
    payment_delay_days: int = 0
    ad_spend: float = 0.0
    cac: float = 1000.0
    office_upgrade: bool = False
    price_hike: float = 0.0
    funding_round: float = 0.0
    funding_month: int = 0

class ExportRequest(BaseModel):
    exceptions: List[Dict[str, Any]]
    format: str

class ChatRequest(BaseModel):
    message: str
    apiKey: Optional[str] = None
    provider: Optional[str] = "openai"
    runId: Optional[str] = None

@app.get("/api/health")
def health():
    return {"status": "ok"}

def read_uploaded_dataframe(contents: bytes, filename: str = "") -> pd.DataFrame:
    # Layer 1: Empty file check (auto-fallback to local generated ledger)
    if not contents or len(contents.strip()) == 0:
        if not os.path.exists("razorpay_ledger.csv"):
            generate_data.main()
        return pd.read_csv("razorpay_ledger.csv")
        
    # Layer 2: Excel format detection
    if filename.endswith(".xlsx") or filename.endswith(".xls") or contents[:4] == b"PK\x03\x04":
        try:
            return pd.read_excel(io.BytesIO(contents))
        except Exception:
            pass

    # Layer 3: Multi-encoding and multi-delimiter fallback decoding
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]
    separators = [None, ",", ";", "\t", "|"]
    
    df = None
    last_err = None
    for enc in encodings:
        for sep in separators:
            try:
                if sep is None:
                    df = pd.read_csv(io.BytesIO(contents), encoding=enc, sep=None, engine="python")
                else:
                    df = pd.read_csv(io.BytesIO(contents), encoding=enc, sep=sep)
                if df is not None and len(df.columns) >= 2:
                    break
            except Exception as e:
                last_err = e
                continue
        if df is not None and len(df.columns) >= 2:
            break
            
    if df is None or len(df) == 0:
        if os.path.exists("razorpay_ledger.csv"):
            return pd.read_csv("razorpay_ledger.csv")
        raise ValueError(f"Could not parse ledger file: {last_err}")
        
    # Layer 4: Column normalization layer
    col_map = {}
    for col in df.columns:
        c_clean = str(col).strip().lower().replace(" ", "").replace("_", "")
        if c_clean in ["transactionid", "txid", "transid", "id", "transno", "referenceno", "ref"]:
            col_map[col] = "TransactionID"
        elif c_clean in ["date", "txdate", "transactiondate", "postingdate", "valuedate"]:
            col_map[col] = "Date"
        elif c_clean in ["description", "desc", "narration", "particulars", "memo", "remarks"]:
            col_map[col] = "Description"
        elif c_clean in ["amount", "amt", "txamount", "debit", "value", "netamount"]:
            col_map[col] = "Amount"
        elif c_clean in ["messycategory", "category", "expensetype", "account"]:
            col_map[col] = "MessyCategory"
        elif c_clean in ["gstin", "gst", "gstno", "taxid"]:
            col_map[col] = "GSTIN"
        elif c_clean in ["tdssection", "tds", "section"]:
            col_map[col] = "TDSSection"
        elif c_clean in ["vendortype", "vendor", "type"]:
            col_map[col] = "VendorType"
        elif c_clean in ["receiptuploaded", "receipt", "hasreceipt", "invoiceattached"]:
            col_map[col] = "ReceiptUploaded"
            
    df = df.rename(columns=col_map)
    
    # Layer 5: Data cleansing and default imputation
    if "TransactionID" not in df.columns:
        df["TransactionID"] = [f"TX-GEN-{i+1:04d}" for i in range(len(df))]
    else:
        df["TransactionID"] = df["TransactionID"].fillna("").astype(str)
        for idx in df.index:
            if not df.at[idx, "TransactionID"].strip():
                df.at[idx, "TransactionID"] = f"TX-GEN-{idx+1:04d}"
                
    if "Date" not in df.columns:
        df["Date"] = "2026-08-01"
    else:
        df["Date"] = df["Date"].fillna("2026-08-01").astype(str)
        
    if "Description" not in df.columns:
        df["Description"] = "Operational Expense"
    else:
        df["Description"] = df["Description"].fillna("Operational Expense").astype(str)
        
    if "Amount" not in df.columns:
        df["Amount"] = 0.0
    else:
        def clean_amt(v):
            if pd.isna(v):
                return 0.0
            if isinstance(v, (int, float)):
                return float(v)
            s = str(v).replace("₹", "").replace("$", "").replace("Rs.", "").replace("Rs", "").replace(",", "").strip()
            try:
                return float(s)
            except Exception:
                return 0.0
        df["Amount"] = df["Amount"].apply(clean_amt)
        
    for col in ["MessyCategory", "GSTIN", "TDSSection", "VendorType"]:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].fillna("").astype(str)
            
    if "ReceiptUploaded" not in df.columns:
        df["ReceiptUploaded"] = "True"
    else:
        df["ReceiptUploaded"] = df["ReceiptUploaded"].fillna("True").astype(str)
        
    return df

@app.post("/api/upload-ledger")
async def upload_ledger(
    file: UploadFile = File(...),
    apiKey: Optional[str] = Form(None),
    provider: Optional[str] = Form("openai")
):
    try:
        if apiKey:
            apiKey = apiKey.strip()
        contents = await file.read()
        filename = file.filename or "uploaded_ledger.csv"
        df = read_uploaded_dataframe(contents, filename)
        
        # Save parsed file locally if filesystem is writable
        try:
            df.to_csv("razorpay_ledger.csv", index=False)
        except Exception:
            pass
        
        # 1. Run the two-stage auditing loop
        audit_results = run_audit(df, api_key=apiKey, provider=provider)
        
        # 2. Evaluate against ground_truth.json
        eval_report = evaluator.evaluate_audit(audit_results, ground_truth_path="ground_truth.json")
        
        # 3. Save run in SQLite database
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        runs_db.save_run(
            run_id=run_id,
            filename=filename,
            match_rate=eval_report["match_rate"],
            precision=eval_report["precision"],
            recall=eval_report["recall"],
            audit_results=audit_results,
            eval_report=eval_report
        )
        
        return {
            "status": "success",
            "run_id": run_id,
            "match_rate": eval_report["match_rate"],
            "precision": eval_report["precision"],
            "recall": eval_report["recall"],
            "audit_results": audit_results,
            "eval_report": eval_report
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed processing file upload: {str(e)}")

@app.post("/api/load-sample")
def load_sample_ledger(
    apiKey: Optional[str] = Form(None),
    provider: Optional[str] = Form("openai")
):
    try:
        if apiKey:
            apiKey = apiKey.strip()
        if not os.path.exists("razorpay_ledger.csv") or not os.path.exists("ground_truth.json"):
            generate_data.main()
        df = pd.read_csv("razorpay_ledger.csv")
        audit_results = run_audit(df, api_key=apiKey, provider=provider)
        eval_report = evaluator.evaluate_audit(audit_results, ground_truth_path="ground_truth.json")
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        runs_db.save_run(
            run_id=run_id,
            filename="razorpay_ledger.csv",
            match_rate=eval_report["match_rate"],
            precision=eval_report["precision"],
            recall=eval_report["recall"],
            audit_results=audit_results,
            eval_report=eval_report
        )
        return {
            "status": "success",
            "run_id": run_id,
            "match_rate": eval_report["match_rate"],
            "precision": eval_report["precision"],
            "recall": eval_report["recall"],
            "audit_results": audit_results,
            "eval_report": eval_report
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed processing file upload: {str(e)}")

@app.get("/api/runs")
def get_past_runs():
    try:
        runs = runs_db.get_runs()
        return {"runs": runs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/run-details")
def get_run_details(run_id: str):
    try:
        details = runs_db.get_run(run_id)
        if not details:
            raise HTTPException(status_code=404, detail="Run history session not found.")
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audit")
def get_audit():
    try:
        if not os.path.exists("razorpay_ledger.csv"):
            generate_data.main()
        results = run_audit()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ledgers")
def get_ledgers():
    try:
        if not os.path.exists("razorpay_ledger.csv"):
            generate_data.main()
        df = pd.read_csv('razorpay_ledger.csv')
        return {"ledger": df.fillna("").to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/forecast")
def get_forecast():
    try:
        results = run_forecast()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scenario")
def get_scenario_forecast(req: ScenarioRequest):
    try:
        results = run_forecast(
            new_hires_count=req.new_hires_count,
            new_hires_salary=req.new_hires_salary,
            new_hires_start_month=req.new_hires_start_month,
            payment_delay_days=req.payment_delay_days,
            ad_spend=req.ad_spend,
            cac=req.cac,
            office_upgrade=req.office_upgrade,
            price_hike=req.price_hike,
            funding_round=req.funding_round,
            funding_month=req.funding_month
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
def trigger_generation():
    try:
        generate_data.main()
        return {"status": "success", "message": "AuraAudit bank ledger and ground truth generated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export-adjustments")
def export_adjustments(req: ExportRequest):
    try:
        exceptions = req.exceptions
        fmt = req.format.lower()
        
        if not exceptions:
            raise HTTPException(status_code=400, detail="No exceptions provided.")
            
        output = io.StringIO()
        
        if fmt == "xero":
            df = pd.DataFrame(exceptions)
            df.to_csv(output, index=False)
            filename = "xero_compliance_audit_exceptions.csv"
            
        elif fmt == "quickbooks":
            output.write("!TRNS\tDATE\tDESC\tACCNT\tAMOUNT\tDOCNUM\n")
            for idx, exc in enumerate(exceptions):
                output.write(f"TRNS\t{exc.get('date')}\t{exc.get('type')}\tTax Adjustment Account\t{exc.get('amount')}\tEXC-{idx}\n")
            filename = "quickbooks_compliance_adjustments.iif"
            
        else:
            df = pd.DataFrame(exceptions)
            df.to_csv(output, index=False)
            filename = "compliance_audit_exceptions.csv"
            
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return StreamingResponse(mem, media_type="text/csv", headers=headers)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_assistant(req: ChatRequest):
    query = req.message.lower()
    api_key = req.apiKey.strip() if req.apiKey else None
    run_id = req.runId
    
    # Load exceptions context from current run history
    run_data = None
    if run_id:
        try:
            run_data = runs_db.get_run(run_id)
        except Exception:
            pass
            
    if not run_data:
        # Fallback to the latest run in database
        try:
            past = runs_db.get_runs()
            if past:
                run_data = runs_db.get_run(past[0]["id"])
        except Exception:
            pass
            
    exceptions_list = run_data.get("audit_results", {}).get("exceptions", []) if run_data else []
    
    # 1. Live LLM execution if API Key is supplied
    if api_key:
        try:
            from openai import OpenAI
            import httpx
            http_client = httpx.Client(verify=False)
            base_url = (
                "https://openrouter.ai/api/v1" if req.provider == "openai"
                else ("https://api.groq.com/openai/v1" if req.provider == "groq" else None)
            )
            client = OpenAI(
                base_url=base_url,
                api_key=api_key,
                http_client=http_client
            )
            
            compact_exc_list = []
            for exc in exceptions_list:
                compact_exc_list.append({
                    "id": exc.get("row_id"),
                    "date": exc.get("date"),
                    "desc": exc.get("description"),
                    "amt": exc.get("amount"),
                    "type": exc.get("type")
                })
            
            context = f"""
            You are an expert Indian CA (Chartered Accountant) and Cash Flow Controller.
            Here is the current state of the AuraAudit reconciliation run:
            - Run ID: {run_data.get('id') if run_data else 'unknown'}
            - Match Rate: {run_data.get('match_rate', 0.0) * 100:.2f}%
            - Exceptions count: {len(exceptions_list)}
            
            Exceptions list:
            {json.dumps(compact_exc_list, indent=2)}
            
            Answer the user's question specifically using this run's stored exceptions and reasoning context. Be concise and precise.
            """
            
            model = "google/gemini-2.5-flash:free"
            if req.provider == "groq":
                model = get_active_groq_model(api_key)
            elif req.provider != "openai":
                model = "gemini-1.5-flash"
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": req.message}
                ],
                max_tokens=400
            )
            return {"reply": response.choices[0].message.content}
        except Exception as e:
            return {"reply": f"⚠️ Live AI Chat failed due to API Key configuration: {str(e)}. Falling back to local run helper.\n\n"}

    # 2. Local Run Helper (repurposed to answer queries regarding specific transaction exceptions)
    reply = ""
    # Check if user asks about a specific Transaction ID
    tx_match = re.search(r"(tx-\w+-\w+(?:-\w+)?)", query)
    
    if tx_match:
        target_tx = tx_match.group(1).upper()
        found_exc = None
        for exc in exceptions_list:
            if exc["tx_id"] == target_tx:
                found_exc = exc
                break
                
        if found_exc:
            reply = f"""
            ### 🔍 Run Audit Detail for {target_tx}:
            * **Compliance Issue:** {found_exc['type'].replace('_', ' ')}
            * **clearing Date:** {found_exc['date']} | **Value:** Rs. {abs(found_exc['amount']):,.2f}
            * **Reasoning Details:** {found_exc['details']}
            * **Confidence Score:** {found_exc.get('confidence', 0.95) * 100:.0f}%
            * **Suggested Fix:** {found_exc['proposed_adjustment']}
            """
        else:
            # Check if it was matched successfully
            audited_list = run_data.get("audit_results", {}).get("audited_transactions", []) if run_data else []
            found_tx = None
            for tx in audited_list:
                if tx["tx_id"] == target_tx:
                    found_tx = tx
                    break
            
            if found_tx:
                reply = f"""
                ### 🔍 Run Audit Detail for {target_tx}:
                * **Status:** Matched Successfully (No exceptions)
                * **Date:** {found_tx['date']} | **Amount:** Rs. {found_tx['amount']}
                * **Description:** {found_tx['description']}
                * **Category:** {found_tx['audited_category']}
                * **Reasoning:** {found_tx.get('reasoning', 'Clean transaction')}
                """
            else:
                reply = f"Could not find transaction {target_tx} in the current audit run history."
                
    elif "accuracy" in query or "rate" in query or "metrics" in query:
        if run_data:
            reply = f"""
            ### 📈 Current Batch Metrics:
            * **Run Session ID:** {run_data['id']}
            * **Reconciliation Match Rate:** {run_data['match_rate'] * 100:.2f}%
            * **Precision:** {run_data['precision'] * 100:.2f}%
            * **Recall:** {run_data['recall'] * 100:.2f}%
            * **Total Transactions Audited:** {run_data.get('eval_report', {}).get('total_transactions', 55)}
            """
        else:
            reply = "No active audit run session is loaded."
    else:
        # Generic summary of exceptions
        if exceptions_list:
            exc_summaries = []
            for exc in exceptions_list[:4]:
                exc_summaries.append(f"- **{exc['tx_id']}**: {exc['type'].replace('_', ' ')} (Rs. {abs(exc['amount']):,.0f})")
            reply = f"""
            ### 📋 Current Run Exceptions Summary ({len(exceptions_list)} issues found):
            {chr(10).join(exc_summaries)}
            
            Ask me about any specific transaction code (e.g. "Why was {exceptions_list[0]['tx_id']} flagged?") or batch accuracy scores.
            """
        else:
            reply = "All transactions in the current batch matched reference rules with 100% confidence. No exceptions found."

    return {"reply": reply}
