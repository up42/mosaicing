import pytest
from pathlib import Path

# pylint: disable=wildcard-import, unused-wildcard-import
from utils.geo import *

from shapely.geometry import shape

# pylint: disable=redefined-outer-name
@pytest.fixture
def df_multipolygon():
    return gpd.GeoDataFrame.from_file(
        Path(__file__).parent / Path("./mock_data/full_coverage_buffered.geojson")
    )


@pytest.fixture
def test_poly():
    return shape(
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [119.46069717407228, -5.1656599047481615],
                    [119.46413040161133, -5.194210278739781],
                    [119.50241088867188, -5.194039322258176],
                    [119.5001792907715, -5.1579664699241885],
                    [119.47477340698242, -5.15830840234196],
                    [119.46069717407228, -5.1656599047481615],
                ]
            ],
        }
    )


@pytest.fixture
def test_poly_buffer_10():
    return shape(
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [119.46065552738624, -5.16557974535648],
                    [119.47473175988688, -5.158228244475686],
                    [119.47473939513839, -5.158224700635304],
                    [119.47474732667415, -5.158221885938315],
                    [119.47475548540086, -5.158219824904106],
                    [119.47476380024617, -5.158218535486784],
                    [119.47477219877769, -5.158218028918682],
                    [119.50017807901376, -5.157876098286475],
                    [119.50018664754586, -5.157876391602663],
                    [119.50019514953121, -5.157877499734234],
                    [119.50020350806403, -5.157879412657397],
                    [119.50021164753609, -5.157882113068589],
                    [119.50021949432076, -5.157885576540823],
                    [119.50022697743896, -5.157889771744836],
                    [119.50023402920114, -5.157894660732352],
                    [119.50024058581968, -5.157900199279369],
                    [119.50024658798581, -5.157906337286259],
                    [119.5002519814062, -5.157913019230852],
                    [119.50025671729392, -5.157920184670754],
                    [119.50026075280987, -5.157927768790041],
                    [119.50026405145023, -5.1579357029855775],
                    [119.50026658337673, -5.157943915487544],
                    [119.50026832568645, -5.157952332008697],
                    [119.50026926261906, -5.157960876416286],
                    [119.5025008653012, -5.194033725977106],
                    [119.50250098673212, -5.1940423784236005],
                    [119.50250028224139, -5.1940510028545335],
                    [119.50249875828696, -5.194059520210457],
                    [119.50249642883877, -5.1940678524134425],
                    [119.50249331525066, -5.194075923082861],
                    [119.50248944606462, -5.194083658235521],
                    [119.50248485674912, -5.194090986963911],
                    [119.50247958937399, -5.194097842086134],
                    [119.50247369222485, -5.194104160761831],
                    [119.5024672193604, -5.194109885068191],
                    [119.5024602301168, -5.194114962530932],
                    [119.50245278856393, -5.194119346605355],
                    [119.50244496291788, -5.194122997102941],
                    [119.50243682491578, -5.1941258805598665],
                    [119.50242844915802, -5.194127970543698],
                    [119.50241991242451, -5.194129247895683],
                    [119.50241129297088, -5.1941297009064265],
                    [119.46413080047051, -5.194300660026603],
                    [119.4641220662702, -5.1943002737630914],
                    [119.46411341045984, -5.1942990411381995],
                    [119.46410491444333, -5.194296973744201],
                    [119.46409665812176, -5.194294091023933],
                    [119.46408871914207, -5.194290420088048],
                    [119.46408117216666, -5.194285995460006],
                    [119.46407408817134, -5.194280858751338],
                    [119.46406753377786, -5.194275058270443],
                    [119.46406157062721, -5.194268648568154],
                    [119.46405625480007, -5.194261689924722],
                    [119.46405163628931, -5.19425424778298],
                    [119.46404775852993, -5.194246392132826],
                    [119.46404465799034, -5.194238196853024],
                    [119.46404236382973, -5.1942297390163725],
                    [119.46404089762359, -5.194221098164891],
                    [119.46060767358922, -5.165670721808635],
                    [119.46060704206562, -5.16566163006447],
                    [119.46060732698652, -5.165652520777695],
                    [119.46060852545487, -5.165643486569735],
                    [119.4606106252848, -5.16563461929867],
                    [119.46061360512567, -5.1656260091251305],
                    [119.46061743467898, -5.165617743595692],
                    [119.4606220750065, -5.165609906752586],
                    [119.46062747892636, -5.165602578279295],
                    [119.46063359149247, -5.165595832690267],
                    [119.46064035055348, -5.165589738573301],
                    [119.46064768738455, -5.165584357892143],
                    [119.46065552738624, -5.16557974535648],
                ]
            ],
        }
    )


