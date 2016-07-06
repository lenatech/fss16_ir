#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import itertools
import jieba
import json
import re
import sqlite3
import ssl
import urllib
from bs4 import BeautifulSoup
from progressbar import ProgressBar


class Translator(object):

    def __init__(self, query):
        self.query = query
        self.query_translations = []

    def translate(self):
        base_url = 'http://dict-co.iciba.com/api/dictionary.php?'

        for word in self.query:
            if word == 'the' or word == 'a' or word == 'an' or word == 'to':
                continue

            url_arg = {
                    'type': 'json',
                    'key':  '78D373D431ECE0514D9A710C7453D375',
                    'w': word.encode('utf-8')
                    }

            api_url = base_url + urllib.urlencode(url_arg)
            unverified_context = ssl._create_unverified_context()
            content = urllib.urlopen(api_url, context=unverified_context).read()
            data = json.loads(content)

            word_translations = []
            for part in data[u'symbols'][0][u'parts']:
                for mean in part[u'means']:
                    meaning = mean.encode('utf-8')
                    meaning = re.compile("\s+|【.*?】+|\[.*?\]+|（.*?）+|[\.0-9]+|[a-zA-Z0-9]").sub('', meaning)
                    meaning = re.split(u'[\uff1b\uff0c\n]', meaning.decode("utf8"))

                    for m in meaning:
                        if len(m) > 4 or len(m) == 0:
                            continue

                        if m not in word_translations:
                            word_translations.append(m)

            self.query_translations.append(word_translations)

    def get_translations(self):
        return self.query_translations


class Evaluation(object):

    def __init__(self):
        jieba.set_dictionary('dict.txt')
        self.doc_tokens = []
        self.query_tokens = []

    def set_doc(self, doc):
        self.doc_tokens = [token for token in jieba.cut(doc, cut_all=True)]

    def set_query(self, query):
        self.query_tokens = query

    def unigram(self):
        self.uni_score = 1.0

        for word in self.query_tokens:
            count = self.count_one_word_in_doc(word)

            self.uni_score = self.uni_score * count / len(self.doc_tokens)

        return self.uni_score

    def bigram(self):
        self.bi_score = 1.0

        for i in range(len(self.query_tokens) - 1):
            count_former = self.count_one_word_in_doc(self.query_tokens[i])
            count_latter = self.count_two_words_in_doc(self.query_tokens[i], self.query_tokens[i + 1])

            if count_former == 0.0:
                return 0.0
            else:
                self.bi_score = self.bi_score * count_latter / count_former

        return self.bi_score

    def count_one_word_in_doc(self, word):
        count = 0.0

        for token in self.doc_tokens:
            if token == word:
                count += 1.0

        return count

    def count_two_words_in_doc(self, word_former, word_latter):
        count = 0.0

        for i in range(len(self.doc_tokens)):
            if self.doc_tokens[i] == word_former:
                j = i + 1
                while j <= i + 20 and j < len(self.doc_tokens):
                    if self.doc_tokens[j] == word_latter:
                        count += 1.0

                    j += 1

        return count


if __name__ == '__main__':
    docs = []
    queries = []
    evaluator = Evaluation()

    standards = sqlite3.connect('db.sqlite')
    docs = standards.execute('SELECT content FROM table_food UNION SELECT content FROM table_trip;')


    while True:
        print 'What do you want to translate?'
        query_tokens = [q.lower() for q in raw_input('> ').split(' ')]

        translator = Translator(query_tokens)
        translator.translate()
        query_translations = translator.get_translations()

        combinations = list(itertools.product(*query_translations))

        top_uni_score = 0.0
        top_uni_translation = 'NOT FOUND'
        top_bi_score = 0.0
        top_bi_translation = 'NOT FOUND'
        bar = ProgressBar()

        for c in bar(combinations):
            translation = ''
            standards = sqlite3.connect('db.sqlite')

            for meaning in c:
                translation += meaning
            
            docs = standards.execute('SELECT content FROM table_food UNION SELECT content FROM table_trip;')

            for doc in docs:
                evaluator.set_doc(doc[0])
                evaluator.set_query(c)

                uni = evaluator.unigram()

                if uni > top_uni_score:
                    top_uni_score = uni
                    top_uni_translation = translation

                if top_bi_score < 1.0:
                    bi = evaluator.bigram()

                    if bi > top_bi_score:
                        top_bi_score = bi
                        top_bi_translation = translation


        print 'Unigram: ' + top_uni_translation + '(' + str(top_uni_score) + ')'
        print 'Bigram: ' + top_bi_translation + '(' + str(top_bi_score) + ')'
        print '\n'
