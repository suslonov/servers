
###    max len for batch 

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
import time
import string

class InputStructWordNoQueue(object):
  def __init__(self, config, input_data, labels, word_dict, name=None, shuffle=True):
    self.batch_size = batch_size = config.batch_size
    data_len = len(input_data)
    self.epoch_size = batch_len = data_len // batch_size
    translator = str.maketrans(string.punctuation, ' '*len(string.punctuation))
    
    input_data_ = []
    x_len = []
    for ic in input_data:
      ic = ic.lower()
      ic = ic.translate(translator)
      iss = list(map((lambda x: word_dict.get(x,0)), ic.split()))
      x_l = len(iss)
      iss.extend([0]*(config.max_document_length-x_l))
      input_data_.append(iss)
      x_len.append(x_l)
    
    x = np.reshape(input_data_, [data_len, config.max_document_length])
    
    with tf.device("/cpu:0"):
      with tf.compat.v1.name_scope(name):
        input_data_ = tf.cast(x, name="input_data", dtype=tf.int32)
        labels_ = tf.strings.to_number(labels, name="labels", out_type=tf.int32)
        x_len_ = tf.convert_to_tensor(value=x_len, dtype=tf.int32, name="x_len")

        data_ = tf.reshape(input_data_[0 : batch_size * batch_len], [batch_size, config.max_document_length])
        targets_ = tf.reshape(labels_[0 : batch_size * batch_len], [batch_size, 1])
        lens = tf.reshape(x_len_[0 : batch_size * batch_len], [batch_size, 1])
      self.input_data, self.targets, self.lens = data_, targets_, lens[:, 0]

class InputStructWord(object):
  def __init__(self, config, input_data, labels, word_dict, name=None, shuffle=True):
    self.batch_size = batch_size = config.batch_size
    data_len = len(input_data)
    self.epoch_size = batch_len = data_len // batch_size
    translator = str.maketrans(string.punctuation, ' '*len(string.punctuation))

    input_data_ = []
    x_len = []
    for ic in input_data:
      ic = ic.lower()
      ic = ic.translate(translator)
      iss = list(map((lambda x: word_dict.get(x,0)), ic.split()))
      x_l = len(iss)
      iss.extend([0]*(config.max_document_length-x_l))
      input_data_.append(iss)
      x_len.append(x_l)
    
    x = np.reshape(input_data_, [data_len, config.max_document_length])
    
    with tf.device("/cpu:0"):
      with tf.compat.v1.name_scope(name):
        input_data_ = tf.cast(x, name="input_data", dtype=tf.int32)
        labels_ = tf.strings.to_number(labels, name="labels", out_type=tf.int32)
        x_len_ = tf.convert_to_tensor(value=x_len, dtype=tf.int32, name="x_len")

        data = tf.reshape(input_data_[0 : batch_size * batch_len], [batch_size, batch_len, config.max_document_length])
        targets = tf.reshape(labels_[0 : batch_size * batch_len], [batch_size, batch_len, 1])
        lens = tf.reshape(x_len_[0 : batch_size * batch_len], [batch_size, batch_len, 1])
        i = tf.compat.v1.train.range_input_producer(batch_len, shuffle=shuffle).dequeue()
        x = tf.slice(data, [0, i, 0], [batch_size, 1, config.max_document_length])
        y = tf.slice(targets, [0, i, 0], [batch_size, 1, 1])
        xl = tf.slice(lens, [0, i, 0], [batch_size, 1, 1])
        
      self.input_data, self.targets, self.lens = x[:, 0, :], y[:, 0, :], xl[:, 0, 0]

