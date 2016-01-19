# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.test import TestCase
from test_app.models import A, AA, AB, BA, BB, CA, CB, CC, FK



class QueryCounts(TestCase):
    def test_complex_models_all_not_including_self(self):
        models = (AA, AB, BA, BB, CA, CB, CC)
        A._default_manager.create()
        FK._default_manager.create()
        for m in models:
            m._default_manager.create()

        with self.assertNumQueries(0):
            tuple(A.polymorphs.models(*models, include_self=False))

    def test_complex_models_all_including_self(self):
        models = (AA, AB, BA, BB, CA, CB, CC)
        A._default_manager.create()
        FK._default_manager.create()
        for m in models:
            m._default_manager.create()
        import pdb; pdb.set_trace()

        with self.assertNumQueries(0):
            tuple(A.polymorphs.models(*models, include_self=True))
