from collections import namedtuple, defaultdict
from functools import partial
from itertools import chain, product
from operator import attrgetter, or_, and_
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet, Manager, Q
from django.db.models.query import prefetch_related_objects, ModelIterable
from django.db.models.constants import LOOKUP_SEP
try:
    from six.moves import range, reduce
except ImportError:
    from django.utils.six.moves import range, reduce


class InvalidModel(ValueError):
    pass


def walk_from_model_to_root(root_model, target_model):
    """
    Given models A, AB(A), BB(AB), and CC(BB)
    if root_model is A, and target_model is CC
    return something like ('cc', 'bb', 'ab')
    which if joined by LOOKUP_SEP would give the select_related() value.
    """
    if not issubclass(target_model, root_model):
        raise InvalidModel("%(child)r is not a subclass of %(root)r" % {
            'child': target_model,
            'root': root_model
        })
    # if root_model is target_model:
    #     import pdb; pdb.set_trace()
    #     raise InvalidModel("%(child)r is the same as %(root)r" % {
    #         'child': target_model,
    #         'root': root_model
    #     })
    parent_link = target_model._meta.get_ancestor_link(root_model)
    while parent_link is not None:
        # >= 1.10
        rel = getattr(parent_link, 'rel', None)
        if rel is None:
            rel = getattr(parent_link, 'related', None)
        yield rel.get_accessor_name()
        parent_model = rel.model
        parent_link = parent_model._meta.get_ancestor_link(root_model)


def discovery_lookup_from_model(root_model, target_model):
    lookups_consumed = tuple(walk_from_model_to_root(root_model=root_model,
                                                     target_model=target_model))
    lookups_iter_reversed = reversed(lookups_consumed)
    return tuple(lookups_iter_reversed)


def generate_relation_combinations(lookup_parts):
    length = len(lookup_parts) + 1
    return tuple(lookup_parts[0:n] for n in range(1, length))


def _generate_q_filters(lookups, isnull, operator):
    def yielder(_lookups):
        for lookupset in _lookups:
            if lookupset:
                q_objs = tuple(Q(**{'%s__isnull' % LOOKUP_SEP.join(part): isnull})
                               for part in lookupset)
                q_objs2 = reduce(and_, q_objs)
                yield q_objs2
    out = reduce(operator, yielder(_lookups=lookups))
    return out

def generate_q_filters(lookups):
    return _generate_q_filters(lookups, isnull=False, operator=or_)


def generate_basemodel_q_filters(lookups):
    return _generate_q_filters(lookups, isnull=True, operator=and_)

def lookups_to_text(lookups):
    """
    Givne a set of elements like [
        ('a', 'b', 'c'),
        ('d', 'e'),
    ]
    return something like:
    ('a__b__c', 'd__e')
    """
    return tuple(LOOKUP_SEP.join(lookup) for lookup in lookups)


def relation_string_for_model(root_model, target_model):
    """
    DUNNO IF I NEED THIS ...
    Given the classes A, B(A), C(B), and D(C) passing in the root_model A and the
    target_model C, 'b__c__d'
    """
    lookups = discovery_lookup_from_model(root_model=root_model, target_model=target_model)
    lookups_as_strings = lookups_to_text([lookups])
    return lookups_as_strings[0]


def calculate_paths(lookups):
    # expects tuples like: ('a', 'b', 'c')

    # go from a lookup of ('a', 'b', 'c') to generating all:
    # (('a',), ('a', 'b'), ('a', 'b', 'c'))
    lookups_with_intermediates = tuple(generate_relation_combinations(lookup)
                                       for lookup in lookups)
    # flatten any duplicates (eg: going through table `a` twice)
    lookups_with_intermediates_flat = set(chain.from_iterable(lookups_with_intermediates))
    joins_as_strings = lookups_to_text(lookups=lookups_with_intermediates_flat)
    result = sorted(lookups_with_intermediates_flat, key=len, reverse=True)
    returndata = result, joins_as_strings, lookups_with_intermediates
    return returndata


def get_startswiths(relations, prefetches):
    """
    given relations [u'ab__bb__cc', u'ab__bb', u'ab']
    and prefetches [u'ab__bb__cc__fk5', u'ab__bb__cc__fk8', u'ab__bb__cc__fk3', u'ab__bb__cc__fk']
    take the prefetches that start with any of the relations BUT substitute
    the prefix entirely.
    """
    prefetches = sorted(prefetches)
    potentials = set()
    data = product(relations, prefetches)
    for relation, prefetch in data:
        fullrel = '%s%s' % (relation, LOOKUP_SEP)
        if prefetch.startswith(relation):
            rel_length = len(fullrel)
            sliced_prefetch = prefetch[rel_length:]
            if sliced_prefetch not in potentials:
                potentials.add(sliced_prefetch)
    result = sorted(potentials)
    return result


def dig_for_obj(obj, attrgetters):
    for attrgetter_ in attrgetters:
        try:
            return attrgetter_(obj)
        except ObjectDoesNotExist:
            continue
    return obj


