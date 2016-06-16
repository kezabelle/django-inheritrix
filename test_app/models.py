# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.db.models import Model, IntegerField, ForeignKey
from django.utils.six import python_2_unicode_compatible
from inheritrix import InheritingManager


class FK(Model):
    pass

class FK2(Model):
    pass


@python_2_unicode_compatible
class A(Model):
    v = IntegerField(default=0)
    fk = ForeignKey(FK, null=True)
    polymorphs = InheritingManager()

    def __str__(self):
        return str(self.pk)


class AA(A):
    v1 = IntegerField(default=1)


class AB(A):
    v1 = IntegerField(default=1)


class BA(AA):
    v2 = IntegerField(default=2)


class BB(AB):
    v2 = IntegerField(default=2)


class CA(BA):
    v3 = IntegerField(default=3)


class CB(BA):
    v3 = IntegerField(default=3)


class CC(BB):
    v3 = IntegerField(default=3)
    fk2 = ForeignKey(FK2, null=True)
