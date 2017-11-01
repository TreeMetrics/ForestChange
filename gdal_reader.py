# /usr/bin/env python

# PRODUCT: EO4Atlantic
# MODULE: gdal_reader.py
# AUTHOR: Treemetrics
# DESCRIPTION: 	Basic tools for read and analyze _raster using gdal.

# COPYRIGHT:	(C) 2017 Treemetrics. All rights reserved.
# ==========================================================================================
""" Basic tools for read and analyze _raster using gdal."""

import numpy as np
from collections import namedtuple

# import gdalconst
from gdalconst import *
import osr

try:
    import gdal  # from gdal import *
    import gdal_array

except ImportError:
    from osgeo import gdal
    # from osgeo import gdalnumeric
    from osgeo import gdal_array

# Global variables
## NO_DATA = settings.NO_DATA

# Register all drivers
gdal.AllRegister()


class Gdal2Py(object):
    """A class holding information about a ogr feature"""

    #info_tuple = namedtuple('info', 'type projection xsize ysize yres xres extent bands bands_type nodata')
    extent_tuple = namedtuple('extent', ['xmin', 'xmax', 'ymin', 'ymax'])

    # Prevents to create dictionaries (low memory).
    __slots__ = ('type', 'filename', 'projection', 'xsize', 'ysize',
                 'yres', 'xres', 'extent', 'bands',
                 'band_type', 'nodata', 'ds', 'array')

    def __init__(self, ds, data=True):
        """ Read gdal data source (instance variable) """

        # if ds is None:
        #     return
        self.type = 'gdal'
        self.filename = ds.GetMetadataItem('FilePath')

        geotransform = ds.GetGeoTransform()

        self.ds = ds
        self.projection = ds.GetProjection()
        self.bands = ds.RasterCount
        self.band_type = ds.GetRasterBand(1).DataType
        self.nodata = ds.GetRasterBand(1).GetNoDataValue()

        # Handy _raster attributes
        self.xsize = ds.RasterXSize
        self.ysize = ds.RasterYSize
        self.xres = geotransform[1]
        self.yres = geotransform[5]

        xmin = geotransform[0]
        ymax = geotransform[3]
        xmax = geotransform[0] + geotransform[1] * ds.RasterXSize
        ymin = ymax + geotransform[5] * ds.RasterYSize

        self.extent = Gdal2Py.extent_tuple(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

        # Data & data structure
        if data:
            self.array = ds2array(ds)

        # ds.GetMetadata('IMAGE_STRUCTURE')


def file_import(file_path):
    """ Load a gdal file to local database """

    if not isvalid(file_path):
        ###  logger.Logging().warning(msg="File cannot be open. Aborting ...")
        return

    src = gdal.Open(file_path)
    src.SetMetadataItem('FilePath', file_path)

    driver = gdal.GetDriverByName('GTiff')
    data_source = driver.CreateCopy(file_path, src, 0)

    return Gdal2Py(ds=data_source, data=True)


def ds2array(ds):
    """Convert ds to python array"""
    nodata = ds.GetRasterBand(1).GetNoDataValue()
    arr = np.float64(gdal_array.DatasetReadAsArray(ds))
    arr[arr == nodata] = np.nan

    if ds.RasterCount == 1:
        return np.array([arr])

    else:
        return arr


def isvalid(source):
    """ Check if the file is a valid gdal _raster"""

    if not source:
        ### logger.Logging().warning(msg="GDAL source not defined.")
        return False

    # Check if file
    try:
        gdal.UseExceptions()
        ds = gdal.Open(source, GA_ReadOnly)
        # gdal.DontUseExceptions()

    except:
        ds = source

    # Check data source
    for i in xrange(ds.RasterCount):
        ds.GetRasterBand(1).Checksum()
        if gdal.GetLastErrorType() != 0:
            return False

    # Check data projection
    projection = ds.GetProjection()
    epsg, proj4 = wkt2epsg(projection)
    if not proj4 or proj4 == '':
        ### logger.Logging().warning(msg="Data source has NOT projection information.")
        return False

    return True


def wkt2epsg(wkt):
    srs = osr.SpatialReference()
    srs.SetFromUserInput(wkt)

    proj4 = srs.ExportToProj4()
    epsg = srs.GetAttrValue("AUTHORITY", 1)

    return epsg, proj4