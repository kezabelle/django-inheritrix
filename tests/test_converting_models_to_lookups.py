# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import pytest
from inheritrix import (discovery_lookup_from_model,
                        walk_from_model_to_root,
                        InvalidModel, generate_relation_combinations,
                        partition_lookups)
from test_app.models import A, AA, AB, BA, BB, CA, CB, CC


def test_model_is_subclass_ok():
    tuple(walk_from_model_to_root(A, AB))


def test_model_is_subclass_raises_error_on_invalid_model():
    class LOL(object):
        pass
    with pytest.raises(InvalidModel):
        tuple(walk_from_model_to_root(A, LOL))
    with pytest.raises(TypeError):
        tuple(walk_from_model_to_root(A, LOL))


def test_self():
    with pytest.raises(InvalidModel):
        discovery_lookup_from_model(A, A)

@pytest.mark.parametrize('model,expected', [
    (AA, ('aa',)),
    (AB, ('ab',)),
])
def test_child(model, expected):
    result = discovery_lookup_from_model(A, model)
    assert result == expected


@pytest.mark.parametrize('model,expected', [
    (BA, ('aa', 'ba')),
    (BB, ('ab', 'bb')),
])
def test_grandchild(model, expected):
    result = discovery_lookup_from_model(A, model)
    assert result == expected


@pytest.mark.parametrize('model,expected', [
    (CA, ('aa', 'ba', 'ca')),
    (CB, ('aa', 'ba', 'cb')),
    (CC, ('ab', 'bb', 'cc'))
])
def test_great_grandchild(model, expected):
    result = discovery_lookup_from_model(A, model)
    assert result == expected


@pytest.mark.parametrize(['indata', 'expected'], [
    (
        ('aa', 'ba', 'ca'),
        (('aa',), ('aa', 'ba'), ('aa', 'ba', 'ca'))
    ),
    (
        ('aa', 'bb', 'cc', 'dd'),
        ((u'aa',), (u'aa', u'bb'), (u'aa', u'bb', u'cc'), (u'aa', u'bb', u'cc', u'dd'))
    ),
    (
        ('aa', 'bb'),
        ((u'aa',), (u'aa', u'bb'))
    ),
    (
        ('aa',),
        ((u'aa',),)
    ),
    (
        (),
        ()
    ),
])
def test_generate_relation_combinations(indata, expected):
    assert generate_relation_combinations(lookup_parts=indata) == expected

@pytest.mark.parametrize(['lookups', 'expected'], [
    (
        ((u'ab', u'bb', u'cc'), (u'ab', u'bb'), (u'aa',), (u'ab',)),
        ((u'ab', u'bb', u'cc'), (u'ab', u'bb'), (u'aa',), (u'ab',)),
    )
])
def test_partition_lookups(lookups, expected):
    assert partition_lookups(lookups=lookups) == expected
