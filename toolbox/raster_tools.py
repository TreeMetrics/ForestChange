# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		saptial_tools.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for raster spatial analysis

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This Basic tools for raster spatial analysis """

import logging

from toolbox import numpy_tools
from toolbox.raster import gdal_utils
from spatial import gdal_import, gdal_reader

def single_bands_to_multiband(bands_list, output=None):

    gdal_bands_list = [gdal_import.src2ds(i) for i in bands_list]
    return gdal_import.gdal_import(gdal_utils.single_bands_to_multiband(gdal_bands_list, output=output))


def poly_clip(raster, polygons, output):

    return gdal_import.gdal_import(gdal_utils.poly_clip(raster, polygons, output))


def merge(src_list, outname, smooth_edges=False):

    src_ds_list = [gdal_reader.GdalReader().gdal2ds(r) for r in src_list]

    return gdal_import.gdal_import(gdal_utils.merge(src_ds_list, outname, smooth_edges=smooth_edges))


def reclassify(input_raster, new_value, old_value_min=None, old_value_max=None, output=None):

    logging.debug('Reclassify raster... ')

    src_ds = gdal_import.src2ds(input_raster)
    raster_array = gdal_reader.GdalReader().ds2array(src_ds)
    nodata = src_ds.GetRasterBand(1).GetNoDataValue()

    reclassify = numpy_tools.reclassify(raster_array, new_value, old_value_min, old_value_max, nodata=nodata)

    print reclassify

    if not output:
        output = 'reclassified'

    return gdal_import.gdal_import(gdal_reader.GdalReader().array2ds(reclassify, output, mask_ds=input_raster))

