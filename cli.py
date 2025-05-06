import argparse
import pandas as pd
import json
import os
import sys
from shapely import wkt

# Import visualization directly (this should work regardless of OSMnx version)
from src.visualization import plot_quality_streets

try:
    from src.extract import load_network, extract_edges, assess_street_quality, load_and_process
    from src.prediction.train import prepare_model_data, build_model, save_model
    from src.prediction.evaluate import evaluate_model
    from src.prediction.apply import predict_quality_streets, transfer_model
    from src.prediction.utils import find_available_models, analyze_features
    from src.adapters import list_adapters
    ADAPTER_IMPORTS_OK = True
except Exception as e:
    print(
        f"Warning: Some imports failed. Certain commands may be unavailable: {e}")
    ADAPTER_IMPORTS_OK = False


def main():
    parser = argparse.ArgumentParser('Street Quality Tool')
    sub = parser.add_subparsers(dest='cmd', required=True)

    # Extract command
    p1 = sub.add_parser(
        'extract', help='Extract & score edges from data source')
    p1.add_argument('-s', '--source', default='Tokyo, JP',
                    help='Place name, file path, or connection string')
    p1.add_argument('-n', '--network',
                    choices=['drive', 'bike', 'walk', 'all'], default='drive',
                    help='Network type to extract')
    p1.add_argument('-o', '--output', help='Output path for CSV file')
    p1.add_argument('-a', '--adapter', help='Explicit adapter type to use')
    p1.add_argument('-c', '--config',
                    help='Path to JSON config file for adapter')

    # Train command
    p2 = sub.add_parser(
        'train', help='Train a model to predict street quality')
    p2.add_argument('-s', '--source', default='Tokyo, JP',
                    help='Place name, file path, or connection string')
    p2.add_argument('-n', '--network',
                    choices=['drive', 'bike', 'walk', 'all'], default='drive',
                    help='Network type to extract')
    p2.add_argument('-o', '--output-dir', default='models',
                    help='Directory to save the trained model')
    p2.add_argument('-a', '--adapter', help='Explicit adapter type to use')
    p2.add_argument('-c', '--config',
                    help='Path to JSON config file for adapter')
    p2.add_argument('--analyze', action='store_true',
                    help='Analyze features before training')

    # Apply command
    p3 = sub.add_parser('apply', help='Apply a trained model to a new region')
    p3.add_argument('-m', '--model', required=True,
                    help='Path to trained model file')
    p3.add_argument('-s', '--source', required=True,
                    help='New region to apply the model to')
    p3.add_argument('-n', '--network',
                    choices=['drive', 'bike', 'walk', 'all'], default='drive',
                    help='Network type to extract')
    p3.add_argument('-o', '--output-dir', default='.',
                    help='Directory to save the output CSV')
    p3.add_argument('-a', '--adapter', help='Explicit adapter type to use')
    p3.add_argument('-c', '--config',
                    help='Path to JSON config file for adapter')

    # List models command
    p4 = sub.add_parser(
        'list-models', help='List all available trained models')
    p4.add_argument('-d', '--models-dir', default='models',
                    help='Directory containing trained models')

    # List adapters command
    p5 = sub.add_parser(
        'list-adapters', help='List all available data source adapters')

    # Visualize command
    p6 = sub.add_parser('visualize', help='Visualize street quality')
    p6.add_argument('-i', '--input', required=True,
                    help='Path to CSV of edges with quality scores')
    p6.add_argument('-o', '--output', default='map',
                    help='Output filename (without extension)')
    p6.add_argument('-g', '--graph',
                    help='Optional: include original graph for context')
    p6.add_argument('-a', '--adapter',
                    help='Explicit adapter type to use for graph')
    p6.add_argument('-c', '--config',
                    help='Path to JSON config file for adapter')

    args = parser.parse_args()

    adapter_config = None
    if hasattr(args, 'config') and args.config:
        try:
            with open(args.config, 'r') as f:
                adapter_config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load adapter config: {e}")
            adapter_config = None

    requires_adapters = args.cmd in [
        'extract', 'train', 'apply', 'list-adapters'
    ]

    if requires_adapters and not ADAPTER_IMPORTS_OK:
        print(
            f"Error: The '{args.cmd}' command requires adapter modules that could not be imported.")
        print("This might be due to compatibility issues with your OSMnx version.")
        print("Possible solutions:")
        print("1. Install a compatible version of OSMnx")
        print("2. Use only the 'visualize' or 'list-models' commands")
        return

    if args.cmd == 'extract':
        try:
            G = load_network(args.source, args.network,
                             args.adapter, adapter_config)
            edges = extract_edges(G, args.adapter, adapter_config)
            print(f"Extracted {len(edges)} edges")

            quality_streets = assess_street_quality(edges)
            print(
                f"Identified {len(quality_streets)} quality streets ({len(quality_streets)/len(edges):.1%})")

            if args.output:
                output_path = args.output
            else:
                source_name = args.source.replace(', ', '_').replace(' ', '_')
                output_path = f"quality_streets_{source_name}.csv"

            quality_streets.to_csv(output_path, index=False)
            print(f"Saved street quality data to: {output_path}")
        except Exception as e:
            print(f"Error during extraction: {e}")
            return

    elif args.cmd == 'train':
        try:
            os.makedirs(args.output_dir, exist_ok=True)

            G = load_network(args.source, args.network,
                             args.adapter, adapter_config)
            edges = extract_edges(G, args.adapter, adapter_config)
            quality_streets = assess_street_quality(edges)

            if args.analyze:
                print("Analyzing features...")
                analysis_dir = os.path.join(
                    args.output_dir, 'feature_analysis')

                df = edges.copy()
                df['is_quality'] = 0
                df.loc[quality_streets.index, 'is_quality'] = 1

                analyze_features(df, target_column='is_quality',
                                 output_dir=analysis_dir)
                print(f"Feature analysis saved to: {analysis_dir}")

            print("Training model...")
            X, y, features = prepare_model_data(
                edges, quality_streets, target_col='is_quality')
            model, X_test, y_test = build_model(X, y)

            print("Evaluating model...")
            evaluation_dir = os.path.join(args.output_dir, 'evaluation')
            evaluate_model(model, X_test, y_test, output_dir=evaluation_dir)

            save_model(model, features, args.source, model_dir=args.output_dir)
        except Exception as e:
            print(f"Error during training: {e}")
            return

    elif args.cmd == 'apply':
        try:
            transfer_model_kwargs = {
                'model_path': args.model,
                'new_region': args.source,
                'network_type': args.network,
                'output_dir': args.output_dir,
            }

            if args.adapter or adapter_config:
                transfer_model_kwargs['adapter_type'] = args.adapter
                transfer_model_kwargs['adapter_config'] = adapter_config

            quality_streets, output_path = transfer_model(
                **transfer_model_kwargs)

            print(
                f"Predicted {len(quality_streets)} quality streets in {args.source}")
            print(f"Results saved to: {output_path}")
        except Exception as e:
            print(f"Error during model application: {e}")
            return

    elif args.cmd == 'list-models':
        try:
            models = find_available_models(args.models_dir)

            if not models:
                print(
                    f"No trained models found in directory: {args.models_dir}")
            else:
                print(f"Found {len(models)} trained models:")
                print("-" * 80)
                for i, model in enumerate(models, 1):
                    print(f"{i}. Region: {model['region']}")
                    print(f"   File: {model['filename']}")
                    print(f"   Created: {model['creation_date']}")
                    print(f"   Features: {', '.join(model['features'])}")
                    print("-" * 80)
        except Exception as e:
            print(f"Error listing models: {e}")
            return

    elif args.cmd == 'list-adapters':
        try:
            adapters = list_adapters()

            print("Available data source adapters:")
            print("-" * 80)
            for adapter_name, formats in adapters.items():
                print(f"Adapter: {adapter_name}")
                print(f"Supported formats: {', '.join(formats)}")
                print("-" * 80)

            print("\nExample adapter configurations:")
            print("""
    # OSM Adapter Config Example:
    {
        "network_type": "drive",
        "simplify": true,
        "retain_all": false
    }

    # Shapefile Adapter Config Example:
    {
        "feature_mapping": {
            "road_width": "width",
            "road_type": "highway",
            "speed_limit": "maxspeed"
        },
        "crs": "EPSG:4326",
        "encoding": "utf-8"
    }

    # PostGIS Adapter Config Example:
    {
        "connection_string": "postgresql://user:password@host:port/dbname",
        "table_name": "streets",
        "geometry_column": "geom",
        "feature_mapping": {
            "road_width": "width",
            "road_type": "highway"
        },
        "where_clause": "road_type IS NOT NULL",
        "limit": 10000
    }
    """)
        except Exception as e:
            print(f"Error listing adapters: {e}")
            return

    elif args.cmd == 'visualize':
        try:
            print(f"Loading data from: {args.input}")
            df = pd.read_csv(args.input)

            if 'geometry' in df.columns and isinstance(df.geometry.iloc[0], str):
                print("Converting geometry strings to spatial objects...")
                df['geometry'] = df['geometry'].apply(wkt.loads)

            G = None
            if args.graph and ADAPTER_IMPORTS_OK:
                try:
                    print(f"Loading graph for context: {args.graph}")
                    G = load_network(args.graph, adapter_type=args.adapter,
                                     adapter_config=adapter_config)
                except Exception as e:
                    print(f"Warning: Could not load graph: {e}")
                    print("Proceeding with visualization without the background graph.")
            elif args.graph:
                print(
                    "Warning: Graph loading requires adapter modules that couldn't be imported.")
                print("Proceeding with visualization without the background graph.")

            print("Creating dope map visualization...")
            plot_quality_streets(G, df, args.output)
            print(f"Visualization saved to: {args.output}.html")

        except Exception as e:
            print(f"Error during visualization: {e}")
            import traceback
            traceback.print_exc()
            return


if __name__ == '__main__':
    main()
