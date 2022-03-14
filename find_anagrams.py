#! /usr/bin/env python3

import sys
from collections import defaultdict
from functools import partial
from itertools import combinations
from os import mkdir
from disjoint_forest import DisjointForest


letters = [chr(i + ord('a')) for i in range(26)]
letter_pairs = list(combinations(letters, r=2))
# this is the map 'a' -> 0 ... 'z' -> 26
char_to_index = dict((chr(i + ord('a')), i) for i in range(26))


def letter_counts(word):
    """ Takes a word and returns a 26-tuple counting how many of each
    (lowercase) letter are in the word. The basic concept to keep in mind is
    that words w1 and w2 are anagrams iff this function maps them to the same
    26-tuple. """
    counts = [0]*26
    for c in word:
        counts[char_to_index[c]] += 1
    return tuple(counts)


""" ADMISSIBLE PAIR SEARCHING STEP
These two functions are used to search the current set of relations for 
admissible pairs of anagrams, i.e. words w1, w2 of the form
    w1 = s1 + alpha + beta + s2
    w2 = s1 + beta + alpha + s2
for strings s1, s2 and characters alpha, beta. """


def admissible_siblings(word):
    """ Given a word, yields all possible admissible siblings of that word.
    Smart enough to not yield word itself if it has a consecutive repeated
    character. """
    for i in range(1, len(word)):
        if word[i-1] != word[i]:
            sibling = word[:i-1] + word[i] + word[i-1] + word[i+1:]
            pair = tuple(sorted([word[i-1], word[i]]))
            yield sibling, pair


def update_admissible_pairs(anagram_dict, pairs):
    """ Given a current list of anagram relations and list of commutators
    already found, update that list of commutators with all newly found
    admissible pairs. Returns the updated list of pairs as well as a flag
    signalling if any new pairs were found. """
    new_pairs = defaultdict(set)
    update_flag = False
    for count in anagram_dict:
        for word in anagram_dict[count]:
            for sibling, pair in admissible_siblings(word):
                if pair not in pairs and sibling in anagram_dict[count] \
                        and anagram_dict[count].are_related(word, sibling):
                    new_pairs[pair].add(tuple(sorted((word, sibling))))
                    update_flag = True
    pairs.update(new_pairs)
    return pairs, update_flag


""" REDUCTION STEP
The following three functions deal with reducing counts, word, and the whole
dictionary according to which commutators have been found so far. """


def reduce_count(count, pairs):
    """ Given a letter count and a set of letter pair commutators, remove from
    the letter count all letters which commute with all others in the count.
    """
    chars = [i for i in range(26) if count[i] != 0]
    new_count = [0]*26
    for i in chars:
        missing_pair = False
        for j in chars:
            if i != j and tuple(sorted([letters[i], letters[j]])) not in pairs:
                missing_pair = True
                break

        if missing_pair:
            new_count[i] = count[i]
    return tuple(new_count)


def reduce_word(word, count):
    """ Given a word and a letter count (which should be a reduced version of
    letter_counts(word)), reduce the word by removing those characters which
    don't appear in count. """
    ret = []
    for c in word:
        if count[char_to_index[c]] > 0:
            ret.append(c)
    return "".join(ret)


def reduce_anagram_dict(anagram_dict, pairs):
    """ Given a a set of relations anagram_dict and set of commutators pairs, 
    reduce the relations according to the commutators. Note that this modifies
    anagram_dict in place. Returns (a reference to) anagram_dict and a flag
    tracking whether or not any reductions occured. """
    existing_counts = list(anagram_dict.keys())
    reduce_flag = False

    for count in existing_counts:
        red_count = reduce_count(count, pairs)
        if red_count != count:
            reduce_flag = True

            reduction_function = partial(reduce_word, count=red_count)
            new_forest = anagram_dict[count].apply_map(reduction_function)
            anagram_dict[red_count].merge(new_forest)

            anagram_dict.pop(count)

    to_delete = [c for c in anagram_dict if len(anagram_dict[c]) == 1]
    for c in to_delete:
        anagram_dict.pop(c)
    return anagram_dict, reduce_flag


""" SETUP FUNCTIONS
The next three functions are the pipeline for taking a dictionary file and
parsing it into the main data structure, which is a dictionary
    letter count -> DisjointForest of words having that letter count. 
The DisjointForests each start with only a single component, since we're
starting off with the relations w1 = w2 whenever w1, w2 are anagrams. """


def load_dictionary(name):
    """ Load a dictionary text file without doing any processing """
    with open(name, 'r') as f:
        return f.readlines()


def process_dictionary(raw):
    """ Clean up the dictionary. Make everything lowercase and filter out any
    words which aren't strictly alphabetic characters """
    dictionary = []
    for word in raw:
        word = word.rstrip().lower()
        if word.isalpha():
            dictionary.append(word)
    return dictionary


