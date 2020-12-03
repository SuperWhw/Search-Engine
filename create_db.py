from os import listdir
import xml.etree.ElementTree as ET
import jieba
import sqlite3
import configparser
from text_process import *


class Doc:
    Doc_id = 0
    Doc_time = ''
    tf = 0
    ld = 0

    def __init__(self, docid, date_time, tf, ld):
        self.Doc_id = docid
        self.Doc_time = date_time
        self.tf = tf
        self.ld = ld

    def __repr__(self):
        return str(self.Doc_id) + '\t' + self.Doc_time + '\t' + str(self.tf) + '\t' + str(self.ld)
    
    def __str__(self):
        return str(self.Doc_id) + '\t' + self.Doc_time + '\t' + str(self.tf) + '\t' + str(self.ld)

class IndexModule:
    postings_lists = {}
    
    def __init__(self, config):
        self.config = config
        self.text_process = TextProcess(config)    
    
    def write_postings_to_db(self, db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute('''DROP TABLE IF EXISTS postings''')
        c.execute('''CREATE TABLE postings
                     (term TEXT PRIMARY KEY, df INTEGER, docs TEXT)''')

        for key, value in self.postings_lists.items():
            doc_list = '\n'.join(map(str,value[1]))
            t = (key, value[0], doc_list)
            c.execute("INSERT INTO postings VALUES (?, ?, ?)", t)

        conn.commit()
        conn.close()
    
    def construct_postings_lists(self):
        files = listdir(self.config['DEFAULT']['doc_file_path'])
        AVG_L = 0

        for f in files:
            root = ET.parse(self.config['DEFAULT']['doc_file_path'] + f).getroot()
            title = root.find('title').text
            body = root.find('body').text
            docid = int(root.find('id').text)
            date_time = root.find('datetime').text

            if int(docid) % 1000 == 0:
                print("1K Done." + str(docid))
            
            try:
                seg_list = jieba.lcut(title + '。' + body, cut_all=False)
            except:
                print("Jieba lcut Error.")
                print(title) 
                continue
            
            ld, cleaned_dict = self.text_process.clean_list(seg_list)
            
            AVG_L = AVG_L + ld
            
            for key, value in cleaned_dict.items():
                d = Doc(docid, date_time, value, ld)
                if key in self.postings_lists:
                    self.postings_lists[key][0] += 1
                    self.postings_lists[key][1].append(d)
                else:
                    self.postings_lists[key] = [1, [d]] # [df, [Doc]]
            
        AVG_L = AVG_L / len(files)
        self.config.set('DEFAULT', 'num_files', str(len(files)))
        self.config.set('DEFAULT', 'avg_l', str(AVG_L))
        with open(self.config['DEFAULT']['config_path'], 'w', encoding = self.config['DEFAULT']['config_encoding']) as configfile:
            self.config.write(configfile)
        
        self.write_postings_to_db(config['DEFAULT']['db_path'])

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("./config.ini", encoding="utf-8")
    im = IndexModule(config)
    im.construct_postings_lists()
