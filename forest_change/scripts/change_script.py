# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		change_script.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Manages change detection for RGBN images

# COPYRIGHT:	(C) 2018 Treemetrics all rights reserved.
# ==========================================================================================


import logging
import os

from scripts import change_analysis
from spatial import gdal_import, ogr_import
from toolbox import raster_tools, image_tools

from spatial import raster_tiles


def main(dataset1, dataset2, output, threshold, parameters, boundary_path=None, tile_size=None, change_index=None):

    # Tiling data set
    if tile_size and tile_size > 0:
        dataset1_tiles = raster_tiles.gdal2tiles(src=dataset1, tile_size=tile_size)
        dataset2_tiles = raster_tiles.gdal2tiles(src=dataset2, tile_size=tile_size)

    else:
        dataset1_tiles = {'0': dataset1}
        dataset2_tiles = {'0': dataset2}

    # if Config()['verbose'] == 'debug':
    #     dataset1_tiles = {}
    #     dataset1_tiles.update(raster_tiles.gdal2tiles(src=dataset1, tile_size=tile_size, tile_id_y=2, tile_id_x=2))
    #
    #     dataset2_tiles = {}
    #     dataset2_tiles.update(raster_tiles.gdal2tiles(src=dataset2, tile_size=tile_size, tile_id_y=2, tile_id_x=2))

    # Get clip areas
    if boundary_path and os.path.exists(boundary_path):
        bounds = ogr_import.ogr_import(boundary_path)

        clipped_dataset1 = {}
        for tile_name, raster_tile in dataset1_tiles.iteritems():

            print 'tile: ' + str(tile_name)
            print 'tile1: ' + str(raster_tile)

            clipped_dataset1[tile_name] = raster_tools.poly_clip(raster=dataset1_tiles[tile_name], polygons=bounds,
                                                                 output=str(tile_name) + "_clipped")
        clipped_dataset2 = {}
        for tile_name, raster_tile in dataset2_tiles.iteritems():
            clipped_dataset2[tile_name] = raster_tools.poly_clip(raster=dataset2_tiles[tile_name], polygons=bounds,
                                                                 output=str(tile_name) + "_clipped")
    else:
        clipped_dataset1 = dataset1_tiles
        clipped_dataset2 = dataset2_tiles

    # Test number of tiles
    if len(clipped_dataset1) == len(clipped_dataset2):
        number_tiles = len(clipped_dataset1)

    else:
        logging.error("dataset 1 has not the same size as dataset 2")
        number_tiles = min(len(clipped_dataset1), len(clipped_dataset2))

    # Runs change detection script for each tile
    logging.info('Stating change detection ...')

    change_rasters = []
    for tile_id in xrange(number_tiles):
        change_rasters.append(change_analysis.main(d1=clipped_dataset1.items()[tile_id][1],
                                                   d2=clipped_dataset2.items()[tile_id][1], parameters=parameters))

    # Merge tiles
    change_raster = raster_tools.merge(src_list=change_rasters, outname='change', smooth_edges=False)

    # Get Change detection for all tiles merged
    # change_raster = image_tools.RasterTools().normalisation(change_raster)

    #threshold = float(threshold) / 100 * 225

    raster_stats = raster_tools.raster_stats(change_raster)

    # Get normalised values
    threshold_maximum = raster_stats['mode'] + (abs((raster_stats['max']-raster_stats['mode'])) * float(threshold)/100)
    threshold_minimum = raster_stats['mode'] - (abs((raster_stats['min']-raster_stats['mode'])) * float(threshold)/100)

    # Remove lower than threshold (positive)
    reclassify_raster = raster_tools.reclassify(change_raster, new_value='nan',
                                                old_value_min=threshold_minimum,
                                                old_value_max=threshold_maximum, output=None)

    # Remove lower than threshold (negative)
    reclassify_raster = raster_tools.reclassify(reclassify_raster, new_value=10,
                                                old_value_min=threshold_maximum, old_value_max=None, output=None)

    reclassify_raster = raster_tools.reclassify(reclassify_raster, new_value=20,
                                                old_value_min=None, old_value_max=threshold_minimum, output=None)

    gdal_import.raster2file(reclassify_raster, file_path=output)

    # Check output
    if not os.path.exists(output):
        raise Exception('Error creating change detection output')

    if change_index:
        output2 = os.path.splitext(output)[0] + 'change_index' + os.path.splitext(output)[1]
        gdal_import.raster2file(change_raster, file_path=output2)

        output = [output, output2]

    logging.info('Change detection successfully completed.')

    return output
