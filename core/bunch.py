# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		bunch.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module is a container for common process variables.

# COPYRIGHT:	(C) 2017 Treemetrics. All rights reserved.
# ==========================================================================================
"""  Manages common process settings, settings and other variables."""


import logging


class Config(object):
    """ Container for private variables related with the processing."""

    """Container to hold groups of objects or settings.

    Registry instances are used by several modules for various tasks.
    They have the following properties:

        - Collection: name of the group of variables (e.g., config, workspace)

        - A `members` property, which lists each item in the registry
        - A `default_members` function, which can be overridden to lazily
          initialize the members list
        - A call interface, allowing the instance to be used as a decorator
          for users to add new items to the registry in their config files
    """

    def __init__(self, collection='default', overwrite=False, init={}):

        self.overwrite = overwrite
        self.container = init

        if collection not in self.container:
            self.container[collection] = {}

        self.container = self.container[collection]

    def __setitem__(self, key, value):

        if key in self.container.keys():
            if not self.overwrite:
                logging.error(msg='Variable ' + str(key) + ' already exist.Use "overwrite" instead.')
                return

        self.container[key] = value

    def __getitem__(self, key):

        if key not in self.container.keys():
            logging.error(msg='Variable "' + str(key) + '" in not defined. Set variable fist.')
            return

        else:
            return self.container[key]

    def __delitem__(self, key):

        del self.container[key]
        return

    def __contains__(self, key):

        if key in self.container.keys():
            return True

    def __getstate__(self):
        return self.__dict__.items()

    def asdict(self):

        return self.container


class Bunch(object):
    """ Container for private variables related with the processing."""

    """Container to hold groups of objects or settings.

    Registry instances are used by several modules for various tasks.
    They have the following properties:

        - Collection: name of the group of variables (e.g., config, workspace)

        - A `members` property, which lists each item in the registry
        - A `default_members` function, which can be overridden to lazily
          initialize the members list
        - A call interface, allowing the instance to be used as a decorator
          for users to add new items to the registry in their config files
    """

    def __init__(self, collection='default', overwrite=False, init={}):

        self.overwrite = overwrite
        self.container = init

        if collection not in self.container:
            self.container[collection] = {}

        self.container = self.container[collection]

    def __setitem__(self, key, value):

        if key in self.container.keys():
            if not self.overwrite:
                logging.error(msg='Variable ' + str(key) + ' already exist.Use "overwrite" instead.')
                return

        self.container[key] = value

    def __getitem__(self, key):

        if key not in self.container.keys():
            logging.error(msg='Variable "' + str(key) + '" in not defined. Set variable fist.')
            return

        else:
            return self.container[key]

    def __delitem__(self, key):

        del self.container[key]
        return

    def __contains__(self, key):

        if key in self.container.keys():
            return True

    def __getstate__(self):
        return self.__dict__.items()

    def asdict(self):

        return self.container

    __getattr__ = __getitem__
    __setattr__ = __setitem__
    __delattr__ = __delitem__
