#!/usr/bin/env python
"""
s2reader reads and processes Sentinel-2 L1C SAFE archives.
This module implements an easy abstraction to the SAFE data format used by the
Sentinel 2 misson of the European Space Agency (ESA)

USAGE:
with s2reader.open_safe(s2_product_path) as s2_product:

    # From Name
    print s2_product.mission
    print s2_product.product_level
    print s2_product.start_time
    print s2_product.processing_baseline
    print s2_product.ROO
    print s2_product.tile_number
    print s2_product.product_id
    print s2_product.format

# From explore dataset
    unzipped_safe = s2reader.extract_all(s2_product_path)
    explore_data =open_safe(s2_product_path):
    for product_id, jp2_files in explore_data.iteritems():
        print product_id
        print jp2_files.keys()  # resolution
        print jp2_files['R10m'].keys()  # bands
        print jp2_files['R10m']['B08']  # jp2 file path

Sentinel-2 bands description 

    #Resolution 10
    # B02 = blue
    # B03 = green
    # B04 = red
    # B08 = nir

    #Resolution 20
    # B05 = red_edge1
    # B06 = red_edge2
    # B07 = red_edge3
    # B8A = red_edge3
    # B11 = snow1
    # B12 = snow2

    # Resolution 60
    # B01 = AOT = Aerosols
    # B09 = vapour
    # B10 = cirrus
    
    # Other bands
    # AOT = Aerosol Optical Thickness map
    # CLD = Raster mask values range from 0 for high confidence clear sky to 100 for high confidence cloudy
    # SCL = Scene Classification. The meaning of the values is indicated in the Category Names of the band.
    # SNW = Raster mask values range from 0 for high confidence NO snow/ice to 100 for high confidence snow/ice
    # TCI = True Colour Images
    # WVP = Scene-average Water Vapour map
"""

import os
import zipfile
import datetime
import logging


def open_safe(safe_file):
    """Return a SentinelDataSet object."""
    if os.path.isdir(safe_file) or os.path.isfile(safe_file):
        return SentinelDataSet(safe_file)
    else:
        raise IOError("file not found: %s" % safe_file)


def extract_all(safe_path, dest_dir=None):

    if not dest_dir:
        dest_dir = os.path.dirname(safe_path)

    filename, extension = os.path.splitext(os.path.normpath(safe_path))
    if extension in [".ZIP", ".zip"]:

        # Extract file
        zip_file = zipfile.ZipFile(safe_path, "r")
        zip_file.extractall(dest_dir)
        # zip_file.extractall(os.path.join(dest_dir, os.path.splitext(os.path.basename(safe_path))[0]) + '.SAFE')
        zip_file.close()

        if not os.path.isdir(os.path.join(dest_dir, os.path.splitext(os.path.basename(safe_path))[0]) + '.SAFE'):
            logging.exception('Error extracting sentinel product directory zip file. ' + str(safe_path))

        return os.path.join(dest_dir, os.path.splitext(os.path.basename(safe_path))[0] + '.SAFE')

    elif extension in [".SAFE"]:
        return safe_path

    else:
        raise IOError("only .SAFE folders or zipped .SAFE folders allowed")


def explore_data(safe_path):
    """ Explore SAFE dataset without independently of manifest XML"""

    path = os.path.normpath(safe_path)
    filename, extension = os.path.splitext(os.path.normpath(path))

    if extension in [".ZIP", ".zip"]:
        raise Exception('Explore data only works for unzipped SAFE format, ' +
                        'Unzip frist using "extract_all" function')

    data = {}
    for dir_path, subdirs, files in os.walk(path):
        # Find Granule dirs
        for name_dir in subdirs:
            if name_dir.lower() == 'granule':
                granule_dir = os.path.join(dir_path, name_dir)

                # Get product name and find img_data dirs
                for product_dir in os.listdir(granule_dir):
                    data[product_dir] = {}

                    if os.path.exists(os.path.join(granule_dir, product_dir, 'IMG_DATA')):
                        img_data_dir = os.path.join(granule_dir, product_dir, 'IMG_DATA')

                        # for root, product_dir, files_name in os.walk(granule_dir):
                        #     for name_dir1 in product_dir:
                        #         if name_dir1.lower() == 'img_data':
                        #             img_data_dir = os.path.join(dir1_path, name_dir1)

                        # Look for resolution folders (e.g. "R20m")
                        for res_dir in os.listdir(img_data_dir):
                            data[product_dir][res_dir] = {}

                            for file_name in os.listdir(os.path.join(img_data_dir, res_dir)):
                                if os.path.splitext(file_name)[1].lower() == ".jp2":

                                    # L2A_T29UNU_20170717T113321_AOT_10m.jp2
                                    image_name_tokens = str(os.path.basename(file_name)).split("_")
                                    # product_level = image_name_tokens[0]
                                    # tile = image_name_tokens[1]
                                    # start_time = image_name_tokens[2]
                                    band = image_name_tokens[3]
                                    # resolution = os.path.basename(image_name_tokens[4])[0]
                                    # resolution = "".join([str(s) for s in resolution.split() if s.isdigit()])
                                    # format_type = os.path.basename(image_name_tokens[4])[1]

                                    data[product_dir][res_dir][band] = os.path.join(
                                        os.path.join(img_data_dir, res_dir), file_name)

                    else:
                        logging.exception('Image data not found for product: ' + str(product_dir))

    if len(data.keys()[0]) == 0:
        logging.exception('No Sentinel .jp2 images found ' + str(data.keys()))

    else:
        return data


