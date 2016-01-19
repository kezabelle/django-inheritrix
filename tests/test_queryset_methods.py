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
    assert results == 2


@pytest.mark.django_db
def test_complex_models():
    for m in (A, CC, FK, AA):
        m._default_manager.create()
    results = A.polymorphs.select_related('fk').models(AA, CC)
    assert results == 2



@pytest.mark.django_db
def test_complex_models_all():
    models = (AA, AB, BA, BB, CA, CB, CC)
    A._default_manager.create()
    FK._default_manager.create()
    for m in models:
        m._default_manager.create()
    results = A.polymorphs.models(*models, include_self=False)
    assert results == 2


@pytest.mark.django_db
def test_complex_models_all_including_self():
    models = (AA, AB, BA, BB, CA, CB, CC)
    A._default_manager.create()
    FK._default_manager.create()
    for m in models:
        m._default_manager.create()
    results = A.polymorphs.models(*models, include_self=True)
    assert results == 2
