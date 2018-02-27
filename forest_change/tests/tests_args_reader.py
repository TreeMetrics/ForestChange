#from unittest import TestCase


from subprocess import call

import argparse
import glob

#from core import args_reader

input_files = glob.glob('some/path/*.foo')

tags = ['module', "---verbosity",  "--s2_product_dir", "--threshold", "--bounds", "--additional_outputs", "--output_dir", "--parameters"]
test_tags = ['Sentinel2', "4", 'tempdir_path', "product_dir_path", "20", "bounds_path",
             "True", "output_dir_path", "parameters"]


main_short_tags = ["-V", "-v", "--tempdir"]
main_tags = ['--version', "---verbosity"]
main_test_tags = ['', "4", 'tempdir_path']


subparsers_list = ['Sentinel2']
s2_change_short_tags = ["-s2n", "-th", "-b", "-o", "-p"  ]
s2_change_tags = ["--s2_product_dir", "--threshold", "--bounds", "--additional_outputs", "--output_dir", "--parameters"]
s2_change_test_tags = ["product_dir_path", "20", "bounds_path",
             "True", "output_dir_path", "parameters"]


# class TestMain(TestCase):
#
#     def create_parser(self):
#
#         #call(["ls", "-l"])
#
#
#
#
#
#         python % s / forest_change_main.py - -tempdir % s
#         Sentinel2 - -s2_product_dir % s - -threshold % s - -additional_outputs % s - o % s
#
#         args = args_reader.main()
#
#         exit()
#
#
#         parser = argparse.ArgumentParser(description='Change Detection test parser',
#                                          formatter_class=argparse.RawTextHelpFormatter)
#
#         subparsers = parser.add_subparsers(title='subcommands', description='test valid subcommands',
#                                            dest='module', help='additional help')
#
#         for tag in main_tags:
#             parser.add_argument(tag)
#
#         Sentinel2_subparser = subparsers.add_parser('Sentinel2', help='test subparser')
#         for tag in s2_change_tags:
#             Sentinel2_subparser.add_argument(tag)
#
#         return parser.parse_args()
#
#     def test_parser(self):
#         parser = self.create_parser()
#         for parameter, key in zip(tags, test_tags):
#             parsed = parser.parse_args([str(parameter), str(key)])
#             parsed = vars(parsed.parse_args())
#             print str(parameter)
#             print str(key)
#             self.assertEqual(parsed[str(parameter)], str(key))


if __name__ == '__main__':


    import sys

    i = 1
    for values in test_tags:
        sys.argv[i:] = values
        i =+ 1

    print sys.argv
    exit()




    #TestMain().test_parser()
