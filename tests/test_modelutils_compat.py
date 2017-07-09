# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

from django.db import models
from django.test import TestCase
from django.contrib.auth import get_user_model
from test_app2.models import (InheritanceManagerTestParent,
                              InheritanceManagerTestChild1,
                              InheritanceManagerTestChild2,
                              InheritanceManagerTestGrandChild1,
                              InheritanceManagerTestGrandChild1_2,
                              InheritanceManagerTestChild3,
                              InheritanceManagerTestRelated)


class InheritanceManagerUsingModelsTests(TestCase):
    def setUp(self):
        self.parent1 = InheritanceManagerTestParent.objects.create()
        self.child1 = InheritanceManagerTestChild1.objects.create()
        self.child2 = InheritanceManagerTestChild2.objects.create()
        self.grandchild1 = InheritanceManagerTestGrandChild1.objects.create()
        self.grandchild1_2 = InheritanceManagerTestGrandChild1_2.objects.create()

    def test_selecting_all_subclasses_specifically_grandchildren(self):
        """
        A bare select_subclasses() should achieve the same results as doing
        select_subclasses and specifying all possible subclasses.
        This test checks grandchildren, so only works on 1.6>=
        """
        objs = InheritanceManagerTestParent.objects.select_subclasses().order_by('pk')
        objsmodels = InheritanceManagerTestParent.objects.select_subclasses(
            InheritanceManagerTestChild1, InheritanceManagerTestChild2,
            InheritanceManagerTestChild3,
            InheritanceManagerTestGrandChild1,
            InheritanceManagerTestGrandChild1_2).order_by('pk')
        self.assertEqual(set(objs._subclasses), set(objsmodels._subclasses))
        self.assertEqual(list(objs), list(objsmodels))

    def test_selecting_all_subclasses_specifically_children(self):
        """
        A bare select_subclasses() should achieve the same results as doing
        select_subclasses and specifying all possible subclasses.
        Note: This is sort of the same test as
        `test_selecting_all_subclasses_specifically_grandchildren` but it
        specifically switches what models are used because that happens
        behind the scenes in a bare select_subclasses(), so we need to
        emulate it.
        """
        objs = InheritanceManagerTestParent.objects.select_subclasses().order_by('pk')

        models = (InheritanceManagerTestChild1,
                  InheritanceManagerTestChild2,
                  InheritanceManagerTestChild3,
                  InheritanceManagerTestGrandChild1,
                  InheritanceManagerTestGrandChild1_2)

        objsmodels = InheritanceManagerTestParent.objects.select_subclasses(
            *models).order_by('pk')
        # order shouldn't matter, I don't think, as long as the resulting
        # queryset (when cast to a list) is the same.
        self.assertEqual(set(objs._subclasses), set(objsmodels._subclasses))
        self.assertEqual(list(objs), list(objsmodels))

    def test_select_subclass_invalid_related_model(self):
        """
        Confirming that giving a stupid model doesn't work.
        """
        regex = '^.+? is not a subclass of .+$'
        with self.assertRaisesRegexp(ValueError, regex):
            InheritanceManagerTestParent.objects.select_subclasses(
                get_user_model()).order_by('pk')

    def test_duplications(self):
        """
        Check that even if the same thing is provided as a string and a model
        that the right results are retrieved.
        """
        # mixing strings and models which evaluate to the same thing is fine.
        objs = InheritanceManagerTestParent.objects.select_subclasses(
            InheritanceManagerTestChild2,
            InheritanceManagerTestChild2).order_by('pk')
        self.assertEqual(list(objs), [
            InheritanceManagerTestParent(pk=self.parent1.pk),
            InheritanceManagerTestParent(pk=self.child1.pk),
            InheritanceManagerTestChild2(pk=self.child2.pk),
            InheritanceManagerTestParent(pk=self.grandchild1.pk),
            InheritanceManagerTestParent(pk=self.grandchild1_2.pk),
        ])

    def test_child_doesnt_accidentally_get_parent(self):
        """
        Given a Child model which also has an InheritanceManager,
        none of the returned objects should be Parent objects.
        """
        objs = InheritanceManagerTestChild1.objects.select_subclasses(
            InheritanceManagerTestGrandChild1).order_by('pk')
        self.assertEqual([
            InheritanceManagerTestChild1(pk=self.child1.pk),
            InheritanceManagerTestGrandChild1(pk=self.grandchild1.pk),
            InheritanceManagerTestChild1(pk=self.grandchild1_2.pk),
        ], list(objs))

    def test_manually_specifying_parent_fk_only_specific_child(self):
        """
        given a Model which inherits from another Model, but also declares
        the OneToOne link manually using `related_name` and `parent_link`,
        ensure that the relation names and subclasses are obtained correctly.
        """
        child3 = InheritanceManagerTestChild3.objects.create()
        results = InheritanceManagerTestParent.objects.all().select_subclasses(
            InheritanceManagerTestChild3)

        expected_objs = [InheritanceManagerTestParent(pk=self.parent1.pk),
                         InheritanceManagerTestParent(pk=self.child1.pk),
                         InheritanceManagerTestParent(pk=self.child2.pk),
                         InheritanceManagerTestParent(pk=self.grandchild1.pk),
                         InheritanceManagerTestParent(pk=self.grandchild1_2.pk),
                         child3]
        self.assertEqual(list(results), expected_objs)

        expected_related_names = [InheritanceManagerTestParent, InheritanceManagerTestChild3]
        self.assertEqual(set(results._subclasses),
                         set(expected_related_names))

    def test_extras_descend(self):
        """
        Ensure that extra(select=) values are copied onto sub-classes.
        """
        results = InheritanceManagerTestParent.objects.select_subclasses().extra(
            select={'foo': 'id + 1'}
        )
        self.assertTrue(all(result.foo == (result.id + 1) for result in results))


class InheritanceManagerRelatedTests(TestCase):
    def setUp(self):
        self.related = InheritanceManagerTestRelated.objects.create()
        self.child1 = InheritanceManagerTestChild1.objects.create(
            related=self.related)
        self.child2 = InheritanceManagerTestChild2.objects.create(
            related=self.related)
        self.grandchild1 = InheritanceManagerTestGrandChild1.objects.create(related=self.related)
        self.grandchild1_2 = InheritanceManagerTestGrandChild1_2.objects.create(related=self.related)

    def get_manager(self):
        return self.related.imtests

    def test_get_method_with_select_subclasses(self):
        with self.assertNumQueries(1):
            o = InheritanceManagerTestParent.objects.select_subclasses().get(
                    id=self.child1.id)
        self.assertIsInstance(o, self.child1.__class__)
        self.assertEqual(o, self.child1)

    def test_annotate_with_select_subclasses(self):
        qs = InheritanceManagerTestParent.objects.select_subclasses().annotate(
            models.Count('id'))
        self.assertEqual(qs.get(id=self.child1.id).id__count, 1)

    def test_annotate_with_named_arguments_with_select_subclasses(self):
        qs = InheritanceManagerTestParent.objects.select_subclasses().annotate(
            test_count=models.Count('id'))
        self.assertEqual(qs.get(id=self.child1.id).test_count, 1)

    def test_annotate_before_select_subclasses(self):
        qs = InheritanceManagerTestParent.objects.annotate(
            models.Count('id')).select_subclasses()
        self.assertEqual(qs.get(id=self.child1.id).id__count, 1)

    def test_annotate_with_named_arguments_before_select_subclasses(self):
        qs = InheritanceManagerTestParent.objects.annotate(
            test_count=models.Count('id')).select_subclasses()
        self.assertEqual(qs.get(id=self.child1.id).test_count, 1)
