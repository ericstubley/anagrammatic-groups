# anagrammatic-groups

This program reads in an english language dictionary as a text file, and outputs a number of text files having to do with the structure of the anagrammatic group with that dictionary.
The math article talking about this project can be found at https://arxiv.org/abs/2111.04517.
Shoot me an email at ericdavidstubley@gmail.com if you stumble across this and are curious to learn more!

Input:
------

This program should be called from the command line as follows:

`python3 find_anagrams.py dictionary.txt`

The file `dictionary.txt` should be a text file containing one word per line of the intended dictionary.

Output:
-------

The program produces a small amount of output on the command line, and a number of text files.
At each iteration of the main loop of the program, the number of current anagraphs and number of currently found anagram pairs (out of 325 = 26 choose 2 possible) is printed.
The following text files are produced as output:

`pairs_i.txt`: at the i-th iteration of the main loop, this text file is created listing for each admissible pair of letters all the current anagrams which realize that commutator. In tests with a number of different dictionaries the number of iterations never exceeded 10.

`pairs_good.txt`: the list of all commutators of two letters exhibited by the program at the end of the main loop

`pairs_bad.txt`: complement of the previous list; list of all commutators of two letters not exhibited by the program at the end of the main loop

`irreds.txt`: the list of all the starting anagram relations which have not been reduced away by the end of the main loop. To fully understand the structure of the anagrammatic group these relations must be dealt with manually.

`history/history_xy.txt`: for each pair of letters x, y, this file contains the list of all anagram sets from the dictionary where the letters x, y appear in different patterns; these anagram pairs are the only one which can ever contribute to commutators of x and y. Placed in a new folder to avoid spamming the current directory with 325 text files.
