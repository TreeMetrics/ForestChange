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
    Forest change detection service
    Returns a .tif file with the forest areas where changes occurred.
    """

    def __init__(self):
        inputs = [
            LiteralInput(
                's2_product_dir',
                's2_product_dir',
                data_type='string',
                abstract="Path to directory containing two temporal Sentinel-2 products (newer and older)",
                min_occurs=1,
                max_occurs=1,
            ),
            LiteralInput(
                'change_threshold',
                'Change threshold 0-100',
                data_type='integer',
                abstract="Change threshold 0-100. Default is 20",
                min_occurs=1,
                max_occurs=1,
            ),
            LiteralInput(
                'additional_outputs',
                'Destination dir name',
                data_type='boolean',
                abstract="Full path to destination directory.",
                min_occurs=1,
                max_occurs=1,
                default=0,
            ),
        ]
        outputs = [
            LiteralOutput(
                'output',
                'ForestChange outputs',
                data_type='string',
                abstract="Directory containing the output generated by ForestChange.",
            )
        ]

        super(ForestChange, self).__init__(
            identifier='ForestChange',
            abstract="""
            Performs change detection analysis between two datasets.
            """,
            version='0.1',
            title="ForestChange",
            metadata=[Metadata('Raster')],
            profile='',
            inputs=inputs,
            outputs=outputs,
        )

    def get_command(self, request, response):
        """
        The service command that will be executed later. Do not do any processing here.
        
        Returns
        -------
        string with the path of a TIF file containing the forest change detection
            The service command to be executed.
                    
            s2_product_dir: Path to directory containing two temporal Sentinel-2 products (newer and older)
            change_threshold: Change threshold 0-100. Default is 30, data type=integer
            dest_dir: Full path to destination file name., data type=string
            output: ForestChange output
        """
        self.temp_path = tempfile.mkdtemp(dir=self.output_dir)
        logger.info('Tempdir: %s', self.temp_path)
        logger.info('Request inputs: %s', request.inputs)

        # Capture Forest Change output in a temp file
        return 'python  %s/forest_change_main.py -v 4 --tempdir %s Sentinel2 --s2_product_dir %s --threshold %s --additional_outputs %s -o %s' % (
            self._package_path,
            self.temp_path,
            self._get_input(request, 's2_product_dir'),
            self._get_input(request, 'change_threshold'),
            self._get_input(request, 'additional_outputs'),
            self.output_dir)

    def set_output(self, request, response):
        """Set the output in the WPS response."""
        response.outputs['output'].data = self.output_dir
        response.outputs['output'].uom = UOM('unity')
        # os.rmdir(self.temp_path)