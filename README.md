# mosaicing
Image mosaicing: constructing multiple scenes of the same area into a larger image

Task [UP-3758](https://geoinformationstore.atlassian.net/browse/UP-3758)

## Installation
Geopandas as used in this repository depends on rtree which cannot be installed
via pip. Use the following before installing other dependencies:

```
brew install spatialindex
```

Training data aois:
https://github.com/up42/lc-training-data-prep/tree/master/data