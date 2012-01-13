#!/usr/bin/python -O

import random
import math
import argparse
import os
import sys
import heapq

# The dictionary bundled with the script. It must be in the same
# dir as the script.
DEFAULT_DICT= os.path.dirname(sys.argv[0]) + "/dict"
# Uncomment to use the system dictionary as the default.
DEFAULT_DICT="/usr/share/dict/words"
WORDS = 4
BAD_CH_LIST = ['\'']

class WordValidator(object):
    def __init__(self, flags):
        self._badChars = BAD_CH_LIST
        self._maxLen = flags.l
        self._skipBad = flags.x

    def isValidWord(self, word):
        if len(word) > self._maxLen or len(word) == 0:
            return False
        if self._skipBad and self._hasBadChar(word):
            return False
        return True

    def _hasBadChar(self, word):
        for char in word:
            if char in self._badChars:
                return True

class Dictionary(object):
    def __init__(self, flags):
        self._dictLen = 0
        self._wordValidator = WordValidator(flags)

class DictionaryList(Dictionary):
    def __init__(self, flags):
        super(DictionaryList, self).__init__(flags)
        self._loadDict(flags.d)

    def __getitem__(self, key):
        return self._dictList[key]

    def __len__(self):
        return self._dictLen

    def _loadDict(self, path):
        self._dictList = []
        dict_file = file(path)
        for line in dict_file:
            word = line.strip()
            if self._wordValidator.isValidWord(word):
                self._dictList.append(word)
        self._dictLen = len(self._dictList)

class RandomDict(object):
    def __init__(self, flags):
        self._dictObj = DictionaryList(flags)
        self._rng = random.SystemRandom()

    def __iter__(self):
        return self

    def __len__(self):
        return len(self._dictObj)

    def next(self):
        return self._dictObj[self._rng.randint(0, len(self) - 1)]

    def __getattr__(self, attr):
        return getattr(self._dictObj, attr)

class RandomDictLowMem(Dictionary):
    def __init__(self, flags):
        super(RandomDictLowMem, self).__init__(flags)
        self._wordCount = flags.w
        self._rng = random.SystemRandom()
        self._dictLen = 0
        self._dictList = []
        self._loadDict(flags.d)

    def _makeValWordTuple(self, word):
        return (self._rng.random(), word)

    def _loadDict(self, path):
        word_q=[]
        self._dictLen = 0
        dict_file = open(path)
        # Load the first n items into the word queue.
        count = 0
        while count < self._wordCount:
            line = dict_file.next()
            word = line.strip()
            if self._wordValidator.isValidWord(word):
                val_word = self._makeValWordTuple(word)
                heapq.heappush(word_q, val_word)
                count += 1
                self._dictLen += 1

        # Iterate through the entire dictionary, giving each word a
        # random value, then pushing and popping from the queue. At
        # the end, the queue will have n words with the highest random
        # values.
        for line in dict_file:
            word = line.strip()
            if self._wordValidator.isValidWord(word):
                val_word = self._makeValWordTuple(word)
                heapq.heappushpop(word_q, val_word)
                self._dictLen += 1

        # Put the queued items in a list, and strip them of their
        # random values.
        self._dictList = []
        val_word_list = heapq.nlargest(self._wordCount, word_q)
        for rand_val, word in val_word_list:
            self._dictList.append(word)

    def __iter__(self):
        cur_word = 0
        for word in self._dictList:
            yield word
        raise StopIteration

    def __len__(self):
        return self._dictLen

class PasswordGen(object):
    def __init__(self, flags):
        if flags.m:
            self._randSource = RandomDictLowMem(flags)
        else:
            self._randSource = RandomDict(flags)
        self._wordCount = flags.w
        self._delimiter = flags.s

    def __iter__(self):
        return self

    def next(self):
        rand_source_iter = iter(self._randSource)
        word_list = [rand_source_iter.next() for i in range(self._wordCount)]
        return self._delimiter.join(word_list)

    def getInfo(self):
        entropy = math.log(len(self._randSource) ** self._wordCount, 2)
        info =  "\nInfo:\n"
        info += "  Entropy: %f bits\n" % entropy
        info += "  Entropy per word: %f bits" % (entropy / self._wordCount)
        return info

def createParser():
    parser = argparse.ArgumentParser(
            description='Generate an xkcd style password.',
            epilog='http://xkcd.com/936/')
    parser.add_argument('w',
            type=int,
            default=WORDS,
            nargs='?',
            help="The number of words in the password. Defaults to 4.")
    parser.add_argument('-d',
            default=DEFAULT_DICT,
            help="The dictionary file. Defaults to %s." % DEFAULT_DICT)
    parser.add_argument('-x',
            action='store_false',
            default=True,
            help="Disable excluding special characters and punctuation.")
    parser.add_argument('-i',
            action='store_true',
            default=False,
            help="Enable showing password information (entropy, etc).")
    parser.add_argument('-s',
            default='-',
            help="Delimit words with a given character/string.")
    parser.add_argument('-l',
            default=100,
            type=int,
            help="The maximum word length. Words must be at or below this length.")
    parser.add_argument('-m',
            action='store_true',
            default=False,
            help="Enable the low memory algorithm.")
    return parser

if __name__ == "__main__":
    parser = createParser()
    flags = parser.parse_args()
    pGen = PasswordGen(flags)
    print pGen.next()
    if flags.i:
        print pGen.getInfo()
