# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
import tensorflow as tf
from tensorflow.python.ops import lookup_ops
from tensorflow.python.layers import core as layers_core
from tensorflow.python.util import nest
import numpy as np
import time
import collections
import argparse
import codecs
from mednlp.utils.utils import unicode_python_2_3

class GNMTAttentionMultiCell(tf.nn.rnn_cell.MultiRNNCell):
    """A MultiCell with GNMT attention style."""

    def __init__(self, attention_cell, cells, use_new_attention=False):
        """Creates a GNMTAttentionMultiCell.

        Args:
          attention_cell: An instance of AttentionWrapper.
          cells: A list of RNNCell wrapped with AttentionInputWrapper.
          use_new_attention: Whether to use the attention generated from current
            step bottom layer's output. Default is False.
        """
        cells = [attention_cell] + cells
        self.use_new_attention = use_new_attention
        super(GNMTAttentionMultiCell, self).__init__(cells, state_is_tuple=True)

    def __call__(self, inputs, state, scope=None):
        """Run the cell with bottom layer's attention copied to all upper layers."""
        if not nest.is_sequence(state):
            raise ValueError(
                "Expected state to be a tuple of length %d, but received: %s"
                % (len(self.state_size), state))

        with tf.variable_scope(scope or "multi_rnn_cell"):
            new_states = []

            with tf.variable_scope("cell_0_attention"):
                attention_cell = self._cells[0]
                attention_state = state[0]
                cur_inp, new_attention_state = attention_cell(inputs, attention_state)
                new_states.append(new_attention_state)

            for i in range(1, len(self._cells)):
                with tf.variable_scope("cell_%d" % i):

                    cell = self._cells[i]
                    cur_state = state[i]

                    if not isinstance(cur_state, tf.contrib.rnn.LSTMStateTuple):
                        raise TypeError("`state[{}]` must be a LSTMStateTuple".format(i))

                    if self.use_new_attention:
                        cur_state = cur_state._replace(h=tf.concat(
                            [cur_state.h, new_attention_state.attention], 1))
                    else:
                        cur_state = cur_state._replace(h=tf.concat(
                            [cur_state.h, attention_state.attention], 1))

                    cur_inp, new_state = cell(cur_inp, cur_state)
                    new_states.append(new_state)

        return cur_inp, tuple(new_states)


