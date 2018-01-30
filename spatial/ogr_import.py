# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		gdal_import.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic tools for import vectors to/from gdal

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================


import logging

from spatial.ogr_reader import ogr2ds
from spatial.ogr2py import Ogr2Py


def ogr_import(ogr_source, import_data=True):
    """ Import to system format"""

    if ogr2ds(ogr_source):

        # Work directly in org
        return ogr2ds(ogr_source)

        # Work in with py-dict
        # return Ogr2Py(ds=ogr_ds, import_data=import_data)

    else:
        logging.error('OGR dataset cannot be imported')


def src2ogr(src):
    logging.debug("Importing file tiles " + str(src))

    if ogr2ds(src):
        return ogr2ds(src)

    else:
        try:
            ogr2ds(src.ds)
            return src.ds

        except:
            logging.error(" Unknown source.")


