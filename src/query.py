import geohash
import pygtrie
import time

from rainbow.src.vector import wktBoundBox, Polygon, createTransformer, Point, MultiPoint
from .trie import Trie as _Trie
from lexpy.trie import Trie as Lexpy_Trie
from lexpy.dawg import DAWG

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

def bbox_query(extent, geohash_list, precision, query_type='builtin', tree=None):
    """Method to query a list of geohashes from an input extent (bounding box query)"""
    #extent format (xmin, xmax, ymin, ymax)

    def _prefix_query(geohash_list, prefix, query_type, tree):
        if query_type == 'builtin':
            return Builtin(geohash_list, tree).prefix_query(prefix)
        elif query_type == 'trie':
            return Trie(geohash_list, tree).prefix_query(prefix)
        elif query_type == 'gtrie':
            return GTrie(geohash_list, tree).prefix_query(prefix)
        elif query_type == 'lexpy_trie':
            return LexpyTrie(geohash_list, tree).prefix_query(prefix)
        elif query_type == 'lexpy_dawg':
            return LexpyDawg(geohash_list, tree).prefix_query(prefix)

    tl_hash = geohash.encode(extent[3], extent[0], precision=precision)
    tr_hash = geohash.encode(extent[3], extent[1], precision=precision)
    br_hash = geohash.encode(extent[2], extent[1], precision=precision)
    bl_hash = geohash.encode(extent[2], extent[0], precision=precision)

    common_hash = commonprefix([tl_hash, tr_hash, br_hash, bl_hash])

    intersecting_hashes = _prefix_query(geohash_list, common_hash, query_type, tree)
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


"""--------------------------- BENCHMARKING ------------------------------"""

def build_lexpy_dawg(geohash_list):
    dawg = DAWG()
    dawg.add_all(geohash_list)
    dawg.reduce()
    return dawg

def build_lexpy_trie(geohash_list):
    trie = Lexpy_Trie()
    trie.add_all(geohash_list)
    return trie

def build_pygtrie(geohash_list):
    trie = pygtrie.PrefixSet(geohash_list)
    for hash in geohash_list:
        trie.add(hash)
    return trie

def build_trie(geohash_list):
    trie = _Trie()
    for hash in geohash_list:
        trie.add(hash)
    return trie

def get_tree(geohash_list, query):
    """Build a tree based on query type"""
    if query == 'builtin':
        return geohash_list
    elif query == 'trie':
        return build_trie(geohash_list)
    elif query == 'gtrie':
        return build_pygtrie(geohash_list)
    elif query == 'lexpy_trie':
        return build_lexpy_trie(geohash_list)
    elif query == 'lexpy_dawg':
        return build_lexpy_dawg(geohash_list)

def _choose_tree(geohash_list, query, tree):
    """Select cached tree or build on the fly"""
    if tree:
        return tree
    else:
        return get_tree(geohash_list, query)


class BaseIndex():

    def __init__(self, geohash_list, query, tree=None):
        self.query = query
        self.geohash_list = geohash_list
        self.tree = self._set_tree(tree)

    def _set_tree(self, tree):
        if tree:
            return tree
        else:
            return get_tree(self.geohash_list, self.query)

class LexpyDawg(BaseIndex):

    def __init__(self, geohash_list, tree=None):
        BaseIndex.__init__(self, geohash_list, 'lexpy_dawg', tree=tree)

    def prefix_query(self, prefix):
        output = self.tree.search_with_prefix(prefix)
        return output

class LexpyTrie(BaseIndex):

    def __init__(self, geohash_list, tree=None):
        BaseIndex.__init__(self, geohash_list, 'lexpy_trie', tree=tree)

    def prefix_query(self, prefix):
        output = self.tree.search_with_prefix(prefix)
        return output

class GTrie(BaseIndex):

    def __init__(self, geohash_list, tree=None):
        BaseIndex.__init__(self, geohash_list, 'gtrie', tree=tree)

    def prefix_query(self, prefix):
        output = [''.join(x) for x in list(self.tree.iter(prefix))]
        return output

class Trie(BaseIndex):

    def __init__(self, geohash_list, tree=None):
        BaseIndex.__init__(self, geohash_list, 'trie', tree=tree)

    def prefix_query(self, prefix):
        output = self.tree.start_with_prefix(prefix)
        return output

class Builtin(BaseIndex):

    def __init__(self, geohash_list, tree=None):
        BaseIndex.__init__(self, geohash_list, 'builtin', tree=tree)

    def prefix_query(self, prefix):
        output = [x for x in self.tree if x.startswith(prefix)]
        return output
