# -*- coding: utf-8 -*-
__author__ = "Zhoulg1"
"""
从人卫教材中抽取疾病，包括疾病名，病因，并发症等等。
"""

import pandas as pd
import re
import numpy as np
import json
import codecs
import sys
if not sys.version > '3':
    reload(sys)
    sys.setdefaultencoding('utf-8')

pat = {u'章': u' *第[一二三四五六七八九十]+章',
       u'节': u' *第[一二三四五六七八九十]+节 ',
       u'块一': u' *[一二三四五六七八九十]+、',
       u'块二': u' *\([一二三四五六七八九十]+\)',
       u'病部': u' *【.*】'
       }

des_field = {
    'cause': u'【病因】',
    'pathogenesis': u'【发病机制】',
    'pathophysiological': u'【病理】',
    'clinical_manifestation': u'【临床表现】',
    'complication': u'【并发症】',
    'lab_check': u'【实验室检查】',
    'other_check': u'【辅助检查】',
    'diagnosis': u'【诊断】',
    'differential_diagnosis': u'【鉴别诊断】',
    'treatment': u'【治疗】',
    'prevention': u'【预防】',
    'prognosis': u'【预后】'}

des_fil = des_field.values()


class BookParser(object):
    def __init__(self, book, pat):
        self.book = book
        self.pat = pat
        pass

    def read_data(self):
        df = pd.read_table(self.book, header=None)
        return df

    def read_sample_data(self, n):
        df = pd.read_table(self.book, header=None)
        return df.sample(n)

    def read_seq_data(self, start=0, end=100):
        df = pd.read_table(self.book, header=None)
        return df.iloc[start:end, ]

    def pre_processing(self, rbook):
        df = rbook.copy()
        df.columns = ['line']
        if not sys.version > '3':
            df.line = df.line.str.decode('utf8').str.strip()
        else:
            df.line = df.line.str.strip()
        drop_lines_msk = df.line.str.match(u'e书联盟电子书下载www.book118.com')
        df = df.loc[~drop_lines_msk]
        df.index = np.arange(df.shape[0])
        return df

    def _mark_line(self, line):
        snl = []
        for sn, pattern in self.pat.items():
            if re.match(pattern, line):
                snl.append(sn)
        if len(snl) == 1:
            return snl[0]
        elif len(snl) == 0:
            return u'正文'
        else:
            print("######### pattern conflict in _mark_line() ##########")
            raise Warning

    def mark_lines(self, ppro):
        df = ppro.copy()
        df['label'] = df.line.apply(lambda line: self._mark_line(line))
        return df

    def mark_block(self, mklines):
        df = mklines.copy()
        df['blk'] = None
        blk = 1
        i = df.shape[0]
        print('mark_block is processing.\ndata total lines: ', i)
        while i > 0:
            i = i - 1
            j = i
            while j > 0 and df.loc[j, 'label'] in {u'正文', u'病部'}:
                j = j - 1
            if i - j > 5:
                if df.loc[j + 1:i, 'label'].unique().shape[0] == 2:
                    df.loc[j:i, 'blk'] = blk
                    blk = blk + 1
                    i = j
        return df

    def filter_block(self, mkblk, des_fil=None):
        print('filter_block is processing')
        new_blk = 1
        if des_fil:
            df = mkblk.copy()
            blks = set(df.blk.dropna().tolist())
            for blk in blks:
                print('old: ', blk)
                msk = df.loc[(df.blk == blk) & (df.label == u'病部'), 'line']
                if (msk.shape[0] == msk.unique().shape[0]) and msk.isin(des_fil).any():  # 出现一次
                    print('new: ', new_blk)
                    df.loc[df.blk == blk, 'blk'] = new_blk
                    new_blk += 1
                else:
                    df.loc[df.blk == blk, 'blk'] = None
            return df

    def extract(self, fblk):
        print('extract is processing')
        grd = fblk.groupby('blk')
        df = grd.nth(1)
        pat1 = u'(?P<chinese_name>[\u4e00-\u9fa5a-zA-Z]+)\((?P<english_name>[^\)]+)\)'
        name = df.line.str.extract(pat1)
        df['ch_name'] = name.chinese_name
        df['en_name'] = name.english_name
        df['definition'] = 0
        df = df.join(pd.DataFrame(columns=des_fil))  # 初始化
        for blk, gp in grd:
            rows = np.arange(1, gp.shape[0])
            defn = []
            for i in rows:
                if gp.iloc[i].label == u'正文':
                    defn.append(gp.iloc[i].line)
                    continue
                else:
                    df.loc[blk, 'definition'] = ''.join(defn)
                    head = i
                    break
            d = {}
            contents = []
            while head in rows:
                content = head + 1
                if gp.iloc[head].label == u'病部':
                    while (content in rows) and gp.iloc[content].label == u'正文':
                        dline = gp.iloc[content].line
                        if dline[-1] == u'。':
                            dline = dline + '\n'
                        contents.append(dline)
                        content += 1
                    d[gp.iloc[head].line] = ''.join(contents)
                    contents = []
                    head = content
            for col in des_fil:
                df.loc[blk, col] = d.get(col)
        return df

    def process(self, do_analysis=False):
        print('pipeline process is processing')
        rbook = self.read_data()
        ppro = self.pre_processing(rbook)
        mklines = self.mark_lines(ppro)
        mkblk = self.mark_block(mklines)
        fblk = self.filter_block(mkblk, des_fil)
        extract = self.extract(fblk)
        print(extract.count(0))
        if not do_analysis:
            return extract
        else:
            return rbook, ppro, mklines, mkblk, fblk, extract

    def save_to_dict(self, output_path, print_name=True, print_detail=False):
        print('save_to_dict is processing')
        df = self.process()
        col_map = {val: key for key, val in des_field.items()}
        col_map['en_name'] = 'disease_name_en'
        df.rename(columns=col_map, inplace=True)
        df = df.loc[df.ch_name.notnull()].copy()
        df = df.drop([u'label', u'line'], axis=1)
        df.fillna('', inplace=True)
        df = df.applymap(lambda s: s.encode('utf-8'))
        print('=== data prepared to dict ===\n', df.count(0))
        diseases = {}
        for row in df.index:
            val = df.loc[row].to_dict()
            key = df.ch_name.loc[row]
            diseases[key] = val
        if print_name:
            count = 0
            for name, disease in diseases.items():
                count += 1
                print('===============================')
                print('count: ', count)
                print('dname:', name)
                if print_detail:
                    for field, content in disease.items():
                        if not content == '':
                            print(field + ':\n', content)
        disease_json = json.dumps(diseases, ensure_ascii=False)
        f_w = codecs.open(output_path, 'w+', 'utf-8')
        f_w.write(str(disease_json))
        f_w.close()
        print('extracted data writen in file: %s' % output_path)


