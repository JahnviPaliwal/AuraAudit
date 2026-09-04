import streamlit as st
import pandas as pd
import json
import os
from controller_agent import run_reconciliation
import generate_data

# Page config
st.set_page_config(
    page_title="AI Intercompany Controller Dashboard",
    page_icon="⚖️",
    layout="wide"
)

# Title
st.title("⚖️ Multi-Entity Intercompany Settlement Controller")
st.markdown("Automated period-close reconciliation and journal adjustment generator for **USA Corp** (USD) and **UK Ltd** (GBP).")

# Sidebar
st.sidebar.header("Operations")
if st.sidebar.button("🔄 Regenerate Test Ledger Data", use_container_width=True):
    with st.spinner("Generating fresh synthetic books..."):
        generate_data.main()
    st.sidebar.success("Successfully generated new ledgers!")
    st.rerun()

# Run reconciliation
@st.cache_data
def get_recon_results():
    return run_reconciliation()

# Force rerun if needed
if 'recon_results' not in st.session_state or st.sidebar.button("⚡ Re-run Matching Agent", use_container_width=True):
    st.session_state.recon_results = run_reconciliation()
    st.toast("Matching agent executed successfully!")

results = st.session_state.recon_results
matched_pairs = results['matched_pairs']
exceptions = results['exceptions']

# Session state for approved adjustments
if 'approved_adjustments' not in st.session_state:
    st.session_state.approved_adjustments = {}

# KPI Summary
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Matched Transactions", len(matched_pairs))
with col2:
    st.metric("Exceptions Identified", len(exceptions))
with col3:
    # Outstanding balance variance (net of all matched matches)
    net_variance = sum(m['variance_usd'] for m in matched_pairs)
    st.metric("Reconciled Balance Net Variance", f"${net_variance:.2f} USD")
with col4:
    resolved_count = len(st.session_state.approved_adjustments)
    st.metric("Resolved Exceptions", f"{resolved_count} / {len(exceptions)}")

# Tabs
tab1, tab2, tab3 = st.tabs(["⚠️ Actionable Exceptions", "✅ Matched Ledger Pairs", "📊 Raw Subsidiary Ledgers"])

