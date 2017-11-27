# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		args_reader.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module manages the inputs and outputs.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================


import os
import argparse
import json
import zipfile
import logging

from version import __version__, __date__, __copyright__
from bunch import Config

TEMPDIR = None

class FileCheck(argparse.Action):
    def __call__(self, parser_i, namespace, values, option_string=None):
        prospective_file = values

        if not prospective_file or not os.path.isfile(prospective_file):
            parser_i.print_help()
            raise Exception('File does not exists. ' + str(prospective_file))

        else:
            setattr(namespace, self.dest, prospective_file)


class FileListCheck(argparse.Action):
    def __call__(self, parser_i, namespace, values, option_string=None):
        prospective_list = values

        field_paths=[]
        for file_path in prospective_list.strip().split(";"):

            if not file_path or not os.path.isfile(file_path):
                parser_i.print_help()
                raise Exception('File does not exists. ' + str(file_path))

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
            parser_i.print_help()
            raise Exception('Sentinel Product directrory does not exists. ' + str(prospective_dir))

        elif os.path.isfile(prospective_dir) and os.path.splitext(prospective_dir)[1].lower() == '.zip':

            # Extract file
            zip_ref = zipfile.ZipFile(prospective_dir, 'r')
            zip_ref.extractall(os.path.join(tempdir, os.path.splitext(os.path.basename(prospective_dir))[0]))
            zip_ref.close()

            prospective_dir = os.path.join(tempdir, os.path.splitext(os.path.basename(prospective_dir))[0])

            if not os.path.isdir(prospective_dir):
                parser_i.print_help()
                raise Exception('Error extracting sentinel product directrory zip file. ' + str(prospective_dir))

        elif not os.path.isdir(prospective_dir):
            parser_i.print_help()
            raise Exception('Sentinel Product directory does not exists. ' + str(prospective_dir))

        data = {}
        for dirpath, subdirs, files in os.walk(prospective_dir):

            # Find Granule dirs
            for name_dir in subdirs:
                if name_dir.lower() == 'granule':
                    granule_dir = os.path.join(dirpath, name_dir)

                    # Get product name and find img_data dirs
                    for product_dir in os.listdir(granule_dir):
                        for dirpath, subdirs, files in os.walk(granule_dir):
                            for name_dir in subdirs:
                                if name_dir.lower() == 'img_data':
                                    img_data_dir = os.path.join(dirpath, name_dir)

                                    # Look for images
                                    dataset_list = []
                                    for dir_im, subdirs_im, files_im in os.walk(img_data_dir):
                                        for file_name in files_im:
                                            if file_name.endswith(".jp2"):
                                                dataset_list.append(os.path.join(dir_im, file_name))

                                    data[product_dir] = dataset_list

        if len(data.keys()[0]) == 0:
            raise Exception('No Sentinel .jp2 images found ' + str(data.keys()))

        elif len(data.keys()) > 1:
            logging.warning('Too many Sentinel datasets, only the first one will be processed' + str(data.keys()[0]))
        #    raise Exception('Too many Sentinel dataset ' + str(data.keys()[0]))

        if len(str(data[data.keys()[0]])) < 3:
            raise Exception('No enough Sentinel .jp2 files found. At least 3 bands are required. Bands dataset1: '
                            + str(data[data.keys()[0]]) + ' Bands dataset2: ' + str(data[data.keys()[1]]))

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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Tools for Forest Change Detection',
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-v', '--version', action='version', version="Forest Spatial" + '\n' +
                                                                     "Version: " + str(__version__) + '\n' +
                                                                     "Last updated " + str(__date__) + '\n' +
                                                                        __copyright__ + '\n')

    parser.add_argument("--DEBUG", action='store_true', help="Create debug files")

    #parser.add_usage_group()
    # parser.add_argument("-s", "--s2_product_dir", action=S2ProductCheck, required=False,
    #                    help="Sentinel 2 output directory")
    # args, leftovers = parser.parse_known_args()
    # if args.s2_product_dir is None:


    parser.add_argument("--tempdir", required=False, help="Temporal directory")
    args, leftovers = parser.parse_known_args()
    global TEMPDIR
    TEMPDIR = args.tempdir


    d1 = parser.add_argument_group('Newer dataset')
    group1 = d1.add_mutually_exclusive_group(required=True)
    group1.add_argument("-b1", "--new_rgbnir_bands", action=FileListCheck,
                    help="List of newer single band files separated by colon: 'red_band;green_band;blue_band;nir_band' ")
    group1.add_argument("-d1", "--new_rgbnir_file", action=FileCheck, required=False,
                   help="Full path of newer multiband dataset (rgbnir TIF format).")
    group1.add_argument("-s2n", "--s2_product_dir_newer", action=S2ProductCheck, required=False,
                        help="Sentinel 2 output directory")

    # Add  old dataset
    d2 = parser.add_argument_group('Older dataset')
    group1 = d2.add_mutually_exclusive_group(required=True)
    group1.add_argument("-b2", "--old_rgbnir_bands", action=FileListCheck,
                    help="List of older single band files separated by colon: 'red_band;green_band;blue_band;nir_band' ")
    group1.add_argument("-d2", "--old_rgbnir_file", action=FileCheck, required=False,
                    help="Full path of older multiband dataset (rgbnir TIF format).")
    group1.add_argument("-s2o", "--s2_product_dir_older", action=S2ProductCheck, required=False,
                        help="Sentinel 2 output directory")

    parser.add_argument("-b", "--bounds", action=FileCheck, required=False,
                        help="Forest boundaries. (Optional)")

    parser.add_argument("-o", "--output", required=True,
                        help="Output file path (TIF format)")

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
