# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		gdal_import.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for import rasters to/from gdal

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================


import logging

from spatial.gdal_reader import GdalReader
from spatial.gdal2py import Gdal2Py


def gdal_import(gdal_src, load_data=True):
    """ Load a gdal file to system format
    :param gdal_src: source gdal dataset
    :param load_data: Boolean . True if wish to save the arrays in the memory.
    """

    logging.debug("Importing file  " + str(gdal_src))

    if src2ds(gdal_src):

        # Work directly in org
        return src2ds(gdal_src)

        # Work in with py-dict
        # return Gdal2Py(ds=src)

    else:
        logging.error('OGR dataset cannot be imported')


def src2ds(src):
    logging.debug("Importing file tiles " + str(src))

    if GdalReader().isvalid(src):
        return src

    else:
        try:
            GdalReader().isvalid(src.ds)
            return src.ds

        except:

            logging.exception(" Unknown source.")


def py2gdal(py_raster):
    """ Convert python format to gdal"""

    if GdalReader().isvalid(py_raster.ds):

        return py_raster.ds

    else:

        geotransform = (py_raster.extent[0], py_raster.xres, 0, py_raster.extent[3], 0, py_raster.yres)

        return GdalReader().array2ds(src_array=py_raster.array, output=py_raster.filename, geotransform=geotransform,
                                     projection=py_raster.projection, nodata=py_raster.nodata)


def sentinel_reader(s2_images_list, bands_order):
    logging.debug('Starting safe_extract_bands...')

    bands_files = []
    for band_number in bands_order:
        for band_file in s2_images_list:
            file_path = str(band_file).lower()
            if file_path.find('_b0' + str(band_number)) > 0 or file_path.find('_b' + str(band_number)) > 0:

                # Sentinel especial case for band 8
                if band_number == '8A' or int(band_number) == 8:
                    if band_number == '8A':
                        if file_path.find('_b8A') > 0:
                            bands_files.append(band_file)

                    elif int(band_number) == 8:
                        if file_path.find('_b08') > 0:
                            bands_files.append(band_file)

                else:
                    bands_files.append(band_file)

    if len(bands_files) != len(bands_order):
        logging.error('Band to be extracted do not match bands pattern' + str(bands_order))

    return bands_files
