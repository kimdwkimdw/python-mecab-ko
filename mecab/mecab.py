from __future__ import annotations

from collections import namedtuple
from typing import List, NamedTuple, Optional, Tuple

import _mecab


def _create_lattice(sentence: str) -> _mecab.Lattice:
    lattice = _mecab.Lattice()
    lattice.add_request_type(_mecab.MECAB_ALLOCATE_SENTENCE)  # Required
    lattice.set_sentence(sentence)

    return lattice


def _parse_has_jongseong(value: str) -> Optional[bool]:
    if value == 'T':
        return True
    elif value == 'F':
        return False
    else:
        return None


class Feature(NamedTuple):
    pos: str
    semantic: str
    has_jongseong: bool
    reading: str
    type: str
    start_pos: str
    end_pos: str
    expression: str

    @classmethod
    def from_node(cls, node: _mecab.Node) -> Feature:
        # Reference:
        # - http://taku910.github.io/mecab/learn.html
        # - https://docs.google.com/spreadsheets/d/1-9blXKjtjeKZqsf4NzHeYJCrr49-nXeRF6D80udfcwY
        # - https://bitbucket.org/eunjeon/mecab-ko-dic/src/master/utils/dictionary/lexicon.py

        # feature = <pos>,<semantic>,<has_jongseong>,<reading>,<type>,<start_pos>,<end_pos>,<expression>
        values = node.feature.split(',')
        assert len(values) == 8

        values = [value if value != '*' else None for value in values]
        return cls(pos=values[0],
                   semantic=values[1],
                   has_jongseong=_parse_has_jongseong(values[2]),
                   reading=values[3],
                   type=values[4],
                   start_pos=values[5],
                   end_pos=values[6],
                   expression=values[7])

class MeCabError(Exception):
    pass


class MeCab:  # APIs are inspried by KoNLPy
    def __init__(self, dicpath: str = ''):
        argument = ''

        if dicpath != '':
            argument = '-d %s' % dicpath

        self.tagger = _mecab.Tagger(argument)

    def parse(self, sentence: str) -> List[Tuple[str, Feature]]:
        lattice = _create_lattice(sentence)
        if not self.tagger.parse(lattice):
            raise MeCabError(self.tagger.what())

        return [
            (node.surface, Feature.from_node(node))
            for node in lattice
        ]

    def pos(self, sentence: str) -> List[Tuple[str, str]]:
        return [
            (surface, feature.pos) for surface, feature in self.parse(sentence)
        ]

    def morphs(self, sentence: str) -> List[str]:
        return [
            surface for surface, _ in self.parse(sentence)
        ]

    def nouns(self, sentence: str) -> List[str]:
        return [
            surface for surface, feature in self.parse(sentence)
            if feature.pos.startswith('N')
        ]
