from osgeo import gdal
import geohash
import json
import time

from rainbow.src.vector import MultiPoint, Polygon, createTransformer
from src import bbox_query

def hashes_to_multipoint(geohashes):
    centroids = []
    for hash in geohashes:
        centroid = geohash.decode(hash)
        centroids.append(centroid[::-1])
    return MultiPoint(centroids)


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

start = time.time()
out_hashes = bbox_query(extent, geohash_list, precision=precision, query='builtin')
print("Runtime: {}".format(time.time()-start))
print(hashes_to_multipoint(out_hashes).ExportToWkt())