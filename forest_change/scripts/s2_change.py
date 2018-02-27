# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		s2_chagne.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module manages the S2 data for change detection

# COPYRIGHT:	(C) 2018 Treemetrics all rights reserved.
# ==========================================================================================

import errno
import logging
import os
import shutil

from scripts import change_script
from spatial import s2reader
from toolbox import raster_tools

from core.bunch import Config


def sentinel2rgbn(s2_product_path, resolution, output='s2_rgbn'):

    if resolution == 10 or str(resolution).lower() == 'r10m':
        resolution = 'R10m'

    elif resolution == 20 or str(resolution).lower() == 'r20m':
        resolution = 'R20m'

    elif resolution == 60 or str(resolution).lower() == 'r60m':
        resolution = 'R60m'

    products_dict = s2reader.explore_data(s2_product_path)

    outputs = {}
    for s2_product in products_dict:
        s2_bands_files = products_dict[s2_product]

        red_band = s2_bands_files[resolution]['B04']
        green_band = s2_bands_files[resolution]['B02']
        blue_band = s2_bands_files[resolution]['B03']

        if resolution == 'R10m':
            nir_band = s2_bands_files[resolution]['B08']
        else:
            nir_band = s2_bands_files[resolution]['B8A']

        # s2_bands_newer = gdal_import.sentinel_reader(args.s2_product_dir_newer, bands_order)
        s2_bands = [red_band, green_band, blue_band, nir_band]

        output = os.path.join(output, '_' + str(s2_product))

        outputs[s2_product] = raster_tools.single_bands_to_multiband(s2_bands, output=output)

    return outputs


def main(args):
    # Config()['sparse'] = False

    # Set tempdir
    if 'tempdir' not in Config() or not os.path.isdir(Config()['tempdir']):
        if 's2_product_dir' in args and args.s2_product_dir:
            tempdir = os.path.join(os.path.abspath(args.s2_product_dir), 'temp')
            Config(overwrite=True)['tempdir'] = tempdir

            if not os.path.isdir(tempdir):
                try:
                    os.makedirs(tempdir)

                except OSError as e:
                    if not e.errno == errno.EEXIST:
                        raise Exception("Error creating temporary directory:" + str(tempdir))

        else:
            raise Exception("'s2_product_dir' has not been defined. Aborting ..")

    else:
        tempdir = Config()['tempdir']

    # Output dir
    if 'output_dir' in args and args.output_dir:
        output_dir = args.output_dir

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    elif 's2_product_dir' in args and args.s2_product_dir:
        output_dir = os.path.join(os.path.abspath(args.s2_product_dir), 'output')

    else:
        raise Exception("'s2_product_dir' has not been defined. Aborting ..")

    if not output_dir or not os.path.isdir(output_dir):
        raise Exception("Output directory cannot not be created in " + str(output_dir) + ". Aborting ...")

    # Get boundaries
    if 'bounds' in args and args.bounds and os.path.isfile(args.bounds):
        boundaries = args.bounds

    elif 'forest_area_path' in Config() and Config()['forest_area_path'] and os.path.isfile(Config()['forest_area_path']):
        boundaries = Config()['forest_area_path']

    else:
        raise Exception('Forest boundaries are not defined. Aborting.')

    # Get S2 Inputs
    logging.info('Importing datasets ...')

    if 's2_product_dir' not in args and args.s2_product_dir:
        raise Exception("'s2_product_dir' has not been defined. Aborting ..")

    products_dict = {}
    datetime_dict = {}
    for s2_product_file in os.listdir(args.s2_product_dir):
        s2_product_path = os.path.join(args.s2_product_dir, s2_product_file)

        # Unzip files if required
        filename, extension = os.path.splitext(os.path.normpath(s2_product_path))
        if extension in [".ZIP", ".zip"]:
            s2_product_path = s2reader.extract_all(os.path.join(args.s2_product_dir, s2_product_file),
                                                   dest_dir=tempdir)

        if s2_product_path.endswith(".SAFE"):
            with s2reader.open_safe(s2_product_path) as s2_product:
                # Get newer and older structure
                datetime_dict[s2_product.product_id] = s2_product.start_time
                products_dict[s2_product.product_id] = s2_product_path

    s2_bands_newer_product = products_dict[[k for k, v in datetime_dict.items() if v == max(datetime_dict.values())][0]]
    s2_bands_older_product = products_dict[[k for k, v in datetime_dict.items() if v == min(datetime_dict.values())][0]]

    # Change detection

    # Parameter space 60m Output
    resolution = 60
    output = os.path.join(output_dir, 'change_output')

    s2_bands_newer_rgbn = sentinel2rgbn(s2_bands_newer_product, resolution=resolution, output='s2_rgbn')
    s2_bands_older_rgbn = sentinel2rgbn(s2_bands_older_product, resolution=resolution, output='s2_rgbn')

    s2_bands_newer_rgbn = s2_bands_newer_rgbn[s2_bands_newer_rgbn.keys()[0]]
    s2_bands_older_rgbn = s2_bands_older_rgbn[s2_bands_older_rgbn.keys()[0]]

    output = change_script.main(s2_bands_newer_rgbn, s2_bands_older_rgbn, output=output,
                                threshold=args.threshold, boundary_path=boundaries,
                                tile_size=None, parameters=args.parameters)

    # Additional 10m output
    if 'additional_outputs' in args and args.additional_outputs:

        resolution = 10
        output = os.path.join(output_dir, 'additional_outputs', 'change_output')

        if not os.path.exists(os.path.dirname(output)):
            os.makedirs(os.path.dirname(output))

        s2_bands_newer_rgbn = sentinel2rgbn(s2_bands_newer_product, resolution=resolution, output='s2_rgbn')
        s2_bands_older_rgbn = sentinel2rgbn(s2_bands_older_product, resolution=resolution, output='s2_rgbn')

        s2_bands_newer_rgbn = s2_bands_newer_rgbn[s2_bands_newer_rgbn.keys()[0]]
        s2_bands_older_rgbn = s2_bands_older_rgbn[s2_bands_older_rgbn.keys()[0]]

        change_script.main(s2_bands_newer_rgbn, s2_bands_older_rgbn, output=output,
                           threshold=args.threshold, boundary_path=boundaries,
                           tile_size=1000, parameters=args.parameters, change_index=True)

    # Wipe temp files
    if not Config()['verbose'] == 'debug':
        if 'tempdir' in Config() and os.path.exists(Config()['tempdir']):
            shutil.rmtree(Config()['tempdir'])

    return output