import geohash
import json
from osgeo import gdal

from rainbow.src.vector import wktBoundBox, Polygon, createTransformer, Point, MultiPoint

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

def bbox_query(extent, geohash_list, precision):
    """Method to query a list of geohashes from an input extent (bounding box query)"""
    #extent format (xmin, xmax, ymin, ymax)
    tl_hash = geohash.encode(extent[3], extent[0], precision=precision)
    tr_hash = geohash.encode(extent[3], extent[1], precision=precision)
    br_hash = geohash.encode(extent[2], extent[1], precision=precision)
    bl_hash = geohash.encode(extent[2], extent[0], precision=precision)

    common_hash = commonprefix([tl_hash, tr_hash, br_hash, bl_hash])

    intersecting_hashes = [x for x in geohash_list if x.startswith(common_hash)]
    centroids = [geohash.decode(x)[::-1] for x in intersecting_hashes]

    xspace = x_spacing(centroids)
    yspace = y_spacing(centroids)

    valid_list = []
    # centroid_list = []

    for idx, hash in enumerate(intersecting_hashes):
        centroid = centroids[idx]
        if centroid[0] < extent[1]+xspace*0.5 and centroid[0] > extent[0]-xspace*0.5 and centroid[1] < extent[3]+yspace*0.5 and centroid[1] > extent[2]-yspace*0.5:
            valid_list.append(hash)
            # centroid_list.append(centroid)
    return valid_list
    # return centroid_list

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

def hashes_to_multipoint(geohashes):
    centroids = []
    for hash in geohashes:
        centroid = geohash.decode(hash)
        centroids.append(centroid[::-1])
    return MultiPoint(centroids)

def commonprefix(m):
    "Given a list of strings, returns the longest common leading component"
    if not m: return ''
    s1 = min(m)
    s2 = max(m)
    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s1


"""ARGS"""
precision = 12
"""END ARGS"""


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
print(p.ExportToWkt())
extent = p.Envelope()

print ("BBOX JACCARD: {}".format(extent_overlap(extent, precision)))
out_hashes = bbox_query(extent, geohash_list, precision=precision)
print(hashes_to_multipoint(out_hashes).ExportToWkt())
