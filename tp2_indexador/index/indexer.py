from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize
from bs4 import BeautifulSoup
import string
import nltk
import os


class Cleaner:
    def __init__(self,stop_words_file:str,language:str,
                        perform_stop_words_removal:bool,perform_accents_removal:bool,
                        perform_stemming:bool):
        self.set_stop_words = self.read_stop_words(stop_words_file)

        self.stemmer = SnowballStemmer(language)
        in_table =  "áéíóúâêôçãẽõü"
        out_table = "aeiouaeocaeou"

        self.accents_translation_table = in_table.maketrans(in_table, out_table)
        self.set_punctuation = set(string.punctuation)

        #flags
        self.perform_stop_words_removal = perform_stop_words_removal
        self.perform_accents_removal = perform_accents_removal
        self.perform_stemming = perform_stemming

    def html_to_plain_text(self,html_doc:str) ->str:
        return BeautifulSoup(html_doc, 'html.parser').get_text()

    def read_stop_words(self,str_file):
        set_stop_words = set()
        with open(str_file, "r", encoding='utf-8') as stop_words_file:
            for line in stop_words_file:
                arr_words = line.split(",")
                [set_stop_words.add(word) for word in arr_words]
                
        return set_stop_words
    
    def is_stop_word(self,term:str):
        return True if term in self.set_stop_words else False

    def word_stem(self,term:str):
        return self.stemmer.stem(term)

    def remove_accents(self,term:str) ->str:
        return term.translate(self.accents_translation_table)

    def preprocess_word(self,term:str) -> str:
        if self.perform_stop_words_removal and self.is_stop_word(term): term = ''
        if self.perform_accents_removal: term = self.remove_accents(term)
        if self.perform_stemming: term = self.word_stem(term)
        
        return term


class HTMLIndexer:
    cleaner = Cleaner(stop_words_file="stopwords.txt",
                        language="portuguese",
                        perform_stop_words_removal=True,
                        perform_accents_removal=True,
                        perform_stemming=True)
    def __init__(self,index):
        self.index = index

    def text_word_count(self,plain_text:str):
        text = nltk.word_tokenize(plain_text)
        dic_word_count = {}
        punctuation = ['.',',',':',';','!','?']
        
        for word in text:
            word = self.cleaner.preprocess_word(word)
            if word != '' and word != ' ' and word not in punctuation:
                dic_word_count[word] = dic_word_count[word] + 1 if word in dic_word_count else 1

        return dic_word_count
    
    def index_text(self,doc_id:int, text_html:str):
        plain_text = HTMLIndexer.cleaner.html_to_plain_text(text_html)
        text = self.text_word_count(plain_text)
        [self.index.index(term_id, doc_id, freq) for term_id, freq in text.items()]

    def index_text_dir(self,path:str):
        for str_sub_dir in os.listdir(path):
            path_sub_dir = f"{path}/{str_sub_dir}"
            
            for file_name in os.listdir(path_sub_dir):
                if file_name.endswith('.html'):
                    new_file_name = file_name.replace('.html', '')
                    with open(f"{path_sub_dir}/{file_name}",  encoding='utf-8') as file:
                        self.index_text(int(new_file_name), file)
