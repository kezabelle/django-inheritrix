# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import pytest
from inheritrix import (discovery_lookup_from_model,
                        walk_from_model_to_root,
                        InvalidModel, generate_relation_combinations,
                        lookups_to_text, relation_string_for_model)
from test_app.models import Jeff, JeffSon, JeffDaughter, JeffGrandSon, JeffGrandDaughter, JeffGreatGrandSon1, JeffGreatGrandSon2, JeffGreatGrandDaughter


def test_model_is_subclass_ok():
    tuple(walk_from_model_to_root(Jeff, JeffDaughter))


def test_model_is_subclass_raises_error_on_invalid_model():
    class LOL(object):
        pass
    with pytest.raises(InvalidModel):
        tuple(walk_from_model_to_root(Jeff, LOL))
    with pytest.raises(ValueError):
        tuple(walk_from_model_to_root(Jeff, LOL))


def test_self():
    result = discovery_lookup_from_model(Jeff, Jeff)
    assert result == ()

@pytest.mark.parametrize('model,expected', [
    (JeffSon, ('jeffson',)),
    (JeffDaughter, ('jeffdaughter',)),
])
def test_child(model, expected):
    result = discovery_lookup_from_model(Jeff, model)
    assert result == expected


@pytest.mark.parametrize('model,expected', [
    (JeffGrandSon, ('jeffson', 'jeffgrandson')),
    (JeffGrandDaughter, ('jeffdaughter', 'jeffgranddaughter')),
])
def test_grandchild(model, expected):
    result = discovery_lookup_from_model(Jeff, model)
    assert result == expected


@pytest.mark.parametrize('model,expected', [
    (JeffGreatGrandSon1, ('jeffson', 'jeffgrandson', 'jeffgreatgrandson1')),
    (JeffGreatGrandSon2, ('jeffson', 'jeffgrandson', 'jeffgreatgrandson2')),
    (JeffGreatGrandDaughter, ('jeffdaughter', 'jeffgranddaughter', 'jeffgreatgranddaughter'))
])
def test_great_grandchild(model, expected):
    result = discovery_lookup_from_model(Jeff, model)
    assert result == expected


@pytest.mark.parametrize(['indata', 'expected'], [
    (
        ('jeffson', 'jeffgrandson', 'jeffgreatgrandson1'),
        (('jeffson',), ('jeffson', 'jeffgrandson'), ('jeffson', 'jeffgrandson', 'jeffgreatgrandson1'))
    ),
    (
        ('jeffson', 'jeffgranddaughter', 'jeffgreatgranddaughter', 'dd'),
        (('jeffson',), ('jeffson', 'jeffgranddaughter'), ('jeffson', 'jeffgranddaughter', 'jeffgreatgranddaughter'), ('jeffson', 'jeffgranddaughter', 'jeffgreatgranddaughter', 'dd'))
    ),
    (
        ('jeffson', 'jeffgranddaughter'),
        (('jeffson',), ('jeffson', 'jeffgranddaughter'))
    ),
    (
        ('jeffson',),
        (('jeffson',),)
    ),
    (
        (),
        ()
    ),
])
def test_generate_relation_combinations(indata, expected):
    assert generate_relation_combinations(lookup_parts=indata) == expected


@pytest.mark.parametrize('model,expected', [
    (JeffSon, 'jeffson'),
    (JeffDaughter, 'jeffdaughter'),
    (JeffGrandSon, 'jeffson__jeffgrandson'),
    (JeffGrandDaughter, 'jeffdaughter__jeffgranddaughter'),
    (JeffGreatGrandSon1, 'jeffson__jeffgrandson__jeffgreatgrandson1'),
    (JeffGreatGrandSon2, 'jeffson__jeffgrandson__jeffgreatgrandson2'),
    (JeffGreatGrandDaughter, 'jeffdaughter__jeffgranddaughter__jeffgreatgranddaughter'),
])
def test_relation_tuples_from_root(model, expected):
    result = relation_string_for_model(Jeff, model)
    assert result == expected
