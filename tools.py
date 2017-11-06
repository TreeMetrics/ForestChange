# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		tools.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for read and analyze raster arrays

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module is a test"""

import numpy as np


def equalization(raster_array, nan=0):
    """Equalization of a 2D array with finite values
    :param raster_array 2D array
    :param nan no data value (finite value)"""

    # Replace nan values
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

    return array_equalized


def normalisation(raster_array):
    """Normalisation of a 2D array to 0-255 
    :param raster_array 2D array"""

    raster_array *= 255.0 / raster_array.max()

    return raster_array


def rgb_intensity(raster_bands, type="luminance"):
    """ Intensity for rgb images 
    :param raster_bands dictionary with the RGB bands
    :param type Type of intensity (only "luminance" supported) 
    """

    if type.lower() == "luminance":
        return (0.3 * raster_bands[2] + 0.59 * raster_bands[1] + 0.11 * raster_bands[0])


def vegetation_index(raster_bands):
    """ Vegetation Index (GRVI, NDVI) for rgb/rgbnir images 
    :param raster_bands dictionary with the RGB bands
    """
    if len(raster_bands) == 3:
        # GRVI = (Green - Red) / (Green + Red) "
        return np.divide(np.array(raster_bands[1], dtype="float32") - np.array(raster_bands[0], dtype="float32"),
              np.array((raster_bands[1] + raster_bands[0]), dtype="float32"))

    elif len(raster_bands) >= 4:
        # GRVI = (NIR - Red) / (NIR + Red) "
        return np.divide(np.array(raster_bands[3], dtype="float32") - np.array(raster_bands[0], dtype="float32"),
              np.array((raster_bands[3] + raster_bands[0]), dtype="float32"))




