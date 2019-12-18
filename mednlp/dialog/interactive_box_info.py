#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import re
from mednlp.dialog.configuration import Constant as constant

class BaseValidator(object):
    """
    基类验证器, 返回True表示验证通过,语句符合交互框定义
    """
    def validate(self, q, interactive_box=None, **kwargs):
        """
        验证通过返回True,
        验证失败返回False
        :param q:  用户语句
        :param interactive_box:  交互框
        :param kwargs:
        :return:
        """
        raise NotImplementedError


class SexValidator(BaseValidator):
    # 科室年龄验证器

    pattern = re.compile('(男|女)')

    def validate(self, q, interactive_box=None, **kwargs):
        """
        验证通过返回True,
        验证失败返回False
        1. q为0,1,2
        2. q里有男, 女文字
        :param q:  用户语句
        :param interactive_box:  交互框
        :param kwargs:
        :return:
        """
        valid_value = q
        if valid_value:
            valid_value = str(valid_value)
            if valid_value in ['0', '1', '2']:
                return True, valid_value
            elif re.search(self.pattern, valid_value):
                sex_temp = re.search(self.pattern, valid_value).group()
                if sex_temp == '男':
                    sex_temp = '2'
                else:
                    sex_temp = '1'
                return True, sex_temp
        return False, None


class AgeValidator(BaseValidator):
    # 科室年龄验证器

    pattern = re.compile('(天|月|年|岁|日)')

    def validate(self, q, interactive_box=None, **kwargs):
        """
        验证通过返回True,
        验证失败返回False
        1. -1 或者数字, 正常接口访问
        2.语句里带有年龄词单位
        :param q:  用户语句
        :param interactive_box:  交互框
        :param kwargs:
        :return:
        """
        valid_value = q
        if valid_value:
            valid_value = str(valid_value)
            if '-1' == valid_value:
                return True, None
            elif valid_value.isdigit():
                return True, valid_value
            elif re.search(self.pattern, valid_value):
                # 拼装成天
                age_temp = 0
                has_age = False
                age_split = re.split(self.pattern, valid_value)
                for index, temp in enumerate(age_split):
                    if temp in ['天', '月', '年', '岁', '日']:
                        if index - 1 >= 0:
                            digests = re.findall(r"\d+", age_split[index - 1])
                            if digests:
                                digest_temp = int(digests[-1])
                                has_age = True
                                if temp in ['天', '日']:
                                    age_temp += digest_temp
                                elif temp == '月':
                                    age_temp += digest_temp * 30
                                else:
                                    age_temp += digest_temp * 365
                # 能得到年龄
                if has_age:
                    return True, str(age_temp)
        return False, None


class SymptomNameValidator(BaseValidator):
    # 科室分诊验证器

    # 都没有是 现在 小微医助里的一个选项
    other_pattern = re.compile('(没有|无|否|都没有)')

    def validate(self, q, interactive_box=None, **kwargs):
        """
        验证通过返回True,
        验证失败返回False
        q输入情况:
        a. 1个症状      eg疼痛
        b. 多个症状,逗号分隔  eg疼痛,下肢麻木
        c. 1句话      eg 我手臂疼痛

        针对不同输入做校验;
        获取交互框的数据
        1.输入词 属于 交互框候选词里, 验证通过
        2.
        :param q:  用户语句
        :param interactive_box:  交互框
        :param kwargs:
        :return:
        """
        valid_value = q
        box_content = None
        if valid_value:
            valid_value = str(valid_value)
            if interactive_box and interactive_box.get('content'):
                box_content = interactive_box['content']
            """
            1.输入词 属于 交互框候选词里, 验证通过
            eg: 比如输入 感冒, 感冒这个词肯定在交互框内,通过
            若输入我感冒了(句子), re.search 时不通过,进行下个场景判断
            """
            if box_content:
                pattern_temp = '(%s)' % '|'.join(valid_value.split(','))
                is_match = re.search(pattern_temp, ','.join(box_content))
                if is_match:
                    return True, valid_value
            # 2.输入词不在交互框内,且是否定词, 比如 都没有, 也表示验证通过
            if re.search(self.other_pattern, valid_value):
                return True, valid_value
            """
            3. 1和2涵盖了APP上手动操作以及 语音上的关键词和否定词, 句子类的需要3支持，
            比如我感冒了, 实体识别的时候识别到感冒(根据type_all判断), 则代表有症状词, 验证通过，
            若 我呵呵了, 没有症状词, 表示未通过
            """
            params = {'q': valid_value}
            entity_result = constant.ai_server.query(params, 'entity_extract')
            if entity_result and entity_result.get('data'):
                symptom_temps = [temp.get('entity_name') for temp in entity_result['data']
                                 if 'symptom' in temp.get('type_all')]
                if symptom_temps:
                    return True, ','.join(symptom_temps)
        return False, None


class InteractiveBoxConstant(object):
    """
    交互框常量类
    """

    key_field = 'field'

    validator = {
        'department': {
            'symptomName': SymptomNameValidator,  # 科室分类症状名验证器
            'age': AgeValidator,
            'sex': SexValidator
        }
    }

if __name__ == '__main__':
    # validator = AgeValidator()
    validator = SexValidator()
    print(validator.validate('我女是男的'))
