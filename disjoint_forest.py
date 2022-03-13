from collections import UserDict


class DisjointForest(UserDict):
    """ Class implementing a disjoint union data structure for use with
    tracking anagram relations. The basic use case is to track sets of
    reduced anagram relations; when the reduction happens some components
    may end up being combined.

    In terms of implementation, a DisjointForest object is essentially a
    dictionary where words map to a representative for a given component.
    The choice of representative is arbitrary and may fluctuate over the
    lifetime of a component. """

    def representative(self, word):
        """ Find the representative of word. If necessary collapse the tree
        structure for more efficient future lookups. """
        if self.data[word] != word:
            rep = self.representative(self.data[word])
            self.data[word] = rep
        return self.data[word]

    def are_related(self, w1, w2):
        """ Test if w1 and w2 are in the same component. """
        return self.representative(w1) == self.representative(w2)

    def add_with_rep(self, word, rep):
        """ Correctly add or update the word and make it have rep as its
        representative. This may include updating the current representatives
        of word or rep if they're in self already. """
        to_update = set([word, rep])
        if word in self.data:
            to_update.add(self.representative(word))
        if rep in self.data:
            to_update.add(self.representative(rep))
        for u in to_update:
            self.data[u] = rep

    def add_relations(self, words):
        """ Given a list of words, put them all into the same component. """
        component_rep = self.representative(words[0])
        for word in words:
            self.add_with_rep(word, component_rep)

    def merge(self, other):
        """ Given a DisjointForest other, merge self and other. If there's
        overlap in the words present components may be combined. """
        for word in other:
            new_rep = other.representative(word)
            self.add_with_rep(word, new_rep)

    def apply_map(self, word_map):
        """ Given a "reduction function" word_map, return a new DisjointForest
        whose words are those of self with word_map applied, preserving all
        existing relations. This may cause components to be combined if the 
        reudction function is not injective. """
        new_forest = DisjointForest()
        for word in self.data:
            mapped_word = word_map(word)
            mapped_rep = word_map(self.representative(word))
            new_forest.add_with_rep(mapped_word, mapped_rep)
        return new_forest
