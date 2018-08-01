from osgeo import gdal
import geohash
import json
import time
from tqdm import tqdm
import pygtrie

from rainbow.src.vector import MultiPoint, Polygon, createTransformer
from src import bbox_query, Trie

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
def query_runner(query, tree=None):
    bbox_query(extent, geohash_list, precision=precision, query=query, tree=tree)
    return timerfunc

if __name__ == '__main__':
    builtin_list = []
    trie_list = []
    gtrie_list = []
    trie_cached_list = []
    gtrie_cached_list = []

    iterations = 100

    cached_gtrie = pygtrie.PrefixSet(geohash_list)
    cached_trie = Trie()
    for hash in geohash_list:
        cached_trie.add(hash)

    for item in tqdm(range(iterations)):
        t = query_runner('builtin')
        builtin_list.append(t)

    for item in tqdm(range(iterations)):
        t = query_runner('trie')
        trie_list.append(t)

    for item in tqdm(range(iterations)):
        t = query_runner('gtrie')
        gtrie_list.append(t)

    for item in tqdm(range(iterations)):
        t = query_runner('trie', tree=cached_trie)
        trie_cached_list.append(t)

    for item in tqdm(range(iterations)):
        t = query_runner('gtrie', tree=cached_gtrie)
        gtrie_cached_list.append(t)



    print("Number of Iterations: {}".format(iterations))
    print("Number of GeoHashes: {}".format(iterations))

    print("BuiltIn Query: {}".format(compute_stats(builtin_list)))
    print("Trie Query (with indexing): {}".format(compute_stats(gtrie_list)))
    print("Trie Query (without indexing): {}".format(compute_stats(trie_cached_list)))
    print("GTrie Query (with indexing): {}".format(compute_stats(trie_list)))
    print("GTrie Query (without indexing): {}".format(compute_stats(gtrie_cached_list)))

    # https: // github.com / aosingh / lexpy


