import sys
from tqdm import tqdm
from random import uniform
import geohash

from geohash_utils.src.query import bbox_query, get_tree
from .timers import timerfunc, nostdout


@timerfunc
def _bbox_query_runner(extent, tree, precision):

    """Method to run a prefix query with timing decorator"""

    matching_hashes = bbox_query(extent, tree, precision)
    return

@timerfunc
def _index_runner(geohash_list, query_type):
    tree = get_tree(geohash_list, query_type)
    return tree


def bbox_query_benchmark(extent, tree, precision, iterations):
    time_list = []
    for _ in tqdm(range(iterations), file=sys.stdout):
        with nostdout():
            output = _bbox_query_runner(extent, tree, precision)
            time_list.append(output[1])
    return time_list

def index_query_benchmark(geohash_list, query_type, iterations):
    time_list = []
    for _ in tqdm(range(iterations), file=sys.stdout):
        with nostdout():
            output = _index_runner(geohash_list, query_type)
            time_list.append(output[1])
    return output[0], time_list

def compute_stats(time_list):

    """Method to compute min/mean/max times from a list of times"""

    mean = sum(time_list)/len(time_list)
    mn = min(time_list)
    mx = max(time_list)
    return {'min': mn,
            'max': mx,
            'mean': mean}

def random_hashes(extent, count, precision):

    """Method to randomly generate a list of geohashes within an extent"""

    def newpoint():
        return uniform(extent[0], extent[1]), uniform(extent[2], extent[3])

    points = [newpoint() for _ in range(count)]
    geohash_list = [geohash.encode(x[1], x[0], precision=precision) for x in points]
    return geohash_list

