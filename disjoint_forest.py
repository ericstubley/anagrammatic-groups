from collections import UserDict

# TODO 
# comments and disclaimers


class DisjointForest(UserDict):
    def representative(self, word):
        if self.data[word] != word:
            rep = self.representative(self.data[word])
            self.data[word] = rep
        return self.data[word]


    def are_related(self, w1, w2):
        return self.representative(w1) == self.representative(w2)


    def add_with_rep(self, word, rep):
        to_update = set([word, rep])
        if word in self.data:
            to_update.add(self.representative(word))
        if rep in self.data:
            to_update.add(self.representative(rep))
        for u in to_update:
            self.data[u] = rep


    def add_relations(self, words):
        component_rep = self.representative(words[0])
        for word in words:
            word_rep = self.representative(word)
            self.data[word_rep] = component_rep


    def merge(self, other):
        for word in other:
            new_rep = other.representative(word)
            self.add_with_rep(word, new_rep)


    def apply_map(self, word_map):
        new_forest = DisjointForest()
        for word in self.data:
            mapped_word = word_map(word)
            mapped_rep = word_map(self.representative(word))
            new_forest.add_with_rep(mapped_word, mapped_rep)
        return new_forest
