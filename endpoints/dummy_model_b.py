

from libraries.model_server_v2 import FlaskWorker

_CONFIG = {
  'WEIGHT'    : 0,
  'BIAS'      : 0,
}

class DummyModelBWorker(FlaskWorker):

  """
  Example implementation of a worker

  Obs: as the worker runs on thread, then no prints are allowed; use `_create_notification` and see all the notifications
       when calling /notifications of the server.
  """

  def __init__(self, **kwargs):
    super(DummyModelBWorker, self).__init__(prefix_log='[DUMB]', **kwargs)
    return


  def _load_model(self):
    ### see docstring in parent
    ### abstract method implementation: no model to be loaded
    return

  def _pre_process(self, inputs):
    ### see docstring in parent
    ### abstract method implementation: parses the request inputs and keep the value for 'INPUT_VALUE'
    if 'INPUT_VALUE' not in inputs.keys():
      raise ValueError('INPUT_VALUE should be defined in inputs')

    s = inputs['INPUT_VALUE']
    return s

  def _predict(self, prep_inputs):
    ### see docstring in parent
    ### abstract method implementation: "in-memory model :)" that adds and subtracts.
    self._create_notification(
      notif='log',
      msg='Predicting on usr_input: {} using {}'.format(prep_inputs, self.config_data)
    )
    val = int(prep_inputs)
    res = '{}*{} + {} = {} PREDICTED'.format(prep_inputs, self.cfg_weight, self.cfg_bias, val * self.cfg_weight + self.cfg_bias)
    return res

  def _post_process(self, pred):
    ### see docstring in parent
    ### abstract method implementation: packs the endpoint answer that will be jsonified
    return {'dummy_model_predict' : pred}