class NKX(BookParser):
    def read_data(self):
        df = pd.read_table(self.book, sep='\n', header=None)  # 与父类 读取数据的分隔符不一样
        return df

    def read_sample_data(self, n):
        df = pd.read_table(self.book, sep='\n', header=None)
        return df.sample(n)

    def read_seq_data(self, start=0, end=100):
        df = pd.read_table(self.book, sep='\n', header=None)
        return df.iloc[start:end, ]

    def extract(self, fblk):
        grd = fblk.groupby('blk')
        df = grd.nth(1)
        pat1 = u'(?P<chinese_name>[\u4e00-\u9fa5a-zA-Z]+)[\（](?P<english_name>[^\）]+)[\）]'  # 用的中文括弧
        name = df.line.str.extract(pat1, expand=True)
        df['ch_name'] = name.chinese_name
        df['en_name'] = name.english_name
        df['definition'] = 0
        df = df.join(pd.DataFrame(columns=des_fil))  # 初始化
        for blk, gp in grd:
            rows = np.arange(1, gp.shape[0])
            defn = []
            for i in rows:
                if gp.iloc[i].label == u'正文':
                    defn.append(gp.iloc[i].line)
                    continue
                else:
                    df.loc[blk, 'definition'] = ''.join(defn)
                    head = i
                    break
            d = {}
            contents = []
            while head in rows:
                content = head + 1
                if gp.iloc[head].label == u'病部':
                    while (content in rows) and gp.iloc[content].label == u'正文':
                        dline = gp.iloc[content].line
                        if dline[-1] == u'。':
                            dline = dline + '\n'
                        contents.append(dline)
                        content += 1
                    d[gp.iloc[head].line] = ''.join(contents)
                    contents = []
                    head = content
            for col in des_fil:
                df.loc[blk, col] = d.get(col)
        return df


