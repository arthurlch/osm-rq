# Street Quality Predictor

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python: 3.8+">
  <img src="https://img.shields.io/badge/OSM-Data%20Ready-green" alt="OSM: Data Ready">
</p>

A robust toolkit for analyzing street networks to identify and predict high-quality streets based on urban design criteria. The project enables data scientists and urban planners to:

- **Extract** street data from various sources (OSM, GeoJSON, Shapefiles, PostGIS)
- **Assess** streets against quality criteria (width, lanes, speed limits, etc.)
- **Train** machine learning models to predict street quality
- **Apply** trained models to new regions
- **Visualize** results with interactive web maps

## 🚀 Installation

### Basic Installation

```bash
git clone https://github.com/arthurlch/osm-rq.git
cd osm-rq

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Optional Dependencies

For working with OSM PBF files (recommended for large areas):

```bash
pip install pyrosm
```

For advanced visualization capabilities:

```bash
pip install folium matplotlib seaborn
```

## 📖 Core Concepts

### What Makes a "Quality Street"?

The toolkit evaluates streets based on several criteria that contribute to pedestrian-friendly, livable urban spaces:

1. **Narrow width** (< 6 meters)
2. **Single lane** design
3. **Appropriate street type** (residential, living_street, service, etc.)
4. **Service type** (e.g., alley)
5. **Low speed limit** (< 30 km/h)

Each criterion contributes to a quality score (0-1), where higher scores indicate better street quality according to these metrics.

### Machine Learning Approach

The system uses a Random Forest classifier to learn patterns from manually scored streets, enabling:

1. **Feature importance analysis** to understand what factors most influence street quality
2. **Transfer learning** to apply patterns from one city to another
3. **Probability-based scoring** for nuanced quality assessment

## 🛠️ Command Line Interface

All functionality is accessible through the CLI:

### Data Extraction

```bash
# Extract from a place name (uses Nominatim geocoding)
python cli.py extract --source "Tokyo, JP" --network drive

# Extract from a GeoJSON file
python cli.py extract --source "streets.geojson" --adapter geojson

# Extract from a Shapefile with custom configuration
python cli.py extract --source "streets.shp" --adapter shapefile --config shapefile_config.json
```

### Model Training

```bash
# Train a model on extracted data
python cli.py train --source "Tokyo, JP" --network drive --output-dir models

# Train with feature analysis (creates visualizations of feature distributions)
python cli.py train --source "Tokyo, JP" --analyze
```

### Model Application

```bash
# Apply a trained model to a new region
python cli.py apply --model models/street_quality_Tokyo_JP.joblib --source "Kyoto, JP"

# Apply with a different network type
python cli.py apply --model models/street_quality_Tokyo_JP.joblib --source "Kyoto, JP" --network walk
```

### Visualization

```bash
# Create an interactive map from quality streets data
python cli.py visualize --input predicted_quality_Kyoto_JP.csv --output kyoto_map

# Visualize with background context
python cli.py visualize --input quality_streets.csv --graph "Kyoto, JP" --output kyoto_context_map
```

### Utility Commands

```bash
# List available trained models
python cli.py list-models

