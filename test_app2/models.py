# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.db import models
from inheritrix import InheritingManager
try:
    from six import python_2_unicode_compatible
except ImportError:
    from django.utils.six import python_2_unicode_compatible

class InheritanceManagerTestRelated(models.Model):
    pass


@python_2_unicode_compatible
class InheritanceManagerTestParent(models.Model):
    # FileField is just a handy descriptor-using field. Refs #6.
    non_related_field_using_descriptor = models.FileField(upload_to="test")
    related = models.ForeignKey(
        InheritanceManagerTestRelated, related_name="imtests", null=True,
        on_delete=models.CASCADE)
    normal_field = models.TextField()
    related_self = models.OneToOneField(
        "self", related_name="imtests_self", null=True,
        on_delete=models.CASCADE)
    objects = InheritingManager()

    def __unicode__(self):
        return unicode(self.pk)

    def __str__(self):
        return "%s(%s)" % (
            self.__class__.__name__[len('InheritanceManagerTest'):],
            self.pk,
        )


class InheritanceManagerTestChild1(InheritanceManagerTestParent):
    non_related_field_using_descriptor_2 = models.FileField(upload_to="test")
    normal_field_2 = models.TextField()
    objects = InheritingManager()


class InheritanceManagerTestGrandChild1(InheritanceManagerTestChild1):
    text_field = models.TextField()


class InheritanceManagerTestGrandChild1_2(InheritanceManagerTestChild1):
    text_field = models.TextField()


class InheritanceManagerTestChild2(InheritanceManagerTestParent):
    non_related_field_using_descriptor_2 = models.FileField(upload_to="test")
    normal_field_2 = models.TextField()


class InheritanceManagerTestChild3(InheritanceManagerTestParent):
    parent_ptr = models.OneToOneField(
        InheritanceManagerTestParent, related_name='manual_onetoone',
        parent_link=True, on_delete=models.CASCADE)
