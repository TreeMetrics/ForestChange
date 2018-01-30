# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		numpy_tools.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for read and analyze raster arrays

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module is a test"""

import collections
import numpy as np
import logging

from core import miscellaneous


def reclassify(array, new_value, old_value_min=None, old_value_max=None, nodata=0):

    print old_value_max
    print old_value_min

    if new_value == 'nan':
        new_value = np.nan

    array = array.astype(np.float)
    nodata = float(nodata)

    array[array == nodata] = np.nan
    np.around(array, decimals=3)

    # Get max and min.
    if not old_value_min and not old_value_max:
        logging.warning('Value for reclassification not defined')

    elif not old_value_min or not miscellaneous.is_float(old_value_min):
        old_value_max = round(float(old_value_max), 3)
        array[array <= old_value_max] = new_value

    elif not old_value_max or not miscellaneous.is_float(old_value_max):
        old_value_min = round(float(old_value_min), 3)
        array[array >= old_value_min] = new_value

    elif old_value_max > old_value_min:
        old_value_max = round(float(old_value_max), 3)
        old_value_min = round(float(old_value_min), 3)

        array[array <= old_value_max] = new_value
        array[array >= old_value_min] = new_value

    elif old_value_max == old_value_min:

        old_value_max = round(float(old_value_max), 3)
        array[array == old_value_max] = new_value

    else:
        logging.warning('Value out of range for reclassification')

    array[array == np.nan] = nodata

    return array


def equalization(bands_list):
    """Equalization of a 2D array with finite values
    :param bands_list List of 2D array"""

    d_bands = []
    for i in xrange(len(bands_list)):

        # Replace nan values
        raster_array = bands_list[i]

        # Equalize histogram
        image_histogram, bins = np.histogram(raster_array.flatten(), 256, normed=True)
        cdf = image_histogram.cumsum()  # cumulative distribution function
        cdf = 255 * cdf / cdf[-1]  # normalize

        # use linear interpolation of cdf to find new pixel values
        image_equalized = np.interp(raster_array.flatten(), bins[:-1], cdf)
        array_equalized = image_equalized.reshape(raster_array.shape)

        # Replace nan values
        if not isinstance(array_equalized, (np.ndarray, np.generic)):
            logging.warning('Failed creating equalization')
            return

        d_bands.append(array_equalized)

    return np.array(d_bands)


def normalisation(bands_list, nodata=0):
    """Normalisation of a 2D array to 0-255 
    :param bands_list List of 2D array"""

    d_bands = []
    for i in xrange(len(bands_list)):

        raster_array = bands_list[i]
        # raster_array[raster_array == nodata] = np.nan

        raster_array = raster_array.astype(np.float16)

        np.seterr(divide='ignore', invalid='ignore')
        raster_array *= 255.0 / raster_array.max()
        # raster_array = np.divide(raster_array, (raster_array.max()/255))

        # mask = np.ma.masked_invalid(raster_array)
        raster_array = np.ma.masked_invalid(raster_array).filled(nodata)
        raster_array = raster_array.astype(np.uint8)

        if not isinstance(raster_array, (np.ndarray, np.generic)):
            logging.warning('Failed creating equalization')
            return

        d_bands.append(raster_array)

    return np.array(d_bands)


def histogram_matching(array1, array2, nodata=0):

    # Histogram matching
    oldshape = array2.shape
    source = array2.ravel()
    template = array1.ravel()

    # get the set of unique pixel values and their corresponding indices and counts

    # isuse with numpy version
    # s_values, bin_idx, s_counts = np.unique(source, return_inverse=True, return_counts=True)

    s_values, bin_idx = np.unique(source, return_inverse=True)
    s_counts = collections.Counter(source).values()

    # slower option
    # s_values =  sorted(set(source))
    # s_counts = [list(source.flatten()).count(v) for v in s_values]

    # isuse with numpy version
    # t_values, t_counts = np.unique(template, return_counts=True)

    t_values = np.unique(template)
    t_counts = collections.Counter(template).values()

    # slower option
    # t_values =  sorted(set(template))
    # t_counts = [list(template.flatten()).count(v) for v in t_values]

    # take the cumsum of the counts and normalize by the number of pixels to
    # get the empirical cumulative distribution functions for the source and
    # template images (maps pixel value --> quantile)
    s_quantiles = np.cumsum(s_counts).astype(np.float64)
    s_quantiles /= s_quantiles[-1]
    t_quantiles = np.cumsum(t_counts).astype(np.float64)
    t_quantiles /= t_quantiles[-1]

    # interpolate linearly to find the pixel values in the template image
    # that correspond most closely to the quantiles in the source image
    interp_t_values = np.interp(s_quantiles, t_quantiles, t_values)

    return np.ma.masked_invalid(interp_t_values[bin_idx].reshape(oldshape)).filled(nodata)


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
    zoneslist = zonesarr.ravel()

    # stats
    # Create a dictionary with the object ID as key, and the
    # locations of each pixel in zonal raster that has the same ID (1D array)
    objects = collections.defaultdict(list)
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

        # Create raster
        outputs['count'] = countarr

    if mean:
        meandic = dict(zip(objects.keys(), [
            np.mean([valuesarr[i, j] for i, j in objects[k] if not valuesarr[i, j] == np.nan]) if k >= 0 else nodata
            for k in objects.keys()]))

        # Assign the values for each objects
        meanarr = map(meandic.get, zoneslist)
        meanarr = np.array(np.reshape(meanarr, (rows, cols)), dtype="float32")

        # Create raster
        outputs['mean'] = meanarr

    if stdev:
        stdndic = dict(zip(objects.keys(), [
            np.std([valuesarr[i, j] for i, j in objects[k] if not valuesarr[i, j] == np.nan]) if k >= 0 else nodata
            for k in objects.keys()]))

        # Assign the values for each objects
        stdarr = map(stdndic.get, zoneslist)
        stdarr = np.array(np.reshape(stdarr, (rows, cols)), dtype="float32")

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

    i = 0
    for array in array_list:
        globals()[alphabet[i]] = array
        i += 1
    # setattr(self, str(alphabet[i]),np.array(gdalr.raster2array(_raster, band=1),dtype='float'))
    # expression = expression.replace(alphabet[i],'self.' + alphabet[i])

    # rasterdic[alphabet[i]].append(np.array(gdalr.raster2array(_raster, band=1),dtype='float'))
    # expression = expression.replace(alphabet[i],'rasterdic[' + alphabet[i] + ']')

    global gexpression
    gexpression = expression

    outarr = eval(gexpression)

    return outarr


