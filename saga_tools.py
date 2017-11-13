# ! /usr/bin/env python

import os
import logging

import saga_api

import gdal_reader

# sys.path.append('/home/puter/forestspatial/trash/dependencies_old/saga-2.1.0/src/saga_core/saga_api')
# saga_lib_path = '/usr/lib/x86_64-linux-gnu/saga'

# Check SAGA version
version = saga_api.SAGA_API_Get_Version()

if not str(saga_api.SAGA_API_Get_Version()).split()[-1] == '2.2.7':
    raise Exception('SAGA GIS version 2.2.7 required. SAGA version ' + str(version) + ' found.')


os.environ['SAGA_MLB'] = '/usr/lib/x86_64-linux-gnu/saga'


# load all module libraries from a directory at once:
if os.name == 'nt':    # Windows
    saga_api.SG_Get_Module_Library_Manager().Add_Directory(os.environ['SAGA_32'], False)
else:                  # Linux
    saga_api.SG_Get_Module_Library_Manager().Add_Directory(os.environ['SAGA_MLB'], False)

# print '__________________'
# print 'number of loaded libraries: ' + str(saga_api.SG_Get_Module_Library_Manager().Get_Count())
# print saga_api.SG_Get_Module_Library_Manager().Get_Summary(saga_api.SG_SUMMARY_FMT_FLAT_NO_INTERACTIVE).c_str()
# print '__________________'


def is_grid(input_grid):
    """ Check raster data
    :param input_grid: unknown source data
    :return: True, False
    """

    # Check gdal
    if gdal_reader.isvalid(input_grid):
        return False

    # Check SAGA
    try:
        #saga_api.CSG_Grid(input_grid)
        input_grid.Get_Extent()

    except:
        raise Exception('Unknown data source ' + str(input_grid))

    return True


def gdal2saga(fgdal):
    # load just the needed module library:
    # if os.name == 'nt':  # Windows
    #    saga_api.SG_Get_Module_Library_Manager().Add_Library(os.environ['SAGA_32'] + '/modules/io_gdal.dll')
    # else:  # Linux
    #    saga_api.SG_Get_Module_Library_Manager().Add_Library(os.environ['SAGA_MLB'] + '/libio_gdal.so')

    logging.debug('Starting gdal2saga...')

    s_gdal = saga_api.CSG_String(fgdal)
    m = saga_api.SG_Get_Module_Library_Manager().Get_Module(saga_api.CSG_String('io_gdal'), 0)
    logging.debug(m.Get_Description().c_str())

    p = m.Get_Parameters()
    p(saga_api.CSG_String('FILES')).Set_Value(s_gdal)

    if m.Execute() == 0:
        logging.error('Error executing module [' + m.Get_Name().c_str() + ']')
        raise Exception('Error executing module [' + m.Get_Name().c_str() + ']')
        return 0

    grid = p(saga_api.CSG_String('GRIDS')).asGrid()

    logging.debug('success')
    return grid


def saga2gdal(input_grid, fgdal_path):

    logging.debug('Starting fgdal_path...')

    m = saga_api.SG_Get_Module_Library_Manager().Get_Module(saga_api.CSG_String('io_gdal'), 1)
    logging.debug(m.Get_Description().c_str())

    p = m.Get_Parameters()
    p(saga_api.CSG_String('GRIDS')).Set_Value(input_grid)
    p(saga_api.CSG_String('FILE')).Set_Value(saga_api.CSG_String(fgdal_path))
    p(saga_api.CSG_String('FORMAT')).Set_Value(1)
    p(saga_api.CSG_String('TYPE')).Set_Value(0)
    p(saga_api.CSG_String('SET_NODATA')).Set_Value(0)
    p(saga_api.CSG_String('NODATA')).Set_Value(0)

    if m.Execute() == 0:
        logging.error('Error executing module [' + m.Get_Name().c_str() + ']')
        return 0

    if not os.path.exists(fgdal_path):
        logging.error(input_grid.Get_File_Name())
        return 0

    logging.debug('success')
    return fgdal_path


def fast_representativeness(input_grid, lod=1, output=None):
    """http://www.saga-gis.org/saga_tool_doc/2.2.0/statistics_grid_0.html"""

    logging.debug('Starting fast_representativeness...')

    # Check input grid format
    if not is_grid(input_grid):
        input_grid = gdal2saga(input_grid)

    # Get fast_representativeness
    m = saga_api.SG_Get_Module_Library_Manager().Get_Module(saga_api.CSG_String('statistics_grid'), 0)
    logging.debug(m.Get_Description().c_str())

    p = m.Get_Parameters()
    p(saga_api.CSG_String('INPUT')).Set_Value(input_grid)
    #p(saga_api.CSG_String('LOD')).Set_Value(lod)

    if m.Execute() == 0:
        logging.error('Error executing module [' + m.Get_Name().c_str() + ']')

        raise Exception('Error executing module [' + m.Get_Name().c_str() + ']')
        return 0

    raise Exception('error2')

    seeds_grid = p(saga_api.CSG_String('SEEDS')).asGrid()

    raise Exception('test')

    # grid = p(saga_api.CSG_String('RESULT_LOD')).asGrid()
    # grid = p(saga_api.CSG_String('RESULT')).asGrid()

    if output:
        saga2gdal(seeds_grid, output)
        return output

    logging.debug('success')
    return seeds_grid


def region_growing(input_grid, output, seeds_method='representativeness', threshold=0):
    """http://saga-gis.sourceforge.net/saga_tool_doc/2.2.7/imagery_segmentation_3.html"""

    # Check input grid format
    if not is_grid(input_grid):
        input_grid = gdal2saga(input_grid)

    logging.debug('Starting region_growing...')

    # Get Seeds
    if seeds_method == 'representativeness':
        seeds_grid = fast_representativeness(input_grid, lod=1)

    raise Exception('eee')

    #grids_list = saga_api.CSG_Parameter_Grid_List(None, input_grid.Get_Type())
    #grids_list.Add_Item(input_grid)


    # Get Image segmentation
    m = saga_api.SG_Get_Module_Library_Manager().Get_Module(saga_api.CSG_String('imagery_segmentation'), 3)
    logging.debug(m.Get_Description().c_str())

    p = m.Get_Parameters()

    p('SEEDS').asGridList().Add_Item(input_grid)

    #p(saga_api.CSG_String('SEEDS')).Set_Value(seeds_grid)
    p(saga_api.CSG_String('FEATURES')).Set_Value(grids_list)
    p(saga_api.CSG_String('NEIGHBOUR')).Set_Value(1)
    p(saga_api.CSG_String('METHOD')).Set_Value(1)
    p(saga_api.CSG_String('THRESHOLD')).Set_Value(threshold)

    if m.Execute() == 0:
        logging.error('Error executing module [' + m.Get_Name().c_str() + ']')
        return 0

    segments_grid = p(saga_api.CSG_String('Segments')).asGrid()

    # grid = p(saga_api.CSG_String('Similarity')).asGrid()
    # grid = p(saga_api.CSG_String('Seeds')).asGrid()

    segments = saga2gdal(segments_grid, output)

    logging.debug('success')
    return segments
