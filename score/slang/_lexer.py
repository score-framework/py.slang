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

import enum
import logging
import ply.lex as lex
from ._common import tokens, ParseError


log = logging.getLogger(__name__)

# need "tokens" for PLY and the next line prevents "unused import" warnings:
tokens


class SyntaxError(ParseError):
    pass

states = (
    ('TAGSTART', 'exclusive'),
    ('TAG', 'exclusive'),
)

t_INITIAL_TEXT = r'[^\n{]+'

t_TAG_POSSIBLEINDENT = r'(?<=\n)[ ]+'


def t_INITIAL_TAG_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    return t


def t_INITIAL_TAG_TAGOPEN(t):
    r'\{'
    log.debug('push_state(TAGSTART)')
    t.lexer.push_state('TAGSTART')
    return t


def t_TAGSTART_TAGNAME(t):
    r'[^>{}]+'
    log.debug('pop_state()')
    t.lexer.pop_state()
    log.debug('push_state(TAG)')
    t.lexer.push_state('TAG')
    return t


t_TAG_TEXT = r'[^\n}>{]+'

t_TAG_TAGARGSEP = r'>'


def t_TAG_TAGCLOSE(t):
    r'\}'
    log.debug('pop_state()')
    t.lexer.pop_state()
    return t


def t_error(t):
    t.linepos = t.lexer.linepos
    raise SyntaxError(t, "Illegal input '%s'" % t.value)

t_TAGSTART_error = t_TAG_error = t_error


# --------------
# Indent support
# ------------------------------------------------------------------------------
# The code for indent tracking is inspired by the following:
# http://www.juanjoconti.com.ar/files/python/ply-examples/GardenSnake/GardenSnake.py.html
# ------------------------------------------------------------------------------

class Lexer:

    def __init__(self, *args, **kwargs):
        self.lexer = lex.lex(*args, **kwargs)

    def input(self, *args, **kwargs):
        self.lexer.input(*args, **kwargs)
        self.lexer.lineno = 1
        stream = iter(self.lexer.token, None)
        stream = self._tag_linepos(stream)
        stream = self._tag_constraints(stream)
        stream = self._emit_indents(stream)
        # need to tag linepos twice:
        # once before INDENT/DEDENT and once afterwards
        stream = self._tag_linepos(stream)
        stream = self._debug(stream)
        self.token_stream = stream

    def token(self):
        try:
            return next(self.token_stream)
        except StopIteration:
            return None

    def _debug(self, stream):
        for token in stream:
            log.debug(token)
            yield token

    def _tag_linepos(self, stream):
        indent = 1
        self.lexer.linepos = linepos = 1
        for token in stream:
            token.linepos = linepos
            if token.type == "NEWLINE":
                linepos = indent
            if token.type == "INDENT":
                indent += len(token.value)
                linepos = indent
            if token.type == "DEDENT":
                indent -= len(token.value)
                linepos = indent
            else:
                linepos += len(token.value)
            self.lexer.linepos = linepos
            yield token

    def _tag_constraints(self, stream):
        # Three INDENT states:
        #  0) no TAGARGSEP hence no need to indent
        #  1) "{x>y}" - TAGARGSEP but no need for an indent
        #  2) "{x>\n  y" - TAGARGSEP NEWLINE and must indent
        class Indent(enum.Enum):
            NO_INDENT = 0
            MAY_INDENT = 1
            MUST_INDENT = 2
        at_line_start = True
        indent = Indent.NO_INDENT
        for token in stream:
            token.at_line_start = at_line_start
            if token.type == "TAGARGSEP":
                at_line_start = False
                indent = Indent.MAY_INDENT
                token.must_indent = False
            elif token.type == "NEWLINE":
                at_line_start = True
                if indent == Indent.MAY_INDENT:
                    indent = Indent.MUST_INDENT
                token.must_indent = False
            elif token.type == "POSSIBLEINDENT":
                assert token.at_line_start
                at_line_start = True
                token.must_indent = False
            else:
                # A real token; only indent after TAGARGSEP NEWLINE
                if indent == Indent.MUST_INDENT:
                    token.must_indent = True
                else:
                    token.must_indent = False
                at_line_start = False
                indent = Indent.NO_INDENT
            yield token

    def _new_token(self, type, lineno, value=None):
        tok = lex.LexToken()
        tok.type = type
        tok.value = value
        tok.lineno = lineno
        tok.lexer = self.lexer
        tok.lexpos = self.lexer.lexpos
        return tok

    def DEDENT(self, lineno, value):
        return self._new_token("DEDENT", lineno, value)

    def INDENT(self, lineno, value):
        return self._new_token("INDENT", lineno, value)

    def _emit_indents(self, tokens):
        # A stack of indentation levels; will never pop item 0
        levels = [0]
        depth = 0
        prev_was_possibleindent = False
        for token in tokens:
            # POSSIBLEINDENT only occurs at the start of the line
            # There may be POSSIBLEINDENT followed by NEWLINE so
            # only track the depth here.  Don't indent/dedent
            # until there's something real.
            if token.type == "POSSIBLEINDENT":
                assert depth == 0
                depth = len(token.value)
                prev_was_possibleindent = True
                # POSSIBLEINDENT tokens are never emitted
                continue
            if token.type == "NEWLINE":
                depth = 0
                if prev_was_possibleindent or token.at_line_start:
                    # ignore blank lines
                    continue
                # pass the other cases on through
                yield token
                continue
            # it must be a real token (not POSSIBLEINDENT, not NEWLINE)
            # which can affect the indentation level
            prev_was_possibleindent = False
            if token.must_indent:
                # The current depth must be larger than the previous level
                if not (depth > levels[-1]):
                    raise SyntaxError(token, "Expected an indented block")
                levels.append(depth)
                yield self.INDENT(token.lineno, ' ' * (depth - levels[-2]))
            elif token.at_line_start:
                # Must be on the same level or one of the previous levels
                if depth == levels[-1]:
                    # At the same level
                    pass
                elif depth > levels[-1]:
                    raise SyntaxError(token, "Unexpected indent")
                else:
                    # Back up; but only if it matches a previous level
                    try:
                        i = levels.index(depth)
                    except ValueError:
                        raise SyntaxError(token, "Inconsistent indentation")
                    self.lexer.lexstatestack.reverse()
                    for _ in range(i + 1, len(levels)):
                        value = ' ' * (levels[-1] - levels[-2])
                        yield self.DEDENT(token.lineno, value)
                        levels.pop()
                        if self.lexer.current_state() == "TAG":
                            self.lexer.pop_state()
                        else:
                            self.lexer.lexstatestack.remove("TAG")
                    self.lexer.lexstatestack.reverse()
            yield token
        # Must dedent any remaining levels
        for _ in range(1, len(levels)):
            value = ' ' * (levels[-1] - levels[-2])
            yield self.DEDENT(token.lineno, value)
            self.lexer.pop_state()

    @property
    def lineno(self):
        return self.lexer.lineno

    @property
    def lexpos(self):
        return self.lexer.lexpos
