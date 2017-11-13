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

NP2GDAL = {
  "uint8": 1,
  "int8": 1,
  "uint16": 2,
  "int16": 3,
  "uint32": 4,
  "int32": 5,
  "float32": 6,
  "float64": 7,
  "complex64": 10,
  "complex128": 11}


class Gdal2Py(object):
    """A class holding information about a ogr feature"""

    extent_tuple = namedtuple('extent', ['xmin', 'xmax', 'ymin', 'ymax'])

    # Prevents to create dictionaries (low memory).
    __slots__ = ('type', 'filename', 'projection', 'xsize', 'ysize',
                 'yres', 'xres', 'extent', 'bands',
                 'dtype', 'nodata', 'ds', 'array', 'epsg')

    def __init__(self, ds, data=True):
        """ Read gdal data source (instance variable) """

        if str(ds).lower() == 'new':
            self.type = 'gdal'
            self.filename = None
            self.ds = None
            self.projection = None
            self.epsg = None
            self.bands = None
            self.dtype = None
            self.nodata = None
            self.xsize = None
            self.ysize = None
            self.xres = None
            self.yres = None
            self.extent = None
            self.array = None

        else:
            self.type = 'gdal'
            self.filename = ds.GetMetadataItem('FilePath')

            geotransform = ds.GetGeoTransform()

            self.ds = ds
            self.projection = ds.GetProjection()
            self.epsg = wkt2epsg(ds.GetProjection())[0]
            self.bands = ds.RasterCount
            self.dtype = ds.GetRasterBand(1).DataType
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


def wkt2epsg(wkt):
    srs = osr.SpatialReference()
    srs.SetFromUserInput(wkt)

    proj4 = srs.ExportToProj4()
    epsg = srs.GetAttrValue("AUTHORITY", 1)

    return epsg, proj4


def file_import(file_path):
    """ Load a gdal file to local database """

    if not isvalid(file_path):
        logging.warning("File cannot be imported. " + str(file_path))
        return

    src = gdal.Open(file_path)
    src.SetMetadataItem('FilePath', file_path)

    # driver = gdal.GetDriverByName('MEM')
    # data_source = driver.CreateCopy(file_path, src, 0)

    return Gdal2Py(ds=src, data=True)


def ds2array(ds):
    """Convert ds to python array"""

    # Dected array type, Numpy nan is only compatible with float64
    # dtype = [key for key, value in NP2GDAL.iteritems() if value == ds.GetRasterBand(1).DataType][0]
    # numpy_array = getattr(np, dtype)
    # arr = numpy_array(gdal_array.DatasetReadAsArray(ds))

    arr = np.float64(gdal_array.DatasetReadAsArray(ds))
    nodata = ds.GetRasterBand(1).GetNoDataValue()
    arr[arr == nodata] = np.nan

    if ds.RasterCount == 1:
        return np.array([arr])

    else:
        return arr


def isvalid(source):
    """ Check if the file is a valid gdal _raster"""

    if not source:
        logging.error("GDAL source not defined.")
        return False

    # Check if file
    try:
        gdal.UseExceptions()
        ds = gdal.Open(source, GA_ReadOnly)
        # gdal.DontUseExceptions()

    except:
        ds = source

    # Check data source
    try:
        for i in xrange(ds.RasterCount):
            ds.GetRasterBand(1).Checksum()
            if gdal.GetLastErrorType() != 0:
                return False

        # Check data projection
        projection = ds.GetProjection()
        epsg, proj4 = wkt2epsg(projection)

    except:
        logging.error("GDAL source cannot be read.")
        return False

    if not proj4 or proj4 == '':
        logging.warning("Data source has NOT projection information.")
        return False

    return True


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
        return 'GDT_Int32'

    return key


