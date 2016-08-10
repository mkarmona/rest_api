'''
Created on Aug 18, 2016

@author: pwankar
'''
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS
from spacy import en
import string
from spacy.en import English


parser = English()

# A custom stoplist
STOPLIST = set()
STOPLIST.update(en.STOPWORDS)
STOPLIST.update(["n't", "'s", "'m", "ca","p"])
STOPLIST.update(list(ENGLISH_STOP_WORDS))
# List of symbols we don't care about
SYMBOLS = " ".join(string.punctuation).split(" ") + ["-----", "---", "...",  "'ve"] 


class TextPreProcessor():
    
    def __init__(self):
        pass

    def tokenize_text(self,sample):

        # get the tokens using spaCy
        tokens = parser(sample)

        # lemmatize
        lemmas = []
        for tok in tokens:
            lemmas.append(tok.lemma_.lower().strip() if tok.lemma_ != "-PRON-" else tok.lower_)
            tokens = lemmas

        # stoplist the tokens
        tokens = [tok for tok in tokens if tok not in STOPLIST]

        # stoplist symbols
        tokens = [tok for tok in tokens if tok not in SYMBOLS]

        # remove large strings of whitespace
        while "" in tokens:
            tokens.remove("")
        while " " in tokens:
            tokens.remove(" ")
        while "\n" in tokens:
            tokens.remove("\n")
        while "\n\n" in tokens:
            tokens.remove("\n\n")
        #print tokens
        return tokens
        