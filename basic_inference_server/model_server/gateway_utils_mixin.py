import json
from datetime import datetime, timedelta

class StateCT:
  CURRENT_STARTUP = 'CURRENT_STARTUP'
  PREVIOUS_STARTUP = 'PREVIOUS_STARTUP'
  LAST_SHUTDOWN = 'LAST_SHUTDOWN'
  LAST_RUNTIME = 'LAST_RUNTIME_HOURS'
  SHUTDOWN = 'SHUTDOWN'
  STARTUP = 'STARTUP'

class _GatewayUtilsMixin(object):
  def __init__(self):
    super(_GatewayUtilsMixin, self).__init__()
    
    self.__gw_state_history = {}
    return
  
  def _elapsed_to_str(self, t):
    return str(timedelta(seconds=int(t)))
  
  def get_hours_difference(self, str_current_start, str_current_stop):
    """
    Calculate the difference in hours between two datetime strings.

    Parameters:
    str_current_start (str): The start datetime in "%Y-%m-%d %H:%M:%S" format.
    str_current_stop (str): The stop datetime in "%Y-%m-%d %H:%M:%S" format.

    Returns:
    float: The difference in hours between the start and stop datetimes.
    """
    format = "%Y-%m-%d %H:%M:%S"
    start = datetime.strptime(str_current_start, format)
    stop = datetime.strptime(str_current_stop, format)

    # Calculate the difference and convert to hours
    difference = stop - start
    str_result = self._elapsed_to_str(difference.total_seconds())

    return str_result
  
  def get_gw_state_history(self):
    return self.__gw_state_history
  
  def load_gw_state_history(self, fn='gw_state_history.json'):
    hist_fn = self.log.get_data_file(fn)
    if hist_fn is not None:
      self.P("Loading gateway state history from: {}".format(hist_fn))
      self.__gw_state_history = self.log.load_data_json(fn)
      self.P("Loaded gateway state history:\n{}".format(
        json.dumps(self.__gw_state_history, indent=2))
      )
    return
  
  def _save_gw_state_history(self, fn='gw_state_history.json'):
    self.log.save_data_json(self.__gw_state_history, fname=fn)
    return
    

  def update_gw_state_history(self, state : str = None):
    if not isinstance(state, str):
      return
    state = state.upper()
    if state == 'SHUTDOWN':
      self.__gw_state_history[StateCT.LAST_SHUTDOWN] = self.log.now_str(
        nice_print=True, short=True
      )
      str_current_start = self.__gw_state_history[StateCT.CURRENT_STARTUP]      
      str_current_stop = self.__gw_state_history[StateCT.LAST_SHUTDOWN]
      # now compute the time elapsed based on the two timestamp strings
      elapsed = self.get_hours_difference(str_current_start, str_current_stop)
      self.__gw_state_history[StateCT.LAST_RUNTIME] = elapsed
    elif state == 'STARTUP':
      self.__gw_state_history[StateCT.PREVIOUS_STARTUP] = self.__gw_state_history.get(StateCT.CURRENT_STARTUP, None)
      self.__gw_state_history[StateCT.CURRENT_STARTUP] = self.log.now_str(
        nice_print=True, short=True
      )
    #endif
    self._save_gw_state_history()
    return