@pytest.fixture
def test_poly_reprojected():
    return shape(
        {
            "type": "Polygon",
            "coordinates": (
                (
                    (-11173410.717541715, 2881464.754732242),
                    (-11167686.104705878, 2880702.1532226824),
                    (-11165792.187196916, 2888171.4658257943),
                    (-11172918.7257647, 2889550.5519448915),
                    (-11174132.388979157, 2884578.8435261217),
                    (-11173410.717541715, 2881464.754732242),
                ),
            ),
        }
    )


@pytest.mark.parametrize(
    "lon, lat, epsg_expected",
    [
        (-79.52826976776123, 8.847423357771518, 32617),  # Panama
        (9.95121, 49.79391, 32632),  # Wuerzburg
        (9.767417, 62.765571, 32632),  # Norway special zone
        (12.809028, 79.026583, 32633),  # Svalbard special zone
    ],
)
def test_get_utm_zone_epsg(lat, lon, epsg_expected):
    epsg = get_utm_zone_epsg(lat=lat, lon=lon)

    assert epsg == epsg_expected


def test_buffer_meter(test_poly, test_poly_buffer_10):
    buffered_poly = buffer_meter(test_poly, 0, 4326)
    assert test_poly.almost_equals(buffered_poly, decimal=0)

    buffered_poly = buffer_meter(
        test_poly,
        0,
        4326,
        use_centroid=False,
        lon=test_poly.centroid.x,
        lat=test_poly.centroid.y,
    )
    assert test_poly.almost_equals(buffered_poly, decimal=0)

    buffered_poly = buffer_meter(
        test_poly,
        10,
        4326,
        use_centroid=False,
        lon=test_poly.centroid.x,
        lat=test_poly.centroid.y,
    )
    assert test_poly_buffer_10.almost_equals(buffered_poly, decimal=6)


def test_reproject_shapely(test_poly, test_poly_reprojected):
    reproject_shape = reproject_shapely(test_poly, 4326, 3275)
    print(dict(reproject_shape.__geo_interface__))
    print(test_poly_reprojected)
    assert reproject_shape.almost_equals(test_poly_reprojected, 6)


def test_explode_mp(df_multipolygon):
    assert len(df_multipolygon) == 4
    exploded_df = explode_mp(df_multipolygon)
    assert len(exploded_df) == 5


def test_get_best_sections_full_coverage(df_multipolygon):
    out_df = get_best_sections_full_coverage(df_multipolygon)
    assert len(out_df) == 5


def test_get_best_sections_full_coverage_topological_error():
    df = gpd.GeoDataFrame.from_file(
        Path(__file__).parent
        / Path("./mock_data/search_results_limited_columns.geojson")
    )
    out_df = get_best_sections_full_coverage(df)
    assert len(out_df) == 73


def test_coverage_percentage(df_multipolygon):
    cov = coverage_percentage(df_multipolygon.loc[[0]], df_multipolygon)
    assert cov >= 100
    cov = coverage_percentage(df_multipolygon.loc[[0]].buffer(10), df_multipolygon)
    assert cov < 100
