# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		args_reader.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module manages the analysis and the outputs.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================


import os
import argparse
from version import __version__, __date__, __copyright__

class FileCheck(argparse.Action):
    def __call__(self, parser_i, namespace, values, option_string=None):
        prospective_file = values

        if not prospective_file or not os.path.exists(prospective_file):
            parser_i.print_help()
            #print 'File does not exists. ' + str(prospective_file)
            #exit()
            raise Exception('File does not exists. ' + str(prospective_file))

        else:
            setattr(namespace, self.dest, prospective_file)


def main():
    ## Parse command line arguments

    # Create the top-level parser
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

    parser.add_argument("-s", "--source", type=str, choices=['sentinel'], default='sentinel', required=True,
                        help="Forest boundaries. (Optional)")

    parser.add_argument("-z", "--settings",
                        default="""{"source": { "sentinel": {"name": "sentinel","bands": {"red_band": 1,"green_band": 3,
                        "blue_band": 1,"nir_band": 8 },"segment_size": 2}}""",
                        help="JSON with parameters for the analysis.(Optional)")

    # Check and get arguments
    args = parser.parse_args()
    # args = vars(parser.parse_args())

    return args
