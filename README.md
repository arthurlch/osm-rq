# Narrow Streets Predictor

A toolkit for extracting OpenStreetMap data (including `.osm.pbf`),  
scoring each street segment for “narrowness,” and  
training/applying a machine‑learning model to predict narrow streets.

---

## 📦 Installation

```bash
git clone https://github.com/arthurlch/osm-nsp.git
cd narrow-streets

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
# Optional: for .osm.pbf support
pip install pyrosm
```

---

## 🗂️ Project Structure

```
osm-nsp/
├── src/
│   ├── __init__.py
│   ├── pbf_loader.py
│   ├── extract.py
│   ├── visualization.py
│   └── predict.py
└── cli.py
```

---

## 🚀 CLI Usage

All commands are exposed via `cli.py`:

```bash
python cli.py <command> [options]
```

- **extract**  
  Extract & score edges from OSM.  
  ```bash
  python cli.py extract \
    --source "Tokyo, JP" \
    --network drive
  ```

- **predict**  
  Train & evaluate the Random Forest on scored data.  
  ```bash
  python cli.py predict \
    --source "Tokyo, JP" \
    --network drive
  ```

- **visualize**  
  Render a Folium map from a CSV of edges with `score` or `predicted` columns.  
  ```bash
  python cli.py visualize \
    --input path/to/edges_with_scores.csv \
    --output map.html
  ```

---

## 📐 Narrow‑Street Scoring

For each edge *i*, we evaluate *J* boolean criteria \(C_{ij}\in\{0,1\}\).  The narrowness score is:

$$
\mathrm{score}_i \;=\;\frac{1}{J}\sum_{j=1}^{J} C_{ij}
\qquad\bigl(0 \le \mathrm{score}_i \le 1\bigr)
$$

Where each criterion is:

| Criterion                        | Indicator                                                                                            |
|----------------------------------|------------------------------------------------------------------------------------------------------|
| **Width < 6 m**                  | \(C_{i1} = 1\) if \(\text{width}_i < 6\), else 0                                                      |
| **Single lane**                  | \(C_{i2} = 1\) if \(\text{lanes}_i = 1\), else 0                                                     |
| **Highway type ∈ T**             | \(C_{i3} = 1\) if \(\text{highway}_i \in T\), else 0                                                  |
| **Service = “alley”**            | \(C_{i4} = 1\) if \(\text{service}_i = \text{"alley"}\), else 0                                       |
| **Maxspeed < 30 km/h**           | \(C_{i5} = 1\) if \(\text{maxspeed}_i < 30\), else 0                                                 |

<div align="center">
<em>T = {residential, living_street, service, track, path, footway}</em>
</div>

---

## 🤖 Prediction Model

We train a Random Forest classifier to learn a mapping:

$$
f: \mathbf{x}_i \;\longmapsto\; \hat y_i \in \{0,1\}
$$

- **Feature vector** \(\mathbf{x}_i\) includes  
  \(`length`, `lanes`, `maxspeed`, `oneway`, `service`, …`\)  
- **Target** \(\hat y_i = 1\) if edge is narrow, else 0  

### Pipeline

1. **Numeric features**  
   - Impute missing values with median  
   - Standard scale (zero mean, unit variance)  
2. **Categorical features**  
   - Impute missing with constant `"missing"`  
   - One‑hot encode  
3. **Classifier**:  
   ```python
   RandomForestClassifier(
       n_estimators=100,
       random_state=42
   )
   ```

---

## 📊 Evaluation

- **Train/Test split**: 70% / 30%  
- **Metrics printed**:  
  - Accuracy  
  - Precision / Recall / F1 (classification report)  
- **Plots saved**:  
  - `confusion_matrix.png`  
  - `feature_importance.png`  

---

## 🔬 Example Workflow

1. **Extract & Score**  
   ```bash
   python cli.py extract \
     --source "Tokyo, JP" \
     --network drive
   ```
2. **Train & Evaluate**  
   ```bash
   python cli.py predict \
     --source "Tokyo, JP"
   ```
3. **Visualize Results**  
   ```bash
   python cli.py visualize \
     --input narrow_Tokyo_JP.csv \
     --output tokyo_map
   ```
   Then open `tokyo_map.html` in your browser.
