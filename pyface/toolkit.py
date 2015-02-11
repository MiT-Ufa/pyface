#------------------------------------------------------------------------------
# Copyright (c) 2007, Riverbank Computing Limited
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
#------------------------------------------------------------------------------

# Standard library imports.
import os
import sys

# Enthought library imports.
from traits.etsconfig.api import ETSConfig


# This is set to the root part of the module path for the selected backend.
_toolkit_backend = None


def _init_toolkit():
    """ Initialise the current toolkit. """

    def import_toolkit(tk):
        try:
            # Try and import the toolkit's pyface backend init module.
            be = 'pyface.ui.%s.' % tk
            __import__(be + 'init')
        except:
            raise
        return be

    # Get the toolkit.
    ETSConfig.toolkit = 'qt4'
    be = import_toolkit(ETSConfig.toolkit)
    global _toolkit_backend
    _toolkit_backend = be


# Do this once then disappear.
_init_toolkit()
del _init_toolkit


def toolkit_object(name):
    """ Return the toolkit specific object with the given name.  The name
    consists of the relative module path and the object name separated by a
    colon.
    """

    mname, oname = name.split(':')
    be_mname = _toolkit_backend + mname

    class Unimplemented(object):
        """ This is returned if an object isn't implemented by the selected
        toolkit.  It raises an exception if it is ever instantiated.
        """

        def __init__(self, *args, **kwargs):
            raise NotImplementedError("the %s pyface backend doesn't implement %s" % (ETSConfig.toolkit, oname))

    be_obj = Unimplemented

    try:
        __import__(be_mname)

        try:
            be_obj = getattr(sys.modules[be_mname], oname)
        except AttributeError:
            pass
    except ImportError, e:

        # Ignore *ANY* errors unless a debug ENV variable is set.
        if 'ETS_DEBUG' in os.environ:

            # Attempt to only skip errors in importing the backend modules.
            # The idea here is that this only happens when the last entry in
            # the traceback's stack frame mentions the toolkit in question.
            import traceback
            frames = traceback.extract_tb(sys.exc_traceback)
            filename, lineno, function, text = frames[-1]
            if not _toolkit_backend in filename:
                raise

    return be_obj
