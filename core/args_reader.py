# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		args_reader.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module manages the inputs and outputs.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================


import argparse
import json
import logging
import os
import zipfile

from bunch import Config
from core import config
from version import __version__, __date__, __copyright__

TEMPDIR = None


class FileCheck(argparse.Action):
    def __call__(self, parser_i, namespace, values, option_string=None):
        prospective_file = values

        if not prospective_file or not os.path.isfile(prospective_file):
            logging.critical('File does not exists. ' + str(prospective_file))
            parser_i.print_help()
            exit(1)

        else:
            setattr(namespace, self.dest, prospective_file)


class FileListCheck(argparse.Action):
    def __call__(self, parser_i, namespace, values, option_string=None):
        prospective_list = values

        field_paths = []
        for file_path in prospective_list.strip().split(";"):

            if not file_path or not os.path.isfile(file_path):
                logging.critical('File does not exists. ' + str(prospective_list))
                parser_i.print_help()
                exit(1)

            else:
                field_paths.append(file_path)

        setattr(namespace, self.dest, field_paths)


class S2ProductCheck(argparse.Action):
    def __call__(self, parser_i, namespace, values, option_string=None):
        prospective_dir = values

        global TEMPDIR
        tempdir = TEMPDIR

        if not tempdir:
            tempdir = os.path.dirname(prospective_dir)

        if not prospective_dir:
            logging.critical('File does not exists. ' + str(prospective_dir))
            parser_i.print_help()
            exit(1)

        elif os.path.isfile(prospective_dir) and os.path.splitext(prospective_dir)[1].lower() == '.zip':

            # Extract file
            zip_ref = zipfile.ZipFile(prospective_dir, 'r')
            zip_ref.extractall(os.path.join(tempdir, os.path.splitext(os.path.basename(prospective_dir))[0]))
            zip_ref.close()

            prospective_dir = os.path.join(tempdir, os.path.splitext(os.path.basename(prospective_dir))[0])

            if not os.path.isdir(prospective_dir):
                logging.critical('Error extracting sentinel product directory zip file. ' + str(prospective_dir))
                parser_i.print_help()
                exit(1)

        elif not os.path.isdir(prospective_dir):
            logging.critical('Sentinel Product directory does not exists. ' + str(prospective_dir))
            parser_i.print_help()
            exit(1)

        data = {}
        for dir_path, subdirs, files in os.walk(prospective_dir):

            # Find Granule dirs
            for name_dir in subdirs:
                if name_dir.lower() == 'granule':
                    granule_dir = os.path.join(dir_path, name_dir)

                    # Get product name and find img_data dirs
                    for product_dir in os.listdir(granule_dir):
                        for dir1_path, subdirs1, files1 in os.walk(granule_dir):
                            for name_dir1 in subdirs1:
                                if name_dir1.lower() == 'img_data':
                                    img_data_dir = os.path.join(dir1_path, name_dir1)

                                    # Look for resolution folders (e.g. "R20m")
                                    resolution_list = []
                                    for res_dir in os.listdir(img_data_dir):
                                        res_dir_str = str(res_dir)
                                        start = res_dir_str.index('R') + 1
                                        end = res_dir_str.index('m', start)

                                        resolution_list.append(res_dir_str[start:end])

                                    if len(resolution_list) >= 1:
                                        resolution_dir = os.path.join(img_data_dir,
                                                                      'R' + str(max(resolution_list)) + 'm')

                                    else:
                                        resolution_dir = img_data_dir

                                    # Check for JP2 files
                                    dataset_list = []
                                    for file_name in os.listdir(resolution_dir):
                                        if file_name.endswith(".jp2"):
                                            dataset_list.append(os.path.join(resolution_dir, file_name))

                                    data[product_dir] = dataset_list

        if len(data.keys()[0]) == 0:
            logging.critical('No Sentinel .jp2 images found ' + str(data.keys()))
            parser_i.print_help()
            exit(1)

        elif len(data.keys()) > 1:
            logging.warning('Too many Sentinel datasets, only the first one will be processed' + str(data.keys()[0]))
        # raise Exception('Too many Sentinel dataset ' + str(data.keys()[0]))

        if len(str(data[data.keys()[0]])) < 3:
            logging.critical('No enough Sentinel .jp2 files found. At least 3 bands are required. Bands dataset1: '
                            + str(data[data.keys()[0]]) + ' Bands dataset2: ' + str(data[data.keys()[1]]))
            parser_i.print_help()
            exit(1)

        else:
            setattr(namespace, self.dest, data[data.keys()[0]])


