import flask
import numpy as np
import json

from time import sleep

from ..model_server.request_utils import get_api_request_body, MSCT
from ..lib_ver import __VER__ as LIB_VER


class _ServerFunctionsMixin(object):
  def __init__(self) -> None:
    super(_ServerFunctionsMixin, self).__init__()
    return
  

  def _view_func_plugin_endpoint(self):
    self._lock_counter.acquire()
    self._counter += 1
    counter = self._counter
    self._lock_counter.release()
    
    try:
      request = flask.request
      method = request.method
      
      params = get_api_request_body(request=request, log=self.log)
      client = params.get('client', 'unk')
  
      self._create_notification( # TODO: do we really need this notification? get_qa is crazy...
        notif='log',
        msg=(counter, "Received '{}' request {} from client '{}' params: {}".format(
          method, counter, client, params
        ))
      )
      failed_request = False
      err_msg = ''
    except Exception as exc:
      failed_request = True
      err_msg = str(self.log.get_error_info()) # maybe use
      self.P("Request processing generated exception: {}".format(err_msg), color='r')

    worker, wid = None, -1
    if method != 'OPTIONS' and not failed_request:
      worker, answer, wid = self._wait_predict(data=params, counter=counter)
    else:
      answer = {'request_error' : err_msg}

    if answer is None:
      jresponse = flask.jsonify({
        "ERROR": "input json does not contain right info or other error has occured",
        "client": client,
        "call_id": counter,
        "input": params,
        'time' : self.log.time_to_str(),
      })
    else:
      if isinstance(answer, dict):
        answer['call_id'] = counter
        answer['time'] = self.log.time_to_str()
        if worker is not None:
          answer['signature'] = '{}:{}:{}'.format(
            self.name,
            worker.__class__.__name__, 
            wid
          )
        jresponse = flask.jsonify(answer)
      else:
        assert isinstance(answer, str)
        jresponse = flask.make_response(answer)
      #endif
    #endif

    jresponse.headers["Access-Control-Allow-Origin"] = "*"
    jresponse.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, DELETE"
    jresponse.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return jresponse

  def _view_func_notifications_endpoint(self):
    server_notifs = self.get_notifications()
    workers_notifs = self.log.flatten_2d_list([w.get_notifications() for w in self._lst_workers])

    all_notifs = server_notifs + workers_notifs

    lst_general_notifs = []
    dct_notifs_per_call = {}
    for notif in all_notifs:
      dct = {
        MSCT.NOTIF_NOTIFICATION_TYPE : notif[MSCT.NOTIF_NOTIFICATION_TYPE],
        MSCT.NOTIF_MODULE : notif[MSCT.NOTIF_MODULE],
        MSCT.TIME   : notif[MSCT.NOTIF_TIME]
      }

      if isinstance(notif['NOTIFICATION'], tuple):
        counter, msg = notif['NOTIFICATION']
        counter = str(counter)
        dct['NOTIF'] = msg

        if counter not in dct_notifs_per_call:
          dct_notifs_per_call[counter] = []

        dct_notifs_per_call[counter].append(dct)
      elif isinstance(notif['NOTIFICATION'], str):
        msg = notif['NOTIFICATION']
        dct['NOTIF'] = msg
        lst_general_notifs.append(dct)
      #endif

    #endfor

    jresponse = flask.jsonify({
      **{"GENERAL" : lst_general_notifs},
      **dct_notifs_per_call
    })
    return jresponse

  def _view_func_workers_endpoint(self):
    request = flask.request
    params = get_api_request_body(request=request, log=self.log)

    nr_workers = params.get(MSCT.NR_WORKERS, None)
    if nr_workers is None:
      return flask.jsonify({'ERROR' : "Bad input. 'NR_WORKERS' not found"})

    self._update_nr_workers(nr_workers)
    return flask.jsonify({'MESSAGE': 'OK'})

  def _view_func_get_paths_endpoint(self):
    return flask.jsonify({MSCT.PATHS : self._paths})  