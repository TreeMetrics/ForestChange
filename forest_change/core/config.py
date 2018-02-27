# /usr/bin/env python
# PROJECT:	    EO4Atlantic
# MODULE:		args_reader.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	Basic configuration holder objects.

# COPYRIGHT:	(C) 2018 Treemetrics all rights reserved.
# ==========================================================================================

"""
Basic configuration holder objects.
"""

import ConfigParser
import logging
import os
import sys

import miscellaneous
from bunch import Config

from miscellaneous import cmd, dict_find
from spatial import gdal_error_handler

config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', "config.cfg"))
home_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def read_config_file(config_file_path):
    config = ConfigParser.ConfigParser()
    config.read(config_file_path)

    config_dict = {}
    for section in config.sections():
        config_dict[section] = {}
        for option in config.options(section):
            config_dict[section][option] = config.get(section, option)

    return config_dict


def verbose_config(level='default'):
    """Verbosity levels:
    Level 4: Debug - Prints detailed debugging info
    Level 4: Verbose - Prints extra info, warnings and errors
    Level 2: Default - Prints info, warnings and errors
    Level 1: Quiet - Prints only warnings and errors
    Level 0: Silent -Does not print anything in terminal."""

    rootLogger = logging.getLogger('')
    if level == 4 or level.lower() == 'debug':
        fmt = "%(levelname)-8.8s %(module)s.py:%(lineno)4s %(message)s [%(asctime)s]"
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt))

        rootLogger.addHandler(handler)
        rootLogger.setLevel(logging.DEBUG)

        # Enable GDAL/OGR exceptions
        gdal_error_handler.install_error_handler()

        logging.debug('Debugging configuration set.')
        Config()['verbose'] = 'debug'

    elif level == 3 or level == 'verbose':
        rootLogger.setLevel(logging.INFO)
        Config()['verbose'] = 'verbose'

    elif level == 2 or level == 'default':
        rootLogger.setLevel(logging.INFO)
        Config()['verbose'] = 'default'

    elif level == 1 or level.lower() == 'quiet':
        rootLogger.setLevel(logging.WARNING)
        Config()['debug'] = 'quiet'

    elif level == 0 or level == 'silent':
        sys.stdout = open(os.devnull, 'w')
        Config()['debug'] = 'silent'


def tempdir_config(tempdir_path):
    if not tempdir_path or not os.path.isdir(tempdir_path):
        os.makedirs(tempdir_path)

    if not tempdir_path or not os.path.isdir(tempdir_path):
        logging.warning('Tempdir not defined')

    else:
        Config(overwrite=True)['tempdir'] = tempdir_path


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
        envidic['saga_cmd'] = str(miscellaneous.find_bins('saga_cmd')).strip()

    if not os.path.exists(str(envidic['saga_cmd'])):
        raise Exception('Error finding SAGA bins. ' + str(envidic['saga_cmd']))

    # Check config file
    if not os.path.exists(config_file):
        raise Exception('Error reading "config.cfg". File not found. Aborting...')

    config_dict = read_config_file(config_file)

    # Check setting files
    if not len(list(dict_find('analysis_parameters_dir', config_dict))) > 0:
        raise Exception('Error reading "config.cfg", variable "analysis_parameters_dir" not found. Aborting...')

    analysis_parameters_dir = list(dict_find('analysis_parameters_dir', config_dict))[0]
    if os.path.isdir(os.path.abspath(analysis_parameters_dir)):
        envidic["analysis_parameters_dir"] = os.path.abspath(analysis_parameters_dir)

    elif os.path.isdir(os.path.join(home_dir, analysis_parameters_dir)):
        envidic["analysis_parameters_dir"] = os.path.join(home_dir, analysis_parameters_dir)

    else:
        raise Exception('Directory containing the parameters for analysis cannot be found.'
                        'Variable "analysis_parameters_dir" is not well defined in "config.cfg" found Aborting...')

        # Find forest areas
    forest_area_path = list(dict_find('forest_area_path', config_dict))[0]
    for dirpath, dirnames, filenames in os.walk(home_dir):
        for filename in [f for f in filenames if f == os.path.basename(forest_area_path)]:
            envidic['forest_area_path'] = os.path.join(dirpath, filename)

    if 'forest_area_path' not in envidic or not envidic['forest_area_path'] or not os.path.exists(
            envidic['forest_area_path']):

        logging.error("forest_area_path not defined")
        raise Exception("forest_area_path not defined")
