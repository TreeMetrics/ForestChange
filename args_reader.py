# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		args_reader.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module manages the analysis and the outputs.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================


import os
import argparse
import json

from version import __version__, __date__, __copyright__
from bunch import Config
import config


config.check_config()

if 'settings_file' in Config():
    settings_json_path = Config()['settings_file']

else:
    raise Exception('Error reading config settings')


class FileCheck(argparse.Action):
    def __call__(self, parser_i, namespace, values, option_string=None):
        prospective_file = values

        if not prospective_file or not os.path.isfile(prospective_file):
            parser_i.print_help()
            #print 'File does not exists. ' + str(prospective_file)
            #exit()
            raise Exception('File does not exists. ' + str(prospective_file))

        else:
            setattr(namespace, self.dest, prospective_file)


class dump_into_namespace(object):
    def __init__(self, adict):
        self.__dict__.update(adict)


def read_json_file(filepath):
    with open(filepath) as data_file:
        return json.load(data_file)


def main():
    # Parse command line arguments

    parser = argparse.ArgumentParser(description='Tools for Forest Change Detection',
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-v', '--version', action='version', version="Forest Spatial" + '\n' +
                                                                     "Version: " + str(__version__) + '\n' +
                                                                     "Last updated " + str(__date__) + '\n' +
                                                                     __copyright__ + '\n')

    parser.add_argument("-d1", "--dataset1", action=FileCheck, required=True,
                        help="Full path of newer dataset (TIF format).")

    parser.add_argument("-d2", "--dataset2", action=FileCheck, required=True,
                        help="Full path of older dataset (TIF format).")

    parser.add_argument("-b", "--bounds", action=FileCheck, required=False,
                        help="Forest boundaries. (Optional)")

    parser.add_argument("-o", "--output", required=True,
                        help="Output file path (TIF format)")

    profiles = read_json_file(settings_json_path)['profiles'].keys()

    parser.add_argument("-p", "--parameters", type=str, choices=profiles, default='sentinel_default', required=False,
                        help="Profiles including the parameters for analysis. "
                             "Check 'settings.json' file to add/change an analysis profile")

    # Check and get arguments
    args = parser.parse_args()

    # Read settings
    parameters = read_json_file(settings_json_path)['profiles'][args.parameters]
    parameters = dump_into_namespace(parameters)

    args.parameters = parameters
    # args = vars(parser.parse_args())

    return args
