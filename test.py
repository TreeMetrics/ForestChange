# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		test.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module is a test.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module is a test"""


import gdal_reader as gdalr
import tools


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

        # Normalise
        d_bands = []
        for i in xrange(d.bands):

            d_array = d.array[i]
            if equalization:
                d_array = tools.equalization(d_array)

                if d_array is None:
                    raise Exception("Error in file equalization: " + str(dataset))

            if normalisation:
                d_array = tools.normalisation(d_array)

                if d_array is None:
                    raise Exception("Error in file normalisation: " + str(dataset))

            d_bands.append(d_array)

        data_dict["d" + str(j)]["normalised"] = d_bands

        # Get Intensity
        intensity = tools.rgb_intensity(d_bands)

        if not intensity is None:
            data_dict["d" + str(j)]["intensity"] = tools.rgb_intensity(d_bands)

        else:
            raise Exception("Error calculation intensity for file: " + str(dataset))

        # Get Vegetation Index
        vi = tools.vegetation_index(d_bands)
        
        if not vi is None:
            data_dict["d" + str(j)]["vi"] = tools.vegetation_index(d_bands)

        else:
            raise Exception("Error calculation vegetation index for file: " + str(dataset))


    #Test outputs
    import os
    gdalr.py2gdal(data_dict["d1"]["intensity"], str(os.path.splitext(output)[0]) + '.tif', data_dict["d1"]["dataset"].ds, driver='GTiff', nodata=0, dtype=None)
    #gdalr.py2gdal(data_dict["d1"]["vi"], os.path.join(os.getcwd(), "veg.tif"), data_dict["d1"]["dataset"].ds, driver='GTiff', nodata=0, dtype=None)
    #gdalr.py2gdal(data_dict["d1"]["normalised"], os.path.join(os.getcwd(), "nor.tif"), data_dict["d1"]["dataset"].ds, driver='GTiff', nodata=0, dtype=None)
    #print os.path.join(os.getcwd(),"int.tif")

    # Segmentation of newer dataset

    # Seed generation

    # Region growing



    # Zonal stats for rasters


    # Segments diference




    exit()