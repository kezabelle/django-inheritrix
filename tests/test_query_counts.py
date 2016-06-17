# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.test import TestCase
from test_app.models import A, AA, AB, BA, BB, CA, CB, CC
from test_app.models import FK, FK2, FK3, FK4, FK5, FK6, FK7, FK8


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


class RelationQueryCounts(TestCase):
    def test_not_doing_any_prefetching_related_via_children(self):
        with self.assertNumQueries(39):
            fk = FK.objects.create()
            fk2 = FK2.objects.create()
            fk3 = FK3.objects.create()
            fk4 = FK4.objects.create()
            fk5 = FK5.objects.create()
            fk6 = FK6.objects.create()
            fk7 = FK7.objects.create()
            fk8 = FK8.objects.create()
            pk_a = A._default_manager.create(fk=fk).pk
            pk_aa = AA._default_manager.create(fk2=fk2).pk
            pk_ab = AB._default_manager.create(fk=fk, fk3=fk3).pk
            pk_ba = BA._default_manager.create(fk2=fk2, fk4=fk4).pk
            pk_bb = BB._default_manager.create(fk3=fk3, fk5=fk5).pk
            pk_ca = CA._default_manager.create(fk4=fk4, fk2=fk2, fk6=fk6).pk
            pk_cb = CB._default_manager.create(fk4=fk4, fk2=fk2, fk7=fk7).pk
            pk_cc = CC._default_manager.create(fk3=fk3, fk5=fk5, fk8=fk8).pk


        with self.assertNumQueries(2):
            a = A._default_manager.get(pk=pk_a)
            assert a.fk == fk

        with self.assertNumQueries(2):
            aa = AA._default_manager.get(pk=pk_aa)
            assert aa.fk2 == fk2
            assert aa.fk is None

        with self.assertNumQueries(3):
            ab = AB._default_manager.get(pk=pk_ab)
            assert ab.fk3 == fk3
            assert ab.fk == fk

        with self.assertNumQueries(3):
            ba = BA._default_manager.get(pk=pk_ba)
            assert ba.fk4 == fk4
            assert ba.fk2 == fk2
            assert ba.fk is None

        with self.assertNumQueries(3):
            bb = BB._default_manager.get(pk=pk_bb)
            assert bb.fk5 == fk5
            assert bb.fk3 == fk3
            assert bb.fk is None

        with self.assertNumQueries(4):
            ca = CA._default_manager.get(pk=pk_ca)
            assert ca.fk6 == fk6
            assert ca.fk2 == fk2
            assert ca.fk4 == fk4
            assert ca.fk is None

        with self.assertNumQueries(4):
            cb = CB._default_manager.get(pk=pk_cb)
            assert cb.fk7 == fk7
            assert cb.fk2 == fk2
            assert cb.fk4 == fk4
            assert cb.fk is None

        with self.assertNumQueries(4):
            cc = CC._default_manager.get(pk=pk_cc)
            assert cc.fk8 == fk8
            assert cc.fk5 == fk5
            assert cc.fk3 == fk3
            assert cc.fk is None

    def test_select_related_is_unaffected(self):
        with self.assertNumQueries(39):
            fk = FK.objects.create()
            fk2 = FK2.objects.create()
            fk3 = FK3.objects.create()
            fk4 = FK4.objects.create()
            fk5 = FK5.objects.create()
            fk6 = FK6.objects.create()
            fk7 = FK7.objects.create()
            fk8 = FK8.objects.create()
            pk_a = A._default_manager.create(fk=fk).pk
            pk_aa = AA._default_manager.create(fk2=fk2).pk
            pk_ab = AB._default_manager.create(fk=fk, fk3=fk3).pk
            pk_ba = BA._default_manager.create(fk2=fk2, fk4=fk4).pk
            pk_bb = BB._default_manager.create(fk3=fk3, fk5=fk5).pk
            pk_ca = CA._default_manager.create(fk4=fk4, fk2=fk2, fk6=fk6).pk
            pk_cb = CB._default_manager.create(fk4=fk4, fk2=fk2, fk7=fk7).pk
            pk_cc = CC._default_manager.create(fk3=fk3, fk5=fk5, fk8=fk8).pk


        with self.assertNumQueries(1):
            a = A.polymorphs.select_related('fk').get(pk=pk_a)
            assert a.fk == fk

        with self.assertNumQueries(1):
            prefetches = ('aa__fk2', 'aa__fk')
            aa = A.polymorphs.select_subclasses(AA).select_related(*prefetches).get(pk=pk_aa)
            assert aa.fk2 == fk2
            assert aa.fk is None

        with self.assertNumQueries(1):
            prefetches = ('ab__fk3', 'ab__fk')
            ab = A.polymorphs.select_subclasses(AB).select_related(*prefetches).get(pk=pk_ab)
            assert ab.fk3 == fk3
            assert ab.fk == fk

        with self.assertNumQueries(1):
            prefetches = ('aa__ba__fk4', 'aa__ba__fk2', 'aa__ba__fk')
            ba = A.polymorphs.select_subclasses(BA).select_related(*prefetches).get(pk=pk_ba)
            assert ba.fk4 == fk4
            assert ba.fk2 == fk2
            assert ba.fk is None

        with self.assertNumQueries(1):
            prefetches = ('ab__bb__fk5', 'ab__bb__fk3', 'ab__bb__fk')
            bb = A.polymorphs.select_subclasses(BB).select_related(*prefetches).get(pk=pk_bb)
            assert bb.fk5 == fk5
            assert bb.fk3 == fk3
            assert bb.fk is None

        with self.assertNumQueries(1):
            prefetches = (
            'aa__ba__ca__fk6', 'aa__ba__ca__fk2', 'aa__ba__ca__fk4',
            'aa__ba__ca__fk')
            ca = A.polymorphs.select_subclasses(CA).select_related(*prefetches).get(pk=pk_ca)
            assert ca.fk6 == fk6
            assert ca.fk2 == fk2
            assert ca.fk4 == fk4
            assert ca.fk is None

        with self.assertNumQueries(1):
            prefetches = (
            'aa__ba__cb__fk7', 'aa__ba__cb__fk2', 'aa__ba__cb__fk4',
            'aa__ba__cb__fk')
            cb = A.polymorphs.select_subclasses(CB).select_related(*prefetches).get(pk=pk_cb)
            assert cb.fk7 == fk7
            assert cb.fk2 == fk2
            assert cb.fk4 == fk4
            assert cb.fk is None

        with self.assertNumQueries(1):
            prefetches = (
            'ab__bb__cc__fk5', 'ab__bb__cc__fk8', 'ab__bb__cc__fk3',
            'ab__bb__cc__fk')
            cc = A.polymorphs.select_subclasses(CC).select_related(*prefetches).get(pk=pk_cc)
            assert cc.fk8 == fk8
            assert cc.fk5 == fk5
            assert cc.fk3 == fk3
            assert cc.fk is None


    def test_prefetch_related(self):
        with self.assertNumQueries(39):
            fk = FK.objects.create()
            fk2 = FK2.objects.create()
            fk3 = FK3.objects.create()
            fk4 = FK4.objects.create()
            fk5 = FK5.objects.create()
            fk6 = FK6.objects.create()
            fk7 = FK7.objects.create()
            fk8 = FK8.objects.create()
            pk_a = A._default_manager.create(fk=fk).pk
            pk_aa = AA._default_manager.create(fk2=fk2).pk
            pk_ab = AB._default_manager.create(fk=fk, fk3=fk3).pk
            pk_ba = BA._default_manager.create(fk2=fk2, fk4=fk4).pk
            pk_bb = BB._default_manager.create(fk3=fk3, fk5=fk5).pk
            pk_ca = CA._default_manager.create(fk4=fk4, fk2=fk2, fk6=fk6).pk
            pk_cb = CB._default_manager.create(fk4=fk4, fk2=fk2, fk7=fk7).pk
            pk_cc = CC._default_manager.create(fk3=fk3, fk5=fk5, fk8=fk8).pk


        with self.assertNumQueries(2):
            a = A.polymorphs.get(pk=pk_a)
            assert a.fk == fk

        with self.assertNumQueries(1):
            prefetches = ('aa__fk2', 'aa__fk')
            aa = A.polymorphs.select_subclasses(AA).prefetch_related(*prefetches).get(pk=pk_aa)
            assert aa.fk2 == fk2
            assert aa.fk is None

        with self.assertNumQueries(1):
            prefetches = ('ab__fk3', 'ab__fk')
            ab = A.polymorphs.select_subclasses(AB).prefetch_related(*prefetches).get(pk=pk_ab)
            assert ab.fk3 == fk3
            assert ab.fk == fk

        with self.assertNumQueries(1):
            prefetches = ('aa__ba__fk4', 'aa__ba__fk2', 'aa__ba__fk')
            ba = A.polymorphs.select_subclasses(BA).prefetch_related(*prefetches).get(pk=pk_ba)
            assert ba.fk4 == fk4
            assert ba.fk2 == fk2
            assert ba.fk is None

        with self.assertNumQueries(1):
            prefetches = ('ab__bb__fk5', 'ab__bb__fk3', 'ab__bb__fk')
            bb = A.polymorphs.select_subclasses(BB).prefetch_related(*prefetches).get(pk=pk_bb)
            assert bb.fk5 == fk5
            assert bb.fk3 == fk3
            assert bb.fk is None

        with self.assertNumQueries(1):
            prefetches = (
            'aa__ba__ca__fk6', 'aa__ba__ca__fk2', 'aa__ba__ca__fk4',
            'aa__ba__ca__fk')
            ca = A.polymorphs.select_subclasses(CA).prefetch_related(*prefetches).get(pk=pk_ca)
            assert ca.fk6 == fk6
            assert ca.fk2 == fk2
            assert ca.fk4 == fk4
            assert ca.fk is None

        with self.assertNumQueries(1):
            prefetches = (
            'aa__ba__cb__fk7', 'aa__ba__cb__fk2', 'aa__ba__cb__fk4',
            'aa__ba__cb__fk')
            cb = A.polymorphs.select_subclasses(CB).prefetch_related(*prefetches).get(pk=pk_cb)
            assert cb.fk7 == fk7
            assert cb.fk2 == fk2
            assert cb.fk4 == fk4
            assert cb.fk is None

        with self.assertNumQueries(1):
            prefetches = (
            'ab__bb__cc__fk5', 'ab__bb__cc__fk8', 'ab__bb__cc__fk3',
            'ab__bb__cc__fk')
            cc = A.polymorphs.select_subclasses(CC).prefetch_related(*prefetches).get(pk=pk_cc)
            assert cc.fk8 == fk8
            assert cc.fk5 == fk5
            assert cc.fk3 == fk3
            assert cc.fk is None

