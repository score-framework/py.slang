# Copyright © 2015 STRG.AT GmbH, Vienna, Austria
#
# This file is part of the The SCORE Framework.
#
# The SCORE Framework and all its parts are free software: you can redistribute
# them and/or modify them under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation which is in the
# file named COPYING.LESSER.txt.
#
# The SCORE Framework and all its parts are distributed without any WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. For more details see the GNU Lesser General Public
# License.
#
# If you have not received a copy of the GNU Lesser General Public License see
# http://www.gnu.org/licenses/.
#
# The License-Agreement realised between you as Licensee and STRG.AT GmbH as
# Licenser including the issue of its valid conclusion and its pre- and
# post-contractual effects is governed by the laws of Austria. Any disputes
# concerning this License-Agreement including the issue of its valid conclusion
# and its pre- and post-contractual effects are exclusively decided by the
# competent court, in whose district STRG.AT GmbH has its registered seat, at
# the discretion of STRG.AT GmbH also the competent court, in whose district the
# Licensee has his registered seat, an establishment or assets.

import re
from ._common import ConfigurationError


class DocDefinition:

    def __init__(self, initial_tags, tags):
        self.initial_tags = initial_tags
        self.tags = tags
        # TODO: needs lots of validation here. See js implementation for some
        # inspiration.

    def tag(self, name):
        try:
            return next(t for t in self.tags if t.name == name)
        except StopIteration:
            return None


class TagDefinition:

    def __init__(self, name, children=['__text__'], *,
                 alias=None, nestable=False,
                 numargs=None, minargs=None, maxargs=None):
        if not alias:
            if not re.match(r'^[a-zA-Z0-9_]+$', name):
                raise ConfigurationError(
                    'Tag "%s" needs an alpha-numeric alias' % name)
            alias = name
        else:
            if not re.match(r'^[a-zA-Z0-9_]+$', alias):
                raise ConfigurationError(
                    'Alias "%s" is not alpha-numeric' % alias)
        self.name = name
        self.alias = alias
        if numargs is not None:
            minargs = numargs
            maxargs = numargs
        self.minargs = minargs
        self.maxargs = maxargs
        self.children = children
        if name in children:
            nestable = True
        self.nestable = nestable
        if self.minargs and not self.children:
            raise ConfigurationError('Tag "%s" must have arguments but has '
                                     'no children definition' % name)