class InheritingModelIterable(ModelIterable):
    def __iter__(self):
        queryset = self.queryset  # type: django.db.models.query.QuerySet
        query = queryset.query  # type: django.db.models.sql.query.Query
        relations_for_attrgetter = tuple(x.replace(LOOKUP_SEP, '.') for x in lookups_to_text(queryset._our_joins))
        attrgetters = tuple(attrgetter(x) for x in relations_for_attrgetter)
        for obj in super(InheritingModelIterable, self).__iter__():
            subobj = dig_for_obj(obj=obj, attrgetters=attrgetters)
            # having got the deepest object, apply any annotations which were
            # on the root version of the object.
            if query.annotations:
                for k in query.annotations.keys():
                    rootval = getattr(obj, k)
                    setattr(subobj, k, rootval)
            if query.extra_select:
                for k in query.extra_select.keys():
                    rootval = getattr(obj, k)
                    setattr(subobj, k, rootval)
            # if query.select_related:
            #     import pdb; pdb.set_trace()
            #     for k in query.select_related.keys():
            #         if k not in set(chain(queryset._our_joins)):
            #             print(k)
            #             rootval = getattr(obj, k)
            #             setattr(subobj, k, rootval)
            yield subobj



class InheritingQuerySet(QuerySet):

    def __init__(self, *args, **kwargs):
        super(InheritingQuerySet, self).__init__(*args, **kwargs)
        self._our_joins = []
        self._subclasses = set()
        self._our_prefetches = {}
        self._iterable_class = InheritingModelIterable

    def _clone(self, *args, **kwargs):
        clone = super(InheritingQuerySet, self)._clone(*args, **kwargs)
        clone._our_joins = self._our_joins[:]
        clone._subclasses = set(self._subclasses)
        clone._our_prefetches = self._our_prefetches
        return clone

    def select_subclasses(self, *subclasses):
        if subclasses == ():
            def get_subclasses(cls):
                for subclass in cls.__subclasses__():
                    yield subclass
                    for subsubclass in get_subclasses(subclass):
                        yield subsubclass
            subclasses = set(get_subclasses(self.model))
        # Support the single API call equivalent from model-utils
        return self.models(*subclasses, include_self=True)

    def models(self, *models, **options):
        clone = self._clone()
        if 'include_self' in options and options['include_self'] is True and clone.model not in models:
            models += (clone.model,)
        models = set(models)
        overlap = clone._subclasses & models
        allow_overlap = 'strict' in options and options['strict'] is True
        if (overlap and not allow_overlap):
            overlaps = ", ".join(repr(x) for x in overlap)
            raise InvalidModel("The following models have already been selected, {!s}".format(overlaps))
        clone._subclasses |= models

        function = partial(discovery_lookup_from_model, root_model=clone.model)
        # generate tuples like: ('a', 'b', 'c')
        lookups = tuple(set(function(target_model=model) for model in clone._subclasses))
        # the decision maker
        our_joins, joins_as_strings, all_combinations = calculate_paths(lookups=lookups)
        clone._our_joins = our_joins
        # we're already in a clone, so play about with it directly.
        clone.query.add_select_related(joins_as_strings)
        # To avoid returning instances without children, we need to do a filter,
        # ensuring the children are isnull=False
        if any(len(combo) > 0 for combo in all_combinations):
            x = generate_q_filters(lookups=all_combinations)
            if self.model in clone._subclasses:
                x = x | generate_basemodel_q_filters(lookups=all_combinations)
            clone.query.add_q(x)
        return clone

    def prefetch_models(self, prefetch_dict):
        clone = self._clone()
        # apply extras grouped by models...
        for key, value in prefetch_dict.items():
            if key not in clone._our_prefetches:
                clone._our_prefetches[key] = []
            clone._our_prefetches[key].extend(value)
        return clone
    #
    # def _fetch_all(self):
    #     if self._result_cache is None:
    #         self._result_cache = list(self.iterator())
    #     has_prefetch_relateds = len(self._prefetch_related_lookups) > 0
    #     has_prefetch_models = len(self._our_prefetches) > 0
    #     needs_prefetches = has_prefetch_relateds or has_prefetch_models
    #     if needs_prefetches and not self._prefetch_done:
    #         self._prefetch_related_objects()

    # def _prefetch_related_objects(self):
    #     things = defaultdict(list)
    #     for index, thing in enumerate(self._result_cache, start=0):
    #         things[thing.__class__].append(thing)
    #
    #     for klass, instances in things.items():
    #         prefetches = list(self._prefetch_related_lookups[:])
    #         if klass in self._our_prefetches:
    #             prefetches.extend(self._our_prefetches[klass])
    #         prefetches = tuple(prefetches)
    #         prefetch_related_objects(instances, prefetches)
    #     return None


InheritingManager = Manager.from_queryset(InheritingQuerySet)
