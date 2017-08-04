import zipcode
from nltk.corpus import stopwords 
from nltk.stem.wordnet import WordNetLemmatizer

import gensim
import random
from gensim import corpora

import json, re, string

def get_plain_text(text, list_of_indices):
	start = 0
	plain_text = ""
	list_of_indices.sort(key=lambda x: x[0])
	for indices in list_of_indices:
		plain_text += text[start:indices[0]]
		start = indices[1] + 1
	plain_text += text[start:]
	return plain_text

def coords2zipcode(latlon, radius=1.5):
	try:
		return zipcode.isinradius(latlon, radius)[0].zip
	except:
		zipcodes = [11232, 10001, 11211, 10026, 11101]
		zipcode = random.sample(zipcodes, 1)[0]
		print (zipcode)
		return zipcode

### Cleaning Data
stop = set(stopwords.words('english') + ['amp', 'rt', '—'])
lemma = WordNetLemmatizer()
translator = str.maketrans(dict.fromkeys(string.punctuation))

def clean(doc):
    punc_free = doc.translate(translator)
    stop_free = " ".join([i for i in punc_free.lower().split() if i not in stop])
    url_free = re.sub(r"http\S+", '', stop_free)
    normalized = " ".join(lemma.lemmatize(word) for word in url_free.split())
    return normalized

#clean and produce bag of words from a list of tweets
def getDocBoW(docs):
    doc_clean = [clean(doc).split() for doc in docs]
    dictionary = corpora.Dictionary(doc_clean)
    return  [dictionary.doc2bow(doc) for doc in doc_clean]

def flatten(list_of_lists):
    return [val for sublist in list_of_lists for val in sublist]