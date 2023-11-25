import flask
import requests


from time import sleep, time
from datetime import timedelta


from .request_utils import get_api_request_body, MSCT
from .gateway_utils_mixin import StateCT

from ..lib_ver import __VER__ as LIB_VER
from app_ver import __VER__ as APP_VER

class _GatewayFunctionMixin(object):
  def __init__(self) -> None:
    super(_GatewayFunctionMixin, self).__init__()
    return
  

  def _view_func_worker(self, path):
    request = flask.request
    params = get_api_request_body(request, self.log)
    signature = params.pop(MSCT.SIGNATURE, None)
    if signature is None:
      return self.get_response({MSCT.ERROR : "Bad input. MSCT.SIGNATURE not found"})

    if signature not in self._servers:
      return self.get_response({
        MSCT.ERROR : "Bad signature {}. Available signatures/servers: {}".format(
          signature, 
          self.active_servers
        )
      })
    
    url = 'http://{}:{}{}'.format(
      self._servers[signature][MSCT.HOST],
      self._servers[signature][MSCT.PORT],
      path
    )
    result = None
    request_time_since_start = time() - self._servers[signature][MSCT.START]
    try:      
      response = requests.post(url, json=params)
      result = self.get_response(response.json())
    except Exception as exc:
      if request_time_since_start < 70:
        msg = "Server '{}' is not responding ({:.1f}s from start) - probably is still in INIT stage: {}".format(
          url, request_time_since_start,
          exc
        )
      else:
        msg = "Server '{}' is not responding ({:.1f}s from start) - probably is DOWN: {}".format(
          url, request_time_since_start,
          exc
        )
      #endif too early or not
      result = self.get_response({
        MSCT.ERROR : msg,
      })
    return result

  def _view_func_start_server(self):
    request = flask.request
    params = get_api_request_body(request, self.log)
    signature = params.get(MSCT.SIGNATURE, None)

    if signature is None:
      return self.get_response({MSCT.ERROR : f"Bad input. {MSCT.SIGNATURE} not found"})

    if self._server_exists(signature):
      return self.get_response({MSCT.ERROR : "Signature {} already started".format(signature)})

    resp = self._start_server(
      server_name=signature,
      port=self._current_server_port,
      execution_path=self._server_execution_path,
      verbosity=0
    )
    if resp:
      self._current_server_port += 1
      return self.get_response({'MESSAGE': 'OK.'})
    else:
      return self.get_response({'MESSAGE': 'Server DISABLED.'})

  def _view_func_kill_server(self):
    request = flask.request
    params = get_api_request_body(request, self.log)
    signature = params.get(MSCT.SIGNATURE, None)

    if signature is None:
      return self.get_response({MSCT.ERROR : f"Bad input. {MSCT.SIGNATURE} not found"})
    
    if signature == '*':
      self.kill_servers()      
    elif not self._server_exists(signature):
      return self.get_response({MSCT.ERROR : "Bad signature {}. Available signatures: {}".format(signature, self.active_servers)})
    else:
      process = self._get_server_process(signature)
      self._kill_server_by_name(signature)
      return self.get_response({'MESSAGE' : 'OK. Killed PID={} with return_code {}.'.format(
        process.pid,
        process.returncode
      )})


  def _view_list_servers(self):
    return self.get_response({
      MSCT.AVAIL_SERVERS : {
        svr_name : self._get_server_status(svr_name)
        for svr_name in self._servers 
      },
    })
  
  
  def _view_system_status(self):
    status, alerts = self._get_system_status(display=True)
    dct_history = self.get_gw_state_history()
    return self.get_response({
      MSCT.SYSTEM_ALERTS : alerts,
      MSCT.SYSTEM_HISTORY : dct_history,
      MSCT.SYSTEM_STATUS : status,
    })
    
    
  def _view_shutdown(self):
    request = flask.request
    params = get_api_request_body(request, self.log)
    signature = params.get(MSCT.SIGNATURE, None)

    if signature is None:
      return self.get_response({MSCT.ERROR : f"Bad input. {MSCT.SIGNATURE} not found"})
    
    if signature.upper() == MSCT.KILL_CMD:
      self.P("Received shutdown command.Confirmation signature: {}".format(signature.upper()))
      self.gw_shutdown()
    #endif done kill 

    if not self._server_exists(signature):
      return self.get_response({MSCT.ERROR : "Bad signature {}. Available signatures: {}".format(signature, self.active_servers)})
    return
  

  def _view_support_status(self):
    ok = True
    request = flask.request
    params = get_api_request_body(request, self.log)
    signature = params.get(MSCT.SIGNATURE, None)

    if signature is None:
      return self.get_response({MSCT.ERROR : f"Bad input. {MSCT.SIGNATURE} not found"})
    message = params.get('msg')
    if message is not None:
      self.P("<STATUS {}>: {}".format(signature, message), color='m')
    if ok:
      return self.get_response({'MESSAGE': 'OK.'})
    else:
      return self.get_response({'MESSAGE': 'ERROR.'})
  