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

class FK3(Model):
    pass

class FK4(Model):
    pass

class FK5(Model):
    pass

class FK6(Model):
    pass

class FK7(Model):
    pass

class FK8(Model):
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
    fk2 = ForeignKey(FK2, null=True)


class AB(A):
    v1 = IntegerField(default=1)
    fk3 = ForeignKey(FK3, null=True)


class BA(AA):
    v2 = IntegerField(default=2)
    fk4 = ForeignKey(FK4, null=True)


class BB(AB):
    v2 = IntegerField(default=2)
    fk5 = ForeignKey(FK5, null=True)


class CA(BA):
    v3 = IntegerField(default=3)
    fk6 = ForeignKey(FK6, null=True)


class CB(BA):
    v3 = IntegerField(default=3)
    fk7 = ForeignKey(FK7, null=True)


class CC(BB):
    v3 = IntegerField(default=3)
    fk8 = ForeignKey(FK8, null=True)
