import geohash
import pygtrie
from lexpy.trie import Trie as Lexpy_Trie
from lexpy.dawg import DAWG
import dawg

from .trie import Trie as _Trie


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


def bbox_query(extent, tree, precision):
    tl_hash = geohash.encode(extent[3], extent[0], precision=precision)
    tr_hash = geohash.encode(extent[3], extent[1], precision=precision)
    br_hash = geohash.encode(extent[2], extent[1], precision=precision)
    bl_hash = geohash.encode(extent[2], extent[0], precision=precision)

    common_hash = commonprefix([tl_hash, tr_hash, br_hash, bl_hash])
    intersecting_hashes = tree.prefix_query(common_hash)
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

def decode_extent(extent):
    decoded = geohash.bbox(extent)
    return [decoded['w'], decoded['e'], decoded['s'], decoded['n']]

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
    return LexpyDawg(dawg)

def build_lexpy_trie(geohash_list):
    trie = Lexpy_Trie()
    trie.add_all(geohash_list)
    return LexpyTrie(trie)

def build_pygtrie(geohash_list):
    trie = pygtrie.PrefixSet(geohash_list)
    for hash in geohash_list:
        trie.add(hash)
    return GTrie(trie)

def build_trie(geohash_list):
    trie = _Trie()
    for hash in geohash_list:
        trie.add(hash)
    return Trie(trie)

def build_completion_dawg(geohash_list):
    d = dawg.CompletionDAWG(geohash_list)
    return CompletionDAWG(d)

def get_tree(geohash_list, query):
    """Build a tree based on query type"""
    if query == 'builtin':
        return Builtin(geohash_list)
    elif query == 'trie':
        return build_trie(geohash_list)
    elif query == 'gtrie':
        return build_pygtrie(geohash_list)
    elif query == 'lexpy_trie':
        return build_lexpy_trie(geohash_list)
    elif query == 'lexpy_dawg':
        return build_lexpy_dawg(geohash_list)
    elif query == 'completion_dawg':
        return build_completion_dawg(geohash_list)


class LexpyDawg():

    def __init__(self, tree):
        self.tree = tree

    def prefix_query(self, prefix):
        output = self.tree.search_with_prefix(prefix)
        return output

class LexpyTrie():

    def __init__(self, tree):
        self.tree = tree

    def prefix_query(self, prefix):
        output = self.tree.search_with_prefix(prefix)
        return output

class GTrie():

    def __init__(self, tree):
        self.tree = tree

    def prefix_query(self, prefix):
        output = [''.join(x) for x in list(self.tree.iter(prefix))]
        return output

class Trie():

    def __init__(self, tree):
        self.tree = tree

    def prefix_query(self, prefix):
        output = self.tree.start_with_prefix(prefix)
        return output

class Builtin():

    def __init__(self, tree):
        self.tree = tree

    def prefix_query(self, prefix):
        output = [x for x in self.tree if x.startswith(prefix)]
        return output

class CompletionDAWG():

    def __init__(self, tree):
        self.tree = tree

    def prefix_query(self, prefix):
        output = self.tree.keys(prefix)
        return output