class InputStructChar1NoQueue(object):
  def __init__(self, config, input_data, labels, name=None):
    self.batch_size = batch_size = config.batch_size
    data_len = len(input_data)
    self.epoch_size = batch_len = data_len // batch_size

    char_processor = tf.contrib.learn.preprocessing.ByteProcessor(config.max_document_length)
    x = list(char_processor.fit_transform(input_data)) # [data_len, max_document_length]
    x_len = [min(len(ix),config.max_document_length) for ix in input_data]
    x = np.reshape(x, [data_len, config.max_document_length])
    with tf.device("/cpu:0"):
      with tf.compat.v1.name_scope(name):
        input_data_ = tf.cast(x, name="input_data", dtype=tf.int32)
        labels_ = tf.strings.to_number(labels, name="labels", out_type=tf.int32)
        x_len_ = tf.convert_to_tensor(value=x_len, dtype=tf.int32, name="x_len")

        data_ = tf.reshape(input_data_[0 : batch_size * batch_len], [batch_size, config.max_document_length])
        targets_ = tf.reshape(labels_[0 : batch_size * batch_len], [batch_size, 1])
        lens = tf.reshape(x_len_[0 : batch_size * batch_len], [batch_size, 1])
  
    self.input_data, self.targets, self.lens = data_, targets_, lens[:, 0]


class InputStructChar1(object):
  def __init__(self, config, input_data, labels, name=None, shuffle=True):
    self.batch_size = batch_size = config.batch_size
    data_len = len(input_data)
    self.epoch_size = batch_len = data_len // batch_size
    
    with tf.device("/cpu:0"):
      char_processor = tf.contrib.learn.preprocessing.ByteProcessor(config.max_document_length)
      x = list(char_processor.fit_transform(input_data)) # [data_len, max_document_length]
      x_len = [min(len(ix),config.max_document_length) for ix in input_data]
      x = np.reshape(x, [data_len, config.max_document_length])
      
      with tf.compat.v1.name_scope(name):
        input_data_ = tf.cast(x, name="input_data", dtype=tf.int32)
        labels_ = tf.strings.to_number(labels, name="labels", out_type=tf.int32)
        x_len_ = tf.convert_to_tensor(value=x_len, dtype=tf.int32, name="x_len")

        data = tf.reshape(input_data_[0 : batch_size * batch_len], [batch_size, batch_len, config.max_document_length])
        targets = tf.reshape(labels_[0 : batch_size * batch_len], [batch_size, batch_len, 1])
        lens = tf.reshape(x_len_[0 : batch_size * batch_len], [batch_size, batch_len, 1])
        i = tf.compat.v1.train.range_input_producer(batch_len, shuffle=shuffle).dequeue()
        x = tf.slice(data, [0, i, 0], [batch_size, 1, config.max_document_length])
        y = tf.slice(targets, [0, i, 0], [batch_size, 1, 1])
        xl = tf.slice(lens, [0, i, 0], [batch_size, 1, 1])
        
      self.input_data, self.targets, self.lens = x[:, 0, :], y[:, 0, :], xl[:, 0, 0]

class SLSTMCharModel(object):
  def __init__(self, is_training, config, input_, type_cell, data_type=tf.float32):
    self._input = input_

    batch_size = input_.batch_size
    hidden_size = config.hidden_size
    vocab_size = config.vocab_size
    doc_len = config.max_document_length
    num_labels = config.num_labels
    
    def lstm_cell(type_cell):
      if type_cell == 'gru':
        return tf.compat.v1.nn.rnn_cell.GRUCell(hidden_size, reuse=tf.compat.v1.get_variable_scope().reuse)
      else:
        return tf.compat.v1.nn.rnn_cell.BasicLSTMCell(hidden_size, reuse=tf.compat.v1.get_variable_scope().reuse)

    attn_cell = lstm_cell
    if is_training and config.keep_prob < 1:
      def attn_cell(type_cell):
        return tf.compat.v1.nn.rnn_cell.DropoutWrapper(lstm_cell(type_cell), output_keep_prob=config.keep_prob)

    cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([attn_cell(type_cell) for _ in range(config.num_layers)], state_is_tuple=True)
    self._initial_state = cell.zero_state(batch_size, data_type)

    embedding = tf.compat.v1.get_variable("embedding", [vocab_size, hidden_size], dtype=data_type)
    inputs = tf.nn.embedding_lookup(params=embedding, ids=input_.input_data)  # [batch_size, doc_len, hidden_size]
    
    if is_training and config.keep_prob < 1:
      inputs = tf.nn.dropout(inputs, 1 - (config.keep_prob))
      
    state = self._initial_state
    with tf.compat.v1.variable_scope("RNN"):
      for step in range(doc_len):
        if step > 0: tf.compat.v1.get_variable_scope().reuse_variables()
        (cell_output, state) = cell(inputs[:, step, :], state)
        if step == 0:
          output = cell_output
        else:
          output = tf.compat.v1.where(tf.not_equal(input_.input_data[:,step], 0), cell_output, output)
        
