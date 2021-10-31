import copy
import sys

letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
            'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
            'w', 'x', 'y', 'z']

letter_pairs = []
for i in range(26):
    for j in range(i+1, 26):
        letter_pairs.append((letters[i], letters[j]))

def letter_counts(word):
	# return a tuple with the number of occurences of each letter in word
	d = {}
	for x in letters:
		d[x] = word.count(x)	
	return tuple([d[x] for x in letters])

def is_anagram(w1, w2):
	# test if w1 and w2 are anagrams
	if len(w1) != len(w2):
		return False

	c1 = letter_counts(w1)
	c2 = letter_counts(w2)
	return c1 == c2

def is_admissible_pair(w1, w2):
	""" test if the anagrams w1, w2 are a single commutation away from each
	other i.e. of the form s_1 alpha beta s_2, s_1 beta alpha s_2"""

	diff_indices = []
	for i in range(len(w1)):
		if w1[i] != w2[i]:
			diff_indices.append(i)

	if len(diff_indices) != 2:
		return False
	elif diff_indices[0] + 1 != diff_indices[1]:
		return False
	else: 
		# return a sorted tuple of the letters
		alpha = w1[diff_indices[0]]
		beta = w1[diff_indices[1]]
		return tuple(sorted((alpha, beta)))

def reduce_count(count, pairs):
	""" given a letter count and list of admissible pairs, determine the
	reduced letter count """

	new_count = [0]*26
	chars = [i for i in range(26) if count[i] != 0]

	for i in chars:
		flag = True
		for j in chars:
			if i != j and tuple(sorted([letters[i], letters[j]])) not in pairs:
				flag = False

		if not flag:
			new_count[i] = count[i]
	return tuple(new_count)

def reduce_word(word, count):
	""" delete the letters from word to make it have letter count the one
	coming from count. This could backfire if you don't use it carefully."""

	red_word = word
	for i in range(26):
		if count[i] == 0:
			red_word = red_word.replace(letters[i], '')
	return red_word	

def load_dictionary(name):
	# load a dictionary text file without doing any processing
	raw = []
	with open(name, 'r') as f:
		for line in f:
			raw.append(line)
	return raw 

def process_dictionary(raw):
	# prepare the dictionary
	dictionary = []
	for x in raw:
		# remove new line
		w = x[:-1]
		w = w.lower()
		if w.isalpha():
			dictionary.append(w)	
	return dictionary

def build_anagrams(dictionary):
	anagram_dict = {}
	for w in dictionary:
		c = letter_counts(w)
		if c in anagram_dict.keys():
			anagram_dict[c].append(w)
		else:
			anagram_dict[c] = [w]	

	to_delete = [c for c in anagram_dict.keys() if len(anagram_dict[c]) <= 1]
	for c in to_delete:
		del anagram_dict[c]

	return anagram_dict

def build_anagraphs(dictionary):
	""" given a dictionary, build the following structure
	- a python dictionary, whose keys are letter_counts
	- for each key, a graph whose vertices are all anagrams with that key
	- the graph at this stage will be complete; any anagrams w1, w2
	give the relation w1=w2 in A
	- at each vertex store a list; at this stage the list is just the word
	at that vertex
	"""

	anagram_dict = build_anagrams(dictionary)

	anagraph_dict = {}
	for c in anagram_dict:
		anagraph_dict[c] = Graph(loops=True)
		anagraph_dict[c].add_clique(anagram_dict[c], loops=True)

	return anagraph_dict

def find_admissible_pairs(anagraphs):
	""" given a dictionary of anagraphs, find a list of admissible pairs """

	admissible_pairs = {}

	for c in anagraphs:
		word_pairs = anagraphs[c].edges()

		for wp in word_pairs:
			w1 = wp[0]
			w2 = wp[1]
			pair = is_admissible_pair(w1, w2)
			if pair and pair in admissible_pairs:
				admissible_pairs[pair].append((w1, w2))
			elif pair:
				admissible_pairs[pair] = [(w1, w2)]
	return admissible_pairs

