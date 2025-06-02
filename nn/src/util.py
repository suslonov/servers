#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 30 16:47:43 2017

@author: anton
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import csv
import string
import collections

class TrainConfig(object):
  """Small config."""
  dataset = 'w'    # w, c, 1, 2
  nn_type = 'bi-lstm-char' #s-lstm-char, d-lstm-char, s-gru-char, d-gru-char, d-lstm-word, d-gru-word, dnn-bag, bi-lstm-char, bi-gru-char
  init_scale = 0.1
  learning_rate = 1.0
  max_grad_norm = 5
  num_layers = 1
  hidden_size = 100
  lr_epoch = 10
  num_epoch = 10
  keep_prob = 1.0
  lr_decay = 0.99
  batch_size = 50
  max_document_length = 100
  vocab_size = 256
  num_labels = 20
  catlist_path = "catlist.csv"   # default
  data_path = ""  # if not "w", should be generated using dataset param
  show_path = "show.csv"
  save_path = "saves"
  
  def __init__(self, dataset=None, nn_type=None, input_length=None, num_layers=None, hidden_size=None, num_labels=None,
               keep_prob=None, learning_rate=None, lr_decay_start=None, lr_decay_rate=None, number_epochs=None,
               catlist_path=None, data_path=None, show_path=None, save_path=None):

    if dataset:
      self.dataset = dataset
    if nn_type:
      self.nn_type = nn_type
      if nn_type[-4:] == 'word':
        self.vocab_size = 12000
      else:
        self.vocab_size = 256
    if input_length:
      self.max_document_length = int(input_length)
    if num_layers:
      self.num_layers = int(num_layers)
    if hidden_size:
      self.hidden_size = int(hidden_size)
    if num_labels:
      self.num_labels = int(num_labels)
    if keep_prob:
      self.keep_prob = float(keep_prob)
    if learning_rate:
      self.learning_rate = float(learning_rate)
    if lr_decay_start:
      self.lr_epoch = int(lr_decay_start)
    if lr_decay_rate:
      self.lr_decay = float(lr_decay_rate)
    if number_epochs:
      self.num_epoch = int(number_epochs)
    if catlist_path:
      self.catlist_path = catlist_path

    if data_path:
      self.data_path = data_path
    elif self.dataset == "c":
      self.data_path = "cola.csv"
    elif self.dataset == "1":
      self.data_path = "1.csv"
    elif self.dataset == "2":
      self.data_path = "2.csv"
        
    if show_path:
      self.show_path = show_path
    if save_path:
      self.save_path = save_path

  def signature(self):
    return self.dataset+'='+self.nn_type+'='+str(self.max_document_length)+'='+str(self.num_layers) \
            +'='+str(self.hidden_size)+'='+str(self.num_labels)+'=Dr'+str(self.keep_prob) \
            +'=LR'+str(self.learning_rate)+'='+str(self.lr_epoch)+'='+str(self.lr_decay)+'='+str(self.num_epoch)

def unpack_name(signature):
  fl=signature.split("=")
  if not len(fl) == 11:
    raise ValueError("Invalid argument - invalid NN signature" + signature)
  return (fl[0],fl[1],fl[2],fl[3],fl[4],fl[5],fl[6][2:],fl[7][2:],fl[8],fl[9],fl[10])

def read_csv_to_tuples(filename):
  with open(filename, 'r') as f:
    reader = csv.reader(f)
    return list(map(tuple, reader))

def get_test_data(filename):
  l = read_csv_to_tuples(filename)
  return list(map(lambda x: x[0], l)), list(map(lambda x: x[1], l))

def create_dict(all_input):
  translator = str.maketrans(string.punctuation, ' '*len(string.punctuation))
  input_collect = []
  for ic in all_input:
    ic = ic.lower()
    ic = ic.translate(translator)
    input_collect.extend(ic.split())

  counter = collections.Counter(input_collect)
  count_pairs = sorted(counter.items(), key=lambda x: (-x[1], x[0]))

  words, _ = list(zip(*count_pairs))
  return dict(zip(words, range(len(words))))
