# Mosaicing

## Installation

```bash
mkvirtualenv --python=$(which python3.7) up42-mosaicing
```

Requires rtree which can not be installed via pip. Use:
```bash
brew install spatialindex
```

```bash
pip install -r requirements.txt
```


## Usage

Image mosaicing: constructing multiple scenes of the same area into a larger image

Task [UP-3758](https://geoinformationstore.atlassian.net/browse/UP-3758)

Training data aois:
https://github.com/up42/lc-training-data-prep/tree/master/data
