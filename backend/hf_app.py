"""
=============================================================================
  🌾 CROP RECOMMENDATION SYSTEM — Gradio App
=============================================================================

SETUP (run once):
    pip install gradio pandas scikit-learn joblib

FILES NEEDED in same directory as this script:
    model1_npk.pkl
    model1_label_encoder.pkl
    model2_full_scored.csv

RUN:
    python crop_recommendation_app.py
    → Opens at http://localhost:7860
=============================================================================
"""

import gradio as gr
import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# LOAD MODELS
# ─────────────────────────────────────────────────────────────────────────────
model1     = joblib.load("model1_npk.pkl")
label_enc1 = joblib.load("model1_label_encoder.pkl")
model2_df  = pd.read_csv("model2_full_scored.csv")

DISTRICTS = sorted(model2_df["District"].unique().tolist())
SEASONS   = sorted(model2_df["Season"].unique().tolist())

# Crop name normaliser for cross-model matching
def norm(name):
    return (str(name).strip().lower()
            .replace(" ", "").replace("(", "").replace(")", "")
            .replace("-", "").replace("/", "").replace("&", ""))

# Build normalised lookup for model2 crops
M2_NORM = {norm(c): c for c in model2_df["Crop"].unique()}

# ─────────────────────────────────────────────────────────────────────────────
# CORE LOGIC
# ─────────────────────────────────────────────────────────────────────────────
def model1_scores(N, P, K, temperature, humidity, ph, rainfall):
    X = pd.DataFrame([[N, P, K, temperature, humidity, ph, rainfall]],
                     columns=["N","P","K","temperature","humidity","ph","rainfall"])
    proba = model1.predict_proba(X)[0]
    return {c: float(p) for c, p in zip(label_enc1.classes_, proba)}

def model2_scores(district, season):
    region = model2_df[
        (model2_df["District"] == district) &
        (model2_df["Season"]   == season)
    ]
    if region.empty:
        return {}
    return dict(zip(region["Crop"], region["Suitability_Score"].astype(float)))

def recommend(N, P, K, temperature, humidity, ph, rainfall,
              district, season, w_model1, top_n):
    w_model2 = round(1 - w_model1, 2)

    m1 = model1_scores(N, P, K, temperature, humidity, ph, rainfall)
    m2 = model2_scores(district, season)

    m1_norm_map = {norm(k): (k, v) for k, v in m1.items()}
    m2_norm_map = {norm(k): (k, v) for k, v in m2.items()}
    all_keys    = set(m1_norm_map) | set(m2_norm_map)

    rows = []
    for key in all_keys:
        _, s1 = m1_norm_map.get(key, (key, 0.0))
        crop_display, s2 = m2_norm_map.get(key, (key, 0.0))
        if key not in m2_norm_map:
            crop_display = m1_norm_map[key][0].title()

        combined = round(w_model1 * s1 + w_model2 * s2, 4)

        region_row = model2_df[
            (model2_df["District"] == district) &
            (model2_df["Season"]   == season) &
            (model2_df["Crop"].apply(norm) == key)
        ]
        reg_label   = region_row["Recommendation"].values[0]   if not region_row.empty else "No regional data"
        hist_grown  = int(region_row["Is_Historically_Grown"].values[0]) if not region_row.empty else 0
        avg_yield   = round(float(region_row["Avg_Yield"].values[0]), 2) if not region_row.empty else 0.0
        freq_pct    = round(float(region_row["Crop_Freq_Pct"].values[0]), 1) if not region_row.empty else 0.0

        rows.append({
            "Crop"              : crop_display,
            "Combined Score"    : combined,
            "Confidence %"      : round(combined * 100, 1),
            "NPK Score"         : round(s1 * 100, 1),
            "Region Score"      : round(s2 * 100, 1),
            "Region Suitability": reg_label,
            "Grown % of Years"  : freq_pct,
            "Avg Yield (T/Ha)"  : avg_yield,
            "Historically Grown": "✅ Yes" if hist_grown else "❌ No",
        })

    df_result = (pd.DataFrame(rows)
                   .sort_values("Combined Score", ascending=False)
                   .head(int(top_n))
                   .reset_index(drop=True))
    df_result.index += 1
    df_result.drop(columns=["Combined Score"], inplace=True)

    # Medal emoji for top 3
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    df_result["Rank"] = [medals.get(i, f"#{i}") for i in df_result.index]
    cols = ["Rank", "Crop", "Confidence %", "NPK Score", "Region Score",
            "Region Suitability", "Grown % of Years", "Avg Yield (T/Ha)", "Historically Grown"]
    return df_result[cols]

