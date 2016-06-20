from collections import namedtuple, defaultdict
from functools import partial
from itertools import chain, product
from operator import attrgetter, or_, and_
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet, Manager, Q
from django.db.models.query import prefetch_related_objects
from django.db.models.constants import LOOKUP_SEP


class InvalidModel(TypeError):
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
    if root_model is target_model:
        raise InvalidModel("%(child)r is the same as %(root)r" % {
            'child': target_model,
            'root': root_model
        })
    parent_link = target_model._meta.get_ancestor_link(root_model)
    while parent_link is not None:
        yield parent_link.related.get_accessor_name()
        parent_model = parent_link.related.model
        parent_link = parent_model._meta.get_ancestor_link(root_model)


def discovery_lookup_from_model(root_model, target_model):
    lookups_consumed = tuple(walk_from_model_to_root(root_model=root_model,
                                                     target_model=target_model))
    lookups_iter_reversed = reversed(lookups_consumed)
    return tuple(lookups_iter_reversed)


def generate_relation_combinations(lookup_parts):
    length = len(lookup_parts) + 1
    return tuple(lookup_parts[0:n] for n in xrange(1, length))


def generate_q_filters(lookups):
    def yielder(lookups):
        for lookupset in lookups:
            q_objs = tuple(Q(**{'%s__isnull' % LOOKUP_SEP.join(part): False})
                           for part in lookupset)
            q_objs2 = reduce(and_, q_objs)
            yield q_objs2
    out = reduce(or_, yielder(lookups=lookups))
    return out


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
    returndata =  result, joins_as_strings, lookups_with_intermediates
    return returndata


def get_startswiths(relations, prefetches):
    """
    given relations [u'ab__bb__cc', u'ab__bb', u'ab']
    and prefetches [u'ab__bb__cc__fk5', u'ab__bb__cc__fk8', u'ab__bb__cc__fk3', u'ab__bb__cc__fk']
    take the prefetches that start with any of the relations BUT substitute
    the prefix entirely.
    """
    def iterable():
        data = product(relations, prefetches)
        for relation, prefetch in data:
            if prefetch.startswith(relation):
                rel_length = len(relation)
                yield prefetch[rel_length:].lstrip('_')
    return sorted(iterable())


def dig_for_obj(obj, attrgetters):
    for attrgetter_ in attrgetters:
        try:
            return attrgetter_(obj)
        except ObjectDoesNotExist:
            continue
    return obj


class InheritingQuerySet(QuerySet):

    def __init__(self, *args, **kwargs):
        super(InheritingQuerySet, self).__init__(*args, **kwargs)
        self._our_joins = []

    def _clone(self, *args, **kwargs):
        clone = super(InheritingQuerySet, self)._clone(*args, **kwargs)
        clone._our_joins = self._our_joins[:]
        return clone

    def select_subclasses(self, *subclasses):
        # Support the single API call equivalent from model-utils
        return self.models(*subclasses, include_self=True)

    def models(self, *models, **options):
        clone = self._clone()
        # if at all possible, remove anything *I* added to select_related.
        # Note: at the moment I have no idea how to unwind the Q objects I put
        # in, so the joins all still happen. Dumb.
        if models == (None,):
            raise ValueError("Cannot unset models() calls")
            # go in depth first order.
            # this is nasty.
            # for field in self._our_joins:
            #     newlevel = clone.query.select_related
            #     for part in field:
            #         if part in newlevel:
            #             previouslevel = newlevel
            #             newlevel = newlevel[part]
            #             if tuple(newlevel.keys()) == ():
            #                 del previouslevel[part]
            # clone._our_joins = []
            # return clone

        function = partial(discovery_lookup_from_model, root_model=clone.model)
        # generate tuples like: ('a', 'b', 'c')
        lookups = tuple(set(function(target_model=model) for model in models))
        # the decision maker
        our_joins, joins_as_strings, all_combinations = calculate_paths(lookups=lookups)
        clone._our_joins = our_joins
        # we're already in a clone, so play about with it directly.
        clone.query.add_select_related(joins_as_strings)
        # To avoid returning instances without children, we need to do a filter,
        # ensuring the children are isnull=False
        if 'include_self' not in options or options['include_self'] is not True:
            x = generate_q_filters(lookups=all_combinations)
            clone.query.add_q(x)
        return clone

    def iterator(self):
        iterator = super(InheritingQuerySet, self).iterator()
        relations_for_attrgetter = tuple(x.replace(LOOKUP_SEP, '.') for x in lookups_to_text(self._our_joins))
        attrgetters = tuple(attrgetter(x) for x in relations_for_attrgetter)
        for obj in iterator:
            yield dig_for_obj(obj=obj, attrgetters=attrgetters)
    #
    def _prefetch_related_objects(self):
        things = defaultdict(list)
        for thing in self._result_cache:
            things[thing.__class__].append(thing)

        function = partial(discovery_lookup_from_model, root_model=self.model)
        for klass, instances in things.items():
            relation_distance = function(target_model=klass)
            our_joins, joins_as_strings, all_combinations = calculate_paths(lookups=[relation_distance])
            things2 = get_startswiths(joins_as_strings, self._prefetch_related_lookups)
            print(things2)
            prefetch_related_objects(instances, self._prefetch_related_lookups)
        return None


InheritingManager = Manager.from_queryset(InheritingQuerySet)
