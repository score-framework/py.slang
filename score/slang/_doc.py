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

from ._common import ParseError


class Document:

    def __init__(self, docdef, args):
        self.docdef = docdef
        self.args = args
        self.validate()
        self.__xml = None

    def validate(self):
        for arg in self.args:
            if isinstance(arg, Text):
                text_allowed = '__text__' in self.docdef.initial_tags
                is_whitespace = re.match(r'^\s+$', str(arg))
                if not text_allowed and not is_whitespace:
                    raise ParseError(arg.token, 'Text not allowed at top level')
            else:
                if arg.name not in self.docdef.initial_tags:
                    raise ParseError(
                        arg.token,
                        'Tag "%s" not allowed at top level' % arg.name)
                arg.validate([])

    def q_one(self, query):
        result = self._xml.xpath(query)
        if not result:
            return None
        return self._q_result(result[0])

    q = q_one

    def q_all(self, query):
        return [self._q_result(x) for x in self._xml.xpath(query)]

    def _q_result(self, result):
        if isinstance(result, str):
            return result
        return self._node2data[result]

    @property
    def _xml(self):
        if self.__xml is not None:
            return self.__xml
        self._node2data = {}
        from lxml.builder import E
        def convert(thing):
            if isinstance(thing, Text):
                return str(thing)
            args = []
            for arg in thing.args:
                argnode = E('__arg__', *list(map(convert, arg)))
                self._node2data[argnode] = arg
                args.append(argnode)
            node = E(thing.tagdef.alias, *args)
            self._node2data[node] = thing
            return node
        self.__xml = E('__doc__', *list(map(convert, self.args)))
        self._node2data[self.__xml] = self
        # from lxml import etree
        # for element in self.__xml.iter():
        #     element.tail = None
        # print(etree.tostring(self.__xml, encoding='unicode',
        #                      pretty_print=True))
        return self.__xml

    def __str__(self):
        return ''.join(map(str, self.args))


class Text:

    def __init__(self, docdef, token, string):
        self.docdef = docdef
        self.token = token
        self.string = string

    def __str__(self):
        return self.string

    def __repr__(self):
        return '<Text %s>' % repr(self.string)


class Tag:

    def __init__(self, docdef, token, name, args=[]):
        self.docdef = docdef
        self.token = token
        self.name = name
        self.build_args(args)

    def build_args(self, args):
        self.args = []
        # combine consecutive Text values to single Text objects
        for arg in args:
            self.args.append([])
            textparts = []
            def appendtext():
                nonlocal textparts
                if not textparts:
                    return
                token = textparts[0].token
                string = ''.join(map(str, textparts))
                self.args[-1].append(Text(self.docdef, token, string))
                textparts = []
            for argpart in arg:
                if isinstance(argpart, Text):
                    textparts.append(argpart)
                else:
                    appendtext()
                    self.args[-1].append(argpart)
            appendtext()

    def validate(self, tagstack):
        tagdef = self._set_tagdef(tagstack)
        t = self.token
        if tagdef.minargs is not None and len(self.args) < tagdef.minargs:
            raise ParseError(t, 'Tag "%s" requires at least %d arguments' %
                             (self.name, tagdef.minargs))
        if tagdef.maxargs is not None and len(self.args) > tagdef.maxargs:
            if not tagdef.maxargs:
                msg = 'Tag "%s" must not have any arguments' % self.name
            else:
                msg = 'Tag "%s" must not have more than %d arguments' % \
                    (self.name, tagdef.maxargs)
            raise ParseError(t, msg)
        if not self.tagdef.nestable:
            if any(tag for tag in tagstack if tag.tagdef == self.tagdef):
                msg = 'Tag "%s" must not be nested' % self.name
                raise ParseError(t, msg)
        try:
            tagstack.append(self)
            for arg in self.args:
                for argpart in arg:
                    if isinstance(argpart, Tag):
                        argpart.validate(tagstack)
        finally:
            tagstack.pop()

    def _set_tagdef(self, tagstack):
        if not tagstack:
            tagdef = self.docdef.tag(self.name)
        else:
            valid = tagstack[-1].tagdef.children
            try:
                name = next(t for t in valid if t.endswith('>' + self.name))
                tagdef = self.docdef.tag(name)
            except StopIteration:
                tagdef = self.docdef.tag(self.name)
                if tagdef and tagdef.name not in valid:
                    msg = 'Tag "%s" not allowed inside "%s" tags' % \
                        (self.name, tagstack[-1].tagdef.name)
                    raise ParseError(self.token, msg)
        if not tagdef:
            msg = 'Tag "%s" invalid' % self.name
            raise ParseError(self.token, msg)
        self.tagdef = tagdef
        return tagdef

    def __str__(self):
        result = '{%s' % self.name
        for arg in self.args:
            result += '>' + ''.join(map(str, arg))
        return result.rstrip() + '}'

    def __repr__(self):
        return '<Tag %s>' % self.name
