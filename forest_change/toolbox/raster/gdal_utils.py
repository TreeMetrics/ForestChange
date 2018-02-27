# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		gdal_utils.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for raster spatial analysis

# COPYRIGHT:	(C) 2018 Treemetrics all rights reserved.
# ==========================================================================================
""" This Basic tools for raster spatial analysis """


# Import modules
try:
    from PIL import Image, ImageDraw

except ImportError:
    import Image
    import ImageDraw

import logging
import math
import numpy as np

from spatial import gdal_import, ogr_import
from spatial import gdal_reader as gdalr
from spatial.gdal_reader import GdalReader
from toolbox.vector import ogr_utils

from spatial import ogr_reader as ogrr

try:
    from osgeo import gdal, ogr, gdal_array
    from osgeo import osr
    from osgeo import ogr

except ImportError:
    import gdal
    import osr
    import ogr

# from gdal import *
# from gdalconst import *


def single_bands_to_multiband(gdal_bands_list, output=None):
    """ Convert several gdal single file to a single gdal datasource"""

    # Get mask
    # src_ds = gdal.OpenShared(gdal_bands_list[0])
    src_ds = GdalReader().gdal2ds(gdal_bands_list[0])
    # src_ds.SetMetadataItem('FilePath', gdal_bands_list[0])

    # Get output
    if not output:
        output = 'image_multiband'

    # Create new ds
    # tmp_ds = gdal.GetDriverByName('MEM').CreateCopy('', src_ds, 0)
    out_ds = gdalr.GdalReader().create_ds(output, src_ds.RasterXSize, src_ds.RasterYSize, len(gdal_bands_list),
                                          src_ds.GetRasterBand(1).DataType)

    out_ds.SetProjection(src_ds.GetProjection())
    out_ds.SetGeoTransform(src_ds.GetGeoTransform())

    i = 0
    for band_dataset in gdal_bands_list:

        i = i + 1
        band_ds = GdalReader().gdal2ds(band_dataset)
        # mask_ds = gdal.OpenShared(band_dataset)
        array_i = band_ds.GetRasterBand(1).ReadAsArray()

        out_ds.GetRasterBand(i).WriteArray(array_i)
        band_ds = None
        del array_i

    if GdalReader().isvalid(out_ds):
        return out_ds

        # file_path = out_ds.GetMetadataItem('FilePath')
        # if driver.ShortName == 'MEM':
        #     return out_ds
        #
        # elif os.path.exists(file_path):
        #     return file_path
        #
        # else:
        #     logging.warning("Failed to create GDAL file. " + str(file_path))
        #     return


def merge(src_ds_list, outname, smooth_edges=False):
    # First layer metadata
    src_ds = GdalReader().gdal2ds(src_ds_list[0])
    src_ds_list = [GdalReader().gdal2ds(r) for r in src_ds_list]
    geotransform = src_ds.GetGeoTransform()
    xres = geotransform[1]
    yres = geotransform[5]
    projection = src_ds.GetProjection()
    nodata = src_ds.GetRasterBand(1).GetNoDataValue()

    # Get common extent
    xmin, xmax, ymin, ymax = GdalReader().get_extent(src_ds)

    bands = src_ds.RasterCount

    for src_i in src_ds_list:

        xmin_i, xmax_i, ymin_i, ymax_i = GdalReader().get_extent(src_i)
        xmax = max(xmax, xmax_i)
        xmin = min(xmin, xmin_i)
        ymax = max(ymax, ymax_i)
        ymin = min(ymin, ymin_i)
        bands = max(bands, src_i.RasterCount)

    # Aligne Pixels
    xmin = math.floor(xmin / xres) * xres
    xmax = math.ceil(xmax / xres) * xres
    ymin = math.floor(ymin / -yres) * -yres
    ymax = math.ceil(ymax / -yres) * -yres

    # Create output if it does not already exist.
    geotransform = [xmin, xres, 0, ymax, 0, yres]
    xsize = int(math.ceil((xmax - xmin) / xres))
    ysize = int(math.ceil((ymin - ymax) / yres))

    # Copy data from source files into output file 1.
    out_array = np.empty((ysize, xsize))
    out_array[:] = np.nan

    borders = []
    for src_i in src_ds_list:
        for band in xrange(1, src_ds.RasterCount + 1):

            geotransform_i = src_i.GetGeoTransform()
            if not int(xres) == int(geotransform_i[1]) or not int(yres) == int(geotransform_i[5]):
                logging.error('Merge cannot be performed because the layer resolution are different: ' +
                              str(xres) + ',' + str(yres) + ' vs. ' + str(geotransform_i[1]) + ','
                              + str(geotransform_i[5]))

                continue

            xmin_i, xmax_i, ymin_i, ymax_i = GdalReader().get_extent(src_i)
            xoff = math.ceil((xmin_i - xmin) / xres)
            yoff = math.ceil((ymax_i - ymax) / yres)

            x_size_i = src_i.RasterXSize
            y_size_i = src_i.RasterYSize
            array_i = GdalReader().ds2array(src_i)

            out_array[yoff:yoff + y_size_i, xoff:xoff + x_size_i] = array_i

            #slice_i = out_array[yoff:yoff + y_size_i, xoff:xoff + x_size_i]
            #out_array[yoff:yoff + y_size_i, xoff:xoff + x_size_i] = np.where(
            #    np.ma.getmask(np.ma.masked_invalid(array_i[band - 1])), slice_i, array_i[band - 1])

            # Edges smoothing
            if smooth_edges:
                mask = np.where(np.ma.getmask(np.ma.masked_invalid(array_i[band - 1])), np.nan, 1)

                if smooth_edges:
                    borders_i = [([i + yoff, j + xoff]
                                  if 0 < [mask[i - 1, j], mask[i + 1, j], mask[i, j - 1], mask[i, j + 1]].count(1) < 4
                                  else None)
                                 if (1 <= i < mask.shape[0] - 1) and (1 <= j < mask.shape[1] - 1) else None
                                 # ([i+yoff, j+xoff] if mask[i, j] == 1 else None)
                                 for i, j in np.ndindex(mask.shape)]
                    borders = borders + borders_i

    # Edges smoothing
    if smooth_edges:
        for k in borders:
            if k:
                out_array[k[0], k[1]] = np.nanmean(out_array[k[0] - 1:k[0] + 1, k[1] - 1:k[1] + 1])

    return GdalReader().array2ds(src_array=out_array, output=outname, projection=projection, geotransform=geotransform,
                                 nodata=nodata)