if __name__ == '__main__':
    pass
abstract_fckx = True
if abstract_fckx:
    pat_fckxmg = \
        {u'章': u' *第[一二三四五六七八九十]+章',
         u'节': u' *第[一二三四五六七八九十]+节',  # 去掉空格
         u'块一': u' *[一二三四五六七八九十]+、',   # 去掉空格，后部+、
         u'块二': u' *\([一二三四五六七八九十]+\)',
         u'病部': u' *【.*】'
         }

    bp = BookParser('../../data/test/fckxmg.txt', pat_fckxmg)
    rbook = bp.read_data()
    ppro = bp.pre_processing(rbook)
    page_mask = ppro.line.str.match('\d{1,3}\Z')
    ppro = ppro.loc[~page_mask]
    ppro.index = np.arange(ppro.shape[0])
    mklines = bp.mark_lines(ppro)
    i = 0
    while i in mklines.index:
        if mklines.loc[i].label == u'病部':
            line = mklines.loc[i].line
            pat_split1 = u'(【.*】)(.+)'
            found = re.findall(pat_split1, line)
            if len(found) == 1:
                line1 = found[0][0]
                line2 = found[0][1]
                new = pd.DataFrame([[line1, u'病部'],
                                    [line2, u'正文']],
                                   columns=mklines.columns
                                   )
                above = mklines.iloc[:i]
                below = mklines.iloc[i+1:].copy()
                mklines = above.append(new, ignore_index=True).append(below, ignore_index=True)
                i += 1
        i += 1
    mkblk = bp.mark_block(mklines)
    fblk = bp.filter_block(mkblk, des_fil)
    print('extract is processing')
    grd = fblk.dropna().groupby('blk')
    df = grd.nth(0)
    pat_split_name = u'[节\)、]'
    name = df.line.str.split(pat_split_name, 1, True)
    df['ch_name'] = name.iloc[:, 1]
    df = df.dropna()
    df.loc[:, 'ch_name'] = df.ch_name.map(lambda s: ''.join(re.findall(u'[^ ]', s)))
    df['en_name'] = ''
    df['definition'] = 0
    df = df.join(pd.DataFrame(columns=des_fil))  # 初始化
    for blk, gp in grd:
        if blk in df.index:
            rows = np.arange(1, gp.shape[0])
            defn = []
            for i in rows:
                if gp.iloc[i].label == u'正文':
                    defn.append(gp.iloc[i].line)
                    continue
                else:
                    df.loc[blk, 'definition'] = ''.join(defn)
                    head = i
                    break
            d = {}
            contents = []
            while head in rows:
                content = head + 1
                if gp.iloc[head].label == u'病部':
                    while (content in rows) and gp.iloc[content].label == u'正文':
                        dline = gp.iloc[content].line
                        if dline[-1] == u'。':
                            dline = dline + '\n'
                        contents.append(dline)
                        content += 1
                    d[gp.iloc[head].line] = ''.join(contents)
                    contents = []
                    head = content
            for col in des_fil:
                df.loc[blk, col] = d.get(col)

    def save_to_dict(df, output_path, print_name=True, print_detail=False):
        print('save_to_dict is processing')
        col_map = {val: key for key, val in des_field.items()}
        col_map['en_name'] = 'disease_name_en'
        df.rename(columns=col_map, inplace=True)
        df = df.loc[df.ch_name.notnull()].copy()
        df = df.drop([u'label', u'line'], axis=1)
        df.fillna('', inplace=True)
        df = df.applymap(lambda s: s.encode('utf-8'))
        print('=== data prepared to dict ===\n', df.count(0))
        diseases = {}
        for row in df.index:
            val = df.loc[row].to_dict()
            key = df.ch_name.loc[row]
            diseases[key] = val
        if print_name:
            count = 0
            for name, disease in diseases.items():
                count += 1
                print('===============================')
                print('count: ', count)
                print('dname:', name)
                if print_detail:
                    for field, content in disease.items():
                        if not content == '':
                            print(field + ':\n', content)
        disease_json = json.dumps(diseases, ensure_ascii=False)
        f_w = codecs.open(output_path, 'w+', 'utf-8')
        f_w.write(str(disease_json))
        f_w.close()
        print('extracted data writen in file: %s' % output_path)

    save_to_dict(df, '../../data/test/fckx.json')

df.to_excel('fckx2.xlsx')

