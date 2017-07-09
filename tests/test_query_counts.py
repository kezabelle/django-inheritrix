# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from unittest import expectedFailure
from django.db.models import Prefetch
from django.test import TestCase

from test_app.models import (Jeff, JeffSon, JeffDaughter, JeffGrandSon, JeffGrandDaughter, JeffGreatGrandSon1, JeffGreatGrandSon2, JeffGreatGrandDaughter)
from test_app.models import RelatesToJeff, RelatesToJeffSon, RelatesToJeffDaughter, RelatesToJeffGrandSon, RelatesToJeffGrandDaughter, RelatesToGreatGrandSon1, RelatesToGreatGrandSon2, RelatesToGreatGrandDaughter


class QueryCounts(TestCase):
    def test_complex_models_all_not_including_self(self):
        models = (JeffSon, JeffDaughter, JeffGrandSon, JeffGrandDaughter, JeffGreatGrandSon1, JeffGreatGrandSon2, JeffGreatGrandDaughter)

        with self.assertNumQueries(32):
            Jeff._default_manager.create()
            RelatesToJeff._default_manager.create()
            for m in models:
                m._default_manager.create()

        with self.assertNumQueries(1):
            tuple(Jeff.polymorphs.models(*models, include_self=False))

    def test_complex_models_all_including_self(self):
        models = (JeffSon, JeffDaughter, JeffGrandSon, JeffGrandDaughter, JeffGreatGrandSon1, JeffGreatGrandSon2, JeffGreatGrandDaughter)

        with self.assertNumQueries(32):
            Jeff._default_manager.create()
            RelatesToJeff._default_manager.create()
            for m in models:
                m._default_manager.create()

        with self.assertNumQueries(1):
            tuple(Jeff.polymorphs.models(*models, include_self=True))

    def test_selecting_just_me_does_the_right_thing(self):
        models = (Jeff,)

        with self.assertNumQueries(3):
            Jeff._default_manager.create()
            RelatesToJeff._default_manager.create()
            for m in models:
                m._default_manager.create()

        with self.assertNumQueries(1):
            x = tuple(Jeff.polymorphs.models(include_self=True))
        self.assertEqual([
            Jeff(pk=1),
            Jeff(pk=2),
            ], list(x))


class SanityChecksTestCase(TestCase):
    def test_cc_prefetch_related(self):
        """
        proving to myself how prefetching from the grandchild works.
        """
        with self.assertNumQueries(9):
            fk3 = RelatesToJeffDaughter.objects.create()
            fk8 = RelatesToGreatGrandDaughter.objects.create()
            fk5 = RelatesToJeffGrandDaughter.objects.create()
            out = JeffGreatGrandDaughter._default_manager.create(fk3=fk3, fk5=fk5, fk8=fk8, fk=None)
        # 1 CC query + 1 each for fk3,fk5,fk8
        with self.assertNumQueries(4):
            list(JeffGreatGrandDaughter.objects.prefetch_related('fk3', 'fk5', 'fk8').filter(pk=out))