# List available data adapters
python cli.py list-adapters
```

## 📊 Street Quality Metrics

For each street segment, the quality score is calculated as:

$$
\text{quality\_score} = \frac{1}{J}\sum_{j=1}^{J} C_{j}
$$

Where each criterion $C_j$ is defined as:

| Criterion | Definition | Weight |
|-----------|------------|--------|
| Width < 6m | $C_1 = 1$ if width < 6m, else 0 | $\frac{1}{J}$ |
| Single lane | $C_2 = 1$ if lanes = 1, else 0 | $\frac{1}{J}$ |
| Highway type | $C_3 = 1$ if highway ∈ {residential, living_street, service, track, path, footway}, else 0 | $\frac{1}{J}$ |
| Service type | $C_4 = 1$ if service = "alley", else 0 | $\frac{1}{J}$ |
| Speed limit | $C_5 = 1$ if maxspeed < 30 km/h, else 0 | $\frac{1}{J}$ |

## 🔬 Data Source Adapters

The toolkit supports multiple data sources through a flexible adapter framework:

### Available Adapters

| Adapter | Formats | Use Case |
|---------|---------|----------|
| OSMAdapter | .osm, .osm.pbf | OpenStreetMap data (worldwide coverage) |
| GeoJSONAdapter | .geojson, .json | Open data portals, custom exports |
| ShapefileAdapter | .shp | GIS data, government sources |
| PostGISAdapter | postgresql:// | Database integration, enterprise setups |

### Custom Adapter Configuration

Each adapter supports configuration options for mapping between different schema conventions:

```json
{
  "feature_mapping": {
    "road_width": "width",
    "road_type": "highway",
    "speed_limit": "maxspeed"
  },
  "crs": "EPSG:4326",
  "encoding": "utf-8"
}
```

## 📚 Machine Learning Pipeline

The prediction pipeline follows these steps:

1. **Data Preparation**
   - Feature extraction from street network
   - Target variable creation (is_quality)
   - Train/test split (70%/30%)

2. **Preprocessing**
   - Numeric features: median imputation + standard scaling
   - Categorical features: constant imputation + one-hot encoding

3. **Model Training**
   - Random Forest classifier (100 estimators)
   - Hyperparameter tuning via grid search

4. **Evaluation**
   - Classification metrics (accuracy, precision, recall, F1)
   - ROC and Precision-Recall curves
   - Feature importance analysis

## 🔧 Advanced Usage

### Customizing Quality Criteria

You can modify the quality assessment criteria by editing the `assess_street_quality` function in `src/extract.py`.

### Adding New Features

To incorporate additional features for prediction:

1. Ensure the feature is extracted in the appropriate adapter
2. Update the feature mapping in the adapter configuration
3. Modify the `prepare_model_data` function to include the new feature

### Extending with New Adapters

To support a new data source:

1. Create a new adapter class that extends `StreetDataAdapter`
2. Implement the required methods (`load_data`, `extract_edges`, `get_supported_formats`)
3. Register the adapter with `adapter_registry.register_adapter(YourAdapter, 'your_adapter')`

## 📈 Example Workflow

### 1. Extract & Score Streets in Tokyo

```bash
python cli.py extract --source "Tokyo, JP" --network drive
```

Output:
```
Extracted 24582 edges
Identified 4912 quality streets (20.0%)
Saved street quality data to: quality_streets_Tokyo_JP.csv
```

### 2. Train a Model on Tokyo Data

```bash
python cli.py train --source "Tokyo, JP" --analyze
```

Output:
```
Analyzing features...
Feature analysis saved to: models/feature_analysis
Training model...
Evaluating model...
Accuracy: 0.9214
              precision    recall  f1-score   support
           0       0.94      0.96      0.95      6192
           1       0.86      0.79      0.82      1366
    accuracy                           0.93      7558
   macro avg       0.90      0.88      0.89      7558
weighted avg       0.93      0.93      0.93      7558

Saved: models/evaluation/confusion_matrix.png
Saved: models/evaluation/feature_importance.png
Saved: models/evaluation/roc_curve.png
Saved: models/evaluation/precision_recall_curve.png
Model saved: models/street_quality_Tokyo_JP.joblib
```

### 3. Apply to a New Region (Kyoto)

```bash
python cli.py apply --model models/street_quality_Tokyo_JP.joblib --source "Kyoto, JP"
```

Output:
```
Using model trained on Tokyo, JP to predict quality streets in Kyoto, JP
Extracted 18741 edges from Kyoto, JP
Using features: ['highway', 'lanes', 'maxspeed', 'service', 'length']
Predicted 3982 quality streets out of 18741 total
Results saved to: predicted_quality_Kyoto_JP.csv
```

### 4. Visualize Results

```bash
python cli.py visualize --input predicted_quality_Kyoto_JP.csv --output kyoto_quality_map
```

Output:
```
Loading data from: predicted_quality_Kyoto_JP.csv
Creating dope map visualization...
Visualization saved to: kyoto_quality_map.html
```

## 📚 API Documentation

The toolkit can also be used as a Python library:

```python
from src.extract import load_and_process
from src.prediction.train import build_model, save_model
from src.prediction.apply import predict_quality_streets
from src.visualization import plot_quality_streets

# Extract street data and assess quality
results = load_and_process("Tokyo, JP", network_type="drive")
edges, quality_streets = results['edges'], results['quality_streets']

# Build and train a model
X, y, features = prepare_model_data(edges, quality_streets)
model, X_test, y_test = build_model(X, y)
save_model(model, features, "Tokyo, JP")

# Apply to new data
new_edges = load_and_process("Kyoto, JP")['edges']
predicted_quality = predict_quality_streets(model, new_edges)

# Create visualization
plot_quality_streets(None, predicted_quality, "kyoto_quality_map")
```

## 🧩 Dependencies

- **Core**: pandas, geopandas, numpy, scikit-learn
- **Networking**: osmnx, pyrosm (optional)
- **Visualization**: matplotlib, seaborn, folium
- **Database**: sqlalchemy (for PostGIS)

## 🤝 Contributing

Contributions are welcome! Areas for improvement include:

- Additional quality criteria based on urban design principles
- Support for more data sources and formats
- Advanced ML models beyond Random Forest
- Improved visualization options

## 📜 License

MIT License