# ─────────────────────────────────────────────────────────────────────────────
# GRADIO UI
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
/* ── Global ── */
body, .gradio-container {
    font-family: 'Georgia', serif !important;
    background: #0e1a0e !important;
    color: #e8f5e8 !important;
}

/* ── Header banner ── */
#header {
    background: linear-gradient(135deg, #1a3a1a 0%, #0d2b0d 50%, #162d16 100%);
    border: 1px solid #2d5a2d;
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 4px;
    box-shadow: 0 4px 32px rgba(0,80,0,0.4), inset 0 1px 0 rgba(100,200,100,0.1);
}
#header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    color: #7dcd7d;
    letter-spacing: -0.5px;
    margin: 0 0 6px 0;
    text-shadow: 0 0 20px rgba(125,205,125,0.3);
}
#header p {
    color: #8ab88a;
    font-size: 0.95rem;
    margin: 0;
    font-style: italic;
}

/* ── Section labels ── */
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #5a9e5a;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #1e3d1e;
}

/* ── Panels ── */
.panel {
    background: #111f11 !important;
    border: 1px solid #1e3d1e !important;
    border-radius: 12px !important;
    padding: 20px !important;
}

/* ── Inputs ── */
label span {
    color: #8ab88a !important;
    font-size: 0.82rem !important;
    font-family: 'Georgia', serif !important;
}
input[type=number], input[type=text], select, textarea,
.gr-input, .gr-box {
    background: #0a150a !important;
    border: 1px solid #2a4a2a !important;
    color: #c8e8c8 !important;
    border-radius: 8px !important;
    font-family: 'Georgia', serif !important;
}
input:focus, select:focus {
    border-color: #4a8a4a !important;
    box-shadow: 0 0 0 2px rgba(74,138,74,0.2) !important;
    outline: none !important;
}

/* ── Sliders ── */
.gr-slider input[type=range] {
    accent-color: #5aaa5a !important;
}

/* ── Button ── */
#submit-btn {
    background: linear-gradient(135deg, #2d6e2d, #1a4a1a) !important;
    color: #c8f0c8 !important;
    border: 1px solid #3a7a3a !important;
    border-radius: 10px !important;
    font-family: 'Georgia', serif !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    padding: 14px 0 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 12px rgba(0,80,0,0.3) !important;
}
#submit-btn:hover {
    background: linear-gradient(135deg, #3a8a3a, #235a23) !important;
    box-shadow: 0 4px 20px rgba(0,120,0,0.4) !important;
    transform: translateY(-1px) !important;
}

