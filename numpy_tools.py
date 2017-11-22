# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		numpy_tools.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for read and analyze raster arrays

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module is a test"""

from collections import defaultdict
import numpy as np
import logging


def equalization(bands_list, nan=0):
    """Equalization of a 2D array with finite values
    :param bands_list List of 2D array
    :param nan no data value (finite value)"""

    d_bands = []
    for i in xrange(len(bands_list)):

        # Replace nan values
        raster_array = bands_list[i]
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

    return d_bands


def normalisation(bands_list):
    """Normalisation of a 2D array to 0-255 
    :param bands_list List of 2D array"""

    d_bands = []
    for i in xrange(len(bands_list)):

        raster_array = bands_list[i]
        raster_array *= 255.0 / raster_array.max()

        if not isinstance(raster_array, (np.ndarray, np.generic)):
            logging.warning('Failed creating equalization')
            return

        d_bands.append(raster_array)

    return d_bands


def rgb_intensity(bands_list):
    """ Intensity for rgb images 
    :param bands_list List of 2D array with the RGB bands
    """

    if len(bands_list) < 3:
        logging.warning('Not enough bands to create intensity')
        return

    else:
        intensity = (0.3 * bands_list[2] + 0.59 * bands_list[1] + 0.11 * bands_list[0])
        return intensity


def vegetation_index(red, green, nir=None):
    """ Vegetation Index (GRVI, NDVI) for rgb/rgbnir images 
    :param red band array
    :param green band array
    :param nir band array (optional)
    """

    if nir is None:
        # GRVI = (Green - Red) / (Green + Red) "
        vi = np.divide(np.array(green, dtype="float32") - np.array(red, dtype="float32"),
                       np.array((green + red), dtype="float32"))

    else:
        # NDVI = (NIR - Red) / (NIR + Red) "
        vi = np.divide(np.array(nir, dtype="float32") - np.array(red, dtype="float32"),
                       np.array((nir + red), dtype="float32"))

    return vi


def zonal_stats(valuesarr, zonesarr, count=True, mean=True, stdev=True, resize=True, nodata=0):

    # Get dimension
    rows = valuesarr.shape[0]
    cols = valuesarr.shape[1]

    if not valuesarr.shape == zonesarr.shape:
        if resize:
            rows = min(valuesarr.shape[0], zonesarr.shape[0])
            cols = min(valuesarr.shape[1], zonesarr.shape[1])

        else:
            logging.error("Zonal Statistics", "Error raster shape does not match: vaulues shape=" +
                          str(valuesarr.shape) + ", zones shape=" + str(zonesarr.shape[1]))
            return

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
        countarr = np.array(np.reshape(countarr, (rows, cols)), dtype="float32")
        countarr[np.isnan(countarr)] = nodata

        # Create raster
        outputs['count'] = countarr

    if mean:
        meandic = dict(zip(objects.keys(), [
            np.mean([valuesarr[i, j] for i, j in objects[k] if not valuesarr[i, j] == np.nan]) if k >= 0 else nodata
            for k in objects.keys()]))

        # Assign the values for each objects
        meanarr = map(meandic.get, zoneslist)
        meanarr = np.array(np.reshape(meanarr, (rows, cols)), dtype="float32")
        meanarr[np.isnan(meanarr)] = nodata

        # Create raster
        outputs['mean'] = meanarr

    if stdev:
        stdndic = dict(zip(objects.keys(), [
            np.std([valuesarr[i, j] for i, j in objects[k] if not valuesarr[i, j] == np.nan]) if k >= 0 else nodata
            for k in objects.keys()]))

        # Assign the values for each objects
        stdarr = map(stdndic.get, zoneslist)
        stdarr = np.array(np.reshape(stdarr, (rows, cols)), dtype="float32")
        stdarr[np.isnan(stdarr)] = nodata

        # Create raster
        outputs['stdev'] = stdarr

    del zonesarr
    del valuesarr

    return outputs


def array_calculator(array_list, expression):
    """ Raster calculator 
        :param expression: use letters for each array by order in the list (e.g.a*2+b)
        :param array_list List of 2D array"""

    logging.info('Initializing _raster calculator...')
    logging.info(expression)

    alphabet = tuple('abcdefghijklmnopqrstuvwxyz')
    # rasterdic = defaultdict(list)

    i = -1
    for array in array_list:
        i += 1
        globals()[alphabet[i]] = array
    # setattr(self, str(alphabet[i]),np.array(gdalr.raster2array(_raster, band=1),dtype='float'))
    # expression = expression.replace(alphabet[i],'self.' + alphabet[i])

    # rasterdic[alphabet[i]].append(np.array(gdalr.raster2array(_raster, band=1),dtype='float'))
    # expression = expression.replace(alphabet[i],'rasterdic[' + alphabet[i] + ']')

    global gexpression
    gexpression = expression

    outarr = eval(gexpression)
    outarr[np.isnan(outarr)] = np.nan

    return outarr
