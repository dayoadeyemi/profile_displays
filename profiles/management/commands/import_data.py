# -*- coding: utf-8 -*-
import csv, os, re, itertools, nltk, codecs
from decimal import Decimal
from profiles.models import Profile
from django.core.management.base import BaseCommand

# regexp to use to find if consessions are availible
match_concessions = re.compile(
    'income|students|unemployed|retired|discount|reduced|trainee',
    re.IGNORECASE)

def split_array(value):
    return str(value).split('|')

def to_decimal(value):
    return Decimal(value[2:]) 

def extract_fees(row):
    """
    This just finds the highest occurence of a value written in GBP (as I am
    assuming concessions would lead to smaller prices), there is an issue here
    where some fees over multiple seesions are picked instead. There is one case
    of '$' being used but it is a typo so we just search for '£'.
    TODO: where multiple prices are found analyse the enclosing sentence to pick
    which one 
    """
    try: 
        return max(row['prices'])
    except ValueError:
        return None

def concessions_availible(row):
    """
    Just finds the words that suggest consessions are availible
    """
    # if 'concession' is mentioned then we assume they allow concessions
    if str(row['about_me']) .lower().find('concession') != -1:
        return True
    # otherwise we are looking for at least 2 of the other words
    elif len(set(match_concessions.findall(str(row['about_me'])))) > 1:
        return True
    else:
        return False

ps = nltk.stem.PorterStemmer()
stopwords = set(nltk.corpus.stopwords.words("english"))
chunkGram = r"""Chunk: {<.*>+}
                                    }<VB.?|IN|DT|TO>+{"""
chunkParser = nltk.RegexpParser(chunkGram)
def parse(text):
    sentences = nltk.sent_tokenize(unicode(text, 'utf-8'))
    return [chunkParser.parse(nltk.pos_tag([ps.stem(word) for word in
        nltk.word_tokenize(sentence) if ps.stem(word) not in stopwords])) for sentence in sentences]

class Command(BaseCommand):
    def handle(self, **options):
        csv_path = os.path.join(os.path.dirname(__file__), 'test_dataset.csv')
        with open(csv_path, 'rb') as csvfile:
            reader =  csv.DictReader(csvfile)
            for row in itertools.islice((row for row in reader), 10):
                # extract the prices
                row['prices'] = map(to_decimal, re.findall('£\d+\s*(?:\.\d\d)?',
                    str(row['about_me'])))
                for t in parse(row['about_me']):
                    t.draw()
                profile = Profile(id=row['id'],
                    about_me=row['about_me'],
                    qualifications=row['qualifications'],
                    counselling_areas=split_array(row['counselling_areas']),
                    consultation_types=split_array(row['consultation_types']),
                    fees=extract_fees(row),
                    concessions_availible=concessions_availible(row))
                profile.save()
                print row['id'], 'saved'