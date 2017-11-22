# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		bunch.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module contains Saga GIS utils.

# COPYRIGHT:	(C) 2017 Treemetrics. All rights reserved.
# ==========================================================================================
""" This module runs Saga Gis utilities adapted to the Forest Spatial requirements. """

import os
from miscellaneous import cmd
from bunch import Config

import logging
import gdal_reader as gdalr


'''
Usage of saga_cmd:
saga_cmd [-h, --help]
saga_cmd [-v, --version]
saga_cmd [-b, --batch]
saga_cmd [-d, --docs]
saga_cmd [-f, --flags][=qrsilpx][-c, --cores][=#] <LIBRARY> <MODULE> <OPTIONS>
saga_cmd [-f, --flags][=qrsilpx][-c, --cores][=#] <SCRIPT>
[-h], [--help]   : help on usage
[-v], [--version]: report version information
[-b], [--batch]  : create a batch file example
[-d], [--docs]   : create module documentation in current working directory
[-c], [--cores]  : number of physical processors to use for computation
[-f], [--flags]  : various flags for general usage [qrsilpx]
q              : no progress report
r              : no messages report
s              : silent mode (no progress and no messages report)
i              : allow user interaction
l              : load translation dictionary
p              : load projections dictionary
x              : use XML markups for synopses and messages
<LIBRARY>        : name of the library
<MODULE>         : either name or index of the module
<OPTIONS>        : module specific options
<SCRIPT>         : saga cmd script file with one or more module calls

Example:
saga_cmd -f=s ta_lighting 0 -ELEVATION=c:\dem.sgrd  -SHADE=c:\shade.sgrd
'''


def _saga_cmd(*args):
    # New saga compatibility ("lib" is missing in libraries)
    arguments = ' '.join(args)

    # version = cmd(os.path.join(Config()['saga_cmd'] + ' -v'))

    # Final command
    command = str(Config()['saga_cmd']) + " " + str(arguments)

    # Silent mode
    # command = str(Config()['saga_cmd']) + ' --flags=s' + " " + str(arguments)

    # Call cmd shell
    cmd(command)


