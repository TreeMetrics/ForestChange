# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		forest_change.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module manages the analysis and the outputs.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module manages the analysis and outputs"""

import errno
import logging
import os
import shutil

from core import args_reader
from core.bunch import Config
from scripts import change_script
from spatial import raster_tiles, gdal_import, ogr_import
from toolbox import raster_tools, image_tools

# Set config and Read args
args = args_reader.main()

# Config()['sparse'] = False

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
        if not e.errno == errno.EEXIST:
            raise Exception("Error creating temporary directory:" + str(tempdir))

Config()['tempdir'] = tempdir
tempdir = os.path.join(os.path.dirname(tempdir), 'temp')

# Output dir
output = args.output
output_dir = os.path.dirname(args.output)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Get Inputs
logging.info('Importing datasets ...')

if 'new_rgbnir_file' in args and args.new_rgbnir_file:
    dataset1 = gdal_import.gdal_import(args.new_rgbnir_file)
    dataset2 = gdal_import.gdal_import(args.old_rgbnir_file)


elif 's2_product_dir_newer' in args and args.s2_product_dir_newer:
    # Rearrange bands
    logging.debug('Starting s2_product_dir_newer...')
    bands_order = [args.red_band, args.green_band, args.blue_band, args.nir_band]

    s2_bands_newer = gdal_import.sentinel_reader(args.s2_product_dir_newer, bands_order)
    dataset1 = raster_tools.single_bands_to_multiband(s2_bands_newer, output='dataset1')

    s2_bands_older = gdal_import.sentinel_reader(args.s2_product_dir_older, bands_order)
    dataset2 = raster_tools.single_bands_to_multiband(s2_bands_older, output='dataset2')

else:
    logging.error('Error reading input datsets')
    raise Exception('Error reading input datsets')


# Tiling datasets for performance

# dataset1_tiles = raster_tiles.gdal2tiles(src=dataset1, tile_size=tile_size)
tile_size = args.tile_size
# dataset1_tiles = {}
# dataset1_tiles.update(raster_tiles.gdal2tiles(src=dataset1, tile_size=tile_size, tile_id_y=3, tile_id_x=3))
# dataset1_tiles.update(raster_tiles.gdal2tiles(src=dataset1, tile_size=tile_size, tile_id_y=2, tile_id_x=3))

dataset2_tiles = raster_tiles.gdal2tiles(src=dataset2, tile_size=tile_size)
# dataset2_tiles = {}
# dataset2_tiles.update(raster_tiles.gdal2tiles(src=dataset2, tile_size=tile_size, tile_id_y=3, tile_id_x=3))
# dataset2_tiles.update(raster_tiles.gdal2tiles(src=dataset2, tile_size=tile_size, tile_id_y=2, tile_id_x=3))

# Get forest areas
if args.bounds and os.path.exists(args.bounds):
    bounds = ogr_import.ogr_import(args.bounds)

    clippled_dataset1 = {}
    for tile_name, raster_tile in dataset1_tiles.iteritems():
        clippled_dataset1[tile_name] = raster_tools.poly_clip(raster=dataset1_tiles[tile_name], polygons=bounds,
                                                              output=str(tile_name) + "_clipped")
    clippled_dataset2 = {}
    for tile_name, raster_tile in dataset2_tiles.iteritems():
        clippled_dataset2[tile_name] = raster_tools.poly_clip(raster=dataset2_tiles[tile_name], polygons=bounds,
                                                              output=str(tile_name) + "_clipped")
else:
    clippled_dataset1 = dataset1_tiles
    clippled_dataset2 = dataset2_tiles

# Test number of tiles
if not len(clippled_dataset1) == len(clippled_dataset2):
    number_tiles = len(clippled_dataset1)

else:
    logging.error("dataset 1 has not the same size as dataset 2")
    number_tiles = min(len(clippled_dataset1), len(clippled_dataset2))

# Runs change detection script for each tile
logging.info('Stating change detection ...')

change_rasters = []
for tile_id in xrange(number_tiles):
    change_rasters.append(change_script.main(d1=clippled_dataset1.items()[tile_id][1],
                                             d2=clippled_dataset2.items()[tile_id][1], settings=args.parameters))

# Merge tiles
change_raster = raster_tools.merge(src_list=change_rasters, outname='change', smooth_edges=False)

# Get Change detection for all tiles merged
change_raster = image_tools.RasterTools().normalisation(change_raster)

threshold = float(args.threshold)/100 * 225

reclassify_raster = raster_tools.reclassify(change_raster, new_value='nan',
                                            old_value_min=None, old_value_max=-threshold, output=None)

reclassify_raster = raster_tools.reclassify(reclassify_raster, new_value='nan',
                                            old_value_min=threshold, old_value_max=None, output=None)

reclassify_raster = raster_tools.reclassify(reclassify_raster, new_value=1,
                                            old_value_min=-threshold, old_value_max=threshold, output=None)

gdal_import.raster2file(reclassify_raster, file_path=output)

output2 = os.path.splitext(output)[0] + 'raw_change' + os.path.splitext(output)[1]
gdal_import.raster2file(change_raster, file_path=output2)

# Check output
if not os.path.exists(output):
    raise Exception('Error creating change detection output')

# Wipe temp files
if not Config()['verbose'] == 'debug':
    if 'tempdir' in Config() and os.path.exists(Config()['tempdir']):
        shutil.rmtree(Config()['tempdir'])

logging.info('Change detection successfully completed.')

