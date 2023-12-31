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

import flask
import numpy as np
import json

from time import sleep

from threading import Lock

from ..public_logger import Logger
from ..generic_obj import BaseObject
from ..plugins_manager_mixin import _PluginsManagerMixin
from ..logger_mixins.serialization_json_mixin import NPJson

from ..model_server.request_utils import MSCT

from ..lib_ver import __VER__ as LIB_VER

from .server_functions import _ServerFunctionsMixin


class FlaskModelServer(BaseObject, _PluginsManagerMixin, _ServerFunctionsMixin):

  app = None

  def __init__(self, log : Logger,
               workers_location : str,
               worker_name : str,
               host_id : str,
               worker_suffix=None,
               microservice_name=None,
               host=None,
               port=None,
               config_endpoint=None,
               execution_path=None,
               verbosity_level=1,
               nr_workers=None
               ):

    """
    Parameters:
    -----------
    log : Logger, mandatory

    workers_location: str, mandatory
      Dotted path of the folder where the business logic of the workers is implemented

    worker_name: str, mandatory
      Which implementation found in `workers_location` is started in this server

    worker_suffix: str, optional
      Which is the suffix of the class name for the started worker
      e.g. if the worker .py file is called 'get_similarity.py', then the name of the class is GetSimilarity<Suffix>.
      If `worker_suffix=Worker`; then the name of the class is GetSimilarityWorker
      The default is None

    host: str, optional
      Host of the gateway
      The default is None ('127.0.0.1')

    port: int, optional
      Port of the gateway
      The default is None (5000)

    config_endpoint: dict, optional
      The configuration of the endpoint:
        * 'NR_WORKERS'
        * other params that will be passed as upstream configuration to the worker
      The default is None ({})

    execution_path: str, optional
      The API rule where the worker logic is executed.
      The default is None ('/analyze')

    verbosity_level: int, optional
      The default is 1

    nr_workers: int, optional
      How many instances of the chosen worker are started.
      The default is None (5)
    """

    self.__version__ = LIB_VER
    self.__host_id = host_id
    self.__workers_location = workers_location
    self.__worker_name = worker_name
    self.__worker_suffix = worker_suffix
    self.__initial_nr_workers = nr_workers or 5
    self.__microservice_name = microservice_name or worker_name
    self.__worker_class_name = None

    self._host = host or '127.0.0.1'
    self._port = port or 5000
    self._execution_path = execution_path or '/analyze'
    self._verbosity_level = verbosity_level
    self._config_endpoint = config_endpoint or {}

    self._lst_workers = []
    self._mask_workers_in_use = []
    self._counter = 0

    self._lock = Lock()
    self._lock_counter = Lock()
    self._paths = None

    super(FlaskModelServer, self).__init__(log=log, prefix_log='[FSKSVR]', maxlen_notifications=1000)
    return

  def startup(self):
    super().startup()
    self._update_nr_workers(self.__initial_nr_workers)
    self._log_banner()

    if not self._execution_path.startswith('/'):
      self._execution_path = '/' + self._execution_path

    self.app = flask.Flask('FlaskModelServer')
    self.app.json_encoder = NPJson
    self.app.add_url_rule(
      rule=self._execution_path,
      endpoint="PluginEndpoint",
      view_func=self._view_func_plugin_endpoint,
      methods=['GET', 'POST', 'OPTIONS']
    )

    self.app.add_url_rule(
      rule=MSCT.RULE_NOTIF,
      endpoint='NotificationsEndpoint',
      view_func=self._view_func_notifications_endpoint,
      methods=['GET', 'POST']
    )

    self.app.add_url_rule(
      rule=MSCT.RULE_UPDATE_WORKERS,
      endpoint='WorkersEndpoint',
      view_func=self._view_func_workers_endpoint,
      methods=['GET', 'POST'],
    )

    self._paths = [self._execution_path, MSCT.RULE_NOTIF, MSCT.RULE_UPDATE_WORKERS]

    self.app.add_url_rule(
      rule=MSCT.RULE_PATHS,
      endpoint='GetPathsEndpoint',
      view_func=self._view_func_get_paths_endpoint,
      methods=['GET', 'POST']
    )

    self.app.run(
      host=self._host,
      port=self._port,
      threaded=True
    )

    return
  
  
  @property
  def name(self):
    return self.__worker_name

  def _log_banner(self):
    _logo = "FlaskModelServer v{} '{}' <{} code={}> started on '{}:{}'".format(
      self.__version__, self.__microservice_name, self.__worker_name, self.__worker_class_name,  self._host, self._port
    )

    self.log.P(_logo, color='g', boxed=True)
    self.log.P("Given full config:\n{}".format(json.dumps(self._config_endpoint, indent=4)))
    return

  def _create_worker(self):
    _module_name, _class_name, _cls_def, _config_dict = self._get_module_name_and_class(
      locations=self.__workers_location,
      name=self.__worker_name,
      suffix=self.__worker_suffix
    )
    
    if _cls_def is None:
      return
    
    self.__worker_class_name = _cls_def.__name__

    worker_id = len(self._mask_workers_in_use)

    worker = _cls_def(
      log=self.log,
      default_config=_config_dict,
      verbosity_level=self._verbosity_level,
      worker_id=worker_id,
      upstream_config=self._config_endpoint
    )

    self._lst_workers.append(worker)
    self._mask_workers_in_use.append(0)
    return

  def _update_nr_workers(self, nr_workers):
    nr_crt_workers = len(self._lst_workers)
    nr_new_workers = nr_workers - nr_crt_workers

    if nr_new_workers > 0:
      str_msg = "Creating {} workers for server '{}'".format(nr_new_workers, self.__worker_name)
      self.P(str_msg, color='g')
      self._create_notification(notif='log', msg=str_msg)
      for _ in range(nr_new_workers):
        self._create_worker()
      str_msg = "Created {} new workers. (were:{}, total:{})".format(nr_new_workers, nr_crt_workers, nr_workers)
      self._create_notification(notif='log', msg=str_msg)
    elif nr_new_workers < 0:
      ###TODO delete only unused
      str_msg = "Should delete {} - not implemented yet".format(-1*nr_new_workers)
      self._create_notification(notif='log', msg=str_msg)
    else:
      str_msg = "Update with no effect, there are already {} workers".format(nr_workers)
      self._create_notification(notif='log', msg=str_msg)
    #endif
    return

  def _mask_worker_locked(self, wid):
    self._mask_workers_in_use[wid] = 1
    return

  def _mask_worker_unlocked(self, wid):
    self._mask_workers_in_use[wid] = 0

  def _find_unlocked_worker(self, counter):
    self._lock.acquire()
    unlocked_workers = np.where(np.array(self._mask_workers_in_use) == 0)[0]
    if unlocked_workers.shape[0] == 0:
      self._lock.release()
      return

    wid = int(np.random.choice(unlocked_workers))
    self._mask_worker_locked(wid)
    self._lock.release()
    return wid

  def _wait_predict(self, data, counter):
    wid = self._find_unlocked_worker(counter)
    if wid is None:
      # All model servers in use. Waiting...

      while wid is None:
        sleep(1)
        wid = self._find_unlocked_worker(counter)
      #endwhile

      # Waiting done.
    #endif

    # now worker is locked...
    worker = self._lst_workers[wid]
    answer = worker.execute(
      inputs=data,
      counter=counter
    )
    self._mask_worker_unlocked(wid)
    return worker, answer, wid

