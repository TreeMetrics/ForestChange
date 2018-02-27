# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		analysis_parameters.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	management of parameters for analysis.

# COPYRIGHT:	(C) 2018 Treemetrics all rights reserved.
# ==========================================================================================


import logging
import os

from core import miscellaneous

from core.bunch import Config


class AnalysisParameters(object):

    def __init__(self):

        self.analysis_parameters_dir = Config()["analysis_parameters_dir"]

    def list_analysis_parameters(self):
        """ Find JSON in the parameter directory """

        setting_json_list = []
        for dirpath, dirnames, filenames in os.walk(self.analysis_parameters_dir):
            setting_json_list = [os.path.join(dirpath, f)
                                 for f in filenames
                                 if not f == 'settings_template.json'
                                 if os.path.splitext(f)[1].lower() == '.json']

        if not len(setting_json_list) >= 1:
            raise Exception('Analysis parameters JSON files cannot be found in the config directory. Aborting...')

        parametres = {}
        for json_file in setting_json_list:

            module_names = miscellaneous.read_json_file(json_file).keys()
            for module_name in module_names:
                module_name = str(module_name).lower()
                parametres[module_name] = {}

                for profile in miscellaneous.read_json_file(json_file)[str(module_name)].keys():
                    profile = str(profile).lower()

                    parametres[module_name][profile] = miscellaneous.read_json_file(json_file)[str(module_name)]

        return parametres

    def list_analysis_profiles(self):
        """ Find JSON in the parameter directory """

        parameters = self.list_analysis_parameters()

        profiles = {}
        for module in parameters.keys():
            profiles[module] = parameters[module].keys()

        return profiles

    def get_analysis_parameters(self, module_name, profile=None):
        # Find JSON in the parameter directory

        parameters = self.list_analysis_parameters()
        module_name = module_name.lower()

        if not module_name.lower() in parameters:
            logging.error('Analysis parameters module not found. Module:' + str(module_name))
            raise Exception('Analysis parameters module not found. Module:' + str(module_name))

        if not profile:
            profile = parameters[module_name].keys()[0]

        if profile in parameters[module_name]:

            return parameters[module_name][profile]

        else:
            logging.error('Analysis parameters profile not found. '
                          'Module:' + str(module_name) + '. Profile:' + str(profile))