class Saga(object):
    def __init__(self):
        """ common variables """

        # self.raster_db = Db(rtype='_raster', overwrite=True)
        # self.vector_db = Db(rtype='_vector', overwrite=True)

        tempdir = Config()['tempdir']
        self.tempdir = os.path.join(tempdir, 'SAGA')

        if not os.path.exists(self.tempdir):
            os.makedirs(self.tempdir)

    def _gdal2saga(self, ds, name=None, overwrite=None):
        """Import multispectral imagery in SAGA and return a dictionary wiht the different bands files."""

        ds_path = ds.GetMetadataItem('FilePath')
        if not name:
            name = os.path.splitext(os.path.basename(ds_path))[0]

        grid_path = os.path.join(self.tempdir, name + '.sgrd')

        if os.path.exists(grid_path):
            if overwrite:
                os.remove(grid_path)

            else:
                logging.error('SAGA import _raster. File already exist.')

        if gdalr.isvalid(ds):
            grid_name = os.path.join(self.tempdir, name)

            # Create output dictionary
            dic_bands = {}

            # _saga_cmd('libio_gdal "GDAL: Import Raster" -GRIDS:"' + grid + '" -FILES="' + raster + '"') #-TRANSFORM

            bands = ds.RasterCount
            for i in xrange(1, bands+1):
                cmd("gdal_translate -of SAGA -b", str(i), '"' + ds_path + '" "' + grid_name + "_" + str(i) + '.sdat"')

                if os.path.exists(grid_name + "_" + str(i) + ".sgrd"):
                    dic_bands[str(i)] = grid_name + "_" + str(i) + ".sgrd"


            return dic_bands

        else:
            logging.error('SAGA import _raster. Format unknown.')

    def _saga2gdal(self, grid_file, epsg=None, output=None):
        """Re-project _raster to srs"""

        grid_file = os.path.splitext(grid_file)[0] + '.sdat'
        if not os.path.exists(grid_file):
            logging.error('SAGA import _raster. File cannot be found.')

        if not output:
            output = os.path.splitext(grid_file)[0] + '.tif'

        cmd('gdal_translate', '-of "GTiff" -a_srs epsg:"' + str(epsg) + '"', '"' + grid_file + '"', '"' + output + '"')

        if not os.path.exists(output):
            logging.error('SAGA import _raster. Output not created.')
            return

        return output

    def _import2saga(self, input_file):

        if os.path.exists(str(input_file)):
            file_ext = os.path.splitext(input_file)[0]

            if file_ext is '.sgrd':
                return input_file

            elif file_ext is '.sdat':
                return os.path.splitext(input_file)[0] + '.sgrd'

            else:
                if gdalr.isvalid(input_file):
                    return self._gdal2saga(input_file)

                else:
                    logging.error('Error importing file to SAGA. Format unknown.')
                    return

        # Check python objecT in the memory
        try:
            input_file.ds

        except:
            logging.error('Error importing object to SAGA. Format unknown.')
            return

        # Create .sgrd file
        name = os.path.splitext(os.path.basename(input_file.filename))[0]
        if not name:
            name = 'grid'

        grid_path = os.path.join(self.tempdir, name)

        dic_bands = {}
        for i in xrange(1, input_file.bands + 1):
            grid_path_i = str(os.path.splitext(grid_path)[0]) + "_" + str(i) + ".sgrd"
            grid = gdalr.py2gdal(py_raster=input_file, file_path=grid_path_i)

            if not grid or not os.path.exists(grid):
                logging.error('SAGA import _raster. Issue found writing ' + str(grid))
                return

            dic_bands[str(i)] = os.path.splitext(grid)[0] + ".sgrd"

        return dic_bands

    def _saga2output(self, sgrd_file, output=None):
        """ Provide the right format to SAGA outputs"""

        if output:
            # OP1: GDAL
            return self._saga2gdal(grid_file=sgrd_file, output=output)  # epsg=epsg,

        elif not output:
            # OP2: Python
            return gdalr.gdal_import(os.path.splitext(sgrd_file)[0] + '.sdat')

        else:
            logging.error('Error _saga2output. Format unknown.')
            return

    def region_growing(self, rlist, seeds=None, output=None, threshold=0, lod=1):
        """Segments multiband grids/images by using the Region Growing algorithm."""

        tempdir = self.tempdir

        gridlist = []
        for raster in rlist:
            grid_bands_dict = self._import2saga(raster)

            for grid in grid_bands_dict.values():
                gridlist.append(grid)

        cmd_list = ';'.join(gridlist)

        # Get seeds
        mask = os.path.join(tempdir, 'mask.sgrd')
        gseeds = os.path.join(tempdir, 'seeds.sgrd')

        if not seeds:
            # Create Seeds from raster
            representativeness = os.path.join(tempdir, 'representativeness.sgrd')
            surface = os.path.join(tempdir, 'surface.sgrd')

            _saga_cmd('statistics_grid 0 -INPUT="' + gridlist[0] + '" -RESULT="' + representativeness +
                      '" -RESULT_LOD="' + surface + '" -SEEDS="' + gseeds + '" -LOD=' + str(lod))

            # Create mask
            _saga_cmd('grid_tools 15', '-INPUT="' + gridlist[0] + '" -RESULT="' + mask +
                      '" -METHOD=0 -OLD=-100 -NEW=1 -SOPERATOR=3')

            # Mask seeds
            _saga_cmd('grid_tools 24', '-GRID:"' + gseeds + '"', '-MASK:"' + mask + '"', '-MASKED:"' + gseeds + '"')

        elif seeds:
            # _saga_cmd('libio_gdal "GDAL: Import Raster" -GRIDS:"' + gseeds + '" -FILES:"' + seeds + '"')
            grid_seeds = self._gdal2saga(seeds.ds, 'grid_seeds')

            # Value to 1
            _saga_cmd('grid_tools 15', '-INPUT="' + gseeds + '" -RESULT="' + grid_seeds +
                      '" -METHOD=0 -OLD=-100 -NEW=1 -SOPERATOR=3')

        else:
            logging.error('region_growing. Seeds are not defined')

        # Segmentation
        outgrid = os.path.join(tempdir, 'segments.sgrd')
        outgrid1 = os.path.join(tempdir, 'Similarity.sgrd')
        outgrid2 = os.path.join(tempdir, 'table.dbf')


        _saga_cmd('imagery_segmentation 3 -SEEDS="' + gseeds + '" -FEATURES="' + cmd_list +
                  '" -SEGMENTS="' + outgrid + '" -SIMILARITY="' + outgrid1 + '" -TABLE="' + outgrid2 +
                  '" -METHOD=1 -NEIGHBOUR=1 -SIG_1=1 -SIG_2=1 -THRESHOLD=' + str(threshold) + ' -LEAFSIZE=256')

        # _saga_cmd('libio_gdal 2 -GRIDS="' + outgrid + '" -FILE="' + output + '"')
        # _saga_cmd('libshapes_grid 6 -GRID="Segments.sgrd" -POLYGONS="Segments.shp" -CLASS_ALL=1 -CLASS_ID= -SPLIT=1')

        _saga_cmd('', 'grid_tools 24', '-GRID:"' + outgrid + '"', '-MASK:"' + mask + '"', '-MASKED:"' + outgrid + '"')

        return self._saga2output(sgrd_file=outgrid, output=output)
