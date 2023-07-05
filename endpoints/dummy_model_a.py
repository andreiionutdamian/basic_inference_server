"""
Copyright (C) 2017-2021 Andrei Damian, andrei.damian@me.com,  All rights reserved.

This software and its associated documentation are the exclusive property of the creator.
Unauthorized use, copying, or distribution of this software, or any portion thereof,
is strictly prohibited.

Parts of this software are licensed and used in software developed by Neural Energy SRL.
Any software proprietary to Neural Energy SRL is covered by Romanian and  Foreign Patents,
patents in process, and are protected by trade secret or copyright law.

Dissemination of this information or reproduction of this material is strictly forbidden unless prior
written permission from the author.

"""

from libraries.model_server_v2 import FlaskWorker

_CONFIG = {
  'WEIGHT'     : 0,
  'BIAS'       : 0,
  'PLACEHOLDER_MODEL' : True,
}

__WORKER_VER__ = '1.2.1'

class PlaceholderModel():
  def __init__(self, log):
    self.log = log
    self.log.P("******** Using a model placeholder *********", color='r')
    return 
  
  def get_similar(self, **kwargs):
    return "same-word-always"

class DummyModelAWorker(FlaskWorker):

  """
  Example implementation of a worker

  Obs: as the worker runs on thread, then no prints are allowed; use `_create_notification` and see all the notifications
       when calling /notifications of the server.
  """

  def __init__(self, **kwargs):
    super(DummyModelAWorker, self).__init__(prefix_log='[DUMA]', **kwargs)
    return


  def _load_model(self):
    ### see docstring in parent
    ### abstract method implementation: no model to be loaded
    self.nlp_model = PlaceholderModel(log=self.log)
    return

  def _pre_process(self, inputs):
    ### see docstring in parent
    ### abstract method implementation: parses the request inputs and keep the value for 'INPUT_VALUE'
    if 'INPUT_VALUE' not in inputs.keys():
      raise ValueError('INPUT_VALUE should be defined in inputs')

    s = inputs['INPUT_VALUE']

    lang = inputs.get('LANGUAGE', inputs.get('language', 'ro'))

    return s, lang

  def _predict(self, prep_inputs):
    ### see docstring in parent
    ### abstract method implementation: "in-memory model :)" that adds and subtracts.
    self._create_notification(
      notif='log',
      msg='Predicting on usr_input: {} using {}'.format(prep_inputs, self.config_data)
    )
    res = ''
    if isinstance(prep_inputs, float):
      val = int(prep_inputs)
      res = '{}*{} + {} = {} PREDICTED'.format(prep_inputs, self.cfg_weight, self.cfg_bias, val * self.cfg_weight + self.cfg_bias)
    else:
      word, lang = prep_inputs
      res = self.nlp_model.get_similar(word=word, lang=lang)
    return res, prep_inputs

  def _post_process(self, pred):
    ### see docstring in parent
    ### abstract method implementation: packs the endpoint answer that will be jsonified
    pred, (inputs, lang) = pred
    result = {
      'dummy_model_a_predict' : pred, 
      'inputs' : {
        'INPUT_VALUE' : inputs, 
        'LANGUAGE' : lang
      }, 
      'worker_ver' : __WORKER_VER__
    }
    return result
