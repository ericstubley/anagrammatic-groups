#! /usr/bin/env python3

import sys
from collections import defaultdict
from functools import partial
from itertools import combinations
from disjoint_forest import DisjointForest


letters = [chr(i + ord('a')) for i in range(26)]
letter_pairs = list(combinations(letters, r=2))
char_to_index = dict((chr(i + ord('a')), i) for i in range(26))
index_to_char = dict((i, chr(i + ord('a'))) for i in range(26))


# TODO
# comments moar
# clean up this file to have a more sensible ordering of functions


def letter_counts(word):
    counts = [0]*26
    for c in word:
        counts[char_to_index[c]] += 1
    return tuple(counts)


def admissible_siblings(word):
    for i in range(1, len(word)):
        if word[i-1] != word[i]:
            sibling = word[:i-1] + word[i] + word[i-1] + word[i+1:]
            pair = tuple(sorted([word[i-1], word[i]]))
            yield sibling, pair


def update_admissible_pairs(anagram_dict, pairs):
    """ iterate through the anagram_dict, searching for more admissible pairs.
    modify the dictionary pairs in place by adding any newly found pairs. """
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


def is_useful_history(anagrams, pair):
    """ given a list of anagrams and a letter pair (alpha, beta) determine if
    more than one pattern of alphas and betas appears among the anagrams; these
    are the anagrams which could possible produce an alpha beta commutation """
    patterns = set()
    for word in anagrams:
        pattern = "".join([c for c in word if c in pair])
        patterns.add(pattern) 

    return len(patterns) > 1


def build_anagram_dict(dictionary):
    """ build a dictionary of 
        letter count -> DisjointForest of words having that letter count
    the forests are initially totally related
    """
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


def reduce_count(count, pairs):
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
    ret = []
    for c in word:
        if count[char_to_index[c]] > 0:
            ret.append(c)
    return "".join(ret)


def reduce_anagram_dict(anagram_dict, pairs):
    """ modify anagram_dict in place, reducing according to pairs """
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


def load_dictionary(name):
    """ load a dictionary text file without doing any processing """
    with open(name, 'r') as f:
        return f.readlines()


def process_dictionary(raw):
    """ clean up the dictionary; make everything lowercase and filter out any
    words which aren't strictly alphabetic characters """
    dictionary = []
    for word in raw:
        word = word.rstrip().lower()
        if word.isalpha():
            dictionary.append(word)
    return dictionary


def make_quality_files(pairs):
    with open("pairs_good.txt", 'w') as f_good, \
            open("pairs_bad.txt", 'w') as f_bad:
        for p in letter_pairs:
            if p in pairs:
                f_good.write(f"{p}\n")
            else:
                f_bad.write(f"{p}\n")


def make_irreducibles_file(irreducibles):
    with open("irreds.txt", 'w') as f:
        for c in irreducibles:
            ls = list(irreducibles[c].keys())
            f.write(f"{ls}\n")


def make_history_files(anagram_dict):
    history_dict = defaultdict(list)
    for c in anagram_dict:
        indices_present = [i for i in range(26) if c[i] != 0]
        for i, j in combinations(indices_present, 2):
            alpha, beta = index_to_char[i], index_to_char[j]
            anagrams = sorted(list(anagram_dict[c].keys()))
            if is_useful_history(anagrams, (alpha, beta)):
                history_dict[(alpha, beta)].append(anagrams)

    for alpha, beta in letter_pairs:
        print(f"\r{alpha}, {beta}", end="")
        with open(f"history/history_{alpha}{beta}.txt", 'w') as f:
            for anagrams in history_dict[(alpha, beta)]:
                f.write(f"{anagrams}\n")
    print("\r", end="")


def make_status_file(step, pairs):
    with open(f"pairs_{step}.txt", 'w') as f:
        for p in letter_pairs:
            if p in pairs:
                f.write(f"{p}, {sorted(list(pairs[p]))}\n") 


def state_of_word(word, anagram_dict, pairs):
    current_count = reduce_count(letter_counts(word), pairs)
    return anagram_dict[current_count]


def main(dictionary_file):
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
