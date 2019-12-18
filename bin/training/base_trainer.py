# ！/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-06-23 Sunday
@Desc:	训练模型程序基类
"""

import os
import global_conf
import tensorflow as tf
from keras.callbacks import ModelCheckpoint
import keras.backend.tensorflow_backend as ktf


class BaseTrainer():
    def __init__(self, **kwargs):
        self.set_tf_session()
        self.model_checkpoint = self._load_model_checkpoint(**kwargs)

    def _load_model_checkpoint(self, **kwargs):
        model_name = kwargs.get('model_name', 'base_model')
        self.model_name = model_name
        checkpoint_name = kwargs.get('checkpoint_name', 'model')
        checkpoint_format = kwargs.get('checkpoint_format', checkpoint_name + '-ep{epoch:03d}-loss{loss:.3f}.h5')
        save_file_path = os.path.join(global_conf.train_data_path, self.model_name, 'checkpoint')
        os.makedirs(save_file_path, exist_ok=True)
        save_file_name = os.path.join(save_file_path, checkpoint_format)
        monitor = kwargs.get('checkpoint_monitor', 'val_categorical_accuracy')
        mode = kwargs.get('checkpoint_mode', 'auto')
        save_best_only = kwargs.get('checkpoint_save_best_only', 'True')
        return ModelCheckpoint(filepath=save_file_name, monitor=monitor, mode=mode, save_best_only=save_best_only)

    def set_tf_session(self, gpu_fraction=1):
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=gpu_fraction, allow_growth=True)
        session = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))
        ktf.set_session(session)
        print('00')