def build_anagram_dict(dictionary):
    """ Create the letter count -> DisjointForest of anagrams dictionary. """
    # make totally unrelated disjoint forests
    anagram_dict = defaultdict(DisjointForest)
    for word in dictionary:
        counts = letter_counts(word)
        anagram_dict[counts][word] = word

    # remove all letter counts where we found no anagram relations
    to_delete = [c for c in anagram_dict if len(anagram_dict[c]) == 1]
    for c in to_delete:
        anagram_dict.pop(c)

    # make each forests totally related
    for count in anagram_dict:
        anagrams = list(anagram_dict[count].keys())
        anagram_dict[count].add_relations(anagrams)

    return anagram_dict


""" HISTORY FUNCTIONS
The next three functions are used to identify and write to files those
anagrams which have the potential to produce useful commutators. This output
is key to proving that some quotients of the anagram group are free; the fact
that j, q, x, z have no mutual history is the proof that the quotient of the 
anagram group by all letters except those is free. """


def is_useful_history(anagrams, pair):
    """ Given a list of anagrams and a pair of letters, return True if it's 
    possible that we could produce any interesting relation between the pair
    using these anagrams. Works by removing all other letters from each word
    and then seeing if more than one such pattern of alphas and betas appears.
    """
    patterns = set()
    for word in anagrams:
        pattern = "".join([c for c in word if c in pair])
        patterns.add(pattern)

    return len(patterns) > 1


def make_history_dict(anagram_dict):
    """ Make a dictionary which maps each letter pair to the lists of anagrams
    which produce interesting relations among those words, as per the previous
    function. """
    history_dict = defaultdict(list)
    for c in anagram_dict:
        indices_present = [i for i in range(26) if c[i] != 0]
        for i, j in combinations(indices_present, 2):
            alpha, beta = letters[i], letters[j]
            anagrams = sorted(list(anagram_dict[c].keys()))
            if is_useful_history(anagrams, (alpha, beta)):
                history_dict[(alpha, beta)].append(anagrams)
    return history_dict


def make_history_files(anagram_dict):
    """ For each pair of letters, write a file that contains a list of all the
    original sets of anagrams which could provide interesting relations
    invoving that pair. """

    history_dict = make_history_dict(anagram_dict)

    try:
        mkdir("history")
    except FileExistsError:
        pass

    for alpha, beta in letter_pairs:
        print(f"\r{alpha}, {beta}", end="")
        with open(f"history/history_{alpha}{beta}.txt", 'w') as f:
            for anagrams in history_dict[(alpha, beta)]:
                f.write(f"{anagrams}\n")
    print("\r", end="")


""" OUTPUT FUNCTIONS
The next three functions deal with creating various types of file output. """


def make_status_file(step, pairs):
    """ Create a file tracking which letter pair commutators have been found
    at the current step, along with the list of anagram relations that gave
    rise to them. """
    with open(f"pairs_{step}.txt", 'w') as f:
        for p in letter_pairs:
            if p in pairs:
                f.write(f"{p}, {sorted(list(pairs[p]))}\n")


def make_quality_files(pairs):
    """ Create files listing which commutator pairs were/weren't found. """
    with open("pairs_good.txt", 'w') as f_good, \
            open("pairs_bad.txt", 'w') as f_bad:
        for p in letter_pairs:
            if p in pairs:
                f_good.write(f"{p}\n")
            else:
                f_bad.write(f"{p}\n")


def make_irreducibles_file(irreducibles):
    """ Create a file listing those relations which remain after the
    commutator finding and reduction steps have finished. """
    with open("irreds.txt", 'w') as f:
        for c in irreducibles:
            ls = list(irreducibles[c].keys())
            f.write(f"{ls}\n")


""" MAIN/TESTING FUNCTIONS """


def state_of_word(word, anagram_dict, pairs):
    """ Used to find the current context of a given word. Not used by any
    other function, is a convenient debugging/tracking tool. """
    current_count = reduce_count(letter_counts(word), pairs)
    if current_count in anagram_dict:
        return anagram_dict[current_count]
    else:
        return None


def main(dictionary_file):
    """ Main routine for taking a dictionary and finding commutator relations
    within it. """
    print("Processing dictionary")
    dictionary_data = process_dictionary(load_dictionary(dictionary_file))
    anagram_dict = build_anagram_dict(dictionary_data)
    pairs = defaultdict(set)

    print("Making history files")
    make_history_files(anagram_dict)

    step = 1
    print("Start of main loop")
    while True:
        print(f"Step {step}")
        num_counts = len(anagram_dict)
        pairs, pair_flag = update_admissible_pairs(anagram_dict, pairs)
        print(f"{num_counts} letter counts, {len(pairs)} admissible pairs")
        anagram_dict, red_flag = reduce_anagram_dict(anagram_dict, pairs)

        make_status_file(step, pairs)

        if not (pair_flag or red_flag):
            break
        step += 1
    print("End of main loop")

    print("Making outcome files")
    make_quality_files(pairs)
    make_irreducibles_file(anagram_dict)
    print("Done!")


if __name__ == "__main__":
    dictionary_file = sys.argv[1]
    main(dictionary_file)
