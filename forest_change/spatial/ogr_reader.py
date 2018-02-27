# /usr/bin/env python

# PRODUCT: EO4Atlantic
# MODULE: gdal_reader.py
# AUTHOR: J. Alejandro Poveda
# DESCRIPTION: 	Basic tools for read and manage raster using ogr.

# COPYRIGHT:	(C) 2018 Treemetrics. All rights reserved.
# ==========================================================================================

import logging
# Import generic python modules
import os
from collections import namedtuple

from core import miscellaneous

from core.bunch import Config

try:
    from osgeo import gdal
    from osgeo import osr
    from osgeo import ogr

except ImportError:
    import gdal
    import osr
    import ogr


#
# class OgrImport(object):
#
#     def __init__(self, overwrite=False):
#
#         basedir = Config()['tempdir']
#         self.tempdir = os.path.join(basedir, 'ogr')
#         if not os.path.exists(self.tempdir):
#             os.makedirs(self.tempdir)
#
#         self.overwrite = overwrite
#         # self.vector_db = DataBase(rtype='_vector', workspace=self.workspace, overwrite=None)
#
#         self.verbosity = Config()['verbose']
#         if self.verbosity == 'debug':  # Debug mode
#             #self.driver = ogr.GetDriverByName('GeoJSON')
#             self.driver = ogr.GetDriverByName('ESRI Shapefile')
#
#         else:
#             self.driver = ogr.GetDriverByName('Memory')
#
#
#     def name_to_output(name=None):


# def name_to_output(name):
#
#     tempdir = Config()['tempdir']
#     verbose_level = Config()['debug']
#
#     if not miscellaneous.os.path.exists(tempdir):
#         miscellaneous.os.makedirs(tempdir)
#
#     if file_path is None:
#         name = miscellaneous.os.path.splitext(file_path)[1].lower() == '.shp':
#
#
#         if verbose_level == 'debug':
#             return ogr.GetDriverByName('ESRI Shapefile')
#
#         else:
#             return ogr.GetDriverByName('Memory')
#
#     else:
#         if miscellaneous.os.path.splitext(file_path)[1].lower() == '.shp':
#             return ogr.GetDriverByName('ESRI Shapefile')
#
#         else:
#             logging.warning("Failed to load driver for file. " + str(file_path))
#             return


def geom2name(code):
    code2name = {'0': 'Unknown', '1': 'Point', '2': 'LineString', '3': 'Polygon', '4': 'MultiPoint',
                 '5': 'MultiLineString', '6': 'MultiPolygon', '7': 'GeometryCollection', '100': 'None',
                 '101': 'LinearRing', '0x80000001': 'Point25D', '0x80000002': 'LineString25D',
                 '0x80000003': 'Polygon25D', '0x80000004': 'MultiPoint25D', '0x80000005': 'MultiLineString25D',
                 '0x80000006': 'MultiPolygon25D', '0x80000007': 'GeometryCollection25D'}

    return code2name[str(code)]


def ogr2ds(source, check_geom=False):
    """ Validate layer.
    empty: when it is expected that the layer is empty
    """

    logging.debug('Validating vector...')

    # Check None values
    if not source:
        logging.error("OGR datasource not defined.")
        return

    # Check if file
    try:

        try:
            ds = ogr.Open(source)  # Depreciated from gdal > 2.0.0

        except:
            ds = gdal.OpenEx(source)

    except:
        ds = source

    # Check data source
    try:
        layer = ds.GetLayer()

    except:
        logging.error("OGR datasource is not valid.")
        return

    # Check geometry

    # for i in xrange(0, layer.GetFeatureCount()):
    #     feature = layer.GetFeature(i)

    for feature in layer:
        geom = feature.GetGeometryRef()

        if check_geom and not geom.IsValid():
            logging.warning('Geometry is not valid for feature ID:' + str(feature.GetFID()))
            return

    layer.ResetReading()

    return ds


def get_fields(ds):
    """Ger ogr field names"""

    # Get layer
    layer = ds.GetLayer(0)
    # feature.GetFieldCount()
    layer_defn = layer.GetLayerDefn()
    field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]

    return field_names


def get_extent(ds):
    layer = ds.GetLayer(0)
    extent = layer.GetExtent()

    extent_tuple = namedtuple('extent', ['xmin', 'xmax', 'ymin', 'ymax'])

    return extent_tuple(xmin=extent[0], xmax=extent[1], ymin=extent[2], ymax=extent[3])


def create_layer(name, geom_type, wkt_proj, file_path=None):

    verbose_level = Config()['verbose']
    tempdir = Config()['tempdir']

    geom_types = {'collection': ogr.wkbGeometryCollection,
                  'point': ogr.wkbPoint,
                  'line': ogr.wkbLineString,
                  'polygon': ogr.wkbPolygon,
                  'multipoint': ogr.wkbMultiPoint,
                  'multiline': ogr.wkbMultiLineString,
                  'multipolygon': ogr.wkbMultiPolygon}

    if str(geom_type).lower() in geom_types:
        geom_type = geom_types[str(geom_type).lower()]

    elif str(geom2name(geom_type)).lower() in geom_types:
        geom_type = geom_types[str(geom2name(geom_type)).lower()]

    else:
        logging.error('Error creating layer. OGR Geometry type unknown. ' + str(geom_type))
        return

    if (file_path and os.path.exists(file_path)) or verbose_level == 'debug':

        if not file_path:
            file_path = miscellaneous.new_unique_file(os.path.join(tempdir, name + '.shp'))

        out_driver = ogr.GetDriverByName("ESRI Shapefile")
        out_ds = out_driver.CreateDataSource(file_path)

    else:
        out_driver = ogr.GetDriverByName('MEMORY')
        out_ds = out_driver.CreateDataSource(name)
        # out_driver.Open(name, 1)

    projection = osr.SpatialReference()
    projection.ImportFromWkt(wkt_proj)

    out_ds.CreateLayer(name, projection, geom_type=geom_type)

    return out_ds
