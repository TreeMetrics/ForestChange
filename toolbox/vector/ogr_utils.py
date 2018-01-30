# /usr/bin/env python

# PRODUCT: EO4Atlantic
# MODULE: ogr_utils.py
# AUTHOR: J. Alejandro Poveda
# DESCRIPTION: 	Basic tools for vector layers.

# COPYRIGHT:	(C) 2017 Treemetrics. All rights reserved.
# ==========================================================================================

from spatial import ogr_reader, ogr_import

try:
    from osgeo import gdal
    from osgeo import osr
    from osgeo import ogr

except ImportError:
    import gdal
    import osr
    import ogr


def reproject(vector, wtk_projection, outname):

    ds = ogr_import.src2ogr(vector)

    # Input SpatialReference
    t_srs = osr.SpatialReference()
    t_srs.ImportFromWkt(wtk_projection)

    in_layer = ds.GetLayer()
    s_srs = in_layer.GetSpatialRef()
    transform = osr.CoordinateTransformation(s_srs, t_srs)

    # Create new layer
    geom_type = in_layer.GetGeomType()
    out_ds = ogr_reader.create_layer(name=outname, wkt_proj=wtk_projection, geom_type=geom_type)
    out_layer = out_ds.GetLayer()

    # Copy field headers
    in_layer_defn = in_layer.GetLayerDefn()
    [out_layer.CreateField(in_layer_defn.GetFieldDefn(i)) for i in range(in_layer_defn.GetFieldCount())]

    # Get features and reproject
    out_layer_defn = out_layer.GetLayerDefn()

    for in_feature in in_layer:
        # get the input geometry
        geom = in_feature.GetGeometryRef()

        # reproject the geometry
        geom.Transform(transform)

        # create a new feature
        out_feature = ogr.Feature(out_layer_defn)

        # set the geometry
        out_feature.SetGeometry(geom)

        # set the attributes
        for a in range(0, out_layer_defn.GetFieldCount()):
            out_feature.SetField(out_layer_defn.GetFieldDefn(a).GetNameRef(), in_feature.GetField(a))

        # add the feature to the shapefile
        out_layer.CreateFeature(out_feature)

        # destroy the features and get the next input feature
        out_feature.Destroy()
        in_feature.Destroy()

    in_layer.ResetReading()
    # ds.Destroy()

    return out_ds
