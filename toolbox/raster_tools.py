# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		saptial_tools.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for raster spatial analysis

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This Basic tools for raster spatial analysis """

import logging

import toolbox.raster.gdal_utils
from spatial import gdal_import, gdal_reader
from raster import gdal_utils


def single_bands_to_multiband(bands_list, output=None):

    gdal_bands_list = [gdal_import.src2ds(i) for i in bands_list]
    return gdal_import.gdal_import(gdal_utils.single_bands_to_multiband(gdal_bands_list, output=output))


def poly_clip(raster, polygons, output):

    return gdal_import.gdal_import(toolbox.raster.gdal_utils.poly_clip(raster, polygons, output))


def merge(src_list, outname, smooth_edges=False):

    src_ds_list = [gdal_reader.GdalReader().gdal2ds(r) for r in src_list]

    return gdal_import.gdal_import(gdal_utils.merge(src_ds_list, outname, smooth_edges=smooth_edges))


def reclassify(input_raster, old_value, new_value, operator, output=None):

    logging.debug('Reclassify raster... ')

    src_ds = gdal_import.src2ds(input_raster)
    raster_array = gdal_reader.GdalReader().ds2array(src_ds)

    reclassify = gdal_utils.reclassify(raster_array, old_value, new_value, operator)

    if not output:
        output = 'reclassified'

    return gdal_import.gdal_import(gdal_reader.GdalReader().array2ds(reclassify, output, mask_ds=input_raster))

