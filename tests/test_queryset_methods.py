# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import pytest

from inheritrix import InvalidModel
from test_app.models import Jeff, JeffSon, JeffDaughter, JeffGrandSon, JeffGrandDaughter, JeffGreatGrandSon1, JeffGreatGrandSon2, JeffGreatGrandDaughter, RelatesToJeff


@pytest.mark.django_db
def test_single_child_model():
    for m in (Jeff, JeffGreatGrandDaughter, RelatesToJeff, JeffSon):
        m._default_manager.create()
    results = tuple(Jeff.polymorphs.select_related('fk').models(JeffSon))
    assert tuple(results) == (JeffSon(pk=3),)


@pytest.mark.django_db
def test_complex_models():
    for m in (Jeff, JeffGreatGrandDaughter, RelatesToJeff, JeffSon):
        m._default_manager.create()
    results = Jeff.polymorphs.select_related('fk').models(JeffSon, JeffGreatGrandDaughter).order_by('pk')
    assert tuple(results) == (JeffGreatGrandDaughter(pk=2), JeffSon(pk=3))



@pytest.mark.django_db
def test_complex_models_all():
    models = (JeffSon, JeffDaughter, JeffGrandSon, JeffGrandDaughter, JeffGreatGrandSon1, JeffGreatGrandSon2, JeffGreatGrandDaughter)
    Jeff._default_manager.create()
    RelatesToJeff._default_manager.create()
    for m in models:
        m._default_manager.create()
    results = Jeff.polymorphs.models(*models, include_self=False)
    assert tuple(results) == (JeffSon(pk=2), JeffDaughter(pk=3), JeffGrandSon(pk=4), JeffGrandDaughter(pk=5),
                              JeffGreatGrandSon1(pk=6), JeffGreatGrandSon2(pk=7), JeffGreatGrandDaughter(pk=8))


@pytest.mark.django_db
def test_complex_models_all_including_self():
    models = (JeffSon, JeffDaughter, JeffGrandSon, JeffGrandDaughter, JeffGreatGrandSon1, JeffGreatGrandSon2, JeffGreatGrandDaughter)
    Jeff._default_manager.create()
    RelatesToJeff._default_manager.create()
    for m in models:
        m._default_manager.create()
    results = Jeff.polymorphs.models(*models, include_self=True)
    assert tuple(results) == (Jeff(pk=1), JeffSon(pk=2), JeffDaughter(pk=3), JeffGrandSon(pk=4), JeffGrandDaughter(pk=5),
                              JeffGreatGrandSon1(pk=6), JeffGreatGrandSon2(pk=7), JeffGreatGrandDaughter(pk=8))


@pytest.mark.django_db
def test_complex_models_a_bunch():
    models = (JeffSon, JeffGreatGrandDaughter)
    Jeff._default_manager.create()
    RelatesToJeff._default_manager.create()
    for m in models:
        m._default_manager.create()
    results = Jeff.polymorphs.models(JeffDaughter, include_self=True).order_by('pk')
    # we didn't ask for JeffGreatGrandDaughter,
    # so we'll never get more than an JeffDaughter.
    assert tuple(results) == (Jeff(pk=1), Jeff(pk=2), JeffDaughter(pk=3))


@pytest.mark.django_db
def test_selecting_BA_doesnt_include_AA():
    """
    If not asking specifically for JeffSon, don't get them back ...
    """
    a = Jeff._default_manager.create()
    aa = JeffSon._default_manager.create()
    ba = JeffGrandSon._default_manager.create()
    results = list(Jeff.polymorphs.select_subclasses(JeffGrandSon))
    assert len(results) == 2
    assert isinstance(results[0], Jeff) is True
    assert isinstance(results[1], JeffGrandSon) is True


@pytest.mark.django_db
def test_selecting_just_me_does_the_right_thing():
    a = Jeff._default_manager.create()
    aa = JeffSon._default_manager.create()
    ba = JeffGrandSon._default_manager.create()
    results = list(Jeff.polymorphs.select_subclasses(Jeff))
    assert len(results) == 3
    assert isinstance(results[0], Jeff) is True
    assert isinstance(results[1], JeffSon) is False
    assert isinstance(results[2], JeffGrandSon) is False


@pytest.mark.django_db
def test_multiple_calls_to_select_subclasses_does_the_right_thing():
    a = Jeff._default_manager.create()
    aa = JeffSon._default_manager.create()
    ba = JeffGrandSon._default_manager.create()
    base = Jeff.polymorphs.select_subclasses(Jeff, JeffSon)
    with pytest.raises(InvalidModel):
        results = base.select_subclasses(Jeff)


@pytest.mark.django_db
def test_multiple_calls_does_the_right_thing():
    a = Jeff._default_manager.create()
    aa = JeffSon._default_manager.create()
    ba = JeffGrandSon._default_manager.create()
    base = Jeff.polymorphs.models(Jeff, JeffSon)
    with pytest.raises(InvalidModel):
        results = base.models(Jeff)


@pytest.mark.django_db
def test_values():
    a = Jeff._default_manager.create()
    aa = JeffSon._default_manager.create()
    ba = JeffGrandSon._default_manager.create()
    results = list(Jeff.polymorphs.models(Jeff, JeffSon, JeffGrandSon).values('pk', 'v'))
    assert results == [{'pk': 1, 'v': 0}, {'pk': 2, 'v': 0}, {'pk': 3, 'v': 0}]



@pytest.mark.django_db
def test_values_list():
    a = Jeff._default_manager.create()
    aa = JeffSon._default_manager.create()
    ba = JeffGrandSon._default_manager.create()
    results = list(Jeff.polymorphs.models(Jeff, JeffSon, JeffGrandSon).values_list('pk', 'v'))
    assert results == [(1, 0), (2, 0), (3, 0)]
