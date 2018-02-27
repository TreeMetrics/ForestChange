# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		raster_tiles.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for raster tiling and big raster support

# COPYRIGHT:	(C) 2018 Treemetrics all rights reserved.
# ==========================================================================================

# Import modules
import numpy as np

from spatial.gdal_reader import GdalReader

from spatial import gdal_import

try:
    from osgeo import gdal
    from osgeo import osr
    from osgeo import ogr

except ImportError:
    import gdal
    import osr
    import ogr

from osgeo import gdal_array


def get_number_tiles(src, tile_size=500):
    # Get number of tiles

    src_ds = gdal_import.src2ds(src)
    xsize = src_ds.RasterXSize
    ysize = src_ds.RasterYSize

    if np.round(xsize / tile_size, 0) - (xsize / tile_size) == 0.0:
        nxtiles = np.round(xsize / tile_size, 0)

    else:
        nxtiles = np.round(xsize / tile_size, 0) + 1

    if np.round(ysize / tile_size, 0) - (ysize / tile_size) == 0.0:
        nytiles = np.round(ysize / tile_size, 0)

    else:
        nytiles = np.round(ysize / tile_size, 0) + 1

    return nxtiles, nytiles


def gdal2tiles(src, tile_size=500, tile_id_y=None, tile_id_x=None):
    """ Load a gdal file to local python instance
    
    :param src: source gdal dataset
    :param tile_size: Tile size
    :param tile_id_y: Single tile ID for Y
    :param tile_id_x: Single tile ID for X
    """

    src_ds = gdal_import.src2ds(src)
    xsize = src_ds.RasterXSize
    ysize = src_ds.RasterYSize
    bands = src_ds.RasterCount
    nxtiles, nytiles = get_number_tiles(src_ds)

    # Read raster as arrays
    dtype = [key for key, value in GdalReader().np2gdal.iteritems() if value == src_ds.GetRasterBand(1).DataType][0]

    if tile_id_x and str(tile_id_x).isdigit() and tile_id_y and str(tile_id_y).isdigit():
        x_tile_range = [tile_id_x]
        y_tile_range = [tile_id_y]

    else:
        x_tile_range = range(nxtiles + 1)
        y_tile_range = range(nytiles + 1)

    tiles = {}
    for xtile in x_tile_range:
        for ytile in y_tile_range:

            # DatasetReadAsArray(ds, xoff=0, yoff=0, win_xsize=None, win_ysize=None)

            if (tile_size * xtile + tile_size) < xsize and (tile_size * ytile + tile_size) < ysize:

                # arr_i = np.array(gdal_array.DatasetReadAsArray(src_ds, xoff=tile_size * xtile, yoff=tile_size * ytile,
                # win_xsize=tile_size, win_ysize=tile_size)).astype(dtype)

                arr_i = np.array(gdal_array.DatasetReadAsArray(src_ds, tile_size * xtile, tile_size * ytile,
                                                               tile_size, tile_size)).astype(dtype)

            else:

                win_xsize = min(tile_size, xsize - tile_size * xtile)
                win_ysize = min(tile_size, ysize - tile_size * ytile)

                if win_xsize < 0 or win_ysize < 0:
                    # Not square shape
                    continue

                # arr_src = np.array(gdal_array.DatasetReadAsArray(src_ds, xoff=tile_size * xtile,
                # yoff=tile_size * ytile, win_xsize=win_xsize, win_ysize=win_ysize)).astype(dtype)
                arr_src = np.array(gdal_array.DatasetReadAsArray(src_ds, tile_size * xtile, tile_size * ytile,
                                                                 win_xsize, win_ysize)).astype(dtype)

                arr_i = np.zeros((bands, win_ysize, win_xsize), dtype=dtype)
                arr_i[:, 0:arr_src.shape[1], 0:arr_src.shape[2]] = arr_src

            # Create raster
            # Geotransform
            geotransform = src_ds.GetGeoTransform()
            top_left_x = geotransform[0] + geotransform[1] * tile_size * xtile + geotransform[2] * tile_size * ytile
            top_left_y = geotransform[3] + geotransform[5] * tile_size * ytile + geotransform[4] * tile_size * xtile

            new_geotransform = [top_left_x, geotransform[1], geotransform[2],
                                top_left_y, geotransform[4], geotransform[5]]

            projection = src_ds.GetProjection()
            nodata = src_ds.GetRasterBand(1).GetNoDataValue()
            name = src_ds.GetMetadataItem('FilePath')

            tiles[str(xtile) + '_' + str(ytile)] = GdalReader().array2ds(arr_i,
                                                                         name + '_' + str(xtile) + '_' + str(ytile),
                                                                         geotransform=new_geotransform,
                                                                         projection=projection)

    return tiles
