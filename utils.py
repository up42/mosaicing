from typing import Union
import math

import shapely
from shapely.geometry import Polygon
import pyproj
from shapely.ops import transform


# pylint: disable=chained-comparison
def get_utm_zone_epsg(lon: float, lat: float) -> int:
    """
    Calculates the suitable UTM crs epsg code for an input geometry point.
    Args:
        lon: Longitude of point
        lat: Latitude of point
    Returns:
        EPSG code i.e. 32658
    """
    zone_number = int((math.floor((lon + 180) / 6) % 60) + 1)

    # Special zones for Norway
    if lat >= 56.0 and lat < 64.0 and lon >= 3.0 and lon < 12.0:
        zone_number = 32
    # Special zones for Svalbard
    elif lat >= 72.0 and lat < 84.0:
        if lon >= 0.0 and lon < 9.0:
            zone_number = 31
        elif lon >= 9.0 and lon < 21.0:
            zone_number = 33
        elif lon >= 21.0 and lon < 33.0:
            zone_number = 35
        elif lon >= 33.0 and lon < 42.0:
            zone_number = 37

    if lat > 0:
        epsg_utm = zone_number + 32600
    else:
        epsg_utm = zone_number + 32700
    return epsg_utm


def buffer_meter(
    poly: Polygon,
    distance: float,
    epsg_in: int,
    use_centroid=True,
    lon: float = None,
    lat: float = None,
    **kwargs,
) -> Polygon:
    """
    Buffers a polygon in meter by temporarily reprojecting to appropiate equal-area UTM
    projection.
    Args:
        poly: Input shapely polygon.
        distance: Buffer size.
        epsg_in: Polygon input crs epsg.
        use_centroid: Uses the polygon centroid to calculate the suitable UTM epsg
            code (default). If false, uses the provided lon lat coordinates instead.
        lon: Optional lon coordinate for UTM epsg calculation.
        lat: Optional lat coordinate for UTM epsg calculation.
        kwargs: Rest of the shapely .buffer() args.
    Returns:
        Buffered polygon (by distance) in original epsg crs.
    """
    if use_centroid:
        lon = poly.centroid.x
        lat = poly.centroid.y

    epsg_utm = get_utm_zone_epsg(lon=lon, lat=lat)
    poly_utm = reproject_shapely(geometry=poly, epsg_in=epsg_in, epsg_out=epsg_utm)
    poly_buff = poly_utm.buffer(distance, **kwargs)
    poly_buff_original_epsg = reproject_shapely(
        geometry=poly_buff, epsg_in=epsg_utm, epsg_out=epsg_in
    )

    return poly_buff_original_epsg


def reproject_shapely(
    geometry: shapely.geometry, epsg_in: Union[str, int], epsg_out: Union[str, int]
) -> shapely.geometry:
    """
    Reprojects shapely geometry to different epsg crs.
    Example:
        reproject_shapely(poly, 4326, 32631)
    Args:
        geometry: input shapely geometry
        epsg_in: input epsg code
        epsg_out: epsg code for reprojection
    """
    project = pyproj.Transformer.from_proj(
        pyproj.Proj(f"epsg:{str(epsg_in)}"), pyproj.Proj(f"epsg:{str(epsg_out)}")
    )
    geometry_reprojected = transform(project.transform, geometry)
    return geometry_reprojected