# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		forest_change.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module manages the analysis and the outputs.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module manages the analysis and outputs"""

import os
import shutil
import errno
import logging

import config
import args_reader
import change_script
from bunch import Config
import gdal_reader as gdalr

# Check configuration
config.check_config()

# Read args
args = args_reader.main()

# Debugging
Config()['debug'] = args.DEBUG

# Set tempdir
if 'tempdir' in args and args.tempdir:
    tempdir = args.tempdir

elif 'new_rgbnir_file' in args and args.new_rgbnir_file:
    tempdir = os.path.join(os.path.dirname(args.new_rgbnir_file), 'temp')

elif 'new_rgbnir_bands' in args and args.new_rgbnir_bands:
    tempdir = os.path.join(os.path.dirname(args.new_rgbnir_bands[0]), 'temp')

elif 's2_product_dir_newer' in args and args.s2_product_dir_newer:
    tempdir = os.path.join(os.path.dirname(args.s2_product_dir_newer[0]), 'temp')

else:
    raise Exception("Temporary directory cannot not been defined. Aborting ..")

if not os.path.exists(tempdir):
    try:
        os.makedirs(tempdir)

    except OSError as e:
        if e.errno != errno.EEXIST:
            raise Exception("Error creating temporary directory:" + str(tempdir))

Config()['tempdir'] = tempdir
tempdir = os.path.join(os.path.dirname(tempdir), 'temp')

# Get Inputs
logging.info('Importing datasets ...')

if 'new_rgbnir_file' in args and args.new_rgbnir_file:
    dataset1 = gdalr.gdal_import(args.new_rgbnir_file)
    dataset2 = gdalr.gdal_import(args.old_rgbnir_file)

elif 'new_rgbnir_bands' in args and args.new_rgbnir_bands:

    # Conver to dataset
    dataset1 = gdalr.gdal_import(gdalr.bands_to_single_ds(args.new_rgbnir_bands))
    dataset2 = gdalr.gdal_import(gdalr.bands_to_single_ds(args.old_rgbnir_bands))


elif 's2_product_dir_newer' in args and args.s2_product_dir_newer:

    raise Exception('here')

    for file_path in args.s2_product_dir_newer:
        file_name = str(os.path.splitext(os.path.basename(file_path))[0]).lower()

        start = file_name.find('_b')
        band_number = file_name[start+2:start+4]



    exit()

else:

    raise Exception("Error getting inputs Aborting ..")

# Runs script
logging.info('Stating change detection ...')
change_raster = change_script.main(d1=dataset1, d2=dataset2, output=args.output, settings=args.parameters)

# Create outputs
logging.info('Creating output file ...')
change_raster_file = gdalr.py2gdal(change_raster, file_path=args.output)

# Wipe temp files
if not Config()['debug']:
    if 'tempdir' in Config() and os.path.exists(Config()['tempdir']):
        shutil.rmtree(Config()['tempdir'])

# Check output
if not os.path.exists(change_raster_file):
    raise Exception('Error creating change detection output')

logging.info('Change detection successfully completed.')
logging.debug(str(change_raster_file))
