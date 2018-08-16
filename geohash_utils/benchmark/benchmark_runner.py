import json
import matplotlib.pyplot as plt
import pandas as pd
import os
import argparse
import geojson
from shapely.geometry import shape

from geohash_utils.benchmark import index_query_benchmark, bbox_query_benchmark, random_hashes, compute_stats

args = {
    "query_iterations": 30,
    "index_iterations": 1,
    "hash_precision": 3,
    "hash_count": 10,
    "geohash_extent": (-112, -110, 41, 43),
    "query_extent": (-111.4, -110.5, 42, 42.9),
    "outfolder": '/Users/jeff/Documents/PersonalRepos/geohash-playground/benchmark_output'
}

class Polygon():
    """
    https://gist.github.com/sgillies/2217756
    """

    def __init__(self, polygon):
        self.polygon = polygon

    @property
    def __geo_interface__(self):
        return geojson.Polygon(self.polygon)


class FullPaths(argparse.Action):
    """Expand user- and relative-paths"""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))

def cli():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('json_args', help="JSON file with input arguments",
    #                     action=FullPaths)
    # args = parser.parse_args()
    # d = json.loads(open(args.json_args, 'r').read())
    d = args

    query_poly = [[[d['query_extent'][0], d['query_extent'][3]],
                   [d['query_extent'][1], d['query_extent'][3]],
                   [d['query_extent'][1], d['query_extent'][2]],
                   [d['query_extent'][0], d['query_extent'][2]],
                   [d['query_extent'][0], d['query_extent'][3]]]]

    bounds = shape(Polygon(query_poly)).bounds
    bounds = [bounds[0], bounds[2], bounds[1], bounds[3]]

    stats_d = {}
    index_d = {}
    query_d = {}
    trie_list = ["builtin", 'trie', 'gtrie', 'lexpy_trie', 'lexpy_dawg', 'completion_dawg']

    geohash_list = random_hashes(d['geohash_extent'], d['hash_count'], d['hash_precision'])

    for item in trie_list:
        print(f"Running benchmarks for {item}")
        tree, index_times = index_query_benchmark(geohash_list, item, d['index_iterations'])
        query_times = bbox_query_benchmark(bounds, tree, d['hash_precision'], d['query_iterations'])
        tree = None
        stats_d.update({item: {"index": compute_stats(index_times),
                               "query": compute_stats(query_times)}})
        index_d.update({item: index_times})
        query_d.update({item: query_times})

    if not os.path.exists(d['outfolder']):
        os.makedirs(d['outfolder'])

    # Writing the stats to file
    with open(os.path.join(d['outfolder'], 'stats.json'), 'w') as f:
        json.dump(stats_d, f, indent=4)

    # Creating the boxplots
    fig, axes = plt.subplots(2)
    index_df = pd.DataFrame(index_d).boxplot(ax=axes.flatten()[0])
    axes[0].set_title(f"Index Benchmark (n={d['index_iterations']})")
    axes[0].set_ylabel("Seconds")
    query_df = pd.DataFrame(query_d).boxplot(ax=axes.flatten()[1])
    axes[1].set_title(f"Query Benchmark (n={d['query_iterations']})")
    axes[1].set_xlabel("Search Algorithm")
    axes[1].set_ylabel("Seconds")
    plt.tight_layout()
    plt.savefig(os.path.join(d['outfolder'], 'bbox_benchmark.png'))

    # Writing metadata
    meta_d = {"geohash_count": d['hash_count'],
              "geohash_extent": d['geohash_extent'],
              "query_extent": d['query_extent'],
              "precision": d['hash_precision'],
              "query_iterations": d['query_iterations'],
              "index_iterations": d['index_iterations'],
              "outfolder": d['outfolder'],
              }
    with open(os.path.join(d['outfolder'], 'metadata.json'), 'w') as f:
        json.dump(meta_d, f, indent=4)


if __name__== '__main__':
    cli()