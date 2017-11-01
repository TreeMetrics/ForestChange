# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		test.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module is a test.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module is a test"""

import numpy as np
import gdal_reader as gdalr

def main(d1, d2, settings):

    print d1
    print d2
    print settings

    d1 = gdalr.file_import(d1)
    d2 = gdalr.file_import(d2)

    # 'type', 'filename', 'projection', 'xsize', 'ysize', 'yres', 'xres', 'extent', 'bands',
    # 'band_type', 'nodata', 'ds', 'array'

    print d1.array
    print d2.array


    exit()