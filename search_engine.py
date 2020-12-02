import jieba
import math
import sys
import operator
import sqlite3
import configparser
from datetime import *
from text_process import *

class SearchEngine:
    
    def __init__(self, config_path, config_encoding):
        self.config_path = config_path
        self.config_encoding = config_encoding
        config = configparser.ConfigParser()
        config.read(config_path, config_encoding)
        self.text_process = TextProcess(config)
        self.conn = sqlite3.connect(config['DEFAULT']['db_path'])
        self.K1 = float(config['DEFAULT']['k1'])
        self.B = float(config['DEFAULT']['b'])
        self.N = int(config['DEFAULT']['n'])
        self.AVG_L = float(config['DEFAULT']['avg_l'])
        

    def __del__(self):
        self.conn.close()

    def fetch_from_db(self, term):
        c = self.conn.cursor()
        c.execute('SELECT * FROM postings WHERE term=?', (term,))
        return(c.fetchone())

    def result_by_BM25(self, sentence):
        seg_list = jieba.lcut(sentence, cut_all=False)
        n, cleaned_dict = self.text_process.clean_list(seg_list)
        BM25_scores = {}
        for term in cleaned_dict.keys():
            r = self.fetch_from_db(term)
            if r is None:
                continue
            df = r[1]
            w = math.log2((self.N - df + 0.5) / (df + 0.5))
            docs = r[2].split('\n')
            for doc in docs:
                docid, date_time, tf, ld = doc.split('\t')
                docid, tf, ld = int(docid), int(tf), int(ld)
                s = (self.K1 * tf * w) / (tf + self.K1 * (1 - self.B + self.B * ld / self.AVG_L))
                BM25_scores[docid] = BM25_scores[docid]+s if docid in BM25_scores else s
        
        BM25_scores = sorted(BM25_scores.items(), key=lambda x: x[1], reverse=True)
        return BM25_scores
    
    def result_by_time(self, sentence):
        seg_list = jieba.lcut(sentence, cut_all=False)
        n, cleaned_dict = self.text_process.clean_list(seg_list)
        now_datetime = datetime.now()
        time_scores = {}
        for term in cleaned_dict.keys():
            r = self.fetch_from_db(term)
            if r is None:
                continue
            docs = r[2].split('\n')
            for doc in docs:
                docid, date_time, tf, ld = doc.split('\t')
                if docid in time_scores:
                    continue
                docid, tf, ld = int(docid), int(tf), int(ld)
                news_datetime = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
                td = timedelta.total_seconds(now_datetime - news_datetime) / 3600
                time_scores[docid] = td
        
        time_scores = sorted(time_scores.items(), key = lambda x: x[1])
        return time_scores
    
    def result_by_hot(self, sentence):
        seg_list = jieba.lcut(sentence, cut_all=False)
        n, cleaned_dict = self.text_process.clean_list(seg_list)
        now_datetime = datetime.now()
        hot_scores = {}
        for term in cleaned_dict.keys():
            r = self.fetch_from_db(term)
            if r is None:
                continue
            df = r[1]
            w = math.log2((self.N - df + 0.5) / (df + 0.5))
            docs = r[2].split('\n')
            for doc in docs:
                docid, date_time, tf, ld = doc.split('\t')
                docid, tf, ld = int(docid), int(tf), int(ld)
                BM25_score = (self.K1 * tf * w) / (tf + self.K1 * (1 - self.B + self.B * ld / self.AVG_L))
                news_datetime = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
                td = timedelta.total_seconds(now_datetime - news_datetime) / 3600

                hot_score = math.log(BM25_score) + 3000 / td
                hot_scores[docid] = hot_scores[docid]+hot_score if docid in hot_scores else hot_score
        
        hot_scores = sorted(hot_scores.items(), key = lambda x: x[1], reverse=True)
        return hot_scores

    def search(self, sentence, sort_type = 0):
        if sort_type == 0:
            return self.result_by_BM25(sentence)
        elif sort_type == 1:
            return self.result_by_time(sentence)
        elif sort_type == 2:
            return self.result_by_hot(sentence)

if __name__ == "__main__":
    se = SearchEngine('./config.ini', 'utf-8')
    rs = se.search('新冠', 0)
    print(rs)