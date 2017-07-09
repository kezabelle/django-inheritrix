# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.db.models import Model, IntegerField, ForeignKey, OneToOneField, \
    ManyToManyField
from django.utils.six import python_2_unicode_compatible
from inheritrix import InheritingManager


class RelatesToJeff(Model):
    pass

class RelatesToJeffSon(Model):
    pass

class RelatesToJeffDaughter(Model):
    pass

class RelatesToJeffGrandSon(Model):
    pass

class RelatesToJeffGrandDaughter(Model):
    pass

class RelatesToGreatGrandSon1(Model):
    pass

class RelatesToGreatGrandSon2(Model):
    pass

class RelatesToGreatGrandDaughter(Model):
    pass


class RelatesToJeffMany(Model):
    pass

@python_2_unicode_compatible
class Jeff(Model):
    v = IntegerField(default=0)
    fk = ForeignKey(RelatesToJeff, null=True)
    m2m = ManyToManyField(RelatesToJeffMany, null=True)
    polymorphs = InheritingManager()

    def __str__(self):
        return str(self.pk)


class JeffSon(Jeff):
    v1 = IntegerField(default=1)
    fk2 = ForeignKey(RelatesToJeffSon, null=True)


class JeffDaughter(Jeff):
    v1 = IntegerField(default=1)
    fk3 = ForeignKey(RelatesToJeffDaughter, null=True)


class JeffGrandSon(JeffSon):
    v2 = IntegerField(default=2)
    fk4 = ForeignKey(RelatesToJeffGrandSon, null=True)


class JeffGrandDaughter(JeffDaughter):
    v2 = IntegerField(default=2)
    o2o = OneToOneField(RelatesToJeffGrandDaughter, null=True)
    fk5 = ForeignKey(RelatesToJeffGrandDaughter, null=True)


class JeffGreatGrandSon1(JeffGrandSon):
    v3 = IntegerField(default=3)
    fk6 = ForeignKey(RelatesToGreatGrandSon1, null=True)


class JeffGreatGrandSon2(JeffGrandSon):
    v3 = IntegerField(default=3)
    fk7 = ForeignKey(RelatesToGreatGrandSon2, null=True)


class JeffGreatGrandDaughter(JeffGrandDaughter):
    v3 = IntegerField(default=3)
    fk8 = ForeignKey(RelatesToGreatGrandDaughter, null=True)
