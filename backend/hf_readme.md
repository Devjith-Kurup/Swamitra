---
license: mit
---

# 🌾 Crop Recommendation System — Maharashtra

A dual-model AI system that recommends the most suitable crops for a given location by combining **soil & climate science** with **26 years of regional farming data** from Maharashtra.

## 🧠 How It Works

This system uses two models that work together:

### Model 1 — Soil & Climate Model (Random Forest)
Predicts crop suitability from soil nutrient levels and weather conditions.

- **Library:** scikit-learn
- **Algorithm:** Random Forest Classifier
- **Training data:** 2,200 samples across 22 crops (100 per crop)
- **Cross-validation accuracy:** 99.6% (5-fold stratified)
- **Format:** joblib / pickle (`.pkl`)

### Model 2 — Regional Suitability Model (Weighted Scoring)
Scores crops based on 26 years of district-level agricultural data (1997–2022) across Maharashtra. No ML training — uses a transparent weighted formula.

- **Data source:** Maharashtra district crop production records
- **Coverage:** 35 districts × 4 seasons × 33 crops = 1,603 scored combinations
- **Scoring formula:**
  ```
  Score = 0.35 × Crop Frequency %
        + 0.25 × Is Historically Grown (≥50% of years)
        + 0.20 × Normalized Avg Yield
        + 0.10 × Dominance Rate
        + 0.05 × Recent Years Grown (post-2015)
        + 0.05 × Yield Stability
  ```

### Combined Output
```
Final Score = w₁ × Model1_probability + w₂ × Model2_score
```
Default weights: **60% soil/climate + 40% regional**. Adjustable via slider.

## 📥 Input Features

### Soil & Climate (Model 1)

| Feature | Range | Unit |
|---|---|---|
| N (Nitrogen) | 0 – 300 | mg/kg |
| P (Phosphorus) | 0 – 300 | mg/kg |
| K (Potassium) | 0 – 300 | mg/kg |
| Temperature | 5 – 50 | °C |
| Humidity | 10 – 100 | % |
| pH | 3.5 – 9.5 | — |
| Rainfall | 20 – 3000 | mm/year |

### Location (Model 2)

| Feature | Options |
|---|---|
| State | Maharashtra |
| District | 35 districts (Ahilyanagar, Akola, Amravati, Beed, Bhandara, Buldhana, Chandrapur, Chhatrapati Sambhajinagar, Dharashiv, Dhule, Gadchiroli, Gondia, Hingoli, Jalgaon, Jalna, Kolhapur, Latur, Mumbai suburban, Nagpur, Nanded, Nandurbar, Nashik, Palghar, Parbhani, Pune, Raigad, Ratnagiri, Sangli, Satara, Sindhudurg, Solapur, Thane, Wardha, Washim, Yavatmal) |
| Season | Kharif · Rabi · Summer · Whole Year |

## 📤 Output

A ranked table of top-N crops with:

| Column | Description |
|---|---|
| Rank | 🥇🥈🥉 for top 3 |
| Crop | Recommended crop name |
| Confidence % | Combined score as percentage |
| NPK Score | Model 1 probability score |
| Region Score | Model 2 suitability score |
| Region Suitability | Highly Suitable / Moderately Suitable / Low / Not Recommended |
| Grown % of Years | How consistently this crop is grown in the selected district |
| Avg Yield (T/Ha) | Historical average yield in that district |
| Historically Grown | Whether this crop has strong regional presence |

## 🌱 Crops Covered

**Model 1 — Soil/Climate (22 crops):**
Apple, Banana, Blackgram, Chickpea, Coconut, Coffee, Cotton, Grapes, Jute, Kidneybeans, Lentil, Maize, Mango, Mothbeans, Mungbean, Muskmelon, Orange, Papaya, Pigeonpeas, Pomegranate, Rice, Watermelon

**Model 2 — Regional (33 crops):**
Arhar/Tur, Bajra, Banana, Castor seed, Cotton, Gram, Grapes, Groundnut, Jowar, Linseed, Maize, Mango, Moong (Green Gram), Niger seed, Onion, Other Cereals, Other Kharif pulses, Other Rabi pulses, Other Summer Pulses, Ragi, Rapeseed & Mustard, Rice, Safflower, Sesamum, Small millets, Soyabean, Sugarcane, Sunflower, Tobacco, Tomato, Urad, Wheat, Other oilseeds

## 💻 Usage (API / Local)

```python
from huggingface_hub import hf_hub_download
import joblib, pandas as pd, numpy as np
# Load Model 1
model1    = joblib.load(hf_hub_download("Sheshank2609/crop-recommendation-system", "model1_npk.pkl"))
label_enc = joblib.load(hf_hub_download("Sheshank2609/crop-recommendation-system", "model1_label_encoder.pkl"))
# Load Model 2 scoring table
model2_df = pd.read_csv(hf_hub_download("Sheshank2609/crop-recommendation-system", "model2_full_scored.csv"))
# --- Model 1: Predict from soil/climate ---
features = np.array([[90, 42, 43, 25, 80, 6.5, 200]])   # N, P, K, temp, humidity, pH, rainfall
proba    = model1.predict_proba(features)[0]
m1_scores = dict(zip(label_enc.classes_, proba))
print("Top soil/climate match:", max(m1_scores, key=m1_scores.get))
# --- Model 2: Regional scores for a district/season ---
region = model2_df[
    (model2_df["District"] == "Akola") &
    (model2_df["Season"]   == "Kharif")
].sort_values("Suitability_Score", ascending=False)
print(region[["Crop", "Suitability_Pct", "Recommendation"]].head(5).to_string(index=False))
```

## 🗂️ Files in This Space

| File | Description |
|---|---|
| `app.py` | Gradio application |
| `model1_npk.pkl` | Trained Random Forest (soil & climate) |
| `model1_label_encoder.pkl` | Crop label encoder for Model 1 |
| `model2_full_scored.csv` | Pre-computed regional suitability scores |
| `requirements.txt` | Python dependencies |

## 📊 Data Coverage

| | Details |
|---|---|
| State | Maharashtra, India |
| Districts | 35 |
| Seasons | Kharif (Jun–Sep), Rabi (Oct–Mar), Summer (Apr–Jun), Whole Year |
| Year range | 1997 – 2022 (26 years) |
| Data source | Maharashtra district-level crop production statistics |


## 🏷️ Suitability Labels

| Label | Score Range | Meaning |
|---|---|---|
| 🟢 Highly Suitable | ≥ 75% | Crop is strongly recommended for this region/season |
| 🟡 Moderately Suitable | 50–74% | Good candidate, moderate regional history |
| 🟠 Low Suitability | 30–49% | Possible but limited regional evidence |
| 🔴 Not Recommended | < 30% | Little to no history of this crop in this district |


## 👨‍💻 Developer

**Sheshank2609**
Built as part of an end-to-end crop advisory AI system combining agronomic science with region-specific farming intelligence for Maharashtra farmers.