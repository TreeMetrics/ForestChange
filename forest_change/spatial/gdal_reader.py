# /usr/bin/env python

# PRODUCT: EO4Atlantic
# MODULE: gdal_reader.py
# AUTHOR: J. Alejandro Poveda
# DESCRIPTION: 	Basic tools for read and manage raster using gdal.

# COPYRIGHT:	(C) 2018 Treemetrics. All rights reserved.
# ==========================================================================================

import logging
import numpy as np
import os
from collections import namedtuple

import osr
from core import miscellaneous
# import gdalconst
from gdalconst import *

from core.bunch import Config

try:
    import gdal  # from gdal import *
    import gdal_array

except ImportError:
    from osgeo import gdal
    # from osgeo import gdalnumeric
    from osgeo import gdal_array

# Register all drivers
gdal.AllRegister()


class GdalReader:

    extent_tuple = namedtuple('extent', ['xmin', 'xmax', 'ymin', 'ymax'])

    np2gdal = {
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

    def __init__(self):
        """ Read gdal data source (instance variable) """

    @staticmethod
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

    @staticmethod
    def wkt2epsg(wkt):
        srs = osr.SpatialReference()
        srs.SetFromUserInput(wkt)

        proj4 = srs.ExportToProj4()
        epsg = srs.GetAttrValue("AUTHORITY", 1)

        return epsg, proj4

    def get_extent(self, src_ds):
        """ Create extents tuple from geotransform"""

        geotransform = src_ds.GetGeoTransform()

        xmin = geotransform[0]
        ymax = geotransform[3]
        xmax = geotransform[0] + geotransform[1] * src_ds.RasterXSize
        ymin = ymax + geotransform[5] * src_ds.RasterYSize

        return self.extent_tuple(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

    @staticmethod
    def world2pixel(geo_matrix, x, y):
        """ Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
        the pixel location of a geospatial coordinate"""

        ul_x = geo_matrix[0]  # min x
        ul_y = geo_matrix[3]  # max y
        x_dist = geo_matrix[1]  # pixel size x
        y_dist = abs(geo_matrix[5])  # pixel size y
        # rtn_x = geo_matrix[2]
        # rtn_y = geo_matrix[4]
        pixel = int((x - ul_x) / x_dist)
        line = int((ul_y - y) / y_dist)

        return pixel, line

    def ds2array(self, src_ds, sparse=False):
        """Convert ds to python array"""

        # Dected array type, Numpy nan is only compatible with float64
        dtype = [key for key, value in self.np2gdal.iteritems() if value == src_ds.GetRasterBand(1).DataType][0]
        numpy_array = getattr(np, dtype)
        arr = numpy_array(gdal_array.DatasetReadAsArray(src_ds))

        # srcArray = gdalnumeric.LoadFile(raster)

        # arr = chunks(np.float64(gdal_array.DatasetReadAsArray(ds)), size=ds.RasterXSize*ds.RasterYSize)

        if sparse:

            from scipy import sparse

            nodata = src_ds.GetRasterBand(1).GetNoDataValue()

            if miscellaneous.is_number(nodata) and nodata is not 0:
                arr[arr == nodata] = 0

            if len(arr) == 2:
                crs_arrs = [sparse.csr_matrix(np.array(arr))]

            elif len(arr) > 2:
                crs_arrs = [sparse.csr_matrix(np.array(band_arr)) for band_arr in arr]

                # arr = sparse.coo_matrix(arr)
                # rows_arr = sparse.csr_matrix(np.array(band_arr))
                # cols_arr = sparse.csc_matrix(arr)

            else:
                logging.error('ds2array. Only 2D (single band) or 3+D (multiple bands) allowed. ' +
                              str(len(arr)) + 'D found.')
                return

            del arr
            return crs_arrs

        else:
            return arr

            # With noData
            # arr = np.float64(gdal_array.DatasetReadAsArray(ds))
            # nodata = ds.GetRasterBand(1).GetNoDataValue()
            #
            # if is_number(nodata):
            #     arr[arr == nodata] = np.nan
            #
            # else:
            #     arr[arr == 0] = np.nan
            #
            # if ds.RasterCount == 1:
            #     return np.array([arr])
            #
            # else:
            #     return arr

    def isvalid(self, ds):
        if self.gdal2ds(ds):
            return True

        else:
            logging.debug("GDAL source is not valid.")
            return False

    def gdal2ds(self, source, check_proj=True):
        """ Check if the file is a valid gdal _raster"""

        if not source:
            logging.error("GDAL source not defined.")
            return False

        # SAGA fix
        if os.path.isfile(str(source)):
            if os.path.splitext(source)[0] == '.sgrd':
                source = os.path.splitext(source)[0] + '.sdat'

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
                ds.GetRasterBand(i + 1).Checksum()
                if gdal.GetLastErrorType() != 0:
                    return False

            # Check data projection
            projection = ds.GetProjection()
            epsg, proj4 = self.wkt2epsg(projection)

        except:
            logging.error("GDAL source cannot be read.")
            return

        if check_proj:
            if not proj4 or proj4 == '':
                logging.warning("Data source has NOT projection information. " + str(source))
                return

        return ds

    def gdal2file(self, source, file_path, driver_name='GTiff'):

        return gdal.GetDriverByName(driver_name).CreateCopy(file_path, source, 0)

    def create_ds(self, name, x_res, y_res, nbands, data_type):
        # Get global variables
        tempdir = Config()['tempdir']
        verbose_level = Config()['verbose']

        file_extention = os.path.splitext(name)[1].lower()
        if os.path.exists(os.path.dirname(name)):

            if file_extention == '.sgrd' or file_extention == '.sdat':
                driver_name = 'SAGA'
                name = miscellaneous.new_unique_file(os.path.splitext(name)[0] + '.sdat')

            else:
                driver_name = 'GTiff'
                name = miscellaneous.new_unique_file(os.path.splitext(name)[0] + '.tif')

        else:

            name = os.path.basename(os.path.splitext(name)[0])

            if verbose_level == 'debug':
                driver_name = 'GTiff'
                name = miscellaneous.new_unique_file(os.path.join(tempdir, str(name) + '.tif'))

            else:
                driver_name = 'MEM'
                name = name

        if not driver_name == 'MEM' and not os.path.exists(tempdir):
            os.makedirs(tempdir)

        out_ds = gdal.GetDriverByName(driver_name).Create(name, x_res, y_res, nbands, data_type)
        out_ds.SetMetadataItem('FilePath', name)

        if not self.gdal2ds(out_ds, check_proj=False):
            logging.error('Gdal dataset cannot be create. ' + str(name))

        return out_ds

    def array2ds(self, src_array, output, mask_ds=None, geotransform=None, projection=None, nodata=None):

        # Size and bands
        if np.array(src_array).ndim == 2:
            nbands = 1
            xsize = len(src_array[0])
            ysize = len(src_array)
            array = np.array([src_array])
            dtype = self.np2type(src_array)

        elif np.array(src_array).ndim == 3:
            nbands = len(src_array)
            xsize = len(src_array[0][0])
            ysize = len(src_array[0])
            array = src_array
            dtype = self.np2type(src_array[0])

        else:
            logging.error('Creating new array2ds failed. Number of bands is not recognised.')
            return

        # Geotransform
        if not geotransform:

            try:
                geotransform = mask_ds.GetGeoTransform()

            except:
                logging.error('Creating new Py raster failed. Geotransform are not defined.')
                return

        # Projection
        if not projection:

            try:
                projection = mask_ds.GetProjection()

            except:
                logging.error('Creating new Py raster failed. Projection are not defined.')
                return

        # Create dataset
        out_ds = self.create_ds(output, xsize, ysize, nbands, dtype)
        out_ds.SetGeoTransform(geotransform)
        out_ds.SetProjection(projection)

        # Replace No data
        try:
            nodata = mask_ds.GetRasterBand(1).GetNoDataValue()

        except:
            pass

        if not miscellaneous.is_number(nodata):
            nodata = 0

        # array[array == np.nan] = nodata

        # Write bands
        for bid in xrange(nbands):
            band = out_ds.GetRasterBand(bid + 1)
            band.WriteArray(array[bid], 0, 0)
            out_ds.GetRasterBand(bid + 1).SetNoDataValue(nodata)
            band.FlushCache()

        if self.isvalid(out_ds):
            return out_ds


# def sen_isvalid(source):
#     if not source:
#         logging.error("Sentinel source not defined.")
#         return False
#
#     print source
#     # Check if file
#     try:
#         gdal.UseExceptions()
#         gdal.Open(source, GA_ReadOnly)
#         # gdal.DontUseExceptions()
#
#     except:Starting single_band_calculator
#         logging.error("Sentinel source cannot be read.")
#         return
#
#     return True

# def path2driver(file_path, name=None):
#     # Get global variables
#     tempdir = Config()['tempdir']
#
#     verbose_level = Config()['verbose']
#
#     if not os.path.exists(tempdir):
#         os.makedirs(tempdir)
#
#     if file_path is None:
#         if verbose_level == 'debug':
#             driver_name = 'GTiff'
#
#             if name:
#                 name = os.path.splitext(os.path.basename(name))[0]
#
#             else:
#                 name = "temp"
#
#             file_path = miscellaneous.new_unique_file(os.path.join(tempdir, str(name) + '.tif'))
#
#         else:
#             driver_name = 'MEM'
#             file_path = ''
#
#     else:
#         if os.path.splitext(file_path)[1].lower() == '.tif' or os.path.splitext(file_path)[1].lower == '.tiff':
#
#             driver_name = 'GTiff'
#             file_path = os.path.splitext(file_path)[0] + '.tif'
#
#         elif os.path.splitext(file_path)[1].lower() == '.sgrd' or os.path.splitext(file_path)[1].lower == '.sdat':
#             driver_name = 'SAGA'
#             file_path = os.path.splitext(file_path)[0] + '.sdat'
#
#         elif isinstance(file_path, str):
#             driver_name = 'GTiff'
#             file_path = os.path.splitext(file_path)[0] + '.tif'
#
#         else:
#             logging.warning("Failed to load driver for file. " + str(file_path))
#             return
#
#     file_path = miscellaneous.new_unique_file(file_path)
#     driver = gdal.GetDriverByName(str(driver_name))
#
#     return driver, file_path


# def array2raster(src_array, output, mask=None, geotransform=None, projection=None, nodata=0):
#     new_raster = Gdal2Py(ds='new')
#     src_array = np.array(src_array)
#     new_raster.filename = output
#
#     # No data
#     if mask and miscellaneous.is_number(mask.nodata):
#         new_raster.nodata = mask.nodata
#
#     else:
#         new_raster.nodata = nodata
#
#     # Size and bands
#     if src_array.ndim == 2:
#         new_raster.bands = 1
#         new_raster.xsize = len(src_array[0])
#         new_raster.ysize = len(src_array)
#         new_raster.array = np.array([src_array])
#         new_raster.dtype = np2type(src_array)
#
#     elif src_array.ndim == 3:
#         new_raster.bands = len(src_array)
#         new_raster.xsize = len(src_array[0][0])
#         new_raster.ysize = len(src_array[0])
#         new_raster.array = src_array
#         new_raster.dtype = np2type(src_array[0])
#
#     else:
#         logging.error('Creating new Py raster failed. Number of bands is not recognised.')
#         return
#
#     # Geotransform
#     if geotransform and len(geotransform) == 6:
#         new_raster.xres = geotransform[1]
#         new_raster.yres = geotransform[5]
#         xmin = geotransform[0]
#         ymax = geotransform[3]
#         xmax = geotransform[0] + geotransform[1] * new_raster.xsize
#         ymin = ymax + geotransform[5] * new_raster.ysize
#
#         new_raster.extent = GdalReader().extent_tuple(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
#
#     else:
#
#         if mask:
#             new_raster.xres = mask.xres
#             new_raster.yres = mask.xres
#             new_raster.extent = mask.extent
#
#         else:
#             logging.error('Creating new Py raster failed. Geotransform are not defined.')
#             return
#
#     # Projection
#     if projection:
#         new_raster.projection = projection
#
#     else:
#         if mask:
#             new_raster.projection = mask.projection
#             new_raster.epsg = mask.epsg
#
#         else:
#             logging.error('Creating new Py raster failed. Projection are not defined.')
#             return
#
#     # Create ds
#     new_raster.ds = py2gdal(py_raster=new_raster)
#     new_raster.filename = new_raster.ds.GetMetadataItem('FilePath')
#
#     return new_raster

# class GdalReader:
#
#     def __init__(self, file_path=None):
#
#         self.tempdir = Config()['tempdir']
#         self.debug = Config()['debug']
#         self.driver = None
#
#         if not os.path.exists(self.tempdir):
#             os.makedirs(self.tempdir)
#
#         if file_path is None:
#             if self.debug:
#                 self.driver_name = 'GTiff'
#                 self.file_path = new_unique_file(os.path.join(self.tempdir, 'temp.tif'))
#
#             else:
#                 self.driver_name = 'MEM'
#                 self.file_path = ''
#
#         else:
#             if os.path.splitext(file_path)[1].lower() == '.tif' or os.path.splitext(file_path)[1].lower == '.tiff':
#                 self.driver_name = 'GTiff'
#                 self.file_path = new_unique_file(os.path.splitext(file_path)[0] + '.tif')
#
#             elif os.path.splitext(file_path)[1].lower() == '.sgrd' or os.path.splitext(file_path)[1].lower == '.sdat':
#                 self.driver_name = 'SAGA'
#                 self.file_path = new_unique_file(os.path.splitext(file_path)[0] + '.sdat')
#
#             else:
#                 logging.warning("Failed to load driver for file. " + str(file_path))
#
#         self.driver = gdal.GetDriverByName(self.driver_name)
#
#
#     def path2driver(self, file_path, name=None):
#         # Get global variables
#
#         if file_path is None:
#             if self.debug:
#                 driver_name = 'GTiff'
#
#                 if name:
#                     name = os.path.splitext(os.path.basename(name))[0]
#
#                 else:
#                     name = "temp"
#
#                 file_path = new_unique_file(os.path.join(self.tempdir, str(name) + '.tif'))
#
#             else:
#                 driver_name = 'MEM'
#                 file_path = ''
#
#         else:
#             if os.path.splitext(file_path)[1].lower() == '.tif' or os.path.splitext(file_path)[1].lower == '.tiff':
#
#                 driver_name = 'GTiff'
#                 file_path = os.path.splitext(file_path)[0] + '.tif'
#
#             elif os.path.splitext(file_path)[1].lower() == '.sgrd' or os.path.splitext(file_path)[1].lower == '.sdat':
#                 driver_name = 'SAGA'
#                 file_path = os.path.splitext(file_path)[0] + '.sdat'
#
#             else:
#                 logging.warning("Failed to load driver for file. " + str(file_path))
#                 return
#
#         file_path = new_unique_file(file_path)
#         self.driver = driver_name
#
#         return file_path
#
#     def bands_to_single_ds(self, bands_list):
#         """ Convert several gdal single file to a single gdal datasource"""
#         src_ds = gdal.OpenShared(bands_list[0])
#         src_ds.SetMetadataItem('FilePath', bands_list[0])
#
#         #file_path = path2driver(file_path=file_path, name=bands_list[0])
#
#         # tmp_ds = gdal.GetDriverByName('MEM').CreateCopy('', src_ds, 0)
#         tmp_ds = self.driver.CreateCopy(self.file_path, src_ds, 0)
#
#         i = 0
#         for mask_path in bands_list[1:]:
#             i = i + 1
#
#             mask_ds = gdal.OpenShared(mask_path)
#             mask = mask_ds.GetRasterBand(1).ReadAsArray()
#
#             tmp_ds.AddBand()
#             tmp_ds.GetRasterBand(i).WriteArray(mask)
#             del mask_ds
#             del mask
#
#         if self.driver == 'MEM':
#             return tmp_ds
#
#         elif os.path.exists(self.file_path):
#             return tmp_ds
#
#         else:
#             logging.warning("Failed to create GDAL file. " + str(self.file_path))
#             return
