# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		change_script.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module is a test.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module is a test"""

from toolbox import RasterTools as PyTools
from saga_cmd import Saga


def main(d1, d2, output, settings):

    equalization = settings.equalization
    normalisation = settings.normalisation

    # Pre-processing for both datasets
    data_dict = {}
    j = 0
    for dataset in (d1, d2):

        # Data storage dict
        j += 1
        data_dict["d" + str(j)] = {}
        data_dict["d" + str(j)]["dataset"] = dataset

        # Normalise
        if equalization:
            dataset = PyTools().equalization(dataset)

        if normalisation:
            dataset = PyTools().normalisation(dataset)

        data_dict["d" + str(j)]["normalised"] = dataset

        # Get Intensity
        intensity = PyTools().rgb_intensity(dataset)

        if intensity:
            data_dict["d" + str(j)]["intensity"] = intensity

        else:
            raise Exception("Error calculation intensity for file: " + str(dataset))

        # Get Vegetation Index
        vi = PyTools().vegetation_index(dataset)

        if vi:
            data_dict["d" + str(j)]["vi"] = vi

        else:
            raise Exception("Error calculation vegetation index for file: " + str(dataset))

    # Segmentation of the dataset
    segments = Saga().region_growing(rlist=[data_dict["d1"]["intensity"]], output=None)

    # Zonal stats for rasters
    stats1 = PyTools().zonal_stats(raster=data_dict["d1"]["intensity"], zones=segments, resize=True)

    stats2 = PyTools().zonal_stats(raster=data_dict["d2"]["intensity"], zones=segments, resize=True)

    # Difference
    diff = PyTools().single_band_calculator(rlist=[stats1['mean'], stats2['mean']], expression='a-b')

    # Change detection

    return diff