def py2gdal(py_raster, file_path=None):

    if not file_path:
        driver_name = 'MEM'
        driver = gdal.GetDriverByName(driver_name)
        file_path = py_raster.filename

    else:
        if os.path.splitext(file_path)[1].lower() == '.tif' or os.path.splitext(file_path)[1].lower == '.tiff':
            driver_name = 'GTiff'
            driver = gdal.GetDriverByName(driver_name)
            file_path = os.path.splitext(file_path)[0] + '.tif'

        elif os.path.splitext(file_path)[1].lower() == '.sgrd' or os.path.splitext(file_path)[1].lower == '.sdat':
            driver_name = 'SAGA'
            driver = gdal.GetDriverByName(driver_name)
            file_path = os.path.splitext(file_path)[0] + '.sdat'

        else:
            logging.warning("Failed to load driver for file. " + str(file_path))
            return

        if os.path.exists(file_path):
            i = 0
            while os.path.exists(file_path):
                i += 1
                file_path = str(os.path.splitext(file_path)[0]) + '_' + str(i) + os.path.splitext(file_path)[1]

    geotransform = (py_raster.extent[0], py_raster.xres, 0, py_raster.extent[3], 0, -py_raster.yres)

    out_ds = driver.Create(file_path, py_raster.xsize, py_raster.ysize, py_raster.bands, py_raster.dtype)
    out_ds.SetMetadataItem('FilePath', py_raster.filename)
    out_ds.SetGeoTransform(geotransform)
    out_ds.SetProjection(py_raster.projection)

    # Replace No data
    src_array = py_raster.array
    src_array[src_array == np.nan] = py_raster.nodata

    # Write bands
    for bid in xrange(py_raster.bands):
        band = out_ds.GetRasterBand(bid + 1)
        band.WriteArray(src_array[bid], 0, 0)
        out_ds.GetRasterBand(bid + 1).SetNoDataValue(py_raster.nodata)
        band.FlushCache()

    # Check tif file
    if driver_name == 'MEM':
        return out_ds

    if os.path.exists(file_path):
        return file_path

    else:
        logging.warning("Failed to create GDAL file. " + str(file_path))
        return


def array2raster(src_array, name, mask=None, geotransform=None, projection=None, nodata=0, ds=False, file_path=None):

    new_raster = Gdal2Py(ds='new')

    if file_path:
        name = file_path

    new_raster.filename = name

    # No data
    if mask:
        new_raster.nodata = mask.nodata

    else:
        new_raster.nodata = nodata

    # Size and bands
    if src_array.ndim == 2:
        new_raster.bands = 1
        new_raster.xsize = len(src_array[0])
        new_raster.ysize = len(src_array)
        new_raster.array = np.array([src_array])
        new_raster.dtype = np2type(src_array)

    elif src_array.ndim == 3:
        new_raster.bands = len(src_array)
        new_raster.xsize = len(src_array[0][0])
        new_raster.ysize = len(src_array[0])
        new_raster.array = src_array
        new_raster.dtype = np2type(src_array[0])

    else:
        logging.error('Creating new Py raster failed. Number of bands is not recognised.')
        return

    # Geotransform
    if geotransform and len(geotransform) == 6:
        new_raster.xres = geotransform[1]
        new_raster.yres = geotransform[5]
        xmin = geotransform[0]
        ymax = geotransform[3]
        xmax = geotransform[0] + geotransform[1] * new_raster.xsize
        ymin = ymax + geotransform[5] * new_raster.ysize

        new_raster.extent = Gdal2Py.extent_tuple(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

    else:

        if mask:
            new_raster.xres = mask.xres
            new_raster.yres = mask.xres
            new_raster.extent = mask.extent

        else:
            logging.error('Creating new Py raster failed. Geotransform are not defined.')
            return

    # Projection
    if projection:
        new_raster.projection = projection

    else:
        if mask:
            new_raster.projection = mask.projection
            new_raster.epsg = mask.epsg

        else:
            logging.error('Creating new Py raster failed. Projection are not defined.')
            return

    if ds:
        new_raster.ds = py2gdal(py_raster=new_raster, file_path=file_path)

    return new_raster
