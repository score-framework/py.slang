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

import ply.yacc as yacc

from ._common import tokens, ParseError
from ._doc import Tag, Text, Document
import threading


# need "tokens" for PLY and the next line prevents "unused import" warnings:
tokens


def p_document(p):
    'document : block'
    p[0] = Document(p.parser.docdef, p[1])


def p_block(p):
    'block : blockcontent'
    p[0] = [p[1]]


def p_block_continuation(p):
    'block : blockcontent block'
    p[0] = [p[1]] + p[2]


def p_block_text(p):
    'blockcontent : text'
    p[0] = p[1]


def p_block_taglist(p):
    'blockcontent : tag'
    p[0] = p[1]


def p_text(p):
    '''text : TEXT
            | NEWLINE
            | POSSIBLEINDENT'''
    # POSSIBLEINDENT is actually never emitted, but PLY
    # will complain if it is not used anywhere.
    p[0] = Text(p.parser.docdef, p.slice[1], p[1])


def p_tag_simple(p):
    'tag : TAGOPEN TAGNAME TAGCLOSE'
    p[0] = Tag(p.parser.docdef, p.slice[1], p[2])


def p_tag_withemptyarg(p):
    'tag : TAGOPEN TAGNAME TAGARGSEP TAGCLOSE'
    p[0] = Tag(p.parser.docdef, p.slice[1], p[2], [[]])


def p_tag_withargs(p):
    'tag : TAGOPEN TAGNAME TAGARGSEP arglist TAGCLOSE'
    p[0] = Tag(p.parser.docdef, p.slice[1], p[2], p[4])


def p_tag_withblockarg(p):
    'tag : TAGOPEN TAGNAME TAGARGSEP NEWLINE INDENT block DEDENT'
    p[0] = Tag(p.parser.docdef, p.slice[1], p[2], [p[6]])


def p_tag_withargsandblockarg(p):
    'tag : TAGOPEN TAGNAME TAGARGSEP arglist TAGARGSEP NEWLINE ' \
        'INDENT block DEDENT'
    p[0] = Tag(p.parser.docdef, p.slice[1], p[2], p[4] + [p[8]])


def p_arglist_leaf(p):
    'arglist : arg'
    p[0] = [p[1]]


def p_arglist(p):
    'arglist : arglist TAGARGSEP arg'
    p[0] = p[1] + [p[3]]


def p_arg(p):
    'arg : argpart'
    p[0] = [p[1]]


def p_arg_continuation(p):
    'arg : argpart arg'
    p[0] = [p[1]] + p[2]


def p_argpart_text(p):
    'argpart : TEXT'
    p[0] = Text(p.parser.docdef, p.slice[1], p[1])


def p_argpart_tag(p):
    'argpart : tag'
    p[0] = p[1]


# Error rule for syntax errors
def p_error(t):
    if t is None:
        raise ParseError(None, 'Unexpected end of input')
    raise ParseError(t, 'Unexpected Token "%s"' % t.type)


# PLY is not thread safe :-(
parse_lock = threading.Lock()


def create(docdef, threadsafe=False):
    from ._lexer import Lexer
    # lexer = Lexer()
    parser = yacc.yacc(debug=False)  # debug=False prevents file `parser.out'
    original_parse = parser.parse
    if threadsafe:
        def parse(self, *args, **kwargs):
            with parse_lock:
                kwargs['lexer'] = Lexer()
                return original_parse(*args, **kwargs)
    else:
        def parse(self, *args, **kwargs):
            kwargs['lexer'] = Lexer()
            return original_parse(*args, **kwargs)
    parser.parse = parse.__get__(parser)
    parser.docdef = docdef
    return parser


__all__ = ['create']
