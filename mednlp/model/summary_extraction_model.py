# -*- coding: utf-8 -*-
import jieba
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer, TfidfTransformer


class SummaryExtractor(object):
    def __init__(self, stopwords_file):
        jieba.initialize()
        self.tfidf_model = TfidfVectorizer(tokenizer=jieba.cut, stop_words=self.load_stopwords(stopwords_file))
        self.input_sentence_limit = 20
        self.input_char_limit = 1000

    def load_stopwords(self, stopword_path):
        with open(stopword_path, encoding="utf-8") as f:
            # stopwords = filter(lambda x: x, list(map(lambda x: x.strip(), f.readlines())))
            stopwords = list(map(lambda x: x.strip(), f.readlines()))
        stopwords.extend([' ', '\t', '\n'])
        return frozenset(stopwords)

    def get_summary(self, query, sentence_limit, preferred_character, maximum_allowed_character):
        query_length = len(query)
        input_sents = list(self.cut_sentence(query))
        if query_length > self.input_char_limit or len(input_sents) > self.input_sentence_limit:
            input_sents = self.get_input_sents(input_sents, query_length, self.input_sentence_limit, self.input_char_limit)
        if len(input_sents) > sentence_limit:
            tfidf_matrix = self.tfidf_model.fit_transform(input_sents)
            normalized_matrix = TfidfTransformer().fit_transform(tfidf_matrix)
            similarity = nx.from_scipy_sparse_matrix(normalized_matrix * normalized_matrix.T)
            scores = nx.pagerank(similarity)
            tops = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            output_sent_num = min(sentence_limit, len(input_sents))
            indices = list(map(lambda x: x[0], tops))[:output_sent_num]
            summary_sents = list(map(lambda idx: input_sents[idx], indices))
        else:
            summary_sents = input_sents
        summary = self.get_output_sent(summary_sents, preferred_character, maximum_allowed_character)
        return summary

    @staticmethod
    def cut_sentence(sentence):
        # if not isinstance(sentence, unicode):
        # sentence = sentence.decode('utf-8')
        delimiters = frozenset(u'。！？')
        buf = []
        for ch in sentence:
            buf.append(ch)
            if delimiters.__contains__(ch):
                yield ''.join(buf)
                buf = []
        if buf:
            yield ''.join(buf)

    @staticmethod
    def get_input_sents(query_sents, query_length, sent_limit, char_limit):
        output_query_sents = []
        if query_length > char_limit:
            current_query_length = 0
            for sent in query_sents:
                if current_query_length + len(sent) < char_limit:
                    output_query_sents.append(sent)
                    current_query_length += len(sent)
                else:
                    break
            if len(output_query_sents) > sent_limit:
                output_query_sents = output_query_sents[:sent_limit]
        else:
            output_query_sents = query_sents[:sent_limit]
        return output_query_sents

    @staticmethod
    def get_output_sent(summary_sents, preferred_character, maximum_allowed_characters):
        sent_length = len(''.join(summary_sents))
        if preferred_character > 0:
            if sent_length < preferred_character < maximum_allowed_characters:
                summary = ''.join(summary_sents)
            else:
                summary = ''
                current_summary_length = 0
                for sent in summary_sents:
                    if current_summary_length + len(sent) < preferred_character:
                        summary += sent
                        current_summary_length = len(summary)
                    elif current_summary_length + len(sent) - preferred_character < preferred_character - current_summary_length:
                        summary += sent
                        break
                    else:
                        break
        else:
            summary = ''.join(summary_sents)
        if maximum_allowed_characters > 0:
            summary = summary[:maximum_allowed_characters]
        return summary


if __name__ == "__main__":
    summary_extractor = SummaryExtractor('../../data/dict/summary_extraction_service/stopwords.txt')
    query = '很多人应该听说过8小时睡眠论，大概意思呢就是，人每天要睡满8个小时，一天的精神才会好，身体才健康。导致很多有强迫症的人，睡之前发现自己睡不到8个小时就会很焦虑，感觉当晚剩下的睡眠都不再有意义，于是便不能好好入睡，甚至破罐子破摔。其实8小时睡眠只是人的平均睡眠时间，并不适用于每个人，个体间可能存在着很大的差异。就像某城市人均月薪资1万，你真的达到一万了吗？你只不过是被平均了而已。有的人可能睡6个小时就足够了，你让他睡8个小时，反而会精神不好，而有的人则需要睡10个小时。这也跟每个人的睡眠质量有关，如果是一直处于半梦半醒的浅睡眠状态，那睡多久也都没用的。而且如果你晚上不睡觉，白天睡满8个小时，同样没有同等效力的，因为你已经打乱了生物钟。生物钟这个东西很奇怪，它是随着昼夜更替走的，也是写在我们基因里的，以前不是有句老话么，日出而作、日落而息，如果你反过来，就像涨潮的时候去赶海，不仅不会有收获，还可能会丢了性命。讲个故事，高三那会，正面临着高考，学习特别紧张，很多同学都抓紧一切能够利用的时间，那时候晚上10点睡觉，早上5点半起床。但是有很多人挑灯夜读，不仅如此，早上四点多就起床跑到教室学习，白天看起来还神采奕奕，精神特别好。谁没有一颗上进的心，别人可以，我为啥不行？所以每天5点半都睡不醒的我设了个闹钟：4点。效果十分明显，当天一整天我都是迷迷糊糊、瞌睡连天，这种状态持续了三天才完全回到最初的状态。这就是跟生物钟对着干的下场。所以，永远不要和生物钟对抗，输的永远都是我们。那我们怎么才能拥有良好的睡眠呢？我们下期再见，谢谢~'
    summary = summary_extractor.get_summary(query, 50, 2000, 1)
    print (summary)
