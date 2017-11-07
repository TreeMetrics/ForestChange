# /usr/bin/env python

# PRODUCT: EO4Atlantic
# MODULE: gdal_reader.py
# AUTHOR: Treemetrics
# DESCRIPTION: 	Basic tools for read and analyze _raster using gdal.

# COPYRIGHT:	(C) 2017 Treemetrics. All rights reserved.
# ==========================================================================================
""" Basic tools for read and analyze _raster using gdal."""


import os
import numpy as np
import logging
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

# Register all drivers
gdal.AllRegister()


class Gdal2Py(object):
    """A class holding information about a ogr feature"""

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
        logging.warning("File cannot be imported. " + str(file_path))
        return

    src = gdal.Open(file_path)
    src.SetMetadataItem('FilePath', file_path)

    #driver = gdal.GetDriverByName('MEM')
    #data_source = driver.CreateCopy(file_path, src, 0)

    return Gdal2Py(ds=src, data=True)


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
        logging.warning("GDAL source not defined.")
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
        logging.warning("Data source has NOT projection information.")
        return False

    return True


def wkt2epsg(wkt):
    srs = osr.SpatialReference()
    srs.SetFromUserInput(wkt)

    proj4 = srs.ExportToProj4()
    epsg = srs.GetAttrValue("AUTHORITY", 1)

    return epsg, proj4


def np2type(data):

    np2gdal = {GDT_Byte: np.uint8,
               GDT_UInt16: np.uint16,
               GDT_Int16: np.int16,
               GDT_UInt32: np.uint32,
               GDT_Int32: np.int32,
               GDT_Float32: np.float32,
               GDT_Float64: np.float64,
               GDT_CInt16: np.complex64,
               GDT_CInt32: np.complex64,
               GDT_CFloat32: np.complex64,
               GDT_CFloat64: np.complex128}

    key = [key for key, value in np2gdal.iteritems() if value == data.dtype][0]

    if data.dtype == np.int64:
        # Note that Int64 is not supported for GDAL
        logging.warning('Int64 is not supported for GDAL')

    return key


def py2gdal(src_array, file_path, ds_base, driver='GTiff', nodata=0, dtype=None):

    # Get required info from ds_base
    driver = gdal.GetDriverByName(driver)
    geotransform = ds_base.GetGeoTransform()
    projection = ds_base.GetProjection()

    # Conver to a 3D numpy array if required
    if isinstance(src_array, list):
        src_array = np.array(src_array)

    if len(src_array.shape) <= 2:
        src_array = np.array([src_array])

    cols = len(src_array[0][0])
    rows = len(src_array[0])
    nbands = len(src_array)

    if rows != ds_base.RasterYSize or cols != ds_base.RasterXSize:
        logging.warning("Columns or rows are not matching the reference dataset")
        return

    # Replace No data
    src_array[src_array == np.nan] = nodata

    # Get dtype from array
    if not dtype:
        if src_array.dtype == np.int64:
            for bid1 in xrange(nbands):
                src_array[bid1] = src_array[bid1].astype(np.int32)

        dtype = np2type(src_array[0])

    out_ds = driver.Create(file_path, cols, rows, nbands, dtype)
    out_ds.SetGeoTransform(geotransform)
    out_ds.SetProjection(projection)

    for bid in xrange(nbands):
        band = out_ds.GetRasterBand(bid + 1)
        band.WriteArray(src_array[bid], 0, 0)
        out_ds.GetRasterBand(bid + 1).SetNoDataValue(nodata)
        band.FlushCache()

    if not os.path.exists(file_path):
        logging.warning("Failed to create GeoTiff file. " + str(file_path))
        return

    return out_ds
