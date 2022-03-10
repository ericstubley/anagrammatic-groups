#! /usr/bin/env python3

import sys
from collections import defaultdict
from itertools import combinations

letters = [chr(i + ord('a')) for i in range(26)]
letter_pairs = list(combinations(letters, r=2))
char_to_index = dict((chr(i + ord('a')), i) for i in range(26))


# TODO
# comments moar
# maybe you actually do need disjoin sets; the reduction and recombining as
#   currently implement is a garbage
# in step two the diwans=windas relation and dwines=widens relations look to
#   be getting erroneously combined to produce the (i, w) commutator too early
# at the beginning same count => complete graph
# later on same count =/=> in a complete graph


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
    for count in anagram_dict:
        for word in anagram_dict[count]:
            for sibling, pair in admissible_siblings(word):
                if pair not in pairs and sibling in anagram_dict[count]:
                    new_pairs[pair].add(tuple(sorted((word, sibling))))
    pairs.update(new_pairs)
    return pairs


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
    letter count -> (dictionary of reduced word -> originating words)
    """
    # the argument to defaultdict needs to be a callable constructor
    anagram_dict = defaultdict(lambda: defaultdict(list)) 
    for word in dictionary:
        counts = letter_counts(word)
        anagram_dict[counts][word].append(word)

    to_delete = [c for c in anagram_dict if len(anagram_dict[c]) == 1]
    for c in to_delete:
        anagram_dict.pop(c)

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

    for count in existing_counts:
        red_count = reduce_count(count, pairs)
        if red_count != count:
            for word in anagram_dict[count]:
                red_word = reduce_word(word, red_count)
                anagram_dict[red_count][red_word] += anagram_dict[count][word]

            anagram_dict.pop(count)

    to_delete = [c for c in anagram_dict if len(anagram_dict[c]) == 1]
    for c in to_delete:
        anagram_dict.pop(c)
    return anagram_dict


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
            ls = []
            for word in irreducibles[c]:
                ls += irreducibles[c][word]
            f.write(f"{ls}\n")


def make_history_files(anagram_dict):
    for alpha, beta in letter_pairs:
        print(f"\r{alpha}, {beta}", end="")
        i, j = char_to_index[alpha], char_to_index[beta]
        with open(f"history/history_{alpha}{beta}.txt", 'w') as f:
            for c in anagram_dict:
                anagrams = sorted(list(anagram_dict[c].keys()))
                if c[i] > 0 and c[j] > 0 and \
                        is_useful_history(anagrams, (alpha, beta)):
                    f.write(f"{anagrams}\n")
    print("\r", end="")


def make_status_file(step, anagram_dict, pairs):
    with open(f"pairs_{step}.txt", 'w') as f:
        for p in letter_pairs:
            if p in pairs:
                f.write(f"{p}, {sorted(list(pairs[p]))}\n") 


if __name__ == "__main__":
    dictionary_file = sys.argv[1]
    print("Processing dictionary")
    dictionary_data = process_dictionary(load_dictionary(dictionary_file)) 
    anagram_dict = build_anagram_dict(dictionary_data)
    pairs = defaultdict(set)

    print("Making history files")
    # make_history_files(anagram_dict)

    step = 1
    while True:
        num_counts, num_pairs = len(anagram_dict), len(pairs)
        print(f"Step {step}")

        pairs = update_admissible_pairs(anagram_dict, pairs)
        anagram_dict = reduce_anagram_dict(anagram_dict, pairs)

        print(f"{num_counts} letter counts, {len(pairs)} admissible pairs")
        make_status_file(step, anagram_dict, pairs)
        if num_counts == len(anagram_dict) and num_pairs == len(pairs):
            break
        step += 1

    print("Making outcome files")
    make_quality_files(pairs)
    make_irreducibles_file(anagram_dict)
    print("Done!")






