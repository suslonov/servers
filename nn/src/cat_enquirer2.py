#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
#from tensorflow.python import debug as tf_debug

import sys
import pickle
import util
import cat_models

def cat_model_enquarer(data, labels, catlist, config):
  data_len = len(data)
  config.batch_size = data_len

  name_saved = config.save_path+'/'+config.signature()+'/'
  if config.nn_type[-4:] == 'word':
    with open(name_saved+'word_dict', 'rb') as f:
      word_dict=pickle.load(f)

  with tf.Graph().as_default():
#    initializer = tf.random_uniform_initializer(-config.init_scale, config.init_scale)    # do I need ?

    if config.nn_type in ['s-lstm-char', 'd-lstm-char', 's-gru-char', 'd-gru-char', 'bi-lstm-char', 'bi-gru-char']:
      show_input = cat_models.InputStructChar1NoQueue(config=config, input_data=data, labels=labels, name="ShowInput")
    elif config.nn_type in ['d-lstm-word', 'd-gru-word']:
      show_input = cat_models.InputStructWordNoQueue(config=config, input_data=data, labels=labels, word_dict=word_dict, name="ShowInput")
    else:
      raise ValueError("Unknown NN type")

    with tf.compat.v1.variable_scope("Model", reuse=False):  #, initializer=initializer):
      if config.nn_type in ['s-lstm-char', 's-gru-char']:
        mshow = cat_models.SLSTMCharModel(is_training=False, config=config, input_=show_input, type_cell=config.nn_type[2:5])
      elif config.nn_type in ['d-lstm-char', 'd-gru-char']:
        mshow = cat_models.DLSTMCharModel(is_training=False, config=config, input_=show_input, type_cell=config.nn_type[2:5])
      elif config.nn_type in ['bi-lstm-char', 'bi-gru-char']:
        mshow = cat_models.BiLSTMCharModel(is_training=False, config=config, input_=show_input, type_cell=config.nn_type[3:6])
      elif config.nn_type in ['d-lstm-word', 'd-gru-word']:
        mshow = cat_models.DLSTMWordModel(is_training=False, config=config, input_=show_input, type_cell=config.nn_type[2:5])
  
    saver = tf.compat.v1.train.Saver(tf.compat.v1.global_variables())

  #  sv = tf.train.Supervisor(logdir=FLAGS.save_path+'1')                   #if Supervisor
  #  with sv.managed_session() as session:                              #if Supervisor
    with tf.compat.v1.Session(config = tf.compat.v1.ConfigProto(device_count = {'GPU': 0})) as session:                                     #if not Supervisor
#        session = tf_debug.LocalCLIDebugWrapperSession(session)
      saver.restore(session, name_saved)
      show_predict = mshow.run_predict(session)
  tf.compat.v1.reset_default_graph()    

  out_list=[]
  for sp, sd, sl in zip(show_predict, data, labels):
    c = list(map(lambda x,y:(x,y[1]), sp[0][1:], catlist))
    c.sort(reverse=True)
    out_list.append((sd, next(cl for cl in catlist if cl[0] == sl)[1], c))
  
  return out_list

def main():
  if len(sys.argv) > 1:
    nn_si = util.unpack_name(sys.argv[1])
  else:
    nn_si = None
  if len(sys.argv) > 2:
    show_path = sys.argv[2]
  else:
    show_path = None
  if len(sys.argv) > 3:
    catlist_path = sys.argv[3]
  else:
    catlist_path = None
  if len(sys.argv) > 4:
    save_path = sys.argv[4]
  else:
    save_path = None

  if nn_si:
    config = util.TrainConfig(dataset=nn_si[0],
                             nn_type=nn_si[1],
                             input_length=nn_si[2],
                             num_layers=nn_si[3],
                             hidden_size=nn_si[4],
                             num_labels=nn_si[5],
                             keep_prob=nn_si[6],
                             learning_rate=nn_si[7],
                             lr_decay_start=nn_si[8],
                             lr_decay_rate=nn_si[9],
                             number_epochs=nn_si[10],
                             catlist_path=catlist_path,
                             show_path=show_path,
                             save_path=save_path)
  else:
    config = util.TrainConfig(catlist_path=catlist_path,
                             show_path=show_path,
                             save_path=save_path)
  
  catlist = util.read_csv_to_tuples(config.catlist_path)
  show_data, show_labels = util.get_test_data(config.show_path)

  out_list = cat_model_enquarer(show_data, show_labels, catlist, config)
  for ol in out_list:
    print(ol)

if __name__ == "__main__":
  main()

