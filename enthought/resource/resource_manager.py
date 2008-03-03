#------------------------------------------------------------------------------
# Copyright (c) 2005, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: Enthought, Inc.
# Description: <Enthought resource package component>
#------------------------------------------------------------------------------
""" The default resource manager.

A resource manager locates and loads application resources such as images and
sounds etc.

"""


# Standard library imports.
import glob, inspect, operator, os
from os.path import join
from zipfile import is_zipfile, ZipFile

# Enthought library imports.
from enthought.traits.api import HasTraits, Instance
from enthought.util.resource import get_path

# Local imports.
from resource_factory import ResourceFactory
from resource_reference import ImageReference


class ResourceManager(HasTraits):
    """ The default resource manager.

    A resource manager locates and loads application resources such as images
    and sounds etc.

    """

    # Allowed extensions for image resources.
    IMAGE_EXTENSIONS = ['.png', '.jpg', '.bmp', '.gif', '.ico']

    # The resource factory is responsible for actually creating resources.
    # This is used so that (for example) different GUI toolkits can create
    # a images in the format that they require.
    resource_factory = Instance(ResourceFactory)

    ###########################################################################
    # 'ResourceManager' interface.
    ###########################################################################

    def locate_image(self, image_name, path, size=None):
        """ Locates an image. """

        if not operator.isSequenceType(path):
            path = [path]

        resource_path = []
        for item in path:
            if isinstance(item, basestring):
                resource_path.append(item)

            else:
                resource_path.extend(self._get_resource_path(item))

        return self._locate_image(image_name, resource_path, size)

    def load_image(self, image_name, path, size=None):
        """ Loads an image. """

        reference = self.locate_image(image_name, path, size)
        if reference is not None:
            image = reference.load()

        else:
            image = None

        return image

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _locate_image(self, image_name, resource_path, size):
        """ Attempts to locate an image resource.

        If the image is found, an image resource reference is returned.
        If the image is NOT found None is returned.

        """

        # If the image name contains a file extension (eg. '.jpg') then we will
        # only accept an an EXACT filename match.
        basename, extension = os.path.splitext(image_name)
        if len(extension) > 0:
            extensions = [extension]
            pattern = image_name

        # Otherwise, we will search for common image suffixes.
        else:
            extensions = self.IMAGE_EXTENSIONS
            pattern = image_name + '.*'

        for dirname in resource_path:
            # Try the 'images' sub-directory first (since that is commonly
            # where we put them!).  If the image is not found there then look
            # in the directory itself.
            if size is None:
                subdirs = ['images', '']

            else:
                subdirs = ['images/%dx%d' % (size[0], size[1]), 'images', '']

            for path in subdirs:
                # Is there anything resembling the image name in the directory?
                filenames = glob.glob(join(dirname, path, pattern))
                for filename in filenames:
                    not_used, extension = os.path.splitext(filename)
                    if extension in extensions:
                        reference = ImageReference(
                            self.resource_factory, filename=filename
                        )

                        return reference

            # Is there an 'images' zip file in the directory?
            zip_filename = join(dirname, 'images.zip')
            if os.path.isfile(zip_filename):
                zip_file = ZipFile(zip_filename, 'r')
                # Try the image name itself, and then the image name with
                # common images suffixes.
                for extension in extensions:
                    try:
                        image_data = zip_file.read(basename + extension)
                        reference = ImageReference(
                            self.resource_factory, data=image_data
                        )

                        return reference

                    except:
                        pass

            # is this a path within a zip file?
            # first, find the zip file in the path
            filepath = dirname
            zippath = ''
            while not is_zipfile(filepath) and \
                  os.path.splitdrive(filepath)[1] != '\\' \
                  and os.path.splitdrive(filepath)[1] != '/':
                filepath, tail = os.path.split(filepath)
                if zippath != '':
                    zippath = tail + '/' + zippath
                else:
                    zippath = tail

            # if we found a zipfile, then look inside it for the image!
            if is_zipfile(filepath):

                zip_file = ZipFile(filepath)
                for subpath in ['images', '']:
                    for extension in extensions:
                        try:
                            # this is a little messy. since zip files don't
                            # recognize a leading slash, we have to be very
                            # particular about how we build this path when
                            # there are empty strings
                            if zippath != '':
                                path = zippath + '/'
                            else:
                                path = ''

                            if subpath != '':
                                path = path + subpath + '/'

                            path = path + basename + extension
                            # now that we have the path we can attempt to load
                            # the image
                            image_data = zip_file.read(path)
                            reference = ImageReference(
                                self.resource_factory, data=image_data
                                )

                            # if there was no exception then return the result
                            return reference

                        except:
                            pass

        return None

    def _get_resource_path(self, object):
        """ Returns the resource path for an object. """

        if hasattr(object, 'resource_path'):
            resource_path = object.resource_path

        else:
            resource_path = self._get_default_resource_path(object)

        return resource_path

    def _get_default_resource_path(self, object):
        """ Returns the default resource path for an object. """

        resource_path = []
        for klass in inspect.getmro(object.__class__):
            try:
                resource_path.append(get_path(klass))

            # We get an attribute error when we get to a C extension type (in
            # our case it will most likley be 'CHasTraits'.  We simply ignore
            # everything after this point!
            except AttributeError:
                break

        return resource_path

#### EOF ######################################################################
