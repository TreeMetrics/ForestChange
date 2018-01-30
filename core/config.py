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
from spatial import gdal_error_handler

config_file = os.path.join(os.path.dirname(__file__), '..', 'config', "config.cfg")


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

    forest_area_path = list(dict_find('forest_area_path', config_dict))[0]
    if os.path.exists(os.path.join(os.path.dirname(__file__), forest_area_path)):
        envidic['forest_area_path'] = os.path.join(os.path.dirname(__file__), forest_area_path)

    elif os.path.exists(forest_area_path):
        envidic['forest_area_path'] = forest_area_path

    else:
        envidic['forest_area_path'] = None
        logging.warning("forest_area_path not defined")


def logging_config(level='default'):
    """Verbosity levels:
    Level 3: Debugging - Prints detailed debugging info
    Level 2: Default -   Prints info, warnings and errors
    Level 1: Quiet -     Prints only warnings and errors
    Level 0: Silent -    Does not print anything in terminal."""

    rootLogger = logging.getLogger('')
    if level == 3 or level.lower() == 'debugging':
        fmt = "%(levelname)-8.8s %(module)s.py:%(lineno)4s %(message)s [%(asctime)s]"
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt))

        rootLogger.addHandler(handler)
        rootLogger.setLevel(logging.DEBUG)

        # Enable GDAL/OGR exceptions
        gdal_error_handler.install_error_handler()

        logging.debug('Debugging configuration set.')
        Config()['verbose'] = 'debug'

    elif level == 2 or level == 'default':
        rootLogger.setLevel(logging.INFO)
        Config()['verbose'] = 'default'

    elif level == 1 or level.lower() == 'quiet':
        rootLogger.setLevel(logging.WARNING)
        Config()['debug'] = 'quiet'

    elif level == 0 or level == 'silent':
        sys.stdout = open(os.devnull, 'w')
        Config()['debug'] = 'silent'


