import geopandas as gpd
from shapely.geometry import box

roads = gpd.read_file("data/lookups/tl_2026_17_prisecroads/tl_2026_17_prisecroads.shp")
roads = roads[roads["MTFCC"].isin(["S1100", "S1200"])]   # primary and secondary roads
roads = roads.clip(box(-88.80, 41.20, -87.20, 42.60))    # wider than the map, so the frame does the cropping
roads["kind"] = roads["FULLNAME"].str.match(r"^I-\s?\d+", na=False).map({True: "interstate", False: "road"})
roads = roads[["FULLNAME", "kind", "geometry"]]
roads["geometry"] = roads.simplify(0.0005)
roads.to_file("data/lookups/highways.geojson", driver="GeoJSON")
print(len(roads), "road segments saved")