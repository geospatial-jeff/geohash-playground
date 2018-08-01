import geohash
import pygtrie
import time

from rainbow.src.vector import wktBoundBox, Polygon, createTransformer, Point, MultiPoint
from .trie import Trie

precision_size = {'1': [500.94e4, 499.26e4],
                  '2': [125.23e4, 624.1e3],
                  '3': [156.1e3, 156.1e3],
                  '4': [39.1e3, 39.1e3],
                  '5': [4.9e3, 4.9e3],
                  '6': [1.2e3, 609.4],
                  '7': [152.9, 152.4],
                  '8': [38.2, 19],
                  '9': [4.8, 4.8],
                  '10': [1.2, 0.595],
                  '11': [0.149, 0.149],
                  '12': [0.037, 0.019]
                  }

def bbox_query(extent, geohash_list, precision, query='builtin'):
    """Method to query a list of geohashes from an input extent (bounding box query)"""
    #extent format (xmin, xmax, ymin, ymax)

    def _prefix_query(geohash_list, prefix, query):
        if query == 'builtin':
            return query_builtin(geohash_list, prefix)
        elif query == 'trie':
            return query_trie(geohash_list, prefix)
        elif query == 'gtrie':
            return query_pygtrie(geohash_list, prefix)

    tl_hash = geohash.encode(extent[3], extent[0], precision=precision)
    tr_hash = geohash.encode(extent[3], extent[1], precision=precision)
    br_hash = geohash.encode(extent[2], extent[1], precision=precision)
    bl_hash = geohash.encode(extent[2], extent[0], precision=precision)

    common_hash = commonprefix([tl_hash, tr_hash, br_hash, bl_hash])

    intersecting_hashes = _prefix_query(geohash_list, common_hash, query)
    print(len(intersecting_hashes))
    centroids = [geohash.decode(x)[::-1] for x in intersecting_hashes]

    xspace = x_spacing(centroids)
    yspace = y_spacing(centroids)

    valid_list = []

    for idx, hash in enumerate(intersecting_hashes):
        centroid = centroids[idx]
        if centroid[0] < extent[1]+xspace*0.5 and centroid[0] > extent[0]-xspace*0.5 and centroid[1] < extent[3]+yspace*0.5 and centroid[1] > extent[2]-yspace*0.5:
            valid_list.append(hash)
    return valid_list

def y_spacing(centroids):
    """Row length is unknown, need to iterate through each row until we get to the next column"""
    l = centroids.copy()
    first_y = l[0][1]
    while l[0][1] == first_y:
        l.pop(0)
    return abs(first_y - l[0][1])

def x_spacing(centroids):
    return abs(centroids[0][0] - centroids[1][0])

def encode_extent(extent, precision):
    tl_hash = geohash.encode(extent[3], extent[0], precision=precision)
    tr_hash = geohash.encode(extent[3], extent[1], precision=precision)
    br_hash = geohash.encode(extent[2], extent[1], precision=precision)
    bl_hash = geohash.encode(extent[2], extent[0], precision=precision)
    return commonprefix([tl_hash, tr_hash, br_hash, bl_hash])

def decode_extent(extent):
    decoded = geohash.bbox(extent)
    return [decoded['w'], decoded['e'], decoded['s'], decoded['n']]

def extent_overlap(extent, precision):
    """Returns the jaccard index of an extent and its encoded > decoded pair."""
    decoded = decode_extent(encode_extent(extent, precision))
    decoded_poly = Polygon(wktBoundBox(decoded))
    original_poly = Polygon(wktBoundBox(extent))

    #Jaccard Index
    jac_index = decoded_poly.Intersection(original_poly.geom).Area() / decoded_poly.Union(original_poly.geom).Area()
    return jac_index

def commonprefix(m):
    "Given a list of strings, returns the longest common leading component"
    if not m: return ''
    s1 = min(m)
    s2 = max(m)
    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s1

def query_builtin(geohash_list, common_hash):
    start = time.time()
    output = [x for x in geohash_list if x.startswith(common_hash)]
    print ("Query Time: {}".format(time.time()-start))
    return output

def query_trie(geohash_list, common_hash):
    trie = Trie()
    for hash in geohash_list:
        trie.add(hash)
    start = time.time()
    output = trie.start_with_prefix(common_hash)
    print ("Query Time: {}".format(time.time()-start))
    return output

def query_pygtrie(geohash_list, common_hash):
    trie = pygtrie.PrefixSet(geohash_list)
    for hash in geohash_list:
        trie.add(hash)
    start = time.time()
    output = [''.join(x) for x in list(trie.iter(common_hash))]
    print("Query Time: {}".format(time.time()-start))
    return output
