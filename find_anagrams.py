#! /usr/bin/env python3

import sys
from collections import defaultdict
from itertools import combinations

letters = [chr(i + ord('a')) for i in range(26)]
letter_pairs = list(combinations(letters, r=2))
char_to_index = dict((chr(i + ord('a')), i) for i in range(26))


def letter_counts(word):
    counts = [0]*26
    for c in word:
        counts[char_to_index[c]] += 1
    return tuple(counts)


# def is_admissible_pair(w1, w2):
#     """ Test if words w1 and w2 are an admissible pair, i.e.
#     w1 = s1 + alpha + beta + s2
#     w2 = s1 + beta + alpha + s2
#     for characters alpha, beta and strings s1, s2. This will report correctly
#     even if w1, w2 aren't anagrams; but for best performance avoid calling
#     this on non-anagram input pairs. """
#     if len(w1) != len(w2):
#         return False 
# 
#     # assume that they are admissible, scan through until we have proof that
#     # they're not. The s1_end, s2_start flags tell us where we think we are in
#     # the process of scanning through the words
#     ret = True
#     s1_end, s2_start = False, False
#     for i in range(len(w1)):
#         if not s1_end and w1[i] != w2[i]:
#             alpha, beta = w1[i], w2[i]
#             s1_end = True
#             ret = False # set to False until we see the commutation happen
#         elif s1_end and not s2_start:
#             if w1[i] == beta and w2[i] == alpha:
#                 s2_start = True
#                 ret = True
#             else:
#                 ret = False
#                 break
#         elif s2_start and w1[i] != w2[i]:
#             ret = False
#             break
#         else: # this encompasses scanning through s1 and s2 if they agree
#             continue
#     ret = ret and s1_end and s2_start
#     if not ret:
#         return False
#     else:
#         return tuple(sorted([alpha, beta]))
# 
# 
#     """ TODO this reads more complex than the original; do some testing?
#     or maybe you're not actually gonna use this because you'll have the lists
#     of admissible siblings """


def admissible_siblings(word):
    for i in range(1, len(word)):
        if word[i-1] != word[i]:
            sibling = word[:i-1] + word[i] + word[i-1] + word[i+1:]
            pair = tuple(sorted([word[i-1], word[i]]))
            yield sibling, pair


def update_admissible_pairs(anagram_dict, pairs):
    """ iterate through the anagram_dict, searching for more admissible pairs.
    modify the set pairs in place by adding any newly found pairs. """
    for count in anagram_dict:
        for word in anagram_dict[count]:
            for sibling, pair in admissible_siblings(word):
                if sibling in anagram_dict[count]:
                    pairs.add(pair)
    return pairs


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


if __name__ == "__main__":
    dictionary_file = sys.argv[1]
    dictionary_data = process_dictionary(load_dictionary(dictionary_file)) 
    anagram_dict = build_anagram_dict(dictionary_data)
    pairs = set()

    count = 1
    while True:
        num_counts, num_pairs = len(anagram_dict), len(pairs)
        print(f"Step {count}")

        pairs = update_admissible_pairs(anagram_dict, pairs)
        anagram_dict = reduce_anagram_dict(anagram_dict, pairs)

        print(f"{num_counts} letter counts, {len(pairs)} admissible pairs")
        if num_counts == len(anagram_dict) and num_pairs == len(pairs):
            break
        count += 1



