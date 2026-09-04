import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # completely blank layout

    # Image assets paths
    img_dir = r"C:\Users\paliw\.gemini\antigravity\brain\a7e2e26c-e3c1-4be8-9fa5-18f4e253e4de"
    crisis_img = os.path.join(img_dir, "finance_crisis_montage_1788458194688.jpg")
    landmines_img = os.path.join(img_dir, "compliance_landmines_3d_1788458131302.jpg")
    summary_img = os.path.join(img_dir, "executive_summary_slide_1788458169420.jpg")
    outro_img = os.path.join(img_dir, "auraaudit_outro_card_1788458115960.jpg")

    # Colors
    bg_dark = RGBColor(11, 12, 16)
    card_bg = RGBColor(23, 23, 23)
    gold = RGBColor(234, 179, 8)
    amber = RGBColor(245, 158, 11)
    emerald = RGBColor(16, 185, 129)
    crimson = RGBColor(239, 68, 68)
    white = RGBColor(255, 255, 255)
    gray = RGBColor(163, 163, 163)

    def set_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = bg_dark
        bg.line.fill.background()
        return bg

    # ==========================================
    # SLIDE 1: Title Slide (Brand Introduction)
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    set_bg(s1)
    
    # Hero Outro Image on Right
    if os.path.exists(outro_img):
        s1.shapes.add_picture(outro_img, Inches(6.5), Inches(1.1), width=Inches(6.2), height=Inches(3.48))

    # Left Typography
    tb = s1.shapes.add_textbox(Inches(0.8), Inches(1.2), Inches(5.4), Inches(5.2))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "PITCH DECK EXTRAS & VISUAL STORYBOARD"
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = amber
    p0.space_after = Pt(12)

    p1 = tf.add_paragraph()
    p1.text = "AuraAudit"
    p1.font.size = Pt(46)
    p1.font.bold = True
    p1.font.color.rgb = gold
    p1.space_after = Pt(10)

    p2 = tf.add_paragraph()
    p2.text = "The Autonomous Financial Controller & Treasury Defense Engine"
    p2.font.size = Pt(20)
    p2.font.bold = True
    p2.font.color.rgb = white
    p2.space_after = Pt(16)

    p3 = tf.add_paragraph()
    p3.text = "Automating period-close multi-entity reconciliation, resolving complex Indian tax landmines (Section 43B(h) & TDS), and safeguarding operational runway."
    p3.font.size = Pt(13)
    p3.font.color.rgb = gray
    p3.space_after = Pt(24)

    # Badges
    p4 = tf.add_paragraph()
    p4.text = "⚡ Two-Stage Hybrid AI  |  ⚖️ Statutory Tax Compliance  |  📈 Monte Carlo Treasury"
    p4.font.size = Pt(11)
    p4.font.bold = True
    p4.font.color.rgb = gold

    # Bottom Pill
    pill = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.5), Inches(5.2), Inches(6.2), Inches(1.0))
    pill.fill.solid()
    pill.fill.fore_color.rgb = card_bg
    pill.line.color.rgb = gold
    ptf = pill.text_frame
    ptf.word_wrap = True
    pp = ptf.paragraphs[0]
    pp.alignment = PP_ALIGN.CENTER
    pp.text = "Live Interactive Demo: auraaudit.ai/demo"
    pp.font.bold = True
    pp.font.size = Pt(14)
    pp.font.color.rgb = gold
    pp2 = ptf.add_paragraph()
    pp2.alignment = PP_ALIGN.CENTER
    pp2.text = "Includes Synthetic Test Suite & Ground-Truth Evaluation Benchmarks"
    pp2.font.size = Pt(10)
    pp2.font.color.rgb = gray


    # ==========================================
    # SLIDE 2: Act I: The Month-End Crisis (0:00 - 0:15)
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_bg(s2)

    # Header
    tb = s2.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.1))
    tf = tb.text_frame
    p0 = tf.paragraphs[0]
    p0.text = "ACT I: THE MONTH-END RECONCILIATION CRISIS [0:00 – 0:15]"
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = crimson
    p1 = tf.add_paragraph()
    p1.text = "Finance Teams Are Drowning in Manual Books While Penalties Compound"
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = white

    # Left Image
    if os.path.exists(crisis_img):
        s2.shapes.add_picture(crisis_img, Inches(0.8), Inches(1.8), width=Inches(6.2), height=Inches(3.48))

    # Right Content Cards
    tb2 = s2.shapes.add_textbox(Inches(7.3), Inches(1.8), Inches(5.2), Inches(5.0))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    pts = [
        ("100+ Hours of Frantic Manual Auditing", "Accountants frantically cross-check thousands of bank ledger feeds, Razorpay receipts, and ERP entries late at night, resulting in inevitable human oversight."),
        ("Statutory Tax Notice Disasters", "Subtle vendor payment delays trigger severe Section 43B(h) non-compliance, automatically disallowing tax deductions and initiating punitive audits."),
        ("Compounding Compound Penalties", "Overlooked MSME vendor invoices rack up mandatory compounding interest at 3x the RBI repo rate—turning minor invoice delays into critical runway drains.")
    ]
    for i, (title, desc) in enumerate(pts):
        pt = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        pt.text = f"🚨 {title}"
        pt.font.bold = True
        pt.font.size = Pt(14)
        pt.font.color.rgb = crimson
        pt.space_after = Pt(3)
        pd = tf2.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(12)
        pd.font.color.rgb = gray
        pd.space_after = Pt(14)

    # Stat bar at bottom
    bar = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.6), Inches(6.2), Inches(1.2))
    bar.fill.solid()
    bar.fill.fore_color.rgb = card_bg
    bar.line.color.rgb = crimson
    btf = bar.text_frame
    bp = btf.paragraphs[0]
    bp.alignment = PP_ALIGN.CENTER
    bp.text = "SURGING PENALTY ACCUMULATION TICKER"
    bp.font.size = Pt(10)
    bp.font.bold = True
    bp.font.color.rgb = crimson
    bp2 = btf.add_paragraph()
    bp2.alignment = PP_ALIGN.CENTER
    bp2.text = "₹4,85,000"
    bp2.font.size = Pt(28)
    bp2.font.bold = True
    bp2.font.color.rgb = crimson


    # ==========================================
    # SLIDE 3: Act I Cont.: The 3 Compliance Landmines (0:15 - 0:45)
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_bg(s3)

    # Header
    tb = s3.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.1))
    tf = tb.text_frame
    p0 = tf.paragraphs[0]
    p0.text = "THE HIGH-STAKES PROBLEM [0:15 – 0:45]"
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = amber
    p1 = tf.add_paragraph()
    p1.text = "The 3 Biggest Indian Regulatory Landmines Destroying Cash Runway"
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = white

    # 3D Diagram Visual in Center
    if os.path.exists(landmines_img):
        s3.shapes.add_picture(landmines_img, Inches(0.8), Inches(1.7), width=Inches(6.2), height=Inches(3.48))

    # Right 3 Detailed Cards
    tb3 = s3.shapes.add_textbox(Inches(7.3), Inches(1.7), Inches(5.2), Inches(5.2))
    tf3 = tb3.text_frame
    tf3.word_wrap = True

    c_pts = [
        ("1. TDS Structuring Traps (Sec 194J & 194R)", "Vendors split retainers into multiple invoices below ₹30,000 or disguise perks/laptops as contractor gifts to evade mandatory withholding tax deductions."),
        ("2. Section 43B(h) MSME Mandate", "Strict statutory deadline: All micro & small enterprise invoices must be cleared within 45 days. No grace periods permitted under current law."),
        ("3. Punitive Double-Whammy Liabilities", "Unsettled MSME bills trigger an immediate 30% corporate tax add-back disallowance PLUS mandatory compounding interest at 3x the RBI repo rate.")
    ]
    for i, (title, desc) in enumerate(c_pts):
        pt = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        pt.text = title
        pt.font.bold = True
        pt.font.size = Pt(13.5)
        pt.font.color.rgb = gold
        pt.space_after = Pt(2)
        pd = tf3.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(11.5)
        pd.font.color.rgb = gray
        pd.space_after = Pt(12)

    # Callout Banner Across Bottom
    banner = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.5), Inches(11.7), Inches(1.2))
    banner.fill.solid()
    banner.fill.fore_color.rgb = card_bg
    banner.line.color.rgb = gold
    bntf = banner.text_frame
    bnp = bntf.paragraphs[0]
    bnp.alignment = PP_ALIGN.CENTER
    bnp.text = "⚠️ KEY EXECUTIVE CALLOUT"
    bnp.font.size = Pt(10)
    bnp.font.bold = True
    bnp.font.color.rgb = amber
    bnp2 = bntf.add_paragraph()
    bnp2.alignment = PP_ALIGN.CENTER
    bnp2.text = "\"One delayed invoice can erase an entire quarter's runway.\""
    bnp2.font.size = Pt(18)
    bnp2.font.bold = True
    bnp2.font.color.rgb = gold


    # ==========================================
    # SLIDE 4: Architecture: Two-Stage Reconciler
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_bg(s4)

    # Header
    tb = s4.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.1))
    tf = tb.text_frame
    p0 = tf.paragraphs[0]
    p0.text = "PROPRIETARY TECHNOLOGY ARCHITECTURE"
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = gold
    p1 = tf.add_paragraph()
    p1.text = "Two-Stage Intelligent Audit: Fast Heuristics + Generative Reasoning"
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = white

    # 3 Architecture Columns
    col_w = Inches(3.7)
    gap = Inches(0.3)

    # Col 1: Stage 1
    c1 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), col_w, Inches(4.8))
    c1.fill.solid()
    c1.fill.fore_color.rgb = card_bg
    c1.line.color.rgb = RGBColor(60, 60, 60)
    c1tf = c1.text_frame
    c1tf.word_wrap = True
    p = c1tf.paragraphs[0]
    p.text = "STAGE 1"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = amber
    p2 = c1tf.add_paragraph()
    p2.text = "Deterministic Heuristics (<10ms)"
    p2.font.size = Pt(15)
    p2.font.bold = True
    p2.font.color.rgb = white
    p2.space_after = Pt(12)
    p3 = c1tf.add_paragraph()
    p3.text = "• Instant mathematical transaction matching\n• Exact amount & currency conversions\n• Date proximity threshold verification\n• Bigram Jaccard fuzzy similarity for misspelled vendor names\n• Filter deterministic compliant rows instantly"
    p3.font.size = Pt(12)
    p3.font.color.rgb = gray

    # Col 2: Stage 2
    c2 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8) + col_w + gap, Inches(1.8), col_w, Inches(4.8))
    c2.fill.solid()
    c2.fill.fore_color.rgb = card_bg
    c2.line.color.rgb = gold
    c2tf = c2.text_frame
    c2tf.word_wrap = True
    p = c2tf.paragraphs[0]
    p.text = "STAGE 2"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = gold
    p2 = c2tf.add_paragraph()
    p2.text = "Generative LLM Reasoning"
    p2.font.size = Pt(15)
    p2.font.bold = True
    p2.font.color.rgb = white
    p2.space_after = Pt(12)
    p3 = c2tf.add_paragraph()
    p3.text = "• Powered by Gemini 2.5 / Groq Llama 3.1\n• Detects intentional invoice splitting (TDS 194J)\n• Evaluates contractor perk classification (Sec 194R)\n• Uncovers typo-induced MSME payment delays\n• Generates precise natural language audit trails"
    p3.font.size = Pt(12)
    p3.font.color.rgb = gray

    # Col 3: Actionable Output
    c3 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8) + (col_w*2) + (gap*2), Inches(1.8), col_w, Inches(4.8))
    c3.fill.solid()
    c3.fill.fore_color.rgb = card_bg
    c3.line.color.rgb = emerald
    c3tf = c3.text_frame
    c3tf.word_wrap = True
    p = c3tf.paragraphs[0]
    p.text = "ACTIONABLE OUTPUT"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = emerald
    p2 = c3tf.add_paragraph()
    p2.text = "ERP Sync & Treasury Defense"
    p2.font.size = Pt(15)
    p2.font.bold = True
    p2.font.color.rgb = white
    p2.space_after = Pt(12)
    p3 = c3tf.add_paragraph()
    p3.text = "• Auto-generated balanced double-entry vouchers\n• 1-Click export to QuickBooks (IIF), Xero & CSV\n• Monte Carlo volatility curve simulation\n• Dynamic MSME payment priority optimization\n• Restores 30% tax write-offs while keeping 3mo reserve"
    p3.font.size = Pt(12)
    p3.font.color.rgb = gray


    # ==========================================
    # SLIDE 5: Executive Impact & ROI (4:40 - 4:52)
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_bg(s5)

    # Header
    tb = s5.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.1))
    tf = tb.text_frame
    p0 = tf.paragraphs[0]
    p0.text = "EXECUTIVE SUMMARY [4:40 – 4:52]"
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = emerald
    p1 = tf.add_paragraph()
    p1.text = "Measurable Financial ROI & Operational Value"
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = white

    # Summary Image Left
    if os.path.exists(summary_img):
        s5.shapes.add_picture(summary_img, Inches(0.8), Inches(1.8), width=Inches(6.2), height=Inches(3.48))

    # Right ROI Points
    tb5 = s5.shapes.add_textbox(Inches(7.3), Inches(1.8), Inches(5.2), Inches(5.2))
    tf5 = tb5.text_frame
    tf5.word_wrap = True

    m_pts = [
        ("85% Reduction in Period-Close Time", "Compresses a 3-week chaotic manual reconciliation ordeal into an autonomous 3-minute verified audit run."),
        ("100% Automated Compliance Guarantee", "Eliminates Section 43B(h) and TDS compliance oversights with multi-subsidiary cross-border accuracy (>96% match rate)."),
        ("Real-Time Monte Carlo Treasury Defense", "Replaces blind backward-looking accounting with forward-looking cash depletion forecasting and automated invoice settlement optimization.")
    ]
    for i, (title, desc) in enumerate(m_pts):
        pt = tf5.paragraphs[0] if i == 0 else tf5.add_paragraph()
        pt.text = f"✨ {title}"
        pt.font.bold = True
        pt.font.size = Pt(13.5)
        pt.font.color.rgb = emerald
        pt.space_after = Pt(2)
        pd = tf5.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(12)
        pd.font.color.rgb = gray
        pd.space_after = Pt(16)

    # Bottom Callout Bar
    bbar = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.6), Inches(6.2), Inches(1.2))
    bbar.fill.solid()
    bbar.fill.fore_color.rgb = card_bg
    bbar.line.color.rgb = emerald
    bbtf = bbar.text_frame
    bbp = bbtf.paragraphs[0]
    bbp.alignment = PP_ALIGN.CENTER
    bbp.text = "TESTED ENTERPRISE BENCHMARK"
    bbp.font.size = Pt(10)
    bbp.font.bold = True
    bbp.font.color.rgb = emerald
    bbp2 = bbtf.add_paragraph()
    bbp2.alignment = PP_ALIGN.CENTER
    bbp2.text = "96.4% Accuracy  |  95.0% Precision  |  97.2% Recall"
    bbp2.font.size = Pt(15)
    bbp2.font.bold = True
    bbp2.font.color.rgb = white


    # ==========================================
    # SLIDE 6: Outro & Call to Action (4:52 - 5:00)
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_bg(s6)

    # Outro Image Full Left
    if os.path.exists(outro_img):
        s6.shapes.add_picture(outro_img, Inches(0.8), Inches(1.3), width=Inches(6.4), height=Inches(3.6))

    # Right Call to Action Card
    card_cta = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.5), Inches(1.3), Inches(5.0), Inches(5.4))
    card_cta.fill.solid()
    card_cta.fill.fore_color.rgb = card_bg
    card_cta.line.color.rgb = gold
    ctf = card_cta.text_frame
    ctf.word_wrap = True

    cp0 = ctf.paragraphs[0]
    cp0.text = "THE AUTONOMOUS CONTROLLER"
    cp0.font.size = Pt(11)
    cp0.font.bold = True
    cp0.font.color.rgb = gold
    cp0.space_after = Pt(8)

    cp1 = ctf.add_paragraph()
    cp1.text = "Take Total Control of Your Startup Runway"
    cp1.font.size = Pt(24)
    cp1.font.bold = True
    cp1.font.color.rgb = white
    cp1.space_after = Pt(14)

    cp2 = ctf.add_paragraph()
    cp2.text = "AuraAudit turns weeks of painful, error-prone accounting into a verified, automated treasury cockpit."
    cp2.font.size = Pt(13)
    cp2.font.color.rgb = gray
    cp2.space_after = Pt(20)

    cp3 = ctf.add_paragraph()
    cp3.text = "🚀 Explore Sandbox & Interactive Demo:"
    cp3.font.size = Pt(12)
    cp3.font.bold = True
    cp3.font.color.rgb = amber
    cp3.space_after = Pt(4)

    cp4 = ctf.add_paragraph()
    cp4.text = "auraaudit.ai/demo"
    cp4.font.size = Pt(16)
    cp4.font.bold = True
    cp4.font.color.rgb = gold
    cp4.space_after = Pt(16)

    cp5 = ctf.add_paragraph()
    cp5.text = "💻 Local Workspace: http://localhost:3000\n📫 Contact: founders@auraaudit.ai"
    cp5.font.size = Pt(11)
    cp5.font.color.rgb = gray

    # Save presentation
    output_path = r"c:\Users\paliw\Documents\antigravity\fervent-lavoisier\AuraAudit_Pitch_Extras.pptx"
    prs.save(output_path)
    print(f"Successfully generated: {output_path}")

if __name__ == "__main__":
    create_deck()