/* ── Output table ── */
.gr-dataframe, table {
    background: #0a150a !important;
    border: 1px solid #1e3d1e !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    font-family: 'Georgia', serif !important;
}
table thead tr th {
    background: #132613 !important;
    color: #7dcd7d !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    padding: 12px 10px !important;
    border-bottom: 1px solid #2a4a2a !important;
}
table tbody tr td {
    color: #c0dcc0 !important;
    font-size: 0.88rem !important;
    padding: 10px 10px !important;
    border-bottom: 1px solid #141f14 !important;
}
table tbody tr:first-child td { color: #ffe57a !important; font-weight: 700 !important; }
table tbody tr:nth-child(2) td { color: #d0d0d0 !important; }
table tbody tr:nth-child(3) td { color: #e0a060 !important; }
table tbody tr:hover td {
    background: #162616 !important;
}

/* ── Tips box ── */
#tips {
    background: #0c1e0c;
    border: 1px solid #1a3a1a;
    border-left: 3px solid #4a8a4a;
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 0.82rem;
    color: #7aaa7a;
    line-height: 1.7;
}

/* ── Tabs ── */
.tab-nav button {
    background: transparent !important;
    color: #5a8a5a !important;
    border: none !important;
    font-family: 'Georgia', serif !important;
    font-size: 0.9rem !important;
    padding: 10px 20px !important;
    border-bottom: 2px solid transparent !important;
}
.tab-nav button.selected {
    color: #7dcd7d !important;
    border-bottom: 2px solid #4a8a4a !important;
}
"""

def run_recommend(N, P, K, temperature, humidity, ph, rainfall,
                  district, season, w_model1, top_n):
    try:
        result = recommend(N, P, K, temperature, humidity, ph, rainfall,
                           district, season, w_model1, int(top_n))
        return result
    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})

with gr.Blocks(css=CSS, title="🌾 Crop Recommendation System") as app:

    gr.HTML("""
    <div id="header">
        <h1>🌾 Crop Recommendation System</h1>
        <p>AI-powered crop advisory combining soil science (Model 1) with regional farming patterns (Model 2) — Maharashtra</p>
    </div>
    """)

    with gr.Tabs():

        # ── TAB 1: Recommend ──────────────────────────────────────────────────
        with gr.Tab("🔍 Get Recommendation"):
            with gr.Row():

                # Left — Soil & Climate
                with gr.Column(scale=1, elem_classes=["panel"]):
                    gr.HTML('<div class="section-label">🧪 Soil Nutrients</div>')
                    with gr.Row():
                        N_input = gr.Number(label="Nitrogen (N) mg/kg", value=90, minimum=0, maximum=300)
                        P_input = gr.Number(label="Phosphorus (P) mg/kg", value=42, minimum=0, maximum=300)
                    with gr.Row():
                        K_input = gr.Number(label="Potassium (K) mg/kg", value=43, minimum=0, maximum=300)
                        ph_input = gr.Slider(label="Soil pH", minimum=3.5, maximum=9.5, value=6.5, step=0.1)

                    gr.HTML('<div class="section-label" style="margin-top:18px">🌡️ Climate</div>')
                    with gr.Row():
                        temp_input     = gr.Number(label="Temperature (°C)", value=25, minimum=5, maximum=50)
                        humidity_input = gr.Number(label="Humidity (%)", value=80, minimum=10, maximum=100)
                    rainfall_input = gr.Number(label="Annual Rainfall (mm)", value=200, minimum=20, maximum=3000)

                # Right — Location & Config
                with gr.Column(scale=1, elem_classes=["panel"]):
                    gr.HTML('<div class="section-label">📍 Location</div>')
                    district_input = gr.Dropdown(label="District", choices=DISTRICTS, value="Akola")
                    season_input   = gr.Dropdown(label="Season",   choices=SEASONS,   value="Kharif")

                    gr.HTML('<div class="section-label" style="margin-top:18px">⚙️ Model Weights</div>')
                    w1_input  = gr.Slider(label="NPK Model Weight (rest goes to Region Model)",
                                          minimum=0.1, maximum=0.9, value=0.6, step=0.05)
                    top_n_input = gr.Slider(label="Top N Crops to Show",
                                            minimum=3, maximum=10, value=5, step=1)

                    gr.HTML('<div id="tips">💡 <b>Tips:</b><br>'
                            '• Kharif = Jun–Sep (monsoon)&nbsp;&nbsp;|&nbsp;&nbsp;Rabi = Oct–Mar (winter)<br>'
                            '• Higher NPK weight = more soil-driven<br>'
                            '• "Historically Grown ✅" means farmers here grow this crop regularly</div>')

                    submit_btn = gr.Button("🌱 Recommend Crops", elem_id="submit-btn")

            # Output table
            gr.HTML('<div class="section-label" style="margin-top:20px">🏆 Recommendations</div>')
            output_table = gr.Dataframe(
                label="",
                wrap=True,
                interactive=False,
            )

            submit_btn.click(
                fn=run_recommend,
                inputs=[N_input, P_input, K_input, temp_input, humidity_input,
                        ph_input, rainfall_input, district_input, season_input,
                        w1_input, top_n_input],
                outputs=output_table
            )

        # ── TAB 2: Regional Browser ────────────────────────────────────────────
        with gr.Tab("🗺️ Regional Crop Browser"):
            gr.HTML('<p style="color:#7aaa7a;font-style:italic;margin-bottom:16px">'
                    'Browse pre-computed regional crop suitability scores — no soil data needed.</p>')
            with gr.Row():
                browse_district = gr.Dropdown(label="District", choices=DISTRICTS, value="Pune")
                browse_season   = gr.Dropdown(label="Season",   choices=SEASONS,   value="Rabi")
                browse_top_n    = gr.Slider(label="Top N",  minimum=3, maximum=15, value=8, step=1)
                browse_btn      = gr.Button("Browse →", scale=0)

            browse_output = gr.Dataframe(label="", interactive=False, wrap=True)

            def browse_region(district, season, top_n):
                region = model2_df[
                    (model2_df["District"] == district) &
                    (model2_df["Season"]   == season)
                ].sort_values("Suitability_Score", ascending=False).head(int(top_n)).reset_index(drop=True)
                region.index += 1
                medals = {1:"🥇",2:"🥈",3:"🥉"}
                out = region[["Crop","Suitability_Pct","Recommendation",
                               "Crop_Freq_Pct","Avg_Yield","Dominance_Rate","Recent_Years_Grown"]].copy()
                out.insert(0, "Rank", [medals.get(i, f"#{i}") for i in out.index])
                out.columns = ["Rank","Crop","Score (%)","Suitability",
                                "Grown (% of Yrs)","Avg Yield (T/Ha)","Dominated (%)","Recent Yrs (post-2015)"]
                return out

            browse_btn.click(fn=browse_region,
                             inputs=[browse_district, browse_season, browse_top_n],
                             outputs=browse_output)

        # ── TAB 3: About ──────────────────────────────────────────────────────
        with gr.Tab("ℹ️ About"):
            gr.HTML("""
            <div style="max-width:700px;line-height:1.9;color:#9ac89a;font-size:0.92rem;padding:10px 0">
                <h3 style="color:#7dcd7d;margin-bottom:16px">How This System Works</h3>

                <b style="color:#b0d8b0">Model 1 — NPK / Soil & Climate (Random Forest)</b><br>
                Trained on 2,200 samples across 22 crops. Inputs: N, P, K, Temperature, Humidity, pH, Rainfall.
                Cross-validation accuracy: <b style="color:#7dcd7d">99.6%</b>.<br><br>

                <b style="color:#b0d8b0">Model 2 — Regional Suitability (Weighted Scoring)</b><br>
                No ML training. Uses 26 years of Maharashtra district-level crop data (1997–2022).
                Covers 35 districts × 4 seasons × 33 crops = 1,603 scored combinations.<br>
                Score formula: <code style="color:#7dcd7d">0.35×Frequency + 0.25×Historical + 0.20×Yield + 0.10×Dominance + 0.10×Recency</code><br><br>

                <b style="color:#b0d8b0">Combined Score</b><br>
                <code style="color:#7dcd7d">Final = w₁ × Model1_prob + w₂ × Model2_score</code><br>
                Default weights: 60% NPK model, 40% Region model. Adjustable via slider.<br><br>

                <b style="color:#b0d8b0">Suitability Labels</b><br>
                🟢 Highly Suitable (≥75%) &nbsp;|&nbsp; 🟡 Moderately Suitable (≥50%)
                &nbsp;|&nbsp; 🟠 Low Suitability (≥30%) &nbsp;|&nbsp; 🔴 Not Recommended (&lt;30%)<br><br>

                <b style="color:#b0d8b0">Data Coverage</b><br>
                State: Maharashtra &nbsp;|&nbsp; Seasons: Kharif, Rabi, Summer, Whole Year
                &nbsp;|&nbsp; Years: 1997–2022
            </div>
            """)

    # Auto-run on load with defaults
    app.load(
        fn=run_recommend,
        inputs=[N_input, P_input, K_input, temp_input, humidity_input,
                ph_input, rainfall_input, district_input, season_input,
                w1_input, top_n_input],
        outputs=output_table
    )

if __name__ == "__main__":
    print("\n🌾 Starting Crop Recommendation System...")
    print("→ Open: http://localhost:7860\n")
    app.launch()  # HuggingFace Spaces handles hosting automatically
