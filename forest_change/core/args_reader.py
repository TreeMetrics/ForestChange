# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		args_reader.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module manages the inputs and outputs.

# COPYRIGHT:	(C) 2018 Treemetrics all rights reserved.
# ==========================================================================================


import argparse
import logging
import os

import config
from analysis_parameters import AnalysisParameters

from spatial import s2reader
from version import __version__, __date__, __copyright__


class SetVerbosity(argparse.Action):
    """ Set verbosity level"""

    def __call__(self, parser_i, namespace, value, option_string=None):
        """ Set verbose level"""

        config.verbose_config(level=value)

        setattr(namespace, self.dest, value)


class SetTempdir(argparse.Action):
    """ Set verbosity level"""

    def __call__(self, parser_i, namespace, value, option_string=None):
        """ Set tempdir"""

        config.tempdir_config(outputdir_path=value)
        setattr(namespace, self.dest, value)


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


class Str2Bool(argparse.Action):
    def __call__(self, parser_i, namespace, values, option_string=None):

        if values.lower() in ('yes', 'true', 't', 'y', '1'):
            setattr(namespace, self.dest, True)

        elif values.lower() in ('no', 'false', 'f', 'n', '0'):
            setattr(namespace, self.dest, False)

        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')


class S2ProductCheck(argparse.Action):
    def __call__(self, parser_i, namespace, values, option_string=None):
        prospective_dir = values

        if not os.path.isdir(prospective_dir):
            logging.error('Directory does not exists. ' + str(prospective_dir))
            parser_i.print_help()
            exit(1)

        safe_file_paths = []
        # for root, dirs, files in os.walk(prospective_dir):
        #     for file_path in files:

        for filename in os.listdir(prospective_dir):
            file_path = os.path.join(prospective_dir, filename)
            filename, extension = os.path.splitext(os.path.normpath(file_path))
            if extension in [".SAFE", ".ZIP", ".zip", ".safe"]:
                safe_file_paths.append(file_path)

        if len(safe_file_paths) == 0:
            logging.error("No Sentinel-2 products found. Only .SAFE folders or zipped .SAFE folders allowed")
            parser_i.print_help()
            exit(1)

        elif len(safe_file_paths) > 2:
            logging.error("Only TWO Sentinel-2 products are allowed. "
                          "These products should have the same extent and different dates")
            parser_i.print_help()
            exit(1)

        else:
            for s2_product_path in safe_file_paths:
                try:
                    with s2reader.open_safe(s2_product_path) as s2_product:
                        if s2_product:
                            setattr(namespace, self.dest, prospective_dir)

                        else:
                            logging.exception('Error reading in Sentinel-2 product' + str(prospective_dir))
                            parser_i.print_help()
                            exit(1)

                except AssertionError:
                    logging.exception('Sentinel-2 format not recognised for ' + str(prospective_dir))
                    parser_i.print_help()
                    exit(1)


class DumpIntoNamespace(object):
    def __init__(self, adict):
        self.__dict__.update(adict)


def define_flags_arg(parser_i):
    """ Flags for verbosity."""

    # group0 = parser_i.add_mutually_exclusive_group(required=False)
    # group0.add_argument("--debug", action="store_true", required=False, help="Create debug files")
    # group0.add_argument("--silent", action="store_true", required=False, help="Create debug files")

    # Other method:
    parser_i.add_argument("-v", "--verbosity", type=int, choices=xrange(5), default=2, action=SetVerbosity,
                          help="0 (silent): Does not print anything in terminal. " + '\n' +
                               "1 (quiet): Prints minimum information for SatForM 3D server function. " + '\n' +
                               "2 (default): Prints basic info, warnings and errors " + '\n' +
                               "3 (verbose): Prints extra info, warnings and errors " + '\n' +
                               "4 (debug): Prints detailed info, debugging, errors and third party errors (stderror)")


# def define_rgb_change_args(parser_i):
#     """ Common flags."""
#
#     parser_i.add_argument("-d1", "--dataset1", action=FileCheck, required=True,
#                           help="Full path of newer dataset (dhm or 4 bands image).")
#
#     parser_i.add_argument("-d2", "--dataset2", action=FileCheck, required=True,
#                           help="Full path of older dataset (dhm or 4 bands image).")
#
#     parser_i.add_argument("-b", "--bounds", action=FileCheck, required=False,
#                           help="Forest boundaries. (Optional)")


def define_s2_change_args(parser_i):
    """ Change detection with Sentinel 2"""

    parser_i.add_argument("-s2n", "--s2_product_dir", action=S2ProductCheck, required=False,
                          help="Path to directory containing two temporal Sentinel-2 products (newer and older)")

    # group1.add_argument("-s2n", "--s2_product_dir_newer", action=S2ProductCheck, required=False,
    #                     help="Sentinel 2 output directory"

    # group2.add_argument("-s2o", "--s2_product_dir_older", action=S2ProductCheck, required=False,
    #                     help="Sentinel 2 output directory")

    parser_i.add_argument("-th", "--threshold", type=int, required=False, default=20,
                          help="Change threshold 0-100. Default is 20")

    # parser_i.add_argument("--tile_size", "--tile_size", type=int, required=False, default=1000,
    #                       help="Tile size for improve performance of analysis. Default is 1000")

    parser_i.add_argument("-b", "--bounds", action=FileCheck, required=False,
                          help="Forest boundaries.")

    parser_i.add_argument("--additional_outputs", action=Str2Bool, required=False,
                          help="Generate additional_outputs at 10m resolution")

    parser_i.add_argument("-o", "--output_dir", required=True, action=SetTempdir, help="Output file path (TIF format)")

    parser_i.add_argument("-p", "--parameters", type=str,
                          choices=AnalysisParameters().list_analysis_profiles()['sentinel2'],
                          default='default', required=False,
                          help="JSON to define the parameters for analysis."
                               "Check 'sentinel2_settings.json' file to add/change a profile for analysis")


def main():

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Tools for Forest Change Detection',
                                     formatter_class=argparse.RawTextHelpFormatter)

    subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands',
                                       dest='module', help='additional help')

    parser.add_argument('-V', '--version', action='version', version="Forest Spatial" + '\n' +
                                                                     "Version: " + str(__version__) + '\n' +
                                                                     "Last updated " + str(__date__) + '\n' +
                                                                     __copyright__ + '\n')

    # Define the arguments for verbosity.
    define_flags_arg(parser)

    # Create the parser for the different command
    # parser_rgb = subparsers.add_parser('RGB', help='Sentinel change detection')
    parser_s2 = subparsers.add_parser('Sentinel2', help='Sentinel change detection')

    # Define the arguments for each command.
    # define_rgb_change_args(parser_rgb)
    define_s2_change_args(parser_s2)

    # Check and get arguments
    args = parser.parse_args()
    # args = vars(parser.parse_args())

    # Get Analysis parameters
    parameters = AnalysisParameters().get_analysis_parameters(module_name=args.module, profile=None)
    parameters = DumpIntoNamespace(parameters)

    args.parameters = parameters

    return args