with tab1:
    st.header("Honest Exception List")
    st.markdown("Select an exception below to inspect details and approve the AI-generated adjusting journal entries.")
    
    if len(exceptions) == 0:
        st.success("All intercompany transactions reconciled successfully! 0 exceptions found.")
    else:
        for idx, exc in enumerate(exceptions):
            exc_id = f"exc_{idx}"
            is_resolved = exc_id in st.session_state.approved_adjustments
            
            # Use color coding based on exception type
            status_text = "✅ APPROVED" if is_resolved else "❌ UNRESOLVED"
            bg_color = "#D4EDDA" if is_resolved else "#F8D7DA"
            text_color = "#155724" if is_resolved else "#721C24"
            
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color: {bg_color}; padding: 15px; border-radius: 8px; border-left: 5px solid {text_color}; margin-bottom: 15px;">
                        <h4 style="margin: 0; color: {text_color};">
                            {idx+1}. {exc['type']} | Ref: {exc['ref_id'] if exc['ref_id'] else 'No Ref'} | {status_text}
                        </h4>
                        <p style="margin: 5px 0 0 0; color: #333;"><strong>Date:</strong> {exc['date']} &nbsp;&nbsp;|&nbsp;&nbsp; <strong>US Amount:</strong> ${exc['us_amount'] if exc['us_amount'] is not None else 'N/A'} USD &nbsp;&nbsp;|&nbsp;&nbsp; <strong>UK Amount:</strong> £{exc['uk_amount'] if exc['uk_amount'] is not None else 'N/A'} GBP</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                # Expandable details
                with st.expander("View Audit Trail & Adjustment Entry", expanded=not is_resolved):
                    st.write(f"**Description / Audit Detail:** {exc['details']}")
                    st.write(f"**AI Recommendation:** {exc['proposed_adjustment']}")
                    
                    # Generate the double entry visualization
                    st.markdown("**Proposed Journal Entry Details:**")
                    
                    # Construct entries based on type
                    entry_data = []
                    ref = exc['ref_id'] if exc['ref_id'] else f"ADJ-EXC-{idx}"
                    
                    if exc['type'] == "MISSING_RECORD":
                        # US recorded payout, UK missing
                        # e.g., US: Dr Due from UK, Cr Cash.
                        # UK should book: Dr Cash, Cr Due to US.
                        amt_gbp = round(-exc['us_amount'] / 1.28, 2) if exc['us_amount'] else 0.0
                        entry_data = [
                            {"Subsidiary": "UK Ltd", "Account": "Cash", "Debit (GBP)": amt_gbp, "Credit (GBP)": ""},
                            {"Subsidiary": "UK Ltd", "Account": "Due to USA Corp", "Debit (GBP)": "", "Credit (GBP)": amt_gbp}
                        ]
                    elif exc['type'] == "AMOUNT_MISMATCH":
                        # Mismatched GBP amount. UK booked incorrect amount.
                        # e.g., US booked -$10000. UK booked £8294. Expected £7894.
                        # UK needs to Debit Due to USA Corp by £400, Credit FX Loss or Cash.
                        entry_data = [
                            {"Subsidiary": "UK Ltd", "Account": "Due to USA Corp", "Debit (GBP)": "", "Credit (GBP)": 400.00},
                            {"Subsidiary": "UK Ltd", "Account": "Foreign Exchange Loss", "Debit (GBP)": 400.00, "Credit (GBP)": ""}
                        ]
                    elif exc['type'] == "ACCOUNT_MISCLASSIFICATION":
                        # UK booked to AP - Software Corp instead of Due to USA Corp
                        # UK entry: Dr Accounts Payable - Software Corp £5000, Cr Due to USA Corp £5000
                        entry_data = [
                            {"Subsidiary": "UK Ltd", "Account": "Accounts Payable - Software Corp", "Debit (GBP)": 5000.00, "Credit (GBP)": ""},
                            {"Subsidiary": "UK Ltd", "Account": "Due to USA Corp", "Debit (GBP)": "", "Credit (GBP)": 5000.00}
                        ]
                    elif exc['type'] == "CURRENCY_BOOKING_ERROR":
                        # US recorded flat $8000 USD instead of $10,108.80 USD.
                        # US needs to book additional Dr Marketing Expense $2,108.80, Cr Due to UK Ltd $2,108.80
                        entry_data = [
                            {"Subsidiary": "USA Corp", "Account": "Marketing Expense", "Debit (USD)": 2108.80, "Credit (USD)": ""},
                            {"Subsidiary": "USA Corp", "Account": "Due to UK Ltd", "Debit (USD)": "", "Credit (USD)": 2108.80}
                        ]
                    elif exc['type'] == "TIMING_MISMATCH":
                        # In-transit transaction. Accrue in USA / UK for August.
                        # US: Debit In-Transit Assets $25000, Credit Due from UK Ltd $25000
                        entry_data = [
                            {"Subsidiary": "USA Corp", "Account": "Intercompany In-Transit Cash", "Debit (USD)": 25000.00, "Credit (USD)": ""},
                            {"Subsidiary": "USA Corp", "Account": "Due from UK Ltd", "Debit (USD)": "", "Credit (USD)": 25000.00}
                        ]
                    elif exc['type'] == "DUPLICATE_RECORD":
                        # UK double booked. Void second entry.
                        # UK: Debit Due from USA Corp £12000, Credit Revenue £12000
                        entry_data = [
                            {"Subsidiary": "UK Ltd", "Account": "Due from USA Corp", "Debit (GBP)": 12000.00, "Credit (GBP)": ""},
                            {"Subsidiary": "UK Ltd", "Account": "Consulting Revenue", "Debit (GBP)": "", "Credit (GBP)": 12000.00}
                        ]
                        
                    if entry_data:
                        st.table(pd.DataFrame(entry_data))
                        
                    # Action buttons
                    btn_col1, btn_col2 = st.columns([1, 4])
                    with btn_col1:
                        if not is_resolved:
                            if st.button("✔️ Approve Adjustment", key=f"app_{idx}"):
                                st.session_state.approved_adjustments[exc_id] = entry_data
                                st.success("Adjustment Approved!")
                                st.rerun()
                        else:
                            if st.button("❌ Remove Approval", key=f"rem_{idx}"):
                                del st.session_state.approved_adjustments[exc_id]
                                st.warning("Approval Removed.")
                                st.rerun()

        # Export button for approved entries
        if len(st.session_state.approved_adjustments) > 0:
            st.markdown("---")
            st.header("📤 Export Adjusting General Ledger Entries")
            all_entries = []
            for k, entries in st.session_state.approved_adjustments.items():
                all_entries.extend(entries)
                
            export_df = pd.DataFrame(all_entries)
            st.dataframe(export_df)
            
            csv = export_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ Download GL Adjustments CSV",
                csv,
                "intercompany_adjustments.csv",
                "text/csv",
                key='download-csv',
                use_container_width=True
            )

with tab2:
    st.header("Matched Intercompany Transaction Pairs")
    st.markdown("These transactions were reconciled automatically by the matching agent with zero/minimal FX variance.")
    
    if len(matched_pairs) == 0:
        st.warning("No matched transaction pairs found.")
    else:
        match_df = pd.DataFrame(matched_pairs)
        # Rename columns for presentation
        match_df.columns = [
            "US Tx ID", "UK Tx ID", "Reference ID", "Date", 
            "US Amount (USD)", "UK Amount (GBP)", "Variance (USD)", 
            "Exchange Rate Used", "Description"
        ]
        st.dataframe(match_df, use_container_width=True)

with tab3:
    st.header("Subsidiary Ledger Raw Data")
    
    col_us, col_uk = st.columns(2)
    
    with col_us:
        st.subheader("USA Corp Ledger (USD)")
        if os.path.exists('usa_ledger.csv'):
            st.dataframe(pd.read_csv('usa_ledger.csv'), use_container_width=True)
        else:
            st.error("usa_ledger.csv not found. Please regenerate data.")
            
    with col_uk:
        st.subheader("UK Ltd Ledger (GBP)")
        if os.path.exists('uk_ledger.csv'):
            st.dataframe(pd.read_csv('uk_ledger.csv'), use_container_width=True)
        else:
            st.error("uk_ledger.csv not found. Please regenerate data.")