class RelationQueryCounts(TestCase):
    def test_not_doing_any_prefetching_related_via_children(self):
        with self.assertNumQueries(39):
            fk = RelatesToJeff.objects.create()
            fk2 = RelatesToJeffSon.objects.create()
            fk3 = RelatesToJeffDaughter.objects.create()
            fk4 = RelatesToJeffGrandSon.objects.create()
            fk5 = RelatesToJeffGrandDaughter.objects.create()
            fk6 = RelatesToGreatGrandSon1.objects.create()
            fk7 = RelatesToGreatGrandSon2.objects.create()
            fk8 = RelatesToGreatGrandDaughter.objects.create()
            pk_a = Jeff._default_manager.create(fk=fk).pk
            pk_aa = JeffSon._default_manager.create(fk2=fk2).pk
            pk_ab = JeffDaughter._default_manager.create(fk=fk, fk3=fk3).pk
            pk_ba = JeffGrandSon._default_manager.create(fk2=fk2, fk4=fk4).pk
            pk_bb = JeffGrandDaughter._default_manager.create(fk3=fk3, fk5=fk5).pk
            pk_ca = JeffGreatGrandSon1._default_manager.create(fk4=fk4, fk2=fk2, fk6=fk6).pk
            pk_cb = JeffGreatGrandSon2._default_manager.create(fk4=fk4, fk2=fk2, fk7=fk7).pk
            pk_cc = JeffGreatGrandDaughter._default_manager.create(fk3=fk3, fk5=fk5, fk8=fk8).pk


        with self.assertNumQueries(2):
            a = Jeff._default_manager.get(pk=pk_a)
            assert a.fk == fk

        with self.assertNumQueries(2):
            aa = JeffSon._default_manager.get(pk=pk_aa)
            assert aa.fk2 == fk2
            assert aa.fk is None

        with self.assertNumQueries(3):
            ab = JeffDaughter._default_manager.get(pk=pk_ab)
            assert ab.fk3 == fk3
            assert ab.fk == fk

        with self.assertNumQueries(3):
            ba = JeffGrandSon._default_manager.get(pk=pk_ba)
            assert ba.fk4 == fk4
            assert ba.fk2 == fk2
            assert ba.fk is None

        with self.assertNumQueries(3):
            bb = JeffGrandDaughter._default_manager.get(pk=pk_bb)
            assert bb.fk5 == fk5
            assert bb.fk3 == fk3
            assert bb.fk is None

        with self.assertNumQueries(4):
            ca = JeffGreatGrandSon1._default_manager.get(pk=pk_ca)
            assert ca.fk6 == fk6
            assert ca.fk2 == fk2
            assert ca.fk4 == fk4
            assert ca.fk is None

        with self.assertNumQueries(4):
            cb = JeffGreatGrandSon2._default_manager.get(pk=pk_cb)
            assert cb.fk7 == fk7
            assert cb.fk2 == fk2
            assert cb.fk4 == fk4
            assert cb.fk is None

        with self.assertNumQueries(4):
            cc = JeffGreatGrandDaughter._default_manager.get(pk=pk_cc)
            assert cc.fk8 == fk8
            assert cc.fk5 == fk5
            assert cc.fk3 == fk3
            assert cc.fk is None

    def test_select_related_is_unaffected(self):
        with self.assertNumQueries(39):
            fk = RelatesToJeff.objects.create()
            fk2 = RelatesToJeffSon.objects.create()
            fk3 = RelatesToJeffDaughter.objects.create()
            fk4 = RelatesToJeffGrandSon.objects.create()
            fk5 = RelatesToJeffGrandDaughter.objects.create()
            fk6 = RelatesToGreatGrandSon1.objects.create()
            fk7 = RelatesToGreatGrandSon2.objects.create()
            fk8 = RelatesToGreatGrandDaughter.objects.create()
            pk_a = Jeff._default_manager.create(fk=fk).pk
            pk_aa = JeffSon._default_manager.create(fk2=fk2).pk
            pk_ab = JeffDaughter._default_manager.create(fk=fk, fk3=fk3).pk
            pk_ba = JeffGrandSon._default_manager.create(fk2=fk2, fk4=fk4).pk
            pk_bb = JeffGrandDaughter._default_manager.create(fk3=fk3, fk5=fk5).pk
            pk_ca = JeffGreatGrandSon1._default_manager.create(fk4=fk4, fk2=fk2, fk6=fk6).pk
            pk_cb = JeffGreatGrandSon2._default_manager.create(fk4=fk4, fk2=fk2, fk7=fk7).pk
            pk_cc = JeffGreatGrandDaughter._default_manager.create(fk3=fk3, fk5=fk5, fk8=fk8).pk


        with self.assertNumQueries(1):
            a = Jeff.polymorphs.select_related('fk').get(pk=pk_a)
            assert a.fk == fk

        with self.assertNumQueries(1):
            prefetches = ('jeffson__fk2', 'jeffson__fk')
            aa = Jeff.polymorphs.select_subclasses(JeffSon).select_related(*prefetches).get(pk=pk_aa)
            assert aa.fk2 == fk2
            assert aa.fk is None

        with self.assertNumQueries(1):
            prefetches = ('jeffdaughter__fk3', 'jeffdaughter__fk')
            ab = Jeff.polymorphs.select_subclasses(JeffDaughter).select_related(*prefetches).get(pk=pk_ab)
            assert ab.fk3 == fk3
            assert ab.fk == fk

        with self.assertNumQueries(1):
            prefetches = ('jeffson__jeffgrandson__fk4', 'jeffson__jeffgrandson__fk2', 'jeffson__jeffgrandson__fk')
            ba = Jeff.polymorphs.select_subclasses(JeffGrandSon).select_related(*prefetches).get(pk=pk_ba)
            assert ba.fk4 == fk4
            assert ba.fk2 == fk2
            assert ba.fk is None

        with self.assertNumQueries(1):
            prefetches = ('jeffdaughter__jeffgranddaughter__fk5', 'jeffdaughter__jeffgranddaughter__fk3', 'jeffdaughter__jeffgranddaughter__fk')
            bb = Jeff.polymorphs.select_subclasses(JeffGrandDaughter).select_related(*prefetches).get(pk=pk_bb)
            assert bb.fk5 == fk5
            assert bb.fk3 == fk3
            assert bb.fk is None

        with self.assertNumQueries(1):
            prefetches = (
            'jeffson__jeffgrandson__jeffgreatgrandson1__fk6', 'jeffson__jeffgrandson__jeffgreatgrandson1__fk2', 'jeffson__jeffgrandson__jeffgreatgrandson1__fk4',
            'jeffson__jeffgrandson__jeffgreatgrandson1__fk')
            ca = Jeff.polymorphs.select_subclasses(JeffGreatGrandSon1).select_related(*prefetches).get(pk=pk_ca)
            assert ca.fk6 == fk6
            assert ca.fk2 == fk2
            assert ca.fk4 == fk4
            assert ca.fk is None

        with self.assertNumQueries(1):
            prefetches = (
            'jeffson__jeffgrandson__jeffgreatgrandson2__fk7', 'jeffson__jeffgrandson__jeffgreatgrandson2__fk2', 'jeffson__jeffgrandson__jeffgreatgrandson2__fk4',
            'jeffson__jeffgrandson__jeffgreatgrandson2__fk')
            cb = Jeff.polymorphs.select_subclasses(JeffGreatGrandSon2).select_related(*prefetches).get(pk=pk_cb)
            assert cb.fk7 == fk7
            assert cb.fk2 == fk2
            assert cb.fk4 == fk4
            assert cb.fk is None

        with self.assertNumQueries(1):
            prefetches = (
            'jeffdaughter__jeffgranddaughter__jeffgreatgranddaughter__fk5', 'jeffdaughter__jeffgranddaughter__jeffgreatgranddaughter__fk8', 'jeffdaughter__jeffgranddaughter__jeffgreatgranddaughter__fk3',
            'jeffdaughter__jeffgranddaughter__jeffgreatgranddaughter__fk')
            cc = Jeff.polymorphs.select_subclasses(JeffGreatGrandDaughter).select_related(*prefetches).get(pk=pk_cc)
            assert cc.fk8 == fk8
            assert cc.fk5 == fk5
            assert cc.fk3 == fk3
            assert cc.fk is None


    def test_copies_down_to_lowest(self):
        with self.assertNumQueries(9):
            fk = RelatesToJeff.objects.create()
            fk2 = RelatesToJeffSon.objects.create()
            root = Jeff._default_manager.create(fk=fk)
            child = JeffGreatGrandSon1._default_manager.create(fk=fk, fk2=fk2)
        with self.assertNumQueries(2):
            only = Jeff.polymorphs.models(JeffGreatGrandSon1).prefetch_related('m2m').select_related('fk')[0]
            matches = only.m2m
            self.assertEqual(set(matches.all()), set())
            self.assertEqual(only.fk, fk)
        self.assertIsInstance(only, JeffSon)
        self.assertIsInstance(only, JeffGreatGrandSon1)


    @expectedFailure
    def test_prefetch_related(self):
        """
        one query for all A children, then 1 each for each of the FKs.
        """
        with self.assertNumQueries(45):
            fk = RelatesToJeff.objects.create()
            fk2 = RelatesToJeffSon.objects.create()
            fk3 = RelatesToJeffDaughter.objects.create()
            fk4 = RelatesToJeffGrandSon.objects.create()
            fk5 = RelatesToJeffGrandDaughter.objects.create()
            fk6 = RelatesToGreatGrandSon1.objects.create()
            fk7 = RelatesToGreatGrandSon2.objects.create()
            fk8 = RelatesToGreatGrandDaughter.objects.create()
            pk_a = Jeff._default_manager.create(fk=fk).pk
            pk_aa = JeffSon._default_manager.create(fk2=fk2).pk
            pk_ab = JeffDaughter._default_manager.create(fk=fk, fk3=fk3).pk
            pk_ba = JeffGrandSon._default_manager.create(fk2=fk2, fk4=fk4).pk
            pk_bb = JeffGrandDaughter._default_manager.create(fk3=fk3, fk5=fk5).pk
            pk_ca = JeffGreatGrandSon1._default_manager.create(fk4=fk4, fk2=fk2, fk6=fk6).pk
            pk_cb = JeffGreatGrandSon2._default_manager.create(fk4=fk4, fk2=fk2, fk7=fk7).pk
            pk_cc = JeffGreatGrandDaughter._default_manager.create(fk3=fk3, fk5=fk5, fk8=fk8).pk
            pk_cc2 = JeffGreatGrandDaughter._default_manager.create(fk3=fk3, fk5=fk5, fk8=fk8).pk

        with self.assertNumQueries(2):
            a = Jeff.polymorphs.get(pk=pk_a)
            assert a.fk == fk

        with self.assertNumQueries(3):
            prefetches = {
                JeffSon: ('fk2', 'fk'),
            }
            results = list(Jeff.polymorphs.select_subclasses(JeffSon).prefetch_models(prefetches).all())
            the_aas = results[1], results[3], results[5], results[6]
            for aa in the_aas:
                assert aa.fk2 == fk2
                assert aa.fk is None

        with self.assertNumQueries(3):
            prefetches = {
                JeffDaughter: ('fk3', 'fk'),
            }
            results = list(Jeff.polymorphs.select_subclasses(JeffDaughter).prefetch_models(prefetches).all())
            ab = results[2]
            assert ab.fk3 == fk3
            assert ab.fk == fk
            the_abs = results[4], results[7], results[8]
            for ab in the_abs:
                assert ab.fk3 == fk3
                assert ab.fk is None

        with self.assertNumQueries(4):
            prefetches = {
                JeffGrandSon: ('fk4', 'fk2', 'fk'),
            }
            ba = Jeff.polymorphs.select_subclasses(JeffGrandSon).prefetch_models(prefetches).get(pk=pk_ba)
            assert ba.fk4 == fk4
            assert ba.fk2 == fk2
            assert ba.fk is None
        #
        with self.assertNumQueries(4):
            prefetches = {
                JeffGrandDaughter: ('fk5', 'fk3', 'fk'),
            }
            bb = Jeff.polymorphs.select_subclasses(JeffGrandDaughter).prefetch_models(prefetches).get(pk=pk_bb)
            assert bb.fk5 == fk5
            assert bb.fk3 == fk3
            assert bb.fk is None

        with self.assertNumQueries(5):
            prefetches = {
                JeffGreatGrandSon1: ('fk6', 'fk2', 'fk4', 'fk'),
            }
            ca = Jeff.polymorphs.select_subclasses(JeffGreatGrandSon1).prefetch_models(prefetches).get(pk=pk_ca)
            assert ca.fk6 == fk6
            assert ca.fk2 == fk2
            assert ca.fk4 == fk4
            assert ca.fk is None

        with self.assertNumQueries(5):
            prefetches = {
                JeffGreatGrandSon2: ('fk7', 'fk2', 'fk4', 'fk'),
            }
            cb = Jeff.polymorphs.select_subclasses(JeffGreatGrandSon2).prefetch_models(prefetches).get(pk=pk_cb)
            assert cb.fk7 == fk7
            assert cb.fk2 == fk2
            assert cb.fk4 == fk4
            assert cb.fk is None

        with self.assertNumQueries(8):
            a_prefetch = Prefetch('fk8', RelatesToGreatGrandDaughter.objects.all())
            prefetches = {
                JeffGreatGrandDaughter: ('fk5', a_prefetch, 'fk3', 'fk'),
                JeffGrandDaughter: ('fk5', 'fk3'),
            }
            results = list(Jeff.polymorphs.models(JeffGrandDaughter, JeffGreatGrandDaughter).prefetch_related('fk').prefetch_models(prefetches).all())
            bb = results[0]
            assert bb.fk5 == fk5
            assert bb.fk3 == fk3
            assert bb.fk is None
            for cc in results[1:]:
                assert cc.fk8 == fk8
                assert cc.fk5 == fk5
                assert cc.fk3 == fk3
                assert cc.fk is None

