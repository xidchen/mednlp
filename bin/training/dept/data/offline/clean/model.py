from mednlp.model.dept_classify_char_pinyin_model import DeptClassifyCharPinyin
import global_conf


class ModelJudge(object):
    def __init__(self):
        self.model = DeptClassifyCharPinyin(cfg_path=global_conf.cfg_path,
                                            model_section='DEPT_CLASSIFY_CHAR_PINYIN_MODEL')

    def need_to_reserve(self, query, dept):
        results = self.model.predict(query)
        top1_wrong = self.obviously_not_correct(results, dept)
        if top1_wrong:
            pred_dept, prob, dept_id = results[0]
            print('pred: {}/{}, label: {}, query:{}'.format(pred_dept, prob, dept, query))

        confuse = self.confuse_query(results)
        if confuse:
            pred_dept, prob, dept_id = results[0]
            print('pred: {}/{}, label: {}, query:{}'.format(pred_dept, prob, dept, query))

        return True in [top1_wrong, confuse]

    @staticmethod
    def obviously_not_correct(results, dept):
        hit = False
        pred_dept, prob, dept_id = results[0]
        if prob > 0.8 and not pred_dept == dept:
            hit = True
        return hit

    def confuse_query(self, results):
        hit = False
        prob_top_5 = [result[1] for result in results]
        prob_sum = sum(prob_top_5)
        if prob_sum < 0.5:
            hit = True
        return hit
