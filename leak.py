from collections import defaultdict


class Leak(object):
    def __init__(self, repo, commit, potential, lines):
        self.repo = repo
        self.leak = commit
        self.potential = potential
        self.lines = lines

    def __str__(self):
        return str(self.leak)

    def __hash__(self):
        return hash(self.potential)

    def __eq__(self, other):
        return hash(self.potential) == hash(other)


class Leaks(defaultdict):
    def __init__(self):
        super().__init__(set)

    def add(self, key, value):
        self.__dict__[key] = value