def poly_clip(raster, polygons, outuput):
    """Clip raster with polygons"""

    src_ds = gdal_import.src2ds(raster)
    poly_ds = ogr_import.src2ogr(polygons)

    # 1.- Reproject vector geometry to same projection as raster
    projection = src_ds.GetProjection()
    poly_reprojected = ogr_utils.reproject(poly_ds, wtk_projection=projection, outname='polygons_reprojected')

    poly_ds = ogr_import.src2ogr(poly_reprojected)
    poly_lyr = poly_ds.GetLayer()

    # Bound box (debbuging code)
    # geom_type = poly_lyr.GetGeomType()
    # outDataSource = ogrr.create_layer('bound_box', geom_type=geom_type, wkt_proj=projection, file_path=None)
    # outLayer = outDataSource.GetLfpayer()
    # outLayerDefn = outLayer.GetLayerDefn()
    # outFeature = ogr.Feature(outLayerDefn)
    # outFeature.SetGeometry(geom)
    # outLayer.CreateFeature(outFeature)
    # outFeature = None
    # outDataSource = None

    # 2.- Filter and extract features
    # Get Raster Extent
    nodata = src_ds.GetRasterBand(1).GetNoDataValue()

    r_min_x, r_max_x, r_min_y, r_max_y = GdalReader().get_extent(src_ds)

    wkt = 'POLYGON((' + ','.join([' '.join([str(r_min_x), str(r_max_y)]), ' '.join([str(r_min_x), str(r_min_y)]),
                                  ' '.join([str(r_max_x), str(r_min_y)]), ' '.join([str(r_max_x), str(r_max_y)]),
                                  ' '.join([str(r_min_x), str(r_max_y)])]) + '))'

    geom = ogr.CreateGeometryFromWkt(wkt)

    poly_lyr.SetSpatialFilter(geom)
    mem_driver = ogr.GetDriverByName('MEMORY')
    filtered_poly_ds = mem_driver.CreateDataSource('filered_polygons')

    # Open the memory datasource with write access and copy content
    mem_driver = ogr.GetDriverByName('MEMORY')
    mem_driver.Open('filered_polygons', 1)
    filtered_poly_ds.CopyLayer(poly_lyr, 'filered_polygons', ['OVERWRITE=YES'])

    poly_lyr.SetSpatialFilter(None)

    # Intersect geometries with boundary box
    geom_type = poly_lyr.GetGeomType()
    clipped_poly_ds = ogrr.create_layer('clipped_polygons', geom_type=geom_type, wkt_proj=projection, file_path=None)

    clipped_poly_lyr = clipped_poly_ds.GetLayer()
    filtered_poly_lyr = filtered_poly_ds.GetLayer()

    clipped_lyr_defn = clipped_poly_lyr.GetLayerDefn()
    infeature = filtered_poly_lyr.GetNextFeature()
    while infeature:
        feat_geom = infeature.GetGeometryRef()
        intersection_geom = feat_geom.Intersection(geom)

        out_feature = ogr.Feature(clipped_lyr_defn)
        out_feature.SetGeometry(intersection_geom)
        clipped_poly_lyr.CreateFeature(out_feature)

        out_feature = None
        infeature = filtered_poly_lyr.GetNextFeature()

    filtered_poly_lyr.ResetReading()
    filtered_poly_lyr = None

    # Bound box (debbuging code)
    # geom_type = poly_lyr.GetGeomType()
    # filtered_poly_ds = ogrr.create_layer('filered_polygons', geom_type=geom_type, wkt_proj=projection,
    #                                     file_path=None)

    # Clip raster to layer extent
    lyr = clipped_poly_lyr
    extent = lyr.GetExtent()

    # Convert the _vector extent to image pixel coordinates
    geo_trans = src_ds.GetGeoTransform()
    # projection = rds.GetProjection()
    ul_x, ul_y = GdalReader().world2pixel(geo_trans, extent[0], extent[3])
    lr_x, lr_y = GdalReader().world2pixel(geo_trans, extent[1], extent[2])

    # Create a new geomatrix for the _raster
    geo_trans = list(geo_trans)
    geo_trans[0] = extent[0]
    geo_trans[3] = extent[3]

    # Get the new array to layer extent
    rarray = gdal_array.DatasetReadAsArray(src_ds)

    if len(rarray.shape) == 3:
        clip = rarray[:, ul_y:lr_y, ul_x:lr_x]

    elif len(rarray.shape) == 2:
        clip = rarray[ul_y:lr_y, ul_x:lr_x]

    else:
        return logging.error('Error in array shape.')

    new_array = clip_raster_array(vds=filtered_poly_ds, raster_array=clip, geotransform=geo_trans, nodata=nodata)

    return GdalReader().array2ds(src_array=np.array(new_array), output=outuput, geotransform=geo_trans,
                                 projection=projection, nodata=nodata)


