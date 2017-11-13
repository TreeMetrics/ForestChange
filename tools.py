# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		tools.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for read and analyze raster arrays

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module is a test"""

import numpy as np
import logging

import os
from bunch import Config
import gdal_reader as gdalr
from collections import defaultdict


class GeoPyTools(object):

    def __init__(self, create_tif=None):
        """ common variables """

        tempdir = Config()['tempdir']
        self.tempdir = os.path.join(tempdir, 'SAGA')
        self.create_tif = create_tif

        if not os.path.exists(self.tempdir):
            os.makedirs(self.tempdir)

    def _import2py(self, input_file, output=None):

        if os.path.exists(str(input_file)):
            if os.path.splitext(input_file)[0] == '.sgrd':
                input_file = os.path.splitext(input_file)[0] + '.sdat'

            if gdalr.isvalid(input_file):
                return gdalr.file_import(input_file)

            else:
                logging.error('Error importing file. Format unknown.')
                return

        try:
            input_file.array

        except:
            logging.error('Error importing object. Format unknown.')
            return

        return input_file

    def _array2raster(self, src_array, name, mask, nodata=0, ds=True, file_path=None):
        """ Provide the right format to PY/GDAL outputs"""

        return gdalr.array2raster(np.array(src_array), name, mask=mask, nodata=nodata, ds=ds, file_path=file_path)

    def equalization(self, input_raster, nan=0):
        """Equalization of a 2D array with finite values
        :param input_raster 2D array
        :param nan no data value (finite value)"""

        input_raster = self._import2py(input_raster)
        raster_arrays = input_raster.array

        d_bands = []
        for i in xrange(len(raster_arrays)):

            # Replace nan values
            raster_array = raster_arrays[i]
            raster_array[np.isnan(raster_array)] = nan

            # Equalize histogram
            image_histogram, bins = np.histogram(raster_array.flatten(), 256, normed=True)
            cdf = image_histogram.cumsum()  # cumulative distribution function
            cdf = 255 * cdf / cdf[-1]  # normalize

            # use linear interpolation of cdf to find new pixel values
            image_equalized = np.interp(raster_array.flatten(), bins[:-1], cdf)
            array_equalized = image_equalized.reshape(raster_array.shape)

            # Replace nan values
            array_equalized[array_equalized == nan] = np.nan

            if not isinstance(array_equalized, (np.ndarray, np.generic)):
                logging.warning('Failed creating equalization')
                return

            d_bands.append(array_equalized)

        name = os.path.splitext(input_raster.filename)[0] + '_eq' + os.path.splitext(input_raster.filename)[1]
        return self._array2raster(d_bands, name=name, mask=input_raster)

    def normalisation(self, input_raster):
        """Normalisation of a 2D array to 0-255 
        :param input_raster 2D array"""

        input_raster = self._import2py(input_raster)
        raster_arrays = input_raster.array

        d_bands = []
        for i in xrange(len(raster_arrays)):

            raster_array = raster_arrays[i]
            raster_array *= 255.0 / raster_array.max()

            if not isinstance(raster_array, (np.ndarray, np.generic)):
                logging.warning('Failed creating equalization')
                return

            d_bands.append(raster_array)

        name = os.path.splitext(input_raster.filename)[0] + '_norm' + os.path.splitext(input_raster.filename)[1]
        return self._array2raster(d_bands, name=name, mask=input_raster)

    def rgb_intensity(self, input_raster, type="luminance"):
        """ Intensity for rgb images 
        :param input_raster dictionary with the RGB bands
        :param type Type of intensity (only "luminance" supported) 
        """
        input_raster = self._import2py(input_raster)
        raster_bands = input_raster.array

        if len(raster_bands) < 3:
            logging.warning('Not enough bands to create intensity')
            return

        if type.lower() == "luminance":
            intensity = (0.3 * raster_bands[2] + 0.59 * raster_bands[1] + 0.11 * raster_bands[0])

        else:
            logging.error('Only Luminance intensity method available at the moment')
            return

        return self._array2raster(intensity, name='intensity', mask=input_raster)

    def vegetation_index(self, input_raster):
        """ Vegetation Index (GRVI, NDVI) for rgb/rgbnir images 
        :param input_raster dictionary with the RGB bands
        """

        input_raster = self._import2py(input_raster)
        raster_bands = input_raster.array

        if len(raster_bands) == 3:
            # GRVI = (Green - Red) / (Green + Red) "
            vi = np.divide(np.array(raster_bands[1], dtype="float32") - np.array(raster_bands[0], dtype="float32"),
                           np.array((raster_bands[1] + raster_bands[0]), dtype="float32"))

        elif len(raster_bands) >= 4:
            # GRVI = (NIR - Red) / (NIR + Red) "
            vi = np.divide(np.array(raster_bands[3], dtype="float32") - np.array(raster_bands[0], dtype="float32"),
                           np.array((raster_bands[3] + raster_bands[0]), dtype="float32"))

        else:
            logging.warning('Not enough bands to create vegetation index.')
            return

        return self._array2raster(vi, name='vi', mask=input_raster)

    def zonal_stats(self, raster, zones, output=None, count=True, mean=True, stdev=True, resize=True):

        raster = self._import2py(raster)
        zones = self._import2py(zones)

        valuesarr = raster.array[0]
        zonesarr = zones.array[0]

        # Get dimension
        cols = zones.xsize
        rows = zones.ysize

        if (not cols == raster.xsize) or (not rows == raster.ysize):
            if resize:
                rows = min(raster.ysize, rows)
                cols = min(raster.xsize, cols)

            else:
                logging.error("Zonal Statistics", "Error raster shape does not match: vaulues shape=(" +
                              str(raster.ysize) + ',' + str(raster.xsize) + ") zones shape=(" + str(rows) +
                              ',' + str(cols) + ')"')

        # No data
        nodata = raster.nodata
        if not nodata:
            nodata = 0

        # Data format
        valuesarr = valuesarr[:rows, :cols]
        zonesarr = zonesarr[:rows, :cols]
        zonesarr[np.isnan(zonesarr)] = nodata  # Doesn't work with nan values
        zoneslist = zonesarr.ravel()

        # stats
        # Create a dictionary with the object ID as key, and the
        # locations of each pixel in zonal raster that has the same ID (1D array)
        objects = defaultdict(list)
        [objects[zonesarr[i, j]].append([i, j]) for i, j in np.ndindex(zonesarr.shape)]

        outputs = {}
        # Now, calculate the mean raster value per zonal dic "label" (table stats)
        if count:
            countdict = dict(zip(objects.keys(), [
                len([valuesarr[i, j] for i, j in objects[k] if not valuesarr[i, j] == np.nan]) if k >= 0 else nodata for
                k in objects.keys()]))

            # Assign the values for each objects
            countarr = map(countdict.get, zoneslist)
            countarr = np.reshape(countarr, (rows, cols))
            countarr[np.isnan(countarr)] = nodata

            # Create raster
            outputs['count'] = (self._array2raster(countarr, name=str(raster.filename + '_count'), mask=raster,
                                                   nodata=nodata))
            del countarr

        if mean:
            meandic = dict(zip(objects.keys(), [
                np.mean([valuesarr[i, j] for i, j in objects[k] if not valuesarr[i, j] == np.nan]) if k >= 0 else nodata
                for k in objects.keys()]))

            # Assign the values for each objects
            meanarr = map(meandic.get, zoneslist)
            meanarr = np.reshape(meanarr, (rows, cols))
            meanarr[np.isnan(meanarr)] = nodata

            # Create raster
            outputs['mean'] = (self._array2raster(meanarr, name=str(raster.filename + '_mean'), mask=raster,
                                                  nodata=nodata))
            del meanarr

        if stdev:
            stdndic = dict(zip(objects.keys(), [
                np.std([valuesarr[i, j] for i, j in objects[k] if not valuesarr[i, j] == np.nan]) if k >= 0 else nodata
                for k in objects.keys()]))

            # Assign the values for each objects
            stdarr = map(stdndic.get, zoneslist)
            stdarr = np.reshape(stdarr, (rows, cols))
            stdarr[np.isnan(stdarr)] = nodata

            # Create raster
            outputs['stdev'] = (self._array2raster(stdarr, name=str(raster.filename + '_stdev'), mask=raster, nodata=nodata))
            del stdarr

        del zonesarr
        del valuesarr

        return outputs

    def single_band_calculator(self, rlist, expression, output=None):
        """ Raster calculator """

        logging.info('Initializing _raster calculator...')
        logging.info(expression)

        alphabet = tuple('abcdefghijklmnopqrstuvwxyz')
        # rasterdic = defaultdict(list)

        i = -1
        for raster in rlist:
            i += 1
            globals()[alphabet[i]] = self._import2py(raster).array[0]
        # setattr(self, str(alphabet[i]),np.array(gdalr.raster2array(_raster, band=1),dtype='float'))
        # expression = expression.replace(alphabet[i],'self.' + alphabet[i])

        # rasterdic[alphabet[i]].append(np.array(gdalr.raster2array(_raster, band=1),dtype='float'))
        # expression = expression.replace(alphabet[i],'rasterdic[' + alphabet[i] + ']')

        global gexpression
        gexpression = expression

        outarr = eval(gexpression)
        outarr[np.isnan(outarr)] = np.nan


        return self._array2raster(outarr, name=str(expression), mask=rlist[0], nodata=rlist[0].nodata, file_path=output)
