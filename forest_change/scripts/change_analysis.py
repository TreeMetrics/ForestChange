# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		change_script.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module is a test.

# COPYRIGHT:	(C) 2018 Treemetrics all rights reserved.
# ==========================================================================================
""" This module is a test"""

from toolbox.image_tools import RasterTools as PyTools


# from toolbox.image_tools import RasterTools as PyTools
# from spatial.saga_cmd import Saga


def main(d1, d2, parameters):

    # settings:
    equalization = None
    normalisation = None
    histogram_matching = None
    method = 'ndvi'       # Intensity, nir or ndvi
    obia = False

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

    return PyTools().single_band_calculator(rlist=[data_dict["d1"]["base_layer"], data_dict["d2"]["base_layer"]],
                                            expression='a-b')