from typing import Union
import math

import shapely
from shapely.geometry import Polygon, box
from shapely.ops import transform, cascaded_union
import pyproj
import geopandas as gpd
from geopandas import GeoDataFrame as GDF
import pandas as pd


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
        epsg_utm = get_utm_zone_epsg(lon=poly.centroid.x, lat=poly.centroid.y)
    else:
        epsg_utm = get_utm_zone_epsg(lon=lon, lat=lat)  # type: ignore
    poly_utm = reproject_shapely(geometry=poly, epsg_in=epsg_in, epsg_out=epsg_utm)
    poly_buff = poly_utm.buffer(distance)
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
        pyproj.Proj(f"epsg:{str(epsg_in)}"),
        pyproj.Proj(f"epsg:{str(epsg_out)}"),
        always_xy=True,
    )
    geometry_reprojected = transform(project.transform, geometry)
    return geometry_reprojected


def explode_mp(df: GDF) -> GDF:
    """
    Explode all multi-polygon geometries in a geodataframe into individual polygon
    geometries.
    Adds exploded polygons as rows at the end of the geodataframe and resets its index.
    Args:
        df: Input GeoDataFrame
    """
    outdf = df[df.geom_type != "MultiPolygon"]

    df_mp = df[df.geom_type == "MultiPolygon"]
    for _, row in df_mp.iterrows():
        df_temp = gpd.GeoDataFrame(columns=df_mp.columns)
        df_temp = df_temp.append([row] * len(row.geometry), ignore_index=True)
        for i in range(len(row.geometry)):
            df_temp.loc[i, "geometry"] = row.geometry[i]
        outdf = outdf.append(df_temp, ignore_index=True)

    outdf = outdf.reset_index(drop=True)
    return outdf


# Allows passing of list for ordering
# pylint: disable=dangerous-default-value
def get_best_sections_full_coverage(
    df, order_by=["cloudCoverage"], min_size_section_sqkm=0.5
):
    """
    Ordered by order_by column, and automatically area_sqkm_clipped
    :param df:
    :param order_by: E.g. ["cloudCoverage", "incidenceAngle"], third order will always be area.
        Be aware that this will to many small sections, better filter incidence angle by treshold.
    :param min_size_section_sqkm:
    :return:
    """
    centroid = box(*df.total_bounds).centroid
    epsg = get_utm_zone_epsg(lon=centroid.x, lat=centroid.y)
    df = df.to_crs(epsg=epsg)

    df["area_sqkm_clipped"] = df.area / 10 ** 6
    df = df.sort_values(by=[*order_by, "area_sqkm_clipped"], axis=0, ascending=False)
    df = df[df["area_sqkm_clipped"] > min_size_section_sqkm]
    if df.shape[0] == 0:
        raise Exception(
            "No data matches optimize parameters! Try again by running a wider search!"
        )

    # Select the best scene as a starting point (lowest cc, highest area.)
    full_coverage = df.iloc[[0]]

    remaining = df.iloc[1:]

    for _ in range(remaining.shape[0]):

        # Get the unioned area of the aoi which is already covered by
        # the selected scenes, subtract that area from all remaining scenes.
        already_covered = gpd.GeoDataFrame(
            pd.DataFrame([0]),
            crs=f"EPSG:{epsg}",
            geometry=[full_coverage.geometry.unary_union],
        )
        remaining_minus_covered = gpd.overlay(
            remaining, already_covered, how="difference"
        )

        # Recalculate the area of the remaining scenes.
        remaining_minus_covered["area_sqkm_new"] = (
            remaining_minus_covered.area / 10 ** 6
        )
        # Remove too small scene sections
        remaining_minus_covered = remaining_minus_covered[
            remaining_minus_covered["area_sqkm_new"] > min_size_section_sqkm
        ]
        if remaining_minus_covered.shape[0] == 0:
            break
        # reorder.
        remaining_minus_covered = remaining_minus_covered.sort_values(
            by=[*order_by, "area_sqkm_new"], axis=0, ascending=False
        )

        # Select the now best scene.
        now_best = remaining_minus_covered.iloc[[0]]
        # Explode potential mutipolygons
        if "MultiPolygon" in now_best.geometry.type.tolist():
            now_best = explode_mp(now_best)
            now_best["area_sqkm_new"] = now_best.area / 10 ** 6
            now_best = now_best[now_best["area_sqkm_new"] > min_size_section_sqkm]
            if now_best.shape[0] == 0:
                continue
        # Add to the results
        full_coverage = full_coverage.append(now_best)
        full_coverage.reset_index(drop=True, inplace=True)

        # Next iteration will not include the selected scene.
        remaining = remaining_minus_covered.iloc[1:]

    full_coverage["full_coverage"] = full_coverage.area / 10 ** 6
    full_coverage.geometry = full_coverage.geometry.buffer(0)

    full_coverage = full_coverage.to_crs(epsg=4326)

    full_coverage = explode_mp(full_coverage)
    full_coverage.geometry = full_coverage.geometry.buffer(0)

    return full_coverage


def coverage_percentage(aoi: GDF, full_coverage: GDF) -> float:
    """
    Calculates percentage of coverage of AOI from full_coverage.
    """

    centroid = box(*full_coverage.total_bounds).centroid
    epsg = get_utm_zone_epsg(lon=centroid.x, lat=centroid.y)
    full_coverage = full_coverage.to_crs(epsg=epsg)
    aoi = aoi.to_crs(epsg=epsg)

    unary_union = gpd.GeoSeries(cascaded_union(full_coverage.geometry))
    cov = (unary_union.area / aoi.area) * 100
    return float(cov)