def reduce_anagraphs(anagraphs_old, pairs):
	"""  given an anagraph dictionary and list of admissible pairs, construct
	a new anagraph dictionary with vertices all the reduced words and edges
	all the reduced edges and any newly implied edges. This has the effect of
	possible generating new relations by connecting previously unconnected
	graphs. """

	anagraphs_new = {}

	for c in anagraphs_old:
		red_c = reduce_count(c, pairs)
		red_w = [reduce_word(w, red_c) for w in anagraphs_old[c].vertices()]

		if red_c not in anagraphs_new.keys():	
			anagraphs_new[red_c] = Graph(loops=True)
		anagraphs_new[red_c].add_vertices(red_w)

		for e in anagraphs_old[c].edges():
			w1 = reduce_word(e[0], red_c)
			w2 = reduce_word(e[1], red_c)
			anagraphs_new[red_c].add_edge(w1, w2)

		# edges are relations w_1=w_2, so by transitivity of equality
		# all the connected components should become complete
		for c in anagraphs_new[red_c].connected_components():
		 	if not anagraphs_new[red_c].is_clique(c, induced=False):
		 		anagraphs_new[red_c].add_clique(c, loops=True)

		anagraphs_new[red_c].remove_multiple_edges()
		anagraphs_new[red_c].remove_loops()


	to_delete = [c for c in anagraphs_new.keys() if len(anagraphs_new[c].vertices()) <=1]
	for c in to_delete:
		del anagraphs_new[c]

	return anagraphs_new

def update_admissible_pairs(anagraphs, pairs):
	""" find admissible_pairs in the current anagraph dictionary, and merge
	with the existing pairs."""
	new_pairs = copy.deepcopy(pairs)

	aps = find_admissible_pairs(anagraphs)

	for p in aps:
		if p not in new_pairs.keys():
			new_pairs[p] = aps[p]

	return new_pairs


def is_useful_history(ls, x):
	""" for a pair of letters x, and list of anagrams ls, strip out all of
	the characters except those in x. If more than one pattern of x0, x1
	appears return that list, otherwise return False. """
	new_ls = []
	for w in ls:
		stripped = "".join([c for c in w if c in x])
		if stripped not in new_ls:
			new_ls.append(stripped)

	ret = True
	if len(new_ls) <= 1:
		return False
	return ret


if __name__ == "__main__":
	dict_name = sys.argv[1]
	raw = load_dictionary(dict_name)
	dictionary = process_dictionary(raw)

	anagraphs = build_anagraphs(dictionary)
	pairs = find_admissible_pairs(anagraphs)
	l1 = len(anagraphs.keys())
	l2 = len(pairs.keys())
	print(l1, l2)

	# this loop iteratively finds more admissible pairs and updates the
	# anagraphs; it breaks when an iteration doesn't find any new admissible
	# pairs and doesn't combine any anagraphs
	count = 1
	while True:

		with open("pairs_{}.txt".format(count), 'w') as fout:
			for x in letter_pairs:
				if x in pairs:
					fout.write("{}, {}\n".format(x, pairs[x]))

		anagraphs = reduce_anagraphs(anagraphs, pairs)
		pairs = update_admissible_pairs(anagraphs, pairs)

		print(len(anagraphs.keys()), len(pairs.keys()))

		if len(anagraphs.keys()) == l1 and len(pairs.keys()) == l2:
			break
		else:
			l1 = len(anagraphs.keys())
			l2 = len(pairs.keys())
			count += 1


	# make good pairs and bad pairs files
	good_pairs = []
	bad_pairs = []

	for x in letter_pairs:
		if x in pairs:
			good_pairs.append(x)
		else:
			bad_pairs.append(x)
	with open("pairs_good.txt", 'w') as fout:
		for x in good_pairs:
			fout.write("{}\n".format(x))
	with open("pairs_bad.txt", 'w') as fout:
		for x in bad_pairs:
			fout.write("{}\n".format(x))

	# make irreds file
	# this lists all the remaining anagram relations that can't be reduced
	with open("irreds.txt", 'w') as fout:
		for c in anagraphs:
			fout.write("{}\n".format(anagraphs[c].vertices()))

	# make history files
	# for each pair of letters, find all original anagram sets where the
	# pattern of the two letters appearing is different
	anagram_dict = build_anagrams(dictionary)
	for x in letter_pairs:
		x0 = ord(x[0]) - 97
		x1 = ord(x[1]) - 97
		with open("history/history_{}{}.txt".format(x[0], x[1]), 'w') as fout:
			for c in anagram_dict:
				if c[x0] > 0 and c[x1] > 0:
					if is_useful_history(anagram_dict[c], x):
						fout.write("{}\n".format(anagram_dict[c]))