class DumpIntoNamespace(object):
    def __init__(self, adict):
        self.__dict__.update(adict)


def read_json_file(filepath):
    with open(filepath) as data_file:
        return json.load(data_file)


def get_settings_profiles(json_file):
    profiles = read_json_file(json_file)['profiles'].keys()

    return profiles


def main():
    # Check configuration
    config.check_config()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Tools for Forest Change Detection',
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-v', '--version', action='version', version="Forest Spatial" + '\n' +
                                                                     "Version: " + str(__version__) + '\n' +
                                                                     "Last updated " + str(__date__) + '\n' +
                                                                     __copyright__ + '\n')

    group0 = parser.add_mutually_exclusive_group(required=False)
    group0.add_argument("--debug", action="store_true", required=False, help="Create debug files")
    group0.add_argument("--silent", action="store_true", required=False, help="Create debug files")

    # Set verbose level
    args, leftovers = parser.parse_known_args()
    if 'debug' in args:
        config.logging_config(level='debugging')

    elif 'silent' in args:
        config.logging_config(level='silent')

    else:
        config.logging_config(level='default')

    # Get tempdir
    parser.add_argument("--tempdir", required=False, help="Temporal directory")
    args, leftovers = parser.parse_known_args()
    global TEMPDIR
    TEMPDIR = args.tempdir

    # Get rest of input data
    d1 = parser.add_argument_group('Newer dataset')
    group1 = d1.add_mutually_exclusive_group(required=True)
    group1.add_argument("-d1", "--new_rgbnir_file", action=FileCheck, required=False,
                        help="Full path of newer multiband dataset (rgbnir TIF format).")
    group1.add_argument("-s2n", "--s2_product_dir_newer", action=S2ProductCheck, required=False,
                        help="Sentinel 2 output directory")

    # Add  old dataset
    d2 = parser.add_argument_group('Older dataset')
    group2 = d2.add_mutually_exclusive_group(required=True)
    group2.add_argument("-d2", "--old_rgbnir_file", action=FileCheck, required=False,
                        help="Full path of older multiband dataset (rgbnir TIF format).")
    group2.add_argument("-s2o", "--s2_product_dir_older", action=S2ProductCheck, required=False,
                        help="Sentinel 2 output directory")

    if os.path.exists(Config()['settings_file']):
        default_bounds = Config()['forest_area_path']

    else:
        default_bounds = None

    parser.add_argument("-th", "--threshold", type=int, required=False, default=20,
                        help="Change threshold 0-100. Default is 20")

    parser.add_argument("--tile_size", "--tile_size", type=int, required=False, default=500,
                        help="Tile size for improve performance of analysis. Default is 500")

    parser.add_argument("-b", "--bounds", action=FileCheck, required=False, default=default_bounds,
                        help="Forest boundaries. (Optional)")

    parser.add_argument("-o", "--output", required=True,
                        help="Output file path (TIF format)")

    args, leftovers = parser.parse_known_args()
    if args.s2_product_dir_newer is not None:
        group3 = parser.add_argument_group('Bands numbering')

        group3.add_argument("-rb", "--red_band", type=int, default=4, help="Red band position")

        group3.add_argument("-gb", "--green_band", type=int, default=3, help="Green band position")

        group3.add_argument("-bb", "--blue_band", type=int, default=2, help="Red band position")

        group3.add_argument("-ib", "--nir_band", type=int, default=8, help="Near-infrared band position")

    # Read settings
    if 'settings_file' in Config():
        settings_json_path = Config()['settings_file']

    else:
        raise Exception('Error reading config settings')

    parser.add_argument("-p", "--parameters", type=str, choices=get_settings_profiles(settings_json_path),
                        default='sentinel_default', required=False,
                        help="Profiles including the parameters for analysis. "
                             "Check 'settings.json' file to add/change an analysis profile")

    # Check and get arguments
    args = parser.parse_args()
    parameters = read_json_file(settings_json_path)['profiles'][args.parameters]
    parameters = DumpIntoNamespace(parameters)

    args.parameters = parameters
    # args = vars(parser.parse_args())

    return args