class SentinelDataSet(object):
    """
    Return SentinelDataSet object.
    This object contains relevant metadata from the SAFE file and its
    containing granules as SentinelGranule() object.
    """

    def __init__(self, path):
        """Assert correct path and initialize."""
        filename, extension = os.path.splitext(os.path.normpath(path))
        if extension not in [".SAFE", ".ZIP", ".zip"]:
            raise IOError("only .SAFE folders or zipped .SAFE folders allowed")
        self.is_zip = True if extension in [".ZIP", ".zip"] else False
        self.path = os.path.normpath(path)

        # Read attributes in the name
        # MMM_MSIL1C_YYYYMMDDHHMMSS_Nxxyy_ROOO_Txxxxx_Product Discriminator.SAFE

        s2_product_tokens = str(os.path.basename(self.path)).split("_")

        self.mission = s2_product_tokens[0]
        self.product_level = s2_product_tokens[1]
        self.start_time = s2_product_tokens[2]
        self.start_time = datetime.datetime.strptime(s2_product_tokens[2], '%Y%m%dT%H%M%S')
        self.processing_baseline = s2_product_tokens[3]
        self.ROO = s2_product_tokens[4]
        self.tile_number = s2_product_tokens[5]
        self.product_id = os.path.splitext(s2_product_tokens[6])[0]
        self.format = os.path.splitext(s2_product_tokens[6])[1]

        # Product level
        # if os.path.join(self._zip_root, "L2A_Manifest.xml") in self._zipfile.namelist() or
        # self.manifest_safe_path = os.path.join(self.path, "L2A_Manifest.xml"):
        if self.product_level == "MSIL2A":
            self.manifest_safe_path = 'L2A_Manifest.xml'

        # elif os.path.join(self._zip_root, "manifest.safe") in self._zipfile.namelist() or
        # self.manifest_safe_path = os.path.join(self.path, "manifest.safe")
        elif self.product_level == "MSIL1C":
            self.manifest_safe_path = 'manifest.safe'

        else:
            raise Exception("Product level not supported. Only 'MSIL1C' and 'S2A' levels are supported.")

        # Get manifest
        if self.is_zip:
            self._zipfile = zipfile.ZipFile(self.path, 'r')
            self._zip_root = os.path.basename(filename)
            if self._zip_root not in self._zipfile.namelist():
                if not filename.endswith(".SAFE"):
                    self._zip_root = os.path.basename(filename) + ".SAFE/"
                else:
                    self._zip_root = os.path.basename(filename) + "/"
                if self._zip_root not in self._zipfile.namelist():
                    logging.exception("unknown zipfile structure")

            self.manifest_safe_path = os.path.join(self._zip_root, self.manifest_safe_path)

        else:
            self._zipfile = None
            self._zip_root = None
            # Find manifest.safe.
            self.manifest_safe_path = os.path.join(self.path, self.manifest_safe_path)

        if not os.path.isfile(self.manifest_safe_path) and self.manifest_safe_path not in self._zipfile.namelist():
            raise Exception("manifest.safe not found: %s" % self.manifest_safe_path)

    def __enter__(self):
        """Return self."""
        return self

    def __exit__(self, t, v, tb):
        """Do cleanup."""
        try:
            self._zipfile.close()
        except AttributeError:
            pass
