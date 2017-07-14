# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import os
import re
import nltk
from decimal import Decimal
from profiles.models import Profile
from django.core.management.base import BaseCommand

import sys  
reload(sys)  
sys.setdefaultencoding('utf8')

def split_array(value):
    return str(value).split('|')

def to_decimal(value):
    return Decimal(value[1:]) or Decimal(0)

def median(lst):
    lst = sorted(lst)
    n = len(lst)
    if n < 1:
            return None
    if n % 2 == 1:
            return lst[n//2]
    else:
            return sum(lst[n//2-1:n//2+1])/2

def extract_fees(row):
    """
    This just finds the median occurence of a value written in GBP (as I am
    assuming concessions would lead to smaller prices, and there might me multi-
    session prices).
    There is one case of '$' being used but it is a typo so I just changed it
    in the DB and continue to search for '£'.
    TODO: finish more complex fee parser save all fees and their associated
    service
    """
    return median(map(to_decimal, re.findall('£\d+\s*(?:\.\d\d)?',
                    str(row['about_me']))))


# regexp to use to find if consessions are availible
match_concessions = re.compile(
    'income|student|unemployed|retired|discount|reduced|trainee|low|cost|poverty',
    re.IGNORECASE)

def concessions_availible(row):
    """
    Just finds the words that suggest consessions are availible
    """
    # if 'concession' is mentioned then we assume they allow concessions
    if unicode(row['about_me'], 'utf-8').lower().find('concession') != -1:
        return True
    # otherwise we are looking for at least 2 of the other words
    elif len(set(match_concessions.findall(str(row['about_me'])))) > 1:
        return True
    else:
        return False

# regexp to use to find if group/family
# group is to vaugue so try match 
# 1) references to group/family therapy
# 2) references to groups/families as a list of services
match_groups = re.compile(
    'groupwork|(groups? (therap\w+|counsell\w+|facilitat\w+|supervi\w+|of|and|or))|((to|with|for|and|or|small|therap\w+|support) groups?)',
    re.IGNORECASE)

match_families = re.compile(
    'families|(famil\w+ (therap\w+|counsell\w+|facilitat\w+|mediat\w+))|((small|therap\w+|support) famil\w+)',
    re.IGNORECASE)

def extract_client_types(row):
    """
    possible client types being "children", "couples", "groups" and "families"
    """
    client_types = set(['individuals'])

    if 'children' in row['about_me'] or 'young' in row['about_me']:
        client_types.add('children')
    if 'couple' in row['about_me']:
        client_types.add('couples')
    if match_groups.search(row['about_me']):
        client_types.add('groups')
    if match_families.search(row['about_me']):
        client_types.add('families')
    
    return list(client_types)

# MORE COMPLEX FEE PARSER
# ps = nltk.stem.PorterStemmer()
# chunkParser = nltk.RegexpParser('''
#     NP: {<DT>? <CD>? <JJ.*>* <NN.?|VBG>+}  # Noun (Like) Phrase
#     NP: {<\(NP\)>}                         # - bracketed
#     NP: {(<NP.?> <,>? <CC> <,>?)* <NP.?>}  # - conjoined
#     NP: {<NP> <IN> <NP>}                   # - described
#     V: {<V.*|:>}                           # Verb
#     PRICE: {<V|JJ|IN>* <£>}
#     SERVICE1: { (<NP.?> <TO|CC>)? <NP.?> <IN>? <,>? <PRICE>}
#     SERVICE2: { <PRICE> (<IN|FW>? <NP.?>)+}
#     ''')
# def parse(text):
#     # if we find ".<many space><Capiltal Letter>" then assume it is a new
#     # sentence, nltk.sent_tokenize misses these
#     clean_text = re.sub(r"£\s+", '£',
#         re.sub(r"\.?\s\s+[A-Z]", (lambda s: '. ' + s.group(0)[-1:]),
#         text))
#     sentences = nltk.sent_tokenize(clean_text
#         .replace('&amp;', 'and')
#         .replace('http://', '')
#         .replace('https://', ''))
#     parsed_sentences = [
#         chunkParser.parse([
#             (word, '£') if '£' in word else (word, tag)
#                 for word, tag in nltk.pos_tag(nltk.word_tokenize(sentence))])
#         for sentence in sentences if '£' in sentence]
#     # return parsed_sentences
#     for parsed in parsed_sentences:
#         for subtree in parsed.subtrees(filter=lambda x: x.label() in ['SERVICE1', 'SERVICE2', 'PRICE']):
#             yield ' '.join(map(lambda x: x[0], subtree.leaves()))


def leaves(tree):
    """Finds NP (nounphrase) leaf nodes of a chunk tree."""
    for subtree in tree.subtrees(filter = lambda t: t.label()=='NP'):
        yield subtree.leaves()

lemmatizer = nltk.WordNetLemmatizer()
stemmer = nltk.PorterStemmer()
def normalise(word):
    """Normalises words to lowercase and stems and lemmatizes it."""
    word = word.lower()
    word = stemmer.stem(word)
    word = lemmatizer.lemmatize(word)
    return word

stopwords =  nltk.corpus.stopwords.words('english')
def acceptable_word(word):
    """Checks conditions for acceptable word: length, stopword."""
    accepted = bool(2 <= len(word) <= 40
        and word.lower() not in stopwords)
    return accepted


def get_terms(tree):
    for leaf in leaves(tree):
        term = [ normalise(w) for w,t in leaf if acceptable_word(w) ]
        yield " ".join(term)

sentence_re = r'''(?x)      # set flag to allow verbose regexps
      ([A-Z])(\.[A-Z])+\.?  # abbreviations, e.g. U.S.A.
    | \w+(-\w+)*            # words with optional internal hyphens
    | \$?\d+(\.\d+)?%?      # currency and percentages, e.g. $12.40, 82%
    | \.\.\.                # ellipsis
    | [][.,;"'?():-_`]      # these are separate tokens
'''
chunker = nltk.RegexpParser(r"""
        NBAR:
            {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, 
                                # terminated with Nouns
            {<JJ|TO|^><VBG>}    # or Noun like Verbs
        NP:
            {<NBAR>}
            {<NBAR><IN|TO><NBAR>}  # Above, connected with in/of/to/etc...
                }$<JJ|TO>+{
    """)
def extract_keywords(row):
    text = re.sub(r"£\s+", '£',
        re.sub(r"\.?\s\s+[A-Z]", (lambda s: '. ' + s.group(0)[-1:]),
        row['about_me']))
    text = text.replace('&amp;', 'and').replace('http://', '').replace('https://', '')
    sentences = nltk.sent_tokenize(text)
    sentences = [nltk.pos_tag(nltk.word_tokenize(sentence)) for sentence in sentences]
    trees = [ chunker.parse(postoks) for postoks in sentences]
    return [term for tree in trees for term in get_terms(tree)]

class Command(BaseCommand):
    def handle(self, **options):
        # import itertools
        csv_path = os.path.join(os.path.dirname(__file__), 'test_dataset.csv')
        with open(csv_path, 'rt',encoding='utf-8') as csvfile:
            reader =  csv.DictReader(csvfile)
            for row in reader: #itertools.islice(reader,739, 740):
                profile = Profile(id=row['id'],
                    about_me=row['about_me'],
                    qualifications=row['qualifications'],
                    counselling_areas=split_array(row['counselling_areas']),
                    consultation_types=split_array(row['consultation_types']),
                    fees=extract_fees(row),
                    concessions_availible=concessions_availible(row),
                    client_types=extract_client_types(row),
                    keywords=extract_keywords(row))
                profile.save()
                print row['id'], 'saved'