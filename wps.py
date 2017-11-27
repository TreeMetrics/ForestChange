"""
Treemetrics forest change detection eo4a service.
"""
import logging
import os
import tempfile

from pywps import LiteralInput, LiteralOutput, UOM
from pywps.app import EO4AProcess
from pywps.app.Common import Metadata


__author__ = "Cian Mac a' Bhaird"

logger = logging.getLogger('PYWPS')


class ForestChange(EO4AProcess):
    """
    forest change detection service
    
    Returns something (or not)
    """

    def __init__(self):
        inputs = [
            LiteralInput(
                's2_product_dir_newer',
                's2_product_dir_newer',
                data_type='string',
                abstract="Full path to Sentinel-2 product directory",
                min_occurs=1,
                max_occurs=1,
            ),
            LiteralInput(
                's2_product_dir_older',
                's2_product_dir_older',
                data_type='string',
                abstract="Full path to Sentinel-2 product directory",
                min_occurs=1,
                max_occurs=1,
            ),
            LiteralInput(
                'destfile',
                'Destination file name',
                data_type='string',
                abstract="Full path to destination file name.",
                min_occurs=1,
                max_occurs=1,
            ),
        ]
        outputs = [
            LiteralOutput(
                'output',
                'ForestChange output',
                data_type='string',
                abstract="Will contain any output generated by ForestChange.",
            )
        ]

        super(ForestChange, self).__init__(
            identifier='ForestChange',
            abstract="""
            Performs change detection analysis between two datasets.
            """,
            version='0.1',
            title="ForestChange",
            metadata=[Metadata('Sentinel')],
            profile='',
            inputs=inputs,
            outputs=outputs,
        )

    def get_command(self, request, response):
        """
        The service command that will be executed later. Do not do any processing here.
        
        Returns
        -------
        string with the path of a TIF file containing the vegetation detection
            The service command to be executed.
        """
        self.temp_path = tempfile.mkdtemp(dir=self.output_dir)
        logger.info('Tempdir: %s', self.temp_path)
        logger.info('Request inputs: %s', request.inputs)

        # Capture Forest Change output in a temp file
        return 'python  %s/forest_change.py --s2_product_dir_newer %s --s2_product_dir_older %s --tempdir %s -o %s' % (
            self._package_path,
            self._get_input(request, 's2_product_dir_newer'),
            self._get_input(request, 's2_product_dir_older'),
            self.temp_path, os.path.join(self.output_dir, self._get_input(request, 'destfile')))

    def set_output(self, request, response):
        """Set the output in the WPS response."""
        response.outputs['output'].data = os.path.join(self.output_dir, self._get_input(request, 'destfile'))
        response.outputs['output'].uom = UOM('unity')
        os.rmdir(self.temp_path)
