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

import os
import sys
import logging
import ConfigParser

from bunch import Config
from miscellaneous import cmd, dict_find

config_file = os.path.join(os.path.dirname(__file__), "config.cfg")


def find_bins(package_name):
    """ Search for binaries in most common places. Only works in Ubuntu systems."""

    return cmd('which', str(package_name))


def read_config_file(config_file_path):
    config = ConfigParser.ConfigParser()
    config.read(config_file_path)

    config_dict = {}
    for section in config.sections():
        config_dict[section] = {}
        for option in config.options(section):
            config_dict[section][option] = config.get(section, option)

    return config_dict


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
    if 'saga_bins' not in envidic:
        envidic['saga_cmd'] = str(find_bins('saga_cmd')).strip()

    if not os.path.exists(str(envidic['saga_cmd'])):
        raise Exception('Error finding SAGA bins. ' + str(envidic['saga_cmd']))

    # Check config file
    if not os.path.exists(config_file):
        raise Exception('Error reading "config.cfg". File not found. Aborting...')

    config_dict = read_config_file(config_file)

    # Check setting file
    if not len(list(dict_find('settings_json_path', config_dict))) > 0:
        raise Exception('Error reading "config.cfg", variable "settings_json_path" not found. Aborting...')

    settings_json_path = list(dict_find('settings_json_path', config_dict))[0]
    if os.path.exists(settings_json_path):
        envidic['settings_file'] = settings_json_path

    elif os.path.exists(os.path.join(os.path.dirname(__file__), settings_json_path)):
        envidic['settings_file'] = os.path.join(os.path.dirname(__file__), settings_json_path)

    else:
        logging.error("Please specify the parameters for analysis. JSON file with parameters is required: " +
                      str(Config()["settings_file"]))

        raise Exception('Settings file "settings.json" cannot be found. Aborting...')
