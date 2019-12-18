# -*- coding: utf-8 -*-
"""
dialog文件夹各个类的功能说明，从点到面，先介绍基本的类,再介绍串联基本类的 管理类(dialog_manager.py)
1.slot.py:  主要实现各种功能的槽
2.dialog_constant.py:   存储常量,不进行方法处理.代码一起动,该类的变量固定。可以被各个类包含
3.process_handler.py:   定义slot的pre_handler(前置处理器),handler(处理器),post_handler(后置处理器),应用在slot.py里
4.dialog_deal.py:   琐碎的类,负责琐碎方法.除了dialog_constant,可以被各个类包含
5.dialog_util.py:   对话工具类,封装一些公共的方法。除了dialog_constant，可以被各个类包含
6.dialog_manager.py 配置slot的类,以及配置slot的一些handler,conf
"""