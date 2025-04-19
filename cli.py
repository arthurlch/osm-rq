import argparse
import pandas as pd

from src.extract import load_network, extract_edges, flag_narrow_streets
from src.visualization import plot_narrow
from src.predict import prepare_model_data, build_model, evaluate_model

# main tooling


def main():
    parser = argparse.ArgumentParser('Narrow Street Tool')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p1 = sub.add_parser('extract')
    p1.add_argument('-s', '--source', default='Tokyo, JP')
    p1.add_argument('-n', '--network',
                    choices=['drive', 'bike', 'walk', 'all'], default='drive')

    p2 = sub.add_parser('predict')
    p2.add_argument('-s', '--source', default='Tokyo, JP')
    p2.add_argument('-n', '--network',
                    choices=['drive', 'bike', 'walk', 'all'], default='drive')

    p3 = sub.add_parser('visualize')
    p3.add_argument('-i', '--input', required=True,
                    help='Path to CSV of edges with scores')
    p3.add_argument('-o', '--output', default='map')

    args = parser.parse_args()

    if args.cmd == 'extract':
        G = load_network(args.source, args.network)
        edges = extract_edges(G)
        print(f"Extracted {len(edges)} edges")

    elif args.cmd == 'predict':
        G = load_network(args.source, args.network)
        edges = extract_edges(G)
        narrow = flag_narrow_streets(edges)
        X, y, feats = prepare_model_data(edges, narrow)
        model, X_test, y_test = build_model(X, y)
        evaluate_model(model, X_test, y_test)

    elif args.cmd == 'visualize':
        df = pd.read_csv(args.input)
        plot_narrow(None, df, args.output)


if __name__ == '__main__':
    main()
