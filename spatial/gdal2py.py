# /usr/bin/env python

# PRODUCT: EO4Atlantic
# MODULE: gdal2py.py
# AUTHOR: J. Alejandro Poveda
# DESCRIPTION: 	Object class to store ogr dataset attributes

# COPYRIGHT:	(C) 2017 Treemetrics. All rights reserved.
# ==========================================================================================

from spatial.gdal_reader import GdalReader


class Gdal2Py(object):
    """A class holding information about a ogr feature"""

    # Prevents to create dictionaries (low memory).
    __slots__ = ('type', 'filename', 'projection', 'xsize', 'ysize',
                 'yres', 'xres', 'extent', 'bands',
                 'dtype', 'nodata', 'ds', 'array', 'epsg')

    def __init__(self, ds, data=True):
        """ Read gdal data source (instance variable) """

        # self.sparse = Config()['sparse']

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

            self.ds = ds
            self.projection = ds.GetProjection()
            self.epsg = GdalReader().wkt2epsg(ds.GetProjection())[0]
            self.bands = ds.RasterCount
            self.dtype = ds.GetRasterBand(1).DataType
            self.nodata = ds.GetRasterBand(1).GetNoDataValue()

            # Handy _raster attributes
            geotransform = ds.GetGeoTransform()
            self.xsize = ds.RasterXSize
            self.ysize = ds.RasterYSize
            self.xres = geotransform[1]
            self.yres = geotransform[5]

            self.extent = GdalReader().get_extent(src_ds=ds)

            # Data & data structure
            if data:
                # if self.sparse:
                #    self.array = ds2array(ds, sparse=True)

                # else:
                self.array = GdalReader().ds2array(ds, sparse=False)
                # ds.GetMetadata('IMAGE_STRUCTURE')
