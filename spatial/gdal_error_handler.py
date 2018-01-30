
import logging

try:
    import gdal
    import gdal_array

except ImportError:
    from osgeo import gdal
    from osgeo import gdal_array

else:
    raise Exception('ERROR: Python bindings of GDAL 2.0.0 or later required')


# example GDAL error handler function
def gdal_error_handler(err_class, err_num, err_msg):
    errtype = {
            gdal.CE_None: 'None',
            gdal.CE_Debug: 'Debug',
            gdal.CE_Warning: 'Warning',
            gdal.CE_Failure: 'Failure',
            gdal.CE_Fatal: 'Fatal'
    }
    err_msg = err_msg.replace('\n', ' ')
    err_class = errtype.get(err_class, 'None')
    logging.error(str(err_class) + '. Error ' + str(err_num) + ':  ' + str(err_msg))

    # print 'Error Number: %s' % (err_num)
    # print 'Error Type: %s' % (err_class)
    # print 'Error Message: %s' % (err_msg)


def install_error_handler():

    # Enable GDAL/OGR exceptions
    gdal.UseExceptions()

    # install error handler
    gdal.PushErrorHandler(gdal_error_handler)

    # Raise a dummy error
    # gdal.Error(1, 2, 'test error')

    # uninstall error handler
    # gdal.PopErrorHandler()