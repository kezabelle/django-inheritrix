# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.test import TestCase
from test_app.models import A, AA, AB, BA, BB, CA, CB, CC, FK, FK2


class QueryCounts(TestCase):
    def test_complex_models_all_not_including_self(self):
        models = (AA, AB, BA, BB, CA, CB, CC)

        with self.assertNumQueries(32):
            A._default_manager.create()
            FK._default_manager.create()
            for m in models:
                m._default_manager.create()

        with self.assertNumQueries(1):
            tuple(A.polymorphs.models(*models, include_self=False))

    def test_complex_models_all_including_self(self):
        models = (AA, AB, BA, BB, CA, CB, CC)

        with self.assertNumQueries(32):
            A._default_manager.create()
            FK._default_manager.create()
            for m in models:
                m._default_manager.create()

        with self.assertNumQueries(1):
            tuple(A.polymorphs.models(*models, include_self=True))

    def test_resetting(self):
        models = (AA, AB, BA, BB, CA, CB, CC)

        with self.assertNumQueries(32):
            A._default_manager.create()
            FK._default_manager.create()
            for m in models:
                m._default_manager.create()

        with self.assertRaises(ValueError):
            tuple(A.polymorphs.select_related('fk').models(*models, include_self=False).models(None))

    def test_prefetching_related_via_children(self):
        models = (AA, CB)

        with self.assertNumQueries(23):
            A._default_manager.create()
            for m in models:
                m._default_manager.create()
            for x in range(1, 3):
                fkx = FK2._default_manager.create()
                CC._default_manager.create(fk2=fkx)


        with self.assertNumQueries(2):
            query = A.polymorphs.models(CC, *models).prefetch_related('ab__bb__cc__fk')
            results = tuple(query)
            assert query._prefetch_related_lookups == ['ab__bb__cc__fk']
            assert results[0] == AA(pk=2)
            assert results[1] == CB(pk=3)
            assert results[2] == CC(pk=4)
            assert results[3] == CC(pk=5)
            # these should not trigger queries
            assert results[2].fk2 == FK2(pk=1)
            assert results[3].fk2 == FK2(pk=2)

