# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		image_tools.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for read and analyze raster arrays

# COPYRIGHT:	(C) 2018 Treemetrics all rights reserved.
# ==========================================================================================
""" This module call the to tools container """

import logging
import numpy as np

from spatial.gdal_reader import GdalReader

import numpy_tools as tools
from spatial import gdal_import


class RasterTools(object):

    # def _import2py(self, src_dataset, memory=False):
    #     """ Import gdal dataset to python.
    #     :param src_dataset: source gdal dataset
    #     :param memory: Boolean . True if wish to save the arrays in the memory."""
    #
    #     return gdalr.gdal2py(src_dataset, memory=memory)

    def _array2raster(self, src_array, name, mask):
        """ Provide the right format to PY/GDAL outputs"""

        return GdalReader().array2ds(src_array, name, mask_ds=mask)

    def equalization(self, input_raster):
        """Equalization of a 2D array with finite values
        :param input_raster 2D array"""

        logging.debug('Starting equalization... ')

        src_ds = gdal_import.src2ds(input_raster)
        raster_arrays = GdalReader().ds2array(src_ds)
        d_bands = tools.equalization(bands_list=raster_arrays)
        # return gdal_import.gdal_import(toolbox.raster.gdal_utils.poly_clip(raster, polygons, output))

        return self._array2raster(d_bands, name='equalization', mask=input_raster)

    def normalisation(self, input_raster):
        """Normalisation of a 2D array to 0-255 
        :param input_raster 2D array"""

        logging.debug('Starting normalisation... ')

        src_ds = gdal_import.src2ds(input_raster)
        raster_arrays = GdalReader().ds2array(src_ds)

        nodata = src_ds.GetRasterBand(1).GetNoDataValue()
        d_bands = tools.normalisation(raster_arrays, nodata=nodata)
        return self._array2raster(d_bands, name="normalization", mask=input_raster)

    def nir(self, input_raster):
        src_ds = gdal_import.src2ds(input_raster)
        raster_array = GdalReader().ds2array(src_ds)
        return self._array2raster(raster_array[3], name="nir", mask=input_raster)

    def histogram_matching(self, input_raster, reference, output='histogram_matching'):

        logging.debug('Starting histogram_matching... ')

        src_ds = gdal_import.src2ds(input_raster)
        raster_array = GdalReader().ds2array(src_ds)

        ref_ds = gdal_import.src2ds(reference)
        ref_array = GdalReader().ds2array(ref_ds)
        nodata = ref_ds.GetRasterBand(1).GetNoDataValue()

        matched_array= tools.histogram_matching(raster_array, ref_array, nodata=nodata)
        return self._array2raster(matched_array, name=output, mask=input_raster)

    def rgb_intensity(self, input_raster):
        """ Intensity for rgb images 
        :param input_raster dictionary with the RGB bands
        """
        logging.debug('Starting rgb_intensity... ')

        src_ds = gdal_import.src2ds(input_raster)
        raster_array = GdalReader().ds2array(src_ds)

        intensity = tools.rgb_intensity(raster_array)
        return self._array2raster(intensity, name='intensity', mask=input_raster)

    def vegetation_index(self, input_raster):
        """ Vegetation Index (GRVI, NDVI) for rgb/rgbnir images 
        :param input_raster dictionary with the RGB bands
        """
        logging.debug('Starting vegetation_index... ')

        src_ds = gdal_import.src2ds(input_raster)
        raster_bands = GdalReader().ds2array(src_ds)

        if len(raster_bands) == 3:
            vi = tools.vegetation_index(red=raster_bands[0], green=raster_bands[1])

        elif len(raster_bands) >= 4:
            vi = tools.vegetation_index(red=raster_bands[0], green=raster_bands[1], nir=raster_bands[3])

        else:
            logging.warning('Not enough bands to create vegetation index.')
            return

        return self._array2raster(vi, name='vi', mask=input_raster)

    def zonal_stats(self, raster, zones, resize=True):

        logging.debug('Starting zonal_stats... ')

        src_ds = gdal_import.src2ds(raster)
        raster_array = GdalReader().ds2array(src_ds)

        zones_ds = gdal_import.src2ds(zones)
        zones_array = GdalReader().ds2array(zones_ds)

        outputs = tools.zonal_stats(valuesarr=raster_array[0], zonesarr=zones_array[0],
                                    resize=resize)

        outputs_dict = {}
        name = 'stats'
        for stat in ['count', 'mean', 'stdev']:
            outputs_dict[str(stat)] = (self._array2raster(outputs[stat], name=str(name + '_' + str(stat)),
                                                          mask=raster))

        return outputs_dict

    def single_band_calculator(self, rlist, expression):
        """ Raster calculator """

        logging.debug('Starting single_band_calculator... ')

        array_list = [GdalReader().ds2array(gdal_import.src2ds(r))[0] if np.array(r).ndim is 2 else
                      GdalReader().ds2array(gdal_import.src2ds(r)) for r in rlist]

        calculation = tools.array_calculator(array_list, expression)

        return self._array2raster(calculation, name=str(expression), mask=rlist[0])
