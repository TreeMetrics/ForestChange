# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		change_script.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module is a test.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module is a test"""

from toolbox.image_tools import RasterTools as PyTools


def main(d1, d2, settings):

    # settings:
    equalization = None
    normalisation = True
    histogram_matching = None
    method = 'nir'       # Intensity, nir or ndvi

    # Pre-processing for both datasets
    data_dict = {}
    j = 0
    for dataset in (d1, d2):

        # Data storage dict
        j += 1
        data_dict["d" + str(j)] = {}
        data_dict["d" + str(j)]["dataset"] = dataset

        if method.lower() == 'nir':
            dataset = PyTools().nir(dataset)
            data_dict["d" + str(j)]["nir"] = dataset

        # Equalization
        if equalization:
             dataset = PyTools().equalization(dataset)

        # Normalise
        if normalisation:
            dataset = PyTools().normalisation(dataset)
            data_dict["d" + str(j)]["normalised"] = dataset

        # Get Method
        if method.lower() == 'intensity':
            base_layer = PyTools().rgb_intensity(dataset)
            data_dict["d" + str(j)]["base_layer"] = base_layer

        elif method.lower() == 'ndvi':
            base_layer = PyTools().vegetation_index(dataset)
            data_dict["d" + str(j)]["base_layer"] = base_layer

        elif method.lower() == 'nir':
            data_dict["d" + str(j)]["base_layer"] = dataset

        else:
            raise Exception("Change detection method not defined")

        del dataset

        # Histogram matching
        if histogram_matching:
            data_dict["d1"]["base_layer"] = PyTools().histogram_matching(input_raster=data_dict["d1"]["base_layer"],
                                                                         reference=data_dict["d2"]["base_layer"],
                                                                         output='hist_matching_dataset1')

    diff = PyTools().single_band_calculator(rlist=[data_dict["d1"]["base_layer"], data_dict["d2"]["base_layer"]],
                                            expression='a-b')

    return diff

    # Object base apporach

    # Segmentation of the dataset
    #segments = Saga().region_growing(rlist=[data_dict["d1"]["intensity"]], output=None)

    # Zonal stats for rasters
    #stats1 = PyTools().zonal_stats(raster=data_dict["d1"]["intensity"], zones=segments, resize=True)

    #stats2 = PyTools().zonal_stats(raster=data_dict["d2"]["intensity"], zones=segments, resize=True)

    # Difference
    #diff = PyTools().single_band_calculator(rlist=[stats1['mean'], stats2['mean']], expression='a-b')