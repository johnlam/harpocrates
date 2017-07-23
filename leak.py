from collections import defaultdict


class Leak(object):
    def __init__(self, commit, potential):
        self.leak = commit
        self.potential = potential

    def __str__(self):
        return str(self.leak)

    def __unicode__(self):
        return unicode(self.leak)

    def __hash__(self):
        return hash(self.potential)

    def __eq__(self, other):
        return hash(self.potential) == hash(other)


class Leaks(object):
    def __init__(self):
        self.details = defaultdict(set)

    def __len__(self):
        return len(self.details.keys())

    def __contains__(self, key):
        if key in self.details:
            return True
        return False

    def __getitem__(self, item):
        return self.details[item]

    def __setitem__(self, item, value):
        self.details[item].add(value)

    def __str__(self):
        return str(self.details)

    def __repr__(self):
        return self.__str__()

    def add(self, key, value):
        self.details[key].add(value)

    def iteritems(self):
        return self.details.iteritems()
