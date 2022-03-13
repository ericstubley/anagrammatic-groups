from collections import UserDict


class DisjointForest(UserDict):
    def add_relations(self, words):
        # put all of words into the same component
        component_rep = self.representative(words[0])
        for word in words:
            word_rep = self.representative(word)
            self.data[word_rep] = component_rep


    def apply_map(self, word_map):
        new_forest = DisjointForest()
        for word in self.data:
            print(word, new_forest)
            mapped_word = word_map(word)
            mapped_rep = word_map(self.representative(word))
            if mapped_word in new_forest:
                new_rep = new_forest.representative(mapped_word)
                new_forest[new_rep] = mapped_rep
            new_forest[mapped_word] = mapped_rep
            if mapped_rep in new_forest:
                new_rep = new_forest.representative(mapped_rep)
                new_forest[new_rep] = mapped_rep
            new_forest[mapped_rep] = mapped_rep
        return new_forest


    def are_related(self, w1, w2):
        return self.representative(w1) == self.representative(w2)


    def representative(self, word):
        if self.data[word] != word:
            rep = self.representative(self.data[word])
            self.data[word] = rep
        return self.data[word]
