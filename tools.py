# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		tools.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for read and analyze raster arrays

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module is a test"""

import gdal_reader as gdalr

try:
    import gdal

except ImportError:
    from osgeo import gdal


from collections import namedtuple

def gdal2Py(filename):
    """A class holding information about a ogr feature"""

    info_tuple = namedtuple('info', 'type projection xsize ysize yres xres extent bands bands_type nodata')
    extent_tuple = namedtuple('extent', ['xmin', 'xmax', 'ymin', 'ymax'])

    __slots__ = ('type', 'filename', 'projection', 'xsize', 'ysize',
                 'yres', 'xres', 'extent', 'bands',
                 'band_type', 'nodata','ds', 'array')
    # Prevents to create dictionaries (low memory).

    def __init__(self, ds, data=True):
        """ Read ogr data source (instance variable) """

