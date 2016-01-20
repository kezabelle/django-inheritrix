# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import pytest
from test_app.models import A, AA, AB, BA, BB, CA, CB, CC, FK


@pytest.mark.django_db
def test_single_child_model():
    for m in (A, CC, FK, AA):
        m._default_manager.create()
    results = tuple(A.polymorphs.select_related('fk').models(AA))
    assert tuple(results) == (AA(pk=3),)


@pytest.mark.django_db
def test_complex_models():
    for m in (A, CC, FK, AA):
        m._default_manager.create()
    results = A.polymorphs.select_related('fk').models(AA, CC).order_by('pk')
    assert tuple(results) == (CC(pk=2), AA(pk=3))



@pytest.mark.django_db
def test_complex_models_all():
    models = (AA, AB, BA, BB, CA, CB, CC)
    A._default_manager.create()
    FK._default_manager.create()
    for m in models:
        m._default_manager.create()
    results = A.polymorphs.models(*models, include_self=False)
    assert tuple(results) == (AA(pk=2), AB(pk=3), BA(pk=4), BB(pk=5),
                              CA(pk=6), CB(pk=7), CC(pk=8))


@pytest.mark.django_db
def test_complex_models_all_including_self():
    models = (AA, AB, BA, BB, CA, CB, CC)
    A._default_manager.create()
    FK._default_manager.create()
    for m in models:
        m._default_manager.create()
    results = A.polymorphs.models(*models, include_self=True)
    assert tuple(results) == (A(pk=1), AA(pk=2), AB(pk=3), BA(pk=4), BB(pk=5),
                              CA(pk=6), CB(pk=7), CC(pk=8))

@pytest.mark.django_db
def test_complex_models_a_bunch():
    models = (AA, CC)
    A._default_manager.create()
    FK._default_manager.create()
    for m in models:
        m._default_manager.create()
    results = A.polymorphs.models(AB, include_self=True).order_by('pk')
    # we didn't ask for CC or BB, so we'll never get more than an AB.
    assert tuple(results) == (A(pk=1), A(pk=2), AB(pk=3))
