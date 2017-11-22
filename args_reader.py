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

from version import __version__, __date__, __copyright__
from bunch import Config


class FileCheck(argparse.Action):
    def __call__(self, parser_i, namespace, values, option_string=None):
        prospective_file = values

        if not prospective_file or not os.path.isfile(prospective_file):
            parser_i.print_help()
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
    d1 = parser.add_argument_group('Newer dataset')
    group1 = d1.add_mutually_exclusive_group(required=True)
    group1.add_argument("-b1", "--new_rgbnir_bands", action=FileListCheck,
                        help="List of newer single band files separated by colon: 'red_band;green_band;blue_band;nir_band' ")
    group1.add_argument("-d1", "--new_rgbnir_file", action=FileCheck, required=False,
                       help="Full path of newer multiband dataset (rgbnir TIF format).")

    d2 = parser.add_argument_group('Older dataset')
    group1 = d2.add_mutually_exclusive_group(required=True)
    group1.add_argument("-b2", "--old_rgbnir_bands", action=FileListCheck,
                        help="List of older single band files separated by colon: 'red_band;green_band;blue_band;nir_band' ")
    group1.add_argument("-d2", "--old_rgbnir_file", action=FileCheck, required=False,
                        help="Full path of older multiband dataset (rgbnir TIF format).")

    parser.add_argument("-b", "--bounds", action=FileCheck, required=False,
                        help="Forest boundaries. (Optional)")

    parser.add_argument("-o", "--output", required=True,
                        help="Output file path (TIF format)")

    parser.add_argument("--tempdir", required=False,
                        help="Temporal directory")

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
