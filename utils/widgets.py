from pathlib import Path

from ipyfilechooser import FileChooser
from ipywidgets import widgets
from IPython.display import display

import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.merge import merge
from rasterio.plot import show
from rasterio.enums import ColorInterp

import up42

from utils.geo import buffer_meter, get_best_sections_full_coverage, coverage_percentage

# To rename filename to directory
# pylint: disable=too-many-ancestors
class DirectoryChooser(FileChooser):
    _LBL_NOFILE = "No directory selected"


class UI:
    # We need the vars for sharing the state
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        self.outdir = None
        self.aoi = None
        self.sensors = None
        self.search_parameters = None
        self.search_results = None
        self.catalog = None
        self.search_results_df = None
        self.clipped = None
        self.full_coverage = None
        self.project = None
        self.workflow = None
        self.jobs = None
        self.order_ids = None
        self.selected_blocks = None
        self.out_path = None

    @staticmethod
    # pylint: disable=unused-argument
    def process_template(widget_list, button, on_button_click_process, **kwargs):
        out = widgets.Output()

        def on_button_click(button):
            with out:
                out.clear_output()
                on_button_click_process(**kwargs)

        button.on_click(on_button_click)
        display(*widget_list, button, out)

    @staticmethod
    def ensure_variables(var_list: tuple = ()):
        return all(var is not None for var in var_list if var_list)

    def authenticate(self, env="com"):
        project_id = widgets.Text(
            description="PROJECT ID", style={"description_width": "initial"}
        )
        project_api_key = widgets.Password(
            description="PROJECT API KEY", style={"description_width": "initial"}
        )
        button = widgets.Button(
            description="Authenticate!"
        )  # pylint: disable=assignment-from-no-return

        def auth(env, project_id, project_api_key):
            # pylint: disable=unused-variable
            api = up42.authenticate(
                project_id=project_id.value,
                project_api_key=project_api_key.value,
                env=env,
            )
            self.catalog = up42.initialize_catalog()

        self.process_template(
            [project_api_key, project_id],
            button,
            auth,
            env=env,
            project_id=project_id,
            project_api_key=project_api_key,
        )

    def choose_output_folder(self):
        fc = DirectoryChooser(filename="my_new_folder", select_default=True)

        fc.title = "<b>Select an output directory</b>"
        button = widgets.Button(description="Save!")

        def save_dir(fc):
            assert fc.selected, "Please select a directory."
            outdir = Path(fc.selected).resolve()
            outdir.mkdir(parents=True, exist_ok=True)
            assert outdir.is_dir(), "Please select a directory, not a file."
            self.outdir = outdir
            print(f"Saved {self.outdir}")

        self.process_template([fc], button, save_dir, fc=fc)

    def load_aoi(self):
        fc = FileChooser(".")
        fc.title = "<b>Select an input geometry file</b>"

        button = widgets.Button(description="Load!")

        def load_aoi(fc):
            assert fc.selected, "Please select a file."
            file_path = Path(fc.selected).resolve()
            assert file_path.is_file(), "Please select a file, not a directory."
            aoi = up42.read_vector_file(file_path, as_dataframe=True)
            display(aoi)
            self.aoi = aoi
            aoi.plot()
            print(f"Saved {aoi}")

        self.process_template([fc], button, load_aoi, fc=fc)

    def create_search_params(self):
        start_date = widgets.DatePicker(
            description="Pick a start date", style={"description_width": "initial"}
        )
        end_date = widgets.DatePicker(
            description="Pick an end date", style={"description_width": "initial"}
        )
        sensors = widgets.RadioButtons(
            options=["pleiades", "spot"],
            value="pleiades",
            description="Sensor",  #
        )
        max_cloudcover = widgets.IntSlider(
            value=20,
            min=0,
            max=100,
            step=1,
            description="Max Cloud Cover (%)",
            style={"description_width": "initial"},
        )
        limit = widgets.IntSlider(
            value=10,
            min=1,
            max=500,
            step=1,
            description="Limit",
        )

        button = widgets.Button(description="Save search params!")

        def create_search_params(start_date, end_date, sensors, max_cloudcover, limit):
            assert self.ensure_variables(
                (self.catalog, self.aoi)
            ), "Please select an AOI and/or authenticate!"
            search_parameters = self.catalog.construct_parameters(
                geometry=self.aoi,
                start_date=start_date.value,
                end_date=end_date.value,
                sensors=[sensors.value],
                max_cloudcover=max_cloudcover.value,
                sortby="cloudCoverage",
                limit=limit.value,
            )
            display(search_parameters)
            self.search_parameters = search_parameters
            self.sensors = sensors.value

        self.process_template(
            [start_date, end_date, sensors, max_cloudcover, limit],
            button,
            create_search_params,
            start_date=start_date,
            end_date=end_date,
            sensors=sensors,
            max_cloudcover=max_cloudcover,
            limit=limit,
        )

    def search_available_images(self):
        out_file = widgets.Checkbox(
            value=False,
            description="Save results of search to file?",
            disabled=False,
            indent=False,
        )

        button = widgets.Button(description="Search catalog!")

        def search_catalog():
            assert self.ensure_variables(
                (self.catalog, self.search_parameters, self.aoi, self.outdir)
            ), "Please run steps before (authenticate, select AOI, select output dir and create search parameters)!"
            search_results = self.catalog.search(
                search_parameters=self.search_parameters, as_dataframe=True
            )
            assert (
                not search_results.empty
            ), "No results found! Try other search parameters."
            search_results["incidenceAngle"] = search_results[
                "providerProperties"
            ].apply(lambda x: x["incidenceAngle"])
            display(search_results)
            self.catalog.plot_coverage(scenes=search_results, aoi=self.aoi)

            # Reduce columns & export
            df = search_results[
                [
                    "geometry",
                    "id",
                    "scene_id",
                    "cloudCoverage",
                    "blockNames",
                    "incidenceAngle",
                ]
            ].copy()
            df["blockNames"] = df["blockNames"].astype(str)
            if out_file.value:
                df.to_file(
                    driver="GeoJSON",
                    filename=self.outdir / "search_results_limited_columns.geojson",
                )
            self.search_results = search_results
            self.search_results_df = df

        self.process_template([out_file], button, search_catalog)

    def show_quicklooks(self):
        button_quicklooks = widgets.Button(description="Show quicklooks!")

        def show_quicklooks():
            assert self.ensure_variables(
                (self.catalog, self.search_results)
            ), "Please run steps before (authenticate and run search)!"
            # Quicklooks
            self.catalog.download_quicklooks(
                image_ids=self.search_results["id"].tolist(),
                sensor=self.sensors,
                output_directory=self.outdir / "quicklooks",
            )
            display(
                self.catalog.map_quicklooks(scenes=self.search_results, aoi=self.aoi)
            )

        self.process_template([], button_quicklooks, show_quicklooks)

    def optimize_coverage(self):
        max_incidence_angle = widgets.FloatSlider(
            value=30.0,
            min=0,
            max=50.0,
            step=0.1,
            description="Max Incidence Angle (degrees)",
            readout_format=".1f",
            style={"description_width": "initial"},
        )
        min_size_section_sqkm = widgets.FloatSlider(
            value=0.5,
            min=0.1,
            max=5,
            step=0.1,
            description="Min Section Size (sqkm)",
            readout_format=".1f",
            style={"description_width": "initial"},
        )
        buffer_size = widgets.IntSlider(
            value=20,
            min=5,
            max=50,
            step=5,
            description="Overlap between scenes (m)",
            style={"description_width": "initial"},
        )
        button = widgets.Button(description="Optimize coverage!")

        def optimize_coverage(max_incidence_angle, min_size_section_sqkm, buffer_size):
            assert self.ensure_variables(
                (self.search_results_df, self.aoi)
            ), "Please run steps before (select AOI and search)!"

            # Clip to aoi
            clipped = gpd.clip(self.search_results_df, self.aoi.iloc[0].geometry)
            clipped.geometry = clipped.geometry.buffer(0)

            clipped.to_file(driver="GeoJSON", filename=self.outdir / "clipped.geojson")
            self.clipped = clipped

            # Iteratively selected the next best scene and add to Dataframe.
            # At each iteration the area criteria is recalculated, as it changes
            # depending on the already selected scenes. Often times a scene
            # which has a big area within the aoi is actually not selected,
            # as another scene which has a similar coverage made it
            # redundant.

            clipped_filtered_angle = self.clipped.copy()
            clipped_filtered_angle = clipped_filtered_angle[
                clipped_filtered_angle.incidenceAngle < max_incidence_angle.value
            ]

            full_coverage = get_best_sections_full_coverage(
                df=clipped_filtered_angle,
                order_by=["cloudCoverage"],
                min_size_section_sqkm=min_size_section_sqkm.value,
            )
            n_scenes = full_coverage.shape[0]
            full_coverage.to_file(
                driver="GeoJSON", filename=self.outdir / "full_coverage.geojson"
            )

            # Buffer all sections by 10m (=5 Pixel 2m), so we ensure that all
            # sections overlap later on (no segment line breaks).
            # Clip again to aoi to avoid unneccesary bigger aoi
            # and complicated geometries
            full_coverage.geometry = full_coverage.geometry.apply(
                lambda poly: buffer_meter(
                    poly=poly,
                    distance=buffer_size.value,
                    epsg_in=4326,
                    use_centroid=False,
                    lon=self.aoi.geometry.iloc[0].centroid.x,
                    lat=self.aoi.geometry.iloc[0].centroid.y,
                )
            )
            full_coverage = gpd.clip(full_coverage, self.aoi.iloc[0].geometry)
            full_coverage.geometry = full_coverage.geometry.buffer(0)

            display(full_coverage)
            up42.plot_coverage(full_coverage, aoi=self.aoi, figsize=(7, 7))

            assert full_coverage is not None, "Result is empty, try other parameters!"
            assert (
                n_scenes == full_coverage.shape[0]
            ), "Something went wrong, a scene was dropped..."
            full_coverage.to_file(
                driver="GeoJSON",
                filename=self.outdir / "full_coverage_buffered.geojson",
            )
            print("=======================================================")
            print("Coverage of AOI is:")
            cov = coverage_percentage(self.aoi, full_coverage)
            print(f"{round(cov)} %")
            if cov < 98:
                print(
                    "WARNING: Coverage could be insufficient! Check full_coverage.geojson"
                )
            print("=======================================================")

            self.full_coverage = full_coverage

        self.process_template(
            [max_incidence_angle, min_size_section_sqkm, buffer_size],
            button,
            optimize_coverage,
            max_incidence_angle=max_incidence_angle,
            min_size_section_sqkm=min_size_section_sqkm,
            buffer_size=buffer_size,
        )

    def test_workflow(self):
        selected_blocks = widgets.RadioButtons(
            options=[
                ["oneatlas-pleiades-fullscene", "pansharpen"],
                ["oneatlas-pleiades-aoiclipped"],
                ["oneatlas-spot-fullscene", "pansharpen"],
                ["oneatlas-spot-aoiclipped"],
            ],
            value=["oneatlas-pleiades-fullscene", "pansharpen"],
            layout={"width": "max-content"},
            description="Blocks to use",
        )
        button = widgets.Button(description="Run test queries!")

        def test_workflow(selected_blocks):
            assert self.ensure_variables(
                (self.full_coverage, self.catalog)
            ), "Please run steps before (optimize coverage)!"

            self.project = up42.initialize_project()
            self.project.update_project_settings(max_concurrent_jobs=10)
            self.workflow = self.project.create_workflow(
                "mosaicking", use_existing=True
            )

            blocks = up42.get_blocks(basic=True)
            self.workflow.add_workflow_tasks(
                [blocks[selected] for selected in selected_blocks.value]
            )

            # Test workflow & availability of sections
            parameters = []
            for _, row in self.full_coverage.iterrows():

                test_parameters = self.workflow.construct_parameters(
                    geometry=row.geometry,
                    geometry_operation="intersects",
                    scene_ids=[row["scene_id"]],
                )
                parameters.append(test_parameters)

            test_jobs = self.workflow.test_jobs_parallel(
                parameters, name="mosaicking_tests"
            )

            test_jobs_df = {}
            for test_job in test_jobs:
                try:
                    estimated_credits = list(
                        test_job.get_jobtasks_results_json().values()
                    )[0]["features"][0]["estimatedCredits"]
                except (KeyError, IndexError):
                    estimated_credits = 0

                test_df = test_job.get_results_json(as_dataframe=True)
                test_df["estimatedCredits"] = estimated_credits
                display(test_df)

                test_jobs_df[test_job.job_id] = test_df

            test_jobs_df = pd.concat(test_jobs_df.values(), keys=test_jobs_df.keys())
            display(test_jobs)
            print("=======================================================")
            print("Generating this mosaic is estimated to cost:")
            print(f"{test_jobs_df['estimatedCredits'].sum()} UP42 credits")
            print("=======================================================")

            self.selected_blocks = selected_blocks.value

            print("finished")

        self.process_template(
            [selected_blocks], button, test_workflow, selected_blocks=selected_blocks
        )

    def run_workflow(self):
        button = widgets.Button(
            description="RUN JOBS! This will cost credits, so be careful.",
            layout={"width": "max-content"},
        )

        def run_workflow():
            assert self.ensure_variables(
                (self.full_coverage, self.outdir, self.catalog)
            ), "Please run steps before (optimize coverage and select outdir)!"

            parameters_list = []
            for _, row in self.full_coverage.iterrows():

                parameters = self.workflow.construct_parameters(
                    geometry=row.geometry,
                    geometry_operation="intersects",
                    scene_ids=[row["scene_id"]],
                )
                parameters_list.append(parameters)
                print(parameters)

            jobs = self.workflow.run_jobs_parallel(parameters_list, name="mosaicking")

            jobs_df = {}
            for job in jobs:
                out_filepaths = job.download_results(
                    output_directory=self.outdir / "sections"
                )
                jobs_df[out_filepaths[0]] = job

            self.jobs = jobs_df

            print("finished")

            # Get order ids

            order_ids = []
            if "fullscene" in self.selected_blocks[0]:
                for _, job in jobs.items():

                    data_jobtask = job.get_jobtasks()[0]

                    order_id = data_jobtask.get_results_json()["features"][0]["orderID"]
                    order_ids.append(order_id)

            self.order_ids = order_ids
            display(order_ids)

        self.process_template([], button, run_workflow)

    def mosaic_sections(self):
        button = widgets.Button(description="Create mosaic!")

        def mosaic_sections():
            assert self.ensure_variables(
                (self.outdir, True)
            ), "Please run steps before (select outdir)!"

            job_results = list(self.outdir.joinpath("sections").glob("*.tif"))
            display(job_results)

            src_files_to_mosaic = []
            for fp in job_results:
                src = rasterio.open(fp)
                src_files_to_mosaic.append(src)

                out_profile = src.profile.copy()  # bzw. src.meta
            display(src_files_to_mosaic)

            mosaic, out_transform = merge(src_files_to_mosaic)
            display(mosaic.shape)

            out_profile.update(
                {
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": out_transform,
                    "blockxsize": 256,
                    "blockysize": 256,
                    "tiled": True,  # Important for definition block structure!
                }
            )

            out_path_folder = self.outdir / "mosaic"
            out_path_folder.mkdir(parents=True, exist_ok=True)
            # Write raster.
            out_path = out_path_folder / "mosaic.tif"
            with rasterio.open(out_path, "w", **out_profile) as dst:
                for i in range(mosaic.shape[0]):
                    dst.write(mosaic[i, ...], i + 1)
                dst.colorinterp = [
                    ColorInterp.red,
                    ColorInterp.green,
                    ColorInterp.blue,
                    ColorInterp.undefined,
                ]
            self.out_path = out_path
            print("DONE!")

        self.process_template([], button, mosaic_sections)

    def view_mosaic(self):
        button = widgets.Button(description="View mosaic!")

        def view_mosaic():
            assert self.ensure_variables(
                (self.out_path, True)
            ), "Please run steps before (mosaic sections)!"

            with rasterio.open(self.out_path) as src:
                _, ax = plt.subplots(nrows=1, ncols=1, figsize=(12, 12))

                show(src, ax=ax)
                plt.show()

        self.process_template([], button, view_mosaic)
