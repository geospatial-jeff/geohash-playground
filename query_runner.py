from osgeo import gdal
import geohash
import json
import time
from tqdm import tqdm
import sys
import contextlib
import pygtrie
from lexpy.trie import Trie as LexpyTrie
from lexpy.dawg import DAWG

from rainbow.src.vector import MultiPoint, Polygon, createTransformer
from src import bbox_query, Trie
from src.query import get_tree

precision=12
geohash_list = []
transformer = createTransformer(3857, 4326)

ds = gdal.OpenEx('/Users/jeff/Documents/Slingshot/DataSources/DGGS/usa_contiguous_24km/grid.shp')
lyr = ds.GetLayer()
for feat in lyr:
    geom = feat.GetGeometryRef()
    poly = Polygon(geom)
    centroid = poly.ReprojectFast(transformer).Centroid().ExportToList()
    ghash = geohash.encode(centroid[1], centroid[0], precision=12)
    geohash_list.append(ghash)

d = {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -111.3961181640625,
              42.38505194970683
            ],
            [
              -110.5611572265625,
              42.38505194970683
            ],
            [
              -110.5611572265625,
              42.97991089691236
            ],
            [
              -111.3961181640625,
              42.97991089691236
            ],
            [
              -111.3961181640625,
              42.38505194970683
            ]
          ]
        ]
      }

p = Polygon(json.dumps(d))
extent = p.Envelope()

def timerfunc(func):
    """
    A timer decorator
    """
    def function_timer(*args, **kwargs):
        """
        A nested function for timing other functions
        """
        start = time.time()
        value = func(*args, **kwargs)
        end = time.time()
        runtime = end - start
        # msg = f"The runtime for {func.__name__} took {runtime} seconds to complete"
        return runtime
    return function_timer

def compute_stats(time_list):
    mean = sum(time_list)/len(time_list)
    mn = min(time_list)
    mx = max(time_list)
    return {'min': mn,
            'max': mx,
            'mean': mean}

@timerfunc
def query_runner(geohash_list, query_type, tree=None):
    bbox_query(extent, geohash_list, precision=precision, query_type=query_type, tree=tree)
    return timerfunc

def benchmark_query(geohash_list, query_type, iterations, index=True):

    def _get_tree():
        if query_type == 'builtin':
            return None
        if not index:
            return get_tree(geohash_list, query_type)
        return None

    time_list = []

    if index:
        print("Query Type: {} (index+query)".format(query_type))
    else:
        print("Query Type: {} (query)".format(query_type))

    tree = _get_tree()
    for _ in tqdm(range(iterations), file=sys.stdout):
        with nostdout():
            t = query_runner(geohash_list, query_type, tree=tree)
            time_list.append(t)
    return compute_stats(time_list)

class DummyFile(object):
  file = None
  def __init__(self, file):
    self.file = file

  def write(self, x):
    # Avoid print() second call (useless \n)
    if len(x.rstrip()) > 0:
        tqdm.write(x, file=self.file)

@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile(sys.stdout)
    yield
    sys.stdout = save_stdout

if __name__ == '__main__':
    iterations = 10
    benchmark_query(geohash_list, 'builtin', iterations)

    #Index = True >> Benchmark will include indexing.
    #Index = False >> Benchmark will not include indexing
    benchmark_query(geohash_list, 'trie', iterations, index=True)
    benchmark_query(geohash_list, 'trie', iterations, index=False)

    benchmark_query(geohash_list, 'gtrie', iterations, index=True)
    benchmark_query(geohash_list, 'gtrie', iterations, index=False)

    benchmark_query(geohash_list, 'lexpy_trie', iterations, index=True)
    benchmark_query(geohash_list, 'lexpy_trie', iterations, index=False)

    benchmark_query(geohash_list, 'lexpy_dawg', iterations, index=True)
    benchmark_query(geohash_list, 'lexpy_dawg', iterations, index=False)
