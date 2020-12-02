from collections import Counter


class TextProcess:
    stop_words = set()

    def __init__(self, config):
        with open(config['DEFAULT']['stop_words_path'], encoding = config['DEFAULT']['stop_words_encoding']) as f:
                stop_words = f.read()
        self.stop_words = set(stop_words.split('\n'))
    
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
        
    def clean_list(self, seg_list):
        cleaned_dict = Counter()
        n = 0
        for word in seg_list:
            word = word.strip().lower()
            if word != '' and not self.is_number(word) and word not in self.stop_words:
                n += 1
                cleaned_dict[word] += 1
        return n, dict(cleaned_dict)