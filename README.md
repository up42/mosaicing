# Mosaicing


## Installation

```bash
mkvirtualenv --python=$(which python3.7) up42-mosaicing
```

Install spatialindex via brew before (!) installing the requirements (to be able to install rtree).

```bash
brew install spatialindex
```

```bash
pip install -r requirements.txt
```

Register jupyter kernel:

```bash
pip install ipykernel
python -m ipykernel install --user --name=up42-mosaicing
```

Select kernel on the top right of the Jupyter notebook.


## Usage

Image mosaicing: constructing multiple scenes of the same area into a larger image

Task [UP-3758](https://geoinformationstore.atlassian.net/browse/UP-3758)

Training data aois:
https://github.com/up42/lc-training-data-prep/tree/master/data
