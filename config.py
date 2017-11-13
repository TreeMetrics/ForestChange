# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		args_reader.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic configuration holder objects.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================

"""
Basic configuration holder objects.
"""

import os, sys
from miscellaneous import cmd
from bunch import Config
import logging

settings_json_path = os.path.join(os.path.dirname(__file__), "settings.json")
tempdir = os.path.join('/home/puter/Documents/temp')

json_template = """ JSON Template: 
    {"profiles": {
    "sentinel_default": {
    "source_name": "sentinel",
    "bands": {
    "red_band": 1,
    "green_band": 3,
    "blue_band": 1,
    "nir_band": 8
    },
    "equalization":"False",
    "normlisation":"False",
    "segment_size": 2
    }
    }
    }"""


def find_bins(package_name):
    """ Search for binaries in most common places. Only works in Ubuntu systems."""

    return cmd('which', str(package_name))


def check_config():
    """ Check configuration variables"""
    logging.info("Checking configuration variables: " + str(cmd('saga_cmd -v')))

    envidic = Config()

    # Check PYTHON
    if not sys.version_info.major == 2 or not sys.version_info.minor == 7:
        raise Exception('Python 2.7 required')

    # Check GDAL
    try:
        import gdal
        import gdal_array

    except ImportError:
        from osgeo import gdal
        from osgeo import gdal_array

    else:
        raise Exception('Error Importing GDAL')

    # Check SAGA
    if not 'saga_bins' in envidic:
        envidic['saga_cmd'] = str(find_bins('saga_cmd')).strip()

    if not os.path.exists(str(envidic['saga_cmd'])):
        raise Exception('Error finding SAGA bins. ' + str(envidic['saga_cmd']))

    # Check setting file
    if os.path.exists(settings_json_path):
        envidic['settings_file'] = settings_json_path

    else:
        logging.error("Please specify the parameters for analysis. JSON file with parameters is required: " +
                      str(Config()["settings_file"]) + str(json_template))

        raise Exception('Settings file "settings.json" cannot be found. Aborting...')

    # Check setting file
    if not tempdir:
        logging.error("Please specify the temp directory.")
        raise Exception('temp directory cannot be found. Aborting...')

    if not os.path.exists(tempdir):
        os.makedirs(tempdir)

    envidic['tempdir'] = tempdir



