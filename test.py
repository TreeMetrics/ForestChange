# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		test.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module is a test.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module is a test"""

import os
import gdal_reader as gdalr
from tools import GeoPyTools as PyTools
from saga_cmd import Saga

def main(d1, d2, output, settings):

    equalization = settings.equalization
    normalisation = settings.normalisation
    bands_schema = [settings.bands["red_band"], settings.bands["green_band"], settings.bands["blue_band"]]

    if "nir_band" in settings.bands:
        bands_schema.append(settings.bands["nir_band"])

    # Pre-processing for both datasets
    data_dict = {}
    j = 0
    for dataset in (d1, d2):

        # Data storage dict
        j += 1
        data_dict["d" + str(j)] = {}

        # Import files
        """'type', 'filename', 'projection', 'xsize', 'ysize', 'yres', 'xres', 'extent', 'bands', 'band_type', 
        'nodata', 'ds', 'array'"""

        d = gdalr.file_import(dataset)

        if not d:
            raise Exception("Error importing file: " + str(dataset))

        data_dict["d" + str(j)]["dataset"] = d

        # Re-arrange bands
        d_array = []
        for bi in xrange(min(len(bands_schema), len(d.array))):
            d_array.append(d.array[bi])

        d.array = d_array

        # Normalise
        if equalization:
            d = PyTools().equalization(d)

        if normalisation:
            d = PyTools().normalisation(d)

        data_dict["d" + str(j)]["normalised"] = d

        # Get Intensity
        intensity = PyTools().rgb_intensity(d)

        if intensity:
            data_dict["d" + str(j)]["intensity"] = intensity

        else:
            raise Exception("Error calculation intensity for file: " + str(dataset))

        # Get Vegetation Index
        vi = PyTools().vegetation_index(d)

        if vi:
            data_dict["d" + str(j)]["vi"] = vi

        else:
            raise Exception("Error calculation vegetation index for file: " + str(dataset))

    # Segmentation of the dataset
    segments = Saga().region_growing(rlist=[data_dict["d1"]["intensity"]], output=None)

    # Zonal stats for rasters
    stats1 = PyTools().zonal_stats(raster=data_dict["d1"]["intensity"], zones=segments,
                                  output=None, count=False, mean=True, stdev=False, resize=True)


    stats2 = PyTools().zonal_stats(raster=data_dict["d2"]["intensity"], zones=segments,
                                  output=None, count=False, mean=True, stdev=False, resize=True)


    diff = PyTools().single_band_calculator(rlist=[stats1['mean'], stats2['mean']], expression='a-b+1',
                                            output=output)

    return diff