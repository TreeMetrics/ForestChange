# /usr/bin/env python

# PRODUCT: EO4Atlantic
# MODULE: gdal2py.py
# AUTHOR: J. Alejandro Poveda
# DESCRIPTION: 	Object class to store gdal dataset attributes

# COPYRIGHT:	(C) 2017 Treemetrics. All rights reserved.
# ==========================================================================================

"""This module contains generic functions for _vector reading."""

import os
from collections import namedtuple
import ogr_reader as ogrr
# from ogr_reader import get_fields, geom2name, get_extent


class Ogr2Py(object):
    """A class holding information about a ogr feature"""

    __slots__ = ('type', 'ds', 'file', 'name', 'projection',
                 'geom_type', 'geom_name', 'nfeatures', 'fields', 'extent', 'features')

    # Prevents to create dictionaries (low memory).

    def __init__(self, ds, import_data=True):

        # if not isvalid(ds):
        #     return

        fields = ogrr.get_fields(ds)
        layer = ds.GetLayer(0)
        features = []

        if not 'fid' and 'FID' in fields:
            feature_def = namedtuple('features', ['fid', 'geom'] + fields)

        else:
            feature_def = namedtuple('features', ['geom'] + fields)

        if import_data:
            for feature in layer:

                if not 'fid' and 'FID' in fields:
                    features.append(feature_def._make([feature.GetFID(), feature.GetGeometryRef().ExportToWkt()] +
                                                      [feature.GetField(field) for field in fields]))

                else:
                    features.append(feature_def._make([feature.GetGeometryRef().ExportToWkt()] +
                                                      [feature.GetField(field) for field in fields]))

            layer.ResetReading()

        self.type = 'ogr'
        self.ds = ds

        try:
            self.file = ds.GetDescription()

        except:
            self.file = ds.GetName()  # Depreciated

        self.name = os.path.splitext(os.path.basename(self.file))[0]
        self.projection = layer.GetSpatialRef().ExportToWkt()
        self.geom_type = layer.GetGeomType()
        self.geom_name = ogrr.geom2name(self.geom_type)
        self.nfeatures = layer.GetFeatureCount()
        self.fields = fields
        self.extent = ogrr.get_extent(ds)
        self.features = features