class NMTmodel(object):
    def __init__(self, model_path, src_vocab_file, tgt_vocab_file):
        self.model_path = model_path
        self.src_vocab_file = src_vocab_file
        self.tgt_vocab_file = tgt_vocab_file
        #self.tgt_vocab_dict = [x.strip() for x in open(self.config.tgt_vocab_file, 'r', encoding='utf-8').readlines()]
        self.tgt_vocab_dict = [unicode_python_2_3(x.strip()) for x in open(self.tgt_vocab_file, 'r').readlines()]

        # hyper-parameters
        self.UNK = '<unk>'
        self.sos = '<s>'
        self.eos = '</s>'
        self.UNK_ID = 0

        self.src_max_len = 60
        self.tgt_max_len_infer = 60

        self.src_vocab_size = 496
        self.tgt_vocab_size = 11050

        self.src_embed_size = 50
        self.tgt_embed_size = 100

        self.num_units = 512
        self.forget_bias = 1.0

        self.infer_batch_size = 100

        self.sos = self.sos.encode("utf-8")
        self.eos = self.eos.encode("utf-8")

    def create_vocab_tables(self):
        self.src_vocab_table = lookup_ops.index_table_from_file(
            self.src_vocab_file, default_value=self.UNK_ID)
        self.tgt_vocab_table = lookup_ops.index_table_from_file(
            self.tgt_vocab_file, default_value=self.UNK_ID)
        self.reverse_tgt_vocab_table = lookup_ops.index_to_string_table_from_file(
            self.tgt_vocab_file, default_value=self.UNK)

    def add_placeholders(self):
        self.src_placeholder = tf.placeholder(shape=[None], dtype=tf.string)
        self.batch_size_placeholder = tf.placeholder(shape=[], dtype=tf.int64)

    def create_dataset_iterator(self):
        self.src_dataset = tf.contrib.data.Dataset.from_tensor_slices(
            self.src_placeholder)
        self.src_eos_id = tf.cast(self.src_vocab_table.lookup(tf.constant(self.eos)), tf.int32)
        self.src_dataset = self.src_dataset.map(lambda src: tf.string_split([src]).values)

        if self.src_max_len:
            self.src_dataset = self.src_dataset.map(lambda src: src[:self.src_max_len])
        # Convert the word strings to ids
        self.src_dataset = self.src_dataset.map(lambda src: tf.cast(self.src_vocab_table.lookup(src), tf.int32))
        # Add in the word counts.
        self.src_dataset = self.src_dataset.map(lambda src: (src, tf.size(src)))

        def batching_func(x):
            return x.padded_batch(
                self.batch_size_placeholder,
                # The entry is the source line rows;
                # this has unknown-length vectors.  The last entry is
                # the source row size; this is a scalar.
                padded_shapes=(tf.TensorShape([None]),  # src
                               tf.TensorShape([])),  # src_len
                # Pad the source sequences with eos tokens.
                # (Though notice we don't generally need to do this since
                # later on we will be masking out calculations past the true sequence.
                padding_values=(self.src_eos_id,  # src
                                0))  # src_len -- unused

        self.batched_dataset = batching_func(self.src_dataset)
        self.batched_iter = self.batched_dataset.make_initializable_iterator()
        (self.src_ids, self.src_seq_len) = self.batched_iter.get_next()
        self.batched_iter_initializer = self.batched_iter.initializer

    def add_embedding_op(self):
        with tf.variable_scope("embeddings"):
            with tf.variable_scope("encoder"):
                self.encoder_embedding = tf.get_variable(
                    "embedding_encoder", [self.src_vocab_size, self.src_embed_size], tf.float32)
                self.src_ids = tf.transpose(self.src_ids)
                self.encoder_emb_inp = tf.nn.embedding_lookup(self.encoder_embedding,
                                                              self.src_ids)

            with tf.variable_scope("decoder"):
                self.decoder_embedding = tf.get_variable(
                    "embedding_decoder", [self.tgt_vocab_size, self.tgt_embed_size], tf.float32)

    def build_output_projection(self):
        # Projection
        with tf.variable_scope("build_network"):
            with tf.variable_scope("decoder/output_projection"):
                self.output_layer_forward = layers_core.Dense(
                    self.tgt_vocab_size, use_bias=False, name="forward_output_projection")
                self.output_layer_backward = layers_core.Dense(
                    self.tgt_vocab_size, use_bias=False, name="backward_output_projection")

    def build_encoder(self):
        # build bi-directional lstm layer
        with tf.variable_scope("encoder"):
            fw_cell = tf.contrib.rnn.BasicLSTMCell(self.num_units, forget_bias=self.forget_bias)
            bw_cell = tf.contrib.rnn.BasicLSTMCell(self.num_units, forget_bias=self.forget_bias)
            bi_outputs, bi_state = tf.nn.bidirectional_dynamic_rnn(
                fw_cell,
                bw_cell,
                self.encoder_emb_inp,
                dtype=tf.float32,
                sequence_length=self.src_seq_len,
                time_major=True)
            bi_lstm_output = tf.concat(bi_outputs, -1)

            second_layer_uni_cell = tf.contrib.rnn.BasicLSTMCell(self.num_units,
                                                                      forget_bias=self.forget_bias)
            third_layer_uni_cell = tf.contrib.rnn.BasicLSTMCell(self.num_units,
                                                                      forget_bias=self.forget_bias)
            third_layer_uni_cell = tf.contrib.rnn.ResidualWrapper(third_layer_uni_cell)
            fouth_layer_uni_cell = tf.contrib.rnn.BasicLSTMCell(self.num_units,
                                                                      forget_bias=self.forget_bias)
            fouth_layer_uni_cell = tf.contrib.rnn.ResidualWrapper(fouth_layer_uni_cell)

            uni_cells = tf.contrib.rnn.MultiRNNCell([second_layer_uni_cell, third_layer_uni_cell, fouth_layer_uni_cell])

            self.encoder_outputs, encoder_state = tf.nn.dynamic_rnn(uni_cells, bi_lstm_output,
                                                                    dtype=tf.float32,
                                                                    sequence_length=self.src_seq_len,
                                                                    time_major=True)
            self.encoder_state = (bi_state[1],) + (encoder_state)

    def build_decoder(self):
        self.batch_size = tf.size(self.src_seq_len)
        tgt_sos_id = tf.cast(self.tgt_vocab_table.lookup(tf.constant(self.sos)),
                             tf.int32)
        tgt_eos_id = tf.cast(self.tgt_vocab_table.lookup(tf.constant(self.eos)),
                             tf.int32)
        maximum_iterations = self.tgt_max_len_infer

        with tf.variable_scope("decoder") as decoder_scope:
            memory = tf.transpose(self.encoder_outputs, [1, 0, 2])
            encoder_state = self.encoder_state
            source_sequence_length = self.src_seq_len
            batch_size = self.batch_size

            attention_mechanism = tf.contrib.seq2seq.BahdanauAttention(self.num_units,
                                                                       memory,
                                                                       memory_sequence_length=source_sequence_length,
                                                                       normalize=True)

            first_layer_cell = tf.contrib.rnn.BasicLSTMCell(self.num_units,
                                                            forget_bias=self.forget_bias)
            second_layer_cell = tf.contrib.rnn.BasicLSTMCell(self.num_units,
                                                             forget_bias=self.forget_bias)
            third_layer_cell = tf.contrib.rnn.BasicLSTMCell(self.num_units,
                                                             forget_bias=self.forget_bias)
            third_layer_cell = tf.contrib.rnn.ResidualWrapper(third_layer_cell)
            fourth_layer_cell = tf.contrib.rnn.BasicLSTMCell(self.num_units,
                                                            forget_bias=self.forget_bias)
            fourth_layer_cell = tf.contrib.rnn.ResidualWrapper(fourth_layer_cell)
            cell_list = [first_layer_cell, second_layer_cell, third_layer_cell, fourth_layer_cell]
            attention_cell = cell_list.pop(0)
            attention_cell = tf.contrib.seq2seq.AttentionWrapper(
                attention_cell,
                attention_mechanism,
                attention_layer_size=None,  # don't use attenton layer.
                output_attention=False,
                alignment_history=True,
                name="attention")
            cell = GNMTAttentionMultiCell(
                attention_cell, cell_list, use_new_attention=True)

            decoder_initial_state = tuple(
                zs.clone(cell_state=es)
                if isinstance(zs, tf.contrib.seq2seq.AttentionWrapperState) else es
                for zs, es in zip(
                    cell.zero_state(batch_size, tf.float32), encoder_state))

            start_tokens = tf.fill([self.batch_size], tgt_sos_id)
            end_token = tgt_eos_id

            # Helper
            helper = tf.contrib.seq2seq.GreedyEmbeddingHelper(
                self.decoder_embedding, start_tokens, end_token)

            # Decoder
            my_forward_decoder = tf.contrib.seq2seq.BasicDecoder(
                cell,
                helper,
                decoder_initial_state,
                output_layer=self.output_layer_forward  # applied per timestep
            )

            # Decoder
            my_backward_decoder = tf.contrib.seq2seq.BasicDecoder(
                cell,
                helper,
                decoder_initial_state,
                output_layer=self.output_layer_backward  # applied per timestep
            )

            # Dynamic decoding
            forward_outputs, forward_final_context_state, _ = tf.contrib.seq2seq.dynamic_decode(
                my_forward_decoder,
                maximum_iterations=maximum_iterations,
                output_time_major=True,
                swap_memory=True,
                scope=decoder_scope)

            backward_outputs, backward_final_context_state, _ = tf.contrib.seq2seq.dynamic_decode(
                my_backward_decoder,
                maximum_iterations=maximum_iterations,
                output_time_major=True,
                swap_memory=True,
                scope=decoder_scope)

            self.forward_logits = forward_outputs.rnn_output
            self.backward_logits = backward_outputs.rnn_output
            forward_sample_id = forward_outputs.sample_id
            backward_sample_id = backward_outputs.sample_id
            self.forward_sample_words = self.reverse_tgt_vocab_table.lookup(tf.to_int64(forward_sample_id))
            self.backward_sample_words = self.reverse_tgt_vocab_table.lookup(tf.to_int64(backward_sample_id))

    def add_logits_op(self):
        with tf.variable_scope("dynamic_seq2seq", dtype=tf.float32):
            self.build_output_projection()
            self.build_encoder()
            self.build_decoder()

    def initialize_session(self):
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.Session(config=config)
        self.saver = tf.train.Saver()
        print ('loading model from: {}'.format(os.path.realpath(self.model_path)))
        ckpt = tf.train.latest_checkpoint(self.model_path)
        self.sess.run(tf.tables_initializer())
        self.saver.restore(self.sess, ckpt)

    def close_session(self):
        """Closes the session"""
        self.sess.close()

    def build(self):
        # create lookup table from dict file
        self.create_vocab_tables()

        # add placeholder for input and output in the tensorflow graph
        self.add_placeholders()

        # adding dataset iterator
        self.create_dataset_iterator()

        # adding embedding op
        self.add_embedding_op()

        # adding logits op
        self.add_logits_op()

        params = tf.trainable_variables()
        # Print trainable variables
        self.print_out("# Trainable variables")
        for param in params:
            self.print_out("  %s, %s, %s" % (param.name, str(param.get_shape()),
                                             param.op.device))
        # initialise session
        self.initialize_session()

    def predict_batch(self, input_file, output_prefix):
        with codecs.getreader("utf-8")(tf.gfile.GFile(input_file, mode="rb")) as f_in:
            input_data = f_in.read().splitlines()
        self.sess.run(self.batched_iter_initializer, feed_dict={self.src_placeholder: input_data,
                                                                self.batch_size_placeholder: self.infer_batch_size
                                                                })
        start_time = time.time()
        num_sentences = 0
        with codecs.getwriter("utf-8")(tf.gfile.GFile(output_prefix + '.chn', mode="wb")) as f_out:
            f_out.write("")  # Write empty string to ensure file is created.
            with codecs.getwriter("utf-8")(tf.gfile.GFile(output_prefix + '_score.txt', mode="w")) as f_score:
                f_score.write("")  # Write empty string to ensure file is created.
                while True:
                    try:
                        forward_logits, backward_logits, forward_nmt_outputs, backward_nmt_outputs = self.sess.run(
                            [self.forward_logits,
                             self.backward_logits,
                             self.forward_sample_words,
                             self.backward_sample_words])
                        forward_nmt_outputs = forward_nmt_outputs.transpose()
                        backward_nmt_outputs = backward_nmt_outputs.transpose()
                        forward_logits = forward_logits.transpose(1, 2, 0)
                        backward_logits = backward_logits.transpose(1, 2, 0)

                        num_sentences += len(forward_nmt_outputs)
                        for sent_id in range(len(forward_nmt_outputs)):
                            translation, score = self.get_translation(forward_nmt_outputs,
                                                                        backward_nmt_outputs,
                                                                        forward_logits,
                                                                        backward_logits,
                                                                        sent_id)
                            f_out.write(unicode_python_2_3(translation + b"\n"))
                            f_score.write((score + "\n"))

                    except tf.errors.OutOfRangeError:
                        self.print_time("  done, num sentences %d" % num_sentences, start_time)
                        break

    def get_translation(self, forward_nmt_outputs, backward_nmt_outputs, forward_logits, backward_logits, sent_id):
        """Given batch decoding outputs, select a sentence and turn to text."""
        # Select a sentence
        forward_output = forward_nmt_outputs[sent_id, :].tolist()
        backward_output = backward_nmt_outputs[sent_id, :].tolist()
        forward_logits = forward_logits[sent_id]
        backward_logits = backward_logits[sent_id]

        # If there is an eos symbol in outputs, cut them at that point.
        len_forward_sequence = len(forward_output)
        if self.eos and self.eos in forward_output:
            len_forward_sequence = forward_output.index(self.eos)
            if len_forward_sequence < 1:
                len_forward_sequence = 1
            forward_logits = forward_logits[:, :len_forward_sequence]
            forward_logits = self.softmax(forward_logits).transpose()

        len_backward_sequence = len(backward_output)
        if self.eos and self.eos in backward_output:
            len_backward_sequence = backward_output.index(self.eos)
            if len_backward_sequence < 1:
                len_backward_sequence = 1
            backward_logits = backward_logits[:, :len_backward_sequence]
            backward_logits = self.softmax(backward_logits).transpose()

        if len_forward_sequence == len_backward_sequence:
            final_logits = 0.5*forward_logits[:len_forward_sequence, :] + 0.5*backward_logits[:len_backward_sequence, :][::-1, :]
        elif len_forward_sequence < len_backward_sequence:
            final_logits = 0.5*forward_logits[:len_forward_sequence, :] + 0.5*backward_logits[:len_forward_sequence, :][::-1, :]
        elif len_forward_sequence > len_backward_sequence:
            final_logits = forward_logits[:len_forward_sequence, :]
            final_logits[- len_backward_sequence:, :] = 0.5*final_logits[- len_backward_sequence:, :] + 0.5*backward_logits[:len_backward_sequence][::-1, :]

        # load tgt vocab dict
        output_ids = final_logits.argmax(axis=-1)
        output_words = [self.tgt_vocab_dict[x].encode() for x in output_ids]
        translation = self.format_text(output_words)

        final_score = []
        for i in range(len(output_ids)):
            final_score.append(final_logits[i][output_ids[i]])
        final_score = [str(x) for x in final_score]
        score = ' '.join(final_score)
        return translation, score

    def predict(self, query):
        self.sess.run(self.batched_iter_initializer, feed_dict={self.src_placeholder: [query],
                                                                self.batch_size_placeholder: 1
                                                                })
        forward_logits, backward_logits, forward_nmt_outputs, backward_nmt_outputs = self.sess.run([self.forward_logits,
                                                                                                    self.backward_logits,
                                                                                                    self.forward_sample_words,
                                                                                                    self.backward_sample_words])
        forward_nmt_outputs = forward_nmt_outputs.transpose()
        backward_nmt_outputs = backward_nmt_outputs.transpose()
        forward_logits = forward_logits.transpose(1, 2, 0)
        backward_logits = backward_logits.transpose(1, 2, 0)

        translation, score = self.get_translation(forward_nmt_outputs,
                                           backward_nmt_outputs,
                                           forward_logits,
                                           backward_logits, 0)
        return translation, score

    @staticmethod
    def softmax(x):
        """Compute softmax values for each sets of scores in x."""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum(axis=0)

    @staticmethod
    def format_text(words):
        """Convert a sequence words into sentence."""
        if (not hasattr(words, "__len__") and  # for numpy array
                not isinstance(words, collections.Iterable)):
            words = [words]
        return b" ".join(words)

    @staticmethod
    def print_time(s, start_time):
        """Take a start time, print elapsed duration, and return a new time."""
        print("%s, time %ds, %s." % (s, (time.time() - start_time), time.ctime()))
        sys.stdout.flush()
        return time.time()

    @staticmethod
    def print_out(s, f=None, new_line=True):
        """Similar to print but with support to flush and output to a file."""
        if isinstance(s, bytes):
            s = s.decode("utf-8")

        if f:
            f.write(s.encode("utf-8"))
            if new_line:
                f.write(b"\n")

        # stdout
        out_s = s.encode("utf-8")
        if not isinstance(out_s, str):
            out_s = out_s.decode("utf-8")
        print(out_s, end="", file=sys.stdout)

        if new_line:
            sys.stdout.write("\n")
        sys.stdout.flush()


if __name__ == "__main__":
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_file", type=str, default='../data/raw/test/without_tone/manually_chosen_test.pinyin')
    parser.add_argument("--out_prefix", type=str, default='../evaluation/test/manually_chosen_test')
    parser.add_argument("--cfg_path", type=str, default='config/inference_hparams.cfg')

    args = parser.parse_args()
    in_file = args.in_file
    out_prefix = args.out_prefix
    cfg_path = args.cfg_path
    model = NMTmodel(cfg_path)
    model.build()
    model.predict_batch(in_file, out_prefix)

