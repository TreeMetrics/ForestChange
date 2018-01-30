


def clip_raster_by_feature_id(vds, raster_array, outname, geotransform, projection=None):

    if len(raster_array.shape) == 3:

        nbands = raster_array.shape[0]

    elif len(raster_array.shape) == 2:
        nbands = 1

    else:
        logging.error('Band data is empty.')
        return

    new_array = []
    for band in xrange(nbands):

        if len(raster_array.shape) == 3:
            raster_array_i = raster_array[band]

        else:
            raster_array_i = raster_array

        ysize, xsize = raster_array_i.shape

        layer = vds.GetLayer(0)
        # Create data mask
        rasterpoly = Image.new("L", (xsize, ysize), 1)
        raster_im = ImageDraw.Draw(rasterpoly)
        inner_ring_im = ImageDraw.Draw(rasterpoly)

        # for fid in xrange(layer.GetFeatureCount()):
        #     feature = layer.GetFeature(fid)
        for feature in layer:
            geoms = feature.GetGeometryRef()

            # extent = geom.GetEnvelope()

            if geoms.GetGeometryName().lower() == "multipolygon":
                for geom in geoms:
                    pts = geom.GetGeometryRef(0)
                    points = [(pts.GetX(p), pts.GetY(p)) for p in range(pts.GetPointCount())]
                    pixels = [gdalr.world2pixel(geotransform, p[0], p[1]) for p in points]
                    raster_im.polygon(pixels, 0)

                    if geom.GetGeometryCount() > 1:
                        for i in xrange(1, geom.GetGeometryCount()):
                            pts = geom.GetGeometryRef(i)
                            points1 = [(pts.GetX(p), pts.GetY(p)) for p in range(pts.GetPointCount())]
                            pixels1 = [gdalr.world2pixel(geotransform, p[0], p[1]) for p in points1]

                            inner_ring_im.polygon(pixels1, 1)

            elif geoms.GetGeometryName().lower() == "polygon":
                pts = geoms.GetGeometryRef(0)
                points = [(pts.GetX(p), pts.GetY(p)) for p in range(pts.GetPointCount())]
                pixels = [gdalr.world2pixel(geotransform, p[0], p[1]) for p in points]

                raster_im.polygon(pixels, 0)

            del feature

        layer.ResetReading()

        ##Image to array
        mask = np.fromstring(rasterpoly.tostring(), 'b')
        mask.shape = rasterpoly.im.size[1], rasterpoly.im.size[0]

        # Clip the image using the mask (Note that np.uint8 does not allow nan values
        new_array.append(np.choose(mask, (raster_array_i, np.nan)).astype(np.float))

    if not outname:
        outname = 'rasterize'

    out_ds = GdalImport_old().array2gdal(src_array=np.array(new_array), filename=outname, projection=projection,
                                     geotransform=geotransform)

    return out_ds