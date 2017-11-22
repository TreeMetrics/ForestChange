# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		toolbox.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for read and analyze raster arrays

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module call the to tools container """

import os
import logging
from bunch import Config
import gdal_reader as gdalr
import numpy_tools as tools


class RasterTools(object):
    def __init__(self, create_tif=None):
        """ common variables """

        tempdir = Config()['tempdir']
        self.tempdir = os.path.join(tempdir)
        self.create_tif = create_tif
        self.debug = Config()['debug']

        if not os.path.exists(self.tempdir):
            os.makedirs(self.tempdir)

    def _import2py(self, src_dataset, memory=False):
        """ Import gdal dataset to python.
        :param src_dataset: source gdal dataset
        :param memory: Boolean . True if wish to save the arrays in the memory."""

        return gdalr.gdal_import(src_dataset, memory=memory)

    def _array2raster(self, src_array, name, mask, nodata=0, ds=True):
        """ Provide the right format to PY/GDAL outputs"""

        if self.debug:
            name = os.path.splitext(os.path.basename(name))[0]
            file_path = os.path.join(self.tempdir, str(name) + '.tif')

        else:
            file_path = None

        return gdalr.array2raster(src_array, name, mask=mask, nodata=nodata, ds=ds, file_path=file_path)

    def equalization(self, input_raster):
        """Equalization of a 2D array with finite values
        :param input_raster 2D array"""

        raster_arrays = input_raster.array
        d_bands = tools.equalization(bands_list=raster_arrays, nan=input_raster.nodata)
        name = os.path.splitext(input_raster.filename)[0] + '_eq' + os.path.splitext(input_raster.filename)[1]
        return self._array2raster(d_bands, name=name, mask=input_raster)

    def normalisation(self, input_raster):
        """Normalisation of a 2D array to 0-255 
        :param input_raster 2D array"""

        raster_arrays = input_raster.array
        d_bands = tools.normalisation(raster_arrays)
        name = os.path.splitext(input_raster.filename)[0] + '_norm' + os.path.splitext(input_raster.filename)[1]
        return self._array2raster(d_bands, name=name, mask=input_raster)

    def rgb_intensity(self, input_raster):
        """ Intensity for rgb images 
        :param input_raster dictionary with the RGB bands
        """

        raster_bands = input_raster.array
        intensity = tools.rgb_intensity(raster_bands)
        return self._array2raster(intensity, name='intensity', mask=input_raster)

    def vegetation_index(self, input_raster):
        """ Vegetation Index (GRVI, NDVI) for rgb/rgbnir images 
        :param input_raster dictionary with the RGB bands
        """
        raster_bands = input_raster.array

        if len(raster_bands) == 3:
            vi = tools.vegetation_index(red=raster_bands[0], green=raster_bands[1])

        elif len(raster_bands) >= 4:
            vi = tools.vegetation_index(red=raster_bands[0], green=raster_bands[1], nir=raster_bands[3])

        else:
            logging.warning('Not enough bands to create vegetation index.')
            return

        return self._array2raster(vi, name='vi', mask=input_raster)

    def zonal_stats(self, raster, zones, resize=True):

        outputs = tools.zonal_stats(valuesarr=raster.array[0], zonesarr=zones.array[0],
                                    resize=resize, nodata=raster.nodata)

        outputs_dict = {}
        for stat in ['count', 'mean', 'stdev']:
            outputs_dict[str(stat)] = (self._array2raster(outputs[stat], name=str(os.path.splitext(raster.filename)[0]
                                                                                  + '_' + str(stat)),
                                                          mask=raster, nodata=raster.nodata))

        return outputs_dict

    def single_band_calculator(self, rlist, expression):
        """ Raster calculator """

        calculation = tools.array_calculator([r.array[0] for r in rlist], expression)

        return self._array2raster(calculation, name=str(expression), mask=rlist[0], nodata=rlist[0].nodata)
