import pytest

from ipywidgets import widgets
from utils.widgets import UI


@pytest.mark.parametrize(
    "ui_method",
    [
        UI.choose_output_folder,
        UI.authenticate,
        UI.load_aoi,
        UI.create_search_params,
        UI.search_available_images,
        UI.show_quicklooks,
        UI.optimize_coverage,
        UI.test_workflow,
        UI.run_workflow,
        UI.mosaic_sections,
        UI.view_mosaic,
    ],
)
def test_ui(ui_method, capsys):
    ui = UI()
    ui_method(ui)

    captured = capsys.readouterr()
    assert captured.out


def test_process_template(capsys):
    button = widgets.Button(description="Authenticate!")

    def a_func():
        pass

    UI.process_template([], button, a_func)
    captured = capsys.readouterr()
    assert captured.out


def test_ensure_variables():
    ui = UI()
    ui.outdir = "path_to_file"
    assert ui.ensure_variables([ui.outdir])
    assert not ui.ensure_variables([ui.outdir, ui.aoi])
    assert not ui.ensure_variables([ui.aoi])