def clip_raster_array(vds, raster_array, geotransform, nodata=0):

    if len(raster_array.shape) == 3:

        nbands = raster_array.shape[0]

    else:
        nbands = 1

    new_array = []
    layer = vds.GetLayer(0)
    layer.ResetReading()

    for band in xrange(nbands):

        if len(raster_array.shape) == 3:
            raster_array_i = raster_array[band]

        else:
            raster_array_i = raster_array

        ysize, xsize = raster_array_i.shape

        # Create data mask
        rasterpoly = Image.new("L", (xsize, ysize), 1)
        raster_im = ImageDraw.Draw(rasterpoly)
        inner_ring_im = ImageDraw.Draw(rasterpoly)

        # for fid in xrange(layer.GetFeatureCount()):
        #     feature = layer.GetFeature(fid)
        for feature in layer:
            geoms = feature.GetGeometryRef()

            if geoms.GetGeometryName().lower() == "multipolygon":
                for geom in geoms:

                    pts = geom.GetGeometryRef(0)
                    points = [(pts.GetX(p), pts.GetY(p)) for p in range(pts.GetPointCount())]
                    pixels = [GdalReader().world2pixel(geotransform, p[0], p[1]) for p in points]
                    raster_im.polygon(pixels, 0)

                    if geom.GetGeometryCount() > 1:
                        for i in xrange(1, geom.GetGeometryCount()):
                            pts = geom.GetGeometryRef(i)
                            points1 = [(pts.GetX(p), pts.GetY(p)) for p in range(pts.GetPointCount())]
                            pixels1 = [GdalReader().world2pixel(geotransform, p[0], p[1]) for p in points1]

                            inner_ring_im.polygon(pixels1, 1)

            elif geoms.GetGeometryName().lower() == "polygon":
                pts = geoms.GetGeometryRef(0)
                points = [(pts.GetX(p), pts.GetY(p)) for p in range(pts.GetPointCount())]
                pixels = [GdalReader().world2pixel(geotransform, p[0], p[1]) for p in points]

                raster_im.polygon(pixels, 0)

            del feature

        layer.ResetReading()

        # Image to array
        try:
            # old version
            mask = np.fromstring(rasterpoly.tostring(), 'b')

        except:
            # new version
            mask = np.fromstring(rasterpoly.tobytes(), 'b')

        mask.shape = rasterpoly.im.size[1], rasterpoly.im.size[0]

        # Clip the image using the mask (Note that np.uint8 does not allow nan values
        new_array.append(np.choose(mask, (raster_array_i, nodata)).astype(np.float))

    return np.array(new_array)