#      output is [batch_size, hidden_size]

    softmax_w = tf.compat.v1.get_variable("softmax_w", [hidden_size, num_labels], dtype=data_type)
    softmax_b = tf.compat.v1.get_variable("softmax_b", [num_labels], dtype=data_type)
    logits = tf.matmul(output, softmax_w) + softmax_b

    logits = tf.reshape(logits, [batch_size, 1, num_labels])
    onehot_targets = tf.one_hot(input_.targets, num_labels, 1, 0)
    loss = tf.compat.v1.losses.softmax_cross_entropy(onehot_labels=onehot_targets, logits=logits)

    self._cost = cost = loss
    self._final_state = state
    self.sm_logits =  tf.nn.softmax(logits, name="sm_logits")

    if not is_training:
      _y = tf.argmax(input=logits, axis=2, output_type=tf.int32)
      c_p = tf.equal(_y, input_.targets)
      self._correct =  tf.reduce_sum(input_tensor=tf.cast(c_p, tf.float32))
      return
    else:
      self._correct =  tf.constant(0.0)

    self._lr = tf.Variable(0.0, trainable=False)
    tvars = tf.compat.v1.trainable_variables()
    grads, _ = tf.clip_by_global_norm(tf.gradients(ys=cost, xs=tvars), config.max_grad_norm)
    optimizer = tf.compat.v1.train.GradientDescentOptimizer(self._lr)    #  try others
    self._train_op = optimizer.apply_gradients(
        zip(grads, tvars),
        global_step=tf.contrib.framework.get_or_create_global_step())

    self._new_lr = tf.compat.v1.placeholder(tf.float32, shape=[], name="new_learning_rate")
    self._lr_update = tf.compat.v1.assign(self._lr, self._new_lr)

  def assign_lr(self, session, lr_value):
    session.run(self._lr_update, feed_dict={self._new_lr: lr_value})

  @property
  def input(self):
    return self._input

  @property
  def initial_state(self):
    return self._initial_state

  @property
  def cost(self):
    return self._cost

  @property
  def correct(self):
    return self._correct

  @property
  def final_state(self):
    return self._final_state

  @property
  def lr(self):
    return self._lr

  @property
  def train_op(self):
    return self._train_op

  def run_epoch(self, session, eval_op=None, verbose=False):
    """Runs the model on the given data."""
    start_time = time.time()
    costs = 0.0
    total_correct = 0.0
    iters = 0
    state = session.run(self.initial_state)
  
    fetches = {
        "cost": self.cost,
        "correct": self.correct,
        "final_state": self.final_state,
    }
    if eval_op is not None:
      fetches["eval_op"] = eval_op
  
    if self.input.epoch_size == 0:
      epoch_size = 1
    else:
      epoch_size = self.input.epoch_size
    
    for step in range(epoch_size):
      feed_dict = {}
      for i, (c, h) in enumerate(self.initial_state):
        feed_dict[c] = state[i].c
        feed_dict[h] = state[i].h
      
      vals = session.run(fetches, feed_dict)
      cost = vals["cost"]
      correct = vals["correct"]
      state = vals["final_state"]
      
      costs += cost
      total_correct +=correct
      iters += 1
  
      if verbose and step % (self.input.epoch_size // 10) == 10:
        print("%.3f cost: %.3f speed: %.0f sentences per second" %
              (step * 1.0 / self.input.epoch_size, (costs / iters),   #np.exp
               iters * self.input.batch_size / (time.time() - start_time)))
    
    return (costs / iters), (total_correct / iters / self.input.batch_size)
  
  
  def run_predict(self, session):
    """Runs the model on the given data."""
    state = session.run(self.initial_state)
    
    fetches = {
        "sm_logits": self.sm_logits,
    }
    feed_dict = {}
    for i, (c, h) in enumerate(self.initial_state):
      feed_dict[c] = state[i].c
      feed_dict[h] = state[i].h
  
    vals = session.run(fetches, feed_dict)
    sm_logits = vals["sm_logits"]
  
    return sm_logits

# =========================================================================================================
  
class DLSTMCharModel(object):
  def __init__(self, is_training, config, input_, type_cell, data_type=tf.float32):
    self._input = input_

    batch_size = input_.batch_size
    hidden_size = config.hidden_size
    vocab_size = config.vocab_size
    num_labels = config.num_labels
    
    def lstm_cell(type_cell):
      if type_cell == 'gru':
        return tf.compat.v1.nn.rnn_cell.GRUCell(hidden_size, reuse=tf.compat.v1.get_variable_scope().reuse)
      else:
        return tf.compat.v1.nn.rnn_cell.BasicLSTMCell(hidden_size, reuse=tf.compat.v1.get_variable_scope().reuse)

    attn_cell = lstm_cell
    if is_training and config.keep_prob < 1:
      def attn_cell(type_cell):
        return tf.compat.v1.nn.rnn_cell.DropoutWrapper(lstm_cell(type_cell), output_keep_prob=config.keep_prob)

    cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([attn_cell(type_cell) for _ in range(config.num_layers)], state_is_tuple=True)

    embedding = tf.compat.v1.get_variable("embedding", [vocab_size, hidden_size], dtype=data_type)
    inputs = tf.nn.embedding_lookup(params=embedding, ids=input_.input_data)  # [batch_size, doc_len, hidden_size]
    
    if is_training and config.keep_prob < 1:
      inputs = tf.nn.dropout(inputs, 1 - (config.keep_prob))

    outputs, _ = tf.compat.v1.nn.dynamic_rnn(cell, inputs, dtype=data_type)   # sequence_length= input_.lens, 
    indices = tf.stack([tf.range(batch_size), tf.subtract(input_.lens, 1)], 1)
    output = tf.gather_nd(outputs, indices) #      output is [batch_size, hidden_size]

    softmax_w = tf.compat.v1.get_variable("softmax_w", [hidden_size, num_labels], dtype=data_type)
    softmax_b = tf.compat.v1.get_variable("softmax_b", [num_labels], dtype=data_type)
    logits = tf.matmul(output, softmax_w) + softmax_b

    logits = tf.reshape(logits, [batch_size, 1, num_labels])
    onehot_targets = tf.one_hot(input_.targets, num_labels, 1, 0)
    loss = tf.compat.v1.losses.softmax_cross_entropy(onehot_labels=onehot_targets, logits=logits)

    self._cost = cost = loss
    self.sm_logits =  tf.nn.softmax(logits, name="sm_logits")

    if not is_training:
      _y = tf.argmax(input=logits, axis=2, output_type=tf.int32)
      c_p = tf.equal(_y, input_.targets)
      self._correct =  tf.reduce_sum(input_tensor=tf.cast(c_p, tf.float32))
      return
    else:
      self._correct =  tf.constant(0.0)

    self._lr = tf.Variable(0.0, trainable=False)
    tvars = tf.compat.v1.trainable_variables()
    grads, _ = tf.clip_by_global_norm(tf.gradients(ys=cost, xs=tvars), config.max_grad_norm)
    optimizer = tf.compat.v1.train.GradientDescentOptimizer(self._lr)    #  try others
    self._train_op = optimizer.apply_gradients(
        zip(grads, tvars),
        global_step=tf.contrib.framework.get_or_create_global_step())

    self._new_lr = tf.compat.v1.placeholder(tf.float32, shape=[], name="new_learning_rate")
    self._lr_update = tf.compat.v1.assign(self._lr, self._new_lr)

  def assign_lr(self, session, lr_value):
    session.run(self._lr_update, feed_dict={self._new_lr: lr_value})

  @property
  def input(self):
    return self._input

  @property
  def cost(self):
    return self._cost

  @property
  def correct(self):
    return self._correct

  @property
  def lr(self):
    return self._lr

  @property
  def train_op(self):
    return self._train_op

  def run_epoch(self, session, eval_op=None, verbose=False):
    """Runs the model on the given data."""
    start_time = time.time()
    costs = 0.0
    total_correct = 0.0
    iters = 0
  
    fetches = {
        "cost": self.cost,
        "correct": self.correct,
    }
    if eval_op is not None:
      fetches["eval_op"] = eval_op
  
    if self.input.epoch_size == 0:
      epoch_size = 1
    else:
      epoch_size = self.input.epoch_size
    
    for step in range(epoch_size):
        
      vals = session.run(fetches)
      cost = vals["cost"]
      correct = vals["correct"]
      
      costs += cost
      total_correct +=correct
      iters += 1
  
      if verbose and step % (self.input.epoch_size // 10) == 10:
        print("%.3f cost: %.3f speed: %.0f sentences per second" %
              (step * 1.0 / self.input.epoch_size, (costs / iters),   #np.exp
               iters * self.input.batch_size / (time.time() - start_time)))
    
    return (costs / iters), (total_correct / iters / self.input.batch_size)
  
  
  def run_predict(self, session):
    """Runs the model on the given data."""
    
    fetches = {
        "sm_logits": self.sm_logits,
    }
  
    vals = session.run(fetches)
    sm_logits = vals["sm_logits"]
  
    return sm_logits
  
# =========================================================================================================
  
class BiLSTMCharModel(object):
  def __init__(self, is_training, config, input_, type_cell, data_type=tf.float32):
    self._input = input_

    batch_size = input_.batch_size
    hidden_size = config.hidden_size
    vocab_size = config.vocab_size
    num_labels = config.num_labels
    
    def lstm_cell(type_cell):
      if type_cell == 'gru':
        return tf.compat.v1.nn.rnn_cell.GRUCell(hidden_size, reuse=tf.compat.v1.get_variable_scope().reuse)
      else:
        return tf.compat.v1.nn.rnn_cell.BasicLSTMCell(hidden_size, reuse=tf.compat.v1.get_variable_scope().reuse)

    attn_cell = lstm_cell
    if is_training and config.keep_prob < 1:
      def attn_cell(type_cell):
        return tf.compat.v1.nn.rnn_cell.DropoutWrapper(lstm_cell(type_cell), output_keep_prob=config.keep_prob)

    cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([attn_cell(type_cell) for _ in range(config.num_layers)], state_is_tuple=True)

    embedding = tf.compat.v1.get_variable("embedding", [vocab_size, hidden_size], dtype=data_type)
    inputs = tf.nn.embedding_lookup(params=embedding, ids=input_.input_data)  # [batch_size, doc_len, hidden_size]
    
    if is_training and config.keep_prob < 1:
      inputs = tf.nn.dropout(inputs, 1 - (config.keep_prob))

    outputs, _ = tf.compat.v1.nn.bidirectional_dynamic_rnn(cell, cell, inputs, sequence_length= input_.lens,dtype=data_type)
    
    indices = tf.stack([tf.range(batch_size), tf.subtract(input_.lens, 1)], 1)
    output_ = tf.concat([outputs[0], outputs[1]], 2)
    output = tf.gather_nd(output_, indices) #      output is [batch_size, hidden_size]

    softmax_w = tf.compat.v1.get_variable("softmax_w", [hidden_size*2, num_labels], dtype=data_type)
    softmax_b = tf.compat.v1.get_variable("softmax_b", [num_labels], dtype=data_type)
    logits = tf.matmul(output, softmax_w) + softmax_b

    logits = tf.reshape(logits, [batch_size, 1, num_labels])
    onehot_targets = tf.one_hot(input_.targets, num_labels, 1, 0)
    loss = tf.compat.v1.losses.softmax_cross_entropy(onehot_labels=onehot_targets, logits=logits)

    self._cost = cost = loss
    self.sm_logits =  tf.nn.softmax(logits, name="sm_logits")

    if not is_training:
      _y = tf.argmax(input=logits, axis=2, output_type=tf.int32)
      c_p = tf.equal(_y, input_.targets)
      self._correct =  tf.reduce_sum(input_tensor=tf.cast(c_p, tf.float32))
      return
    else:
      self._correct =  tf.constant(0.0)

    self._lr = tf.Variable(0.0, trainable=False)
    tvars = tf.compat.v1.trainable_variables()
    grads, _ = tf.clip_by_global_norm(tf.gradients(ys=cost, xs=tvars), config.max_grad_norm)
    optimizer = tf.compat.v1.train.GradientDescentOptimizer(self._lr)    #  try others
    self._train_op = optimizer.apply_gradients(
        zip(grads, tvars),
        global_step=tf.contrib.framework.get_or_create_global_step())

    self._new_lr = tf.compat.v1.placeholder(tf.float32, shape=[], name="new_learning_rate")
    self._lr_update = tf.compat.v1.assign(self._lr, self._new_lr)

  def assign_lr(self, session, lr_value):
    session.run(self._lr_update, feed_dict={self._new_lr: lr_value})

  @property
  def input(self):
    return self._input

  @property
  def cost(self):
    return self._cost

  @property
  def correct(self):
    return self._correct

  @property
  def lr(self):
    return self._lr

  @property
  def train_op(self):
    return self._train_op

  def run_epoch(self, session, eval_op=None, verbose=False):
    """Runs the model on the given data."""
    start_time = time.time()
    costs = 0.0
    total_correct = 0.0
    iters = 0
  
    fetches = {
        "cost": self.cost,
        "correct": self.correct,
    }
    if eval_op is not None:
      fetches["eval_op"] = eval_op
  
    if self.input.epoch_size == 0:
      epoch_size = 1
    else:
      epoch_size = self.input.epoch_size
    
    for step in range(epoch_size):
        
      vals = session.run(fetches)
      cost = vals["cost"]
      correct = vals["correct"]
      
      costs += cost
      total_correct +=correct
      iters += 1
  
      if verbose and step % (self.input.epoch_size // 10) == 10:
        print("%.3f cost: %.3f speed: %.0f sentences per second" %
              (step * 1.0 / self.input.epoch_size, (costs / iters),   #np.exp
               iters * self.input.batch_size / (time.time() - start_time)))
    
    return (costs / iters), (total_correct / iters / self.input.batch_size)
  
  
  def run_predict(self, session):
    """Runs the model on the given data."""
    
    fetches = {
        "sm_logits": self.sm_logits,
    }
  
    vals = session.run(fetches)
    sm_logits = vals["sm_logits"]
  
    return sm_logits
  
# =========================================================================================================

class DLSTMWordModel(object):
  def __init__(self, is_training, config, input_, type_cell, data_type=tf.float32):
    self._input = input_

    batch_size = input_.batch_size
    hidden_size = config.hidden_size
    vocab_size = config.vocab_size
    num_labels = config.num_labels
    
    def lstm_cell(type_cell):
      if type_cell == 'gru':
        return tf.compat.v1.nn.rnn_cell.GRUCell(hidden_size, reuse=tf.compat.v1.get_variable_scope().reuse)
      else:
        return tf.compat.v1.nn.rnn_cell.BasicLSTMCell(hidden_size, reuse=tf.compat.v1.get_variable_scope().reuse)

    attn_cell = lstm_cell
    if is_training and config.keep_prob < 1:
      def attn_cell(type_cell):
        return tf.compat.v1.nn.rnn_cell.DropoutWrapper(lstm_cell(type_cell), output_keep_prob=config.keep_prob)

    cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([attn_cell(type_cell) for _ in range(config.num_layers)], state_is_tuple=True)

    embedding = tf.compat.v1.get_variable("embedding", [vocab_size, hidden_size], dtype=data_type)
    inputs = tf.nn.embedding_lookup(params=embedding, ids=input_.input_data)  # [batch_size, doc_len, hidden_size]
    
    if is_training and config.keep_prob < 1:
      inputs = tf.nn.dropout(inputs, 1 - (config.keep_prob))

    outputs, _ = tf.compat.v1.nn.dynamic_rnn(cell, inputs, dtype=data_type)   # sequence_length= input_.lens, 
    indices = tf.stack([tf.range(batch_size), tf.subtract(input_.lens, 1)], 1)
    output = tf.gather_nd(outputs, indices) #      output is [batch_size, hidden_size]

    softmax_w = tf.compat.v1.get_variable("softmax_w", [hidden_size, num_labels], dtype=data_type)
    softmax_b = tf.compat.v1.get_variable("softmax_b", [num_labels], dtype=data_type)
    logits = tf.matmul(output, softmax_w) + softmax_b

    logits = tf.reshape(logits, [batch_size, 1, num_labels])
    onehot_targets = tf.one_hot(input_.targets, num_labels, 1, 0)
    loss = tf.compat.v1.losses.softmax_cross_entropy(onehot_labels=onehot_targets, logits=logits)

    self._cost = cost = loss
    self.sm_logits =  tf.nn.softmax(logits, name="sm_logits")

    _y = tf.argmax(input=logits, axis=2, output_type=tf.int32)
    c_p = tf.equal(_y, input_.targets)
    self._correct =  tf.reduce_sum(input_tensor=tf.cast(c_p, tf.float32))

    if not is_training:
      return

    self._lr = tf.Variable(0.0, trainable=False)
    tvars = tf.compat.v1.trainable_variables()
    grads, _ = tf.clip_by_global_norm(tf.gradients(ys=cost, xs=tvars), config.max_grad_norm)
    optimizer = tf.compat.v1.train.GradientDescentOptimizer(self._lr)    #  try others
    self._train_op = optimizer.apply_gradients(
        zip(grads, tvars),
        global_step=tf.contrib.framework.get_or_create_global_step())

    self._new_lr = tf.compat.v1.placeholder(tf.float32, shape=[], name="new_learning_rate")
    self._lr_update = tf.compat.v1.assign(self._lr, self._new_lr)

  def assign_lr(self, session, lr_value):
    session.run(self._lr_update, feed_dict={self._new_lr: lr_value})

  @property
  def input(self):
    return self._input

  @property
  def cost(self):
    return self._cost

  @property
  def correct(self):
    return self._correct

  @property
  def lr(self):
    return self._lr

  @property
  def train_op(self):
    return self._train_op

  def run_epoch(self, session, eval_op=None, verbose=False):
    """Runs the model on the given data."""
    start_time = time.time()
    costs = 0.0
    total_correct = 0.0
    iters = 0
  
    fetches = {
        "cost": self.cost,
        "correct": self.correct,
    }
    if eval_op is not None:
      fetches["eval_op"] = eval_op
  
    if self.input.epoch_size == 0:
      epoch_size = 1
    else:
      epoch_size = self.input.epoch_size
    
    for step in range(epoch_size):
        
      vals = session.run(fetches)
      cost = vals["cost"]
      correct = vals["correct"]
      
      costs += cost
      total_correct +=correct
      iters += 1
  
      if verbose and step % (self.input.epoch_size // 10) == 10:
        print("%.3f cost: %.3f speed: %.0f sentences per second" %
              (step * 1.0 / self.input.epoch_size, (costs / iters),   #np.exp
               iters * self.input.batch_size / (time.time() - start_time)))
    
    return (costs / iters), (total_correct / iters / self.input.batch_size)
  
  
  def run_predict(self, session):
    """Runs the model on the given data."""
    
    fetches = {
        "sm_logits": self.sm_logits,
    }
  
    vals = session.run(fetches)
    sm_logits = vals["sm_logits"]
  
    return sm_logits
  
