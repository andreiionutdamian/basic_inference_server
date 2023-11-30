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
import sys
import platform
import os
import signal
import subprocess
import json
import requests
import psutil

import flask

from functools import partial
from time import sleep, time


from ..public_logger import Logger
from ..generic_obj import BaseObject
from ..logger_mixins.serialization_json_mixin import NPJson
from .request_utils import MSCT


from . import run_server as run_server_module

from ..lib_ver import __VER__ as LIB_VER
from app_ver import __VER__ as APP_VER

from .gateway_functions import _GatewayFunctionMixin
from .gateway_utils_mixin import _GatewayUtilsMixin, StateCT

DEFAULT_NR_WORKERS = 5
DEFAULT_HOST = '127.0.0.1'

DEFAULT_SERVER_PATHS = [
  MSCT.RULE_RUN,
  MSCT.RULE_NOTIF,
  MSCT.RULE_UPDATE_WORKERS
]

MONITORED_PACKAGES = [
  'numpy',
  'flask',
  'transformers',
  'torch',
  'tensorflow',
  'accelerate',
  'tokenizers',
  'Werkzeug',
  'python-telegram-bot',  
]


def get_packages(monitored_packages=None):
  import pkg_resources
  packs = [x for x in pkg_resources.working_set]
  maxlen = max([len(x.key) for x in packs]) + 1
  if isinstance(monitored_packages, list) and len(monitored_packages) > 0:
    packs = [
      "{}{}".format(x.key + ' ' * (maxlen - len(x.key)), x.version) for x in packs    
      if x.key in monitored_packages
    ]
  else:
    packs = [
      "{}{}".format(x.key + ' ' * (maxlen - len(x.key)), x.version) for x in packs    
    ]
  packs = sorted(packs)  
  return packs  

class FlaskGateway(
  BaseObject,
  _GatewayFunctionMixin,
  _GatewayUtilsMixin,
  ):

  app = None

  def __init__(self, log : Logger,
               workers_location : str,
               host_id : str,
               server_names=None,
               workers_suffix=None,
               host=None,
               port=None,
               first_server_port=None,
               server_execution_path=None,
               **kwargs
              ):

    """
    Parameters:
    -----------
    log : Logger, mandatory

    workers_location: str, mandatory
      Dotted path of the folder where the business logic of the workers is implemented

    server_names: List[str], optional
      The names of the servers that will be run when the gateway is opened. This names should be names of .py files
      found in `workers_location`
      The default is None (it takes all the keys in MSCT.CONFIG_ENDPOINTS)

    workers_suffix: str, optional
      For each worker, which is the suffix of the class name.
      e.g. if the worker .py file is called 'get_similarity.py', then the name of the class is GetSimilarity<Suffix>.
      If `workers_suffix=Worker`; then the name of the class is GetSimilarityWorker
      The default is None

    host: str, optional
      Host of the gateway
      The default is None ('127.0.0.1')

    port: int, optional
      Port of the gateway
      The default is None (5000)

    first_server_port: int, optional
      Port of the first server (the ports are allocated sequentially starting with `first_port_server`)
      The default is None (port+1)

    server_execution_path: str, optional
      The API rule where the worker logic is executed.
      The default is None (MSCT.RULE_DEFAULT)
    """

    self.__version__ = LIB_VER

    self._start_server_names = server_names
    self._host = host or '127.0.0.1'
    self._port = port or 5000
    self.__host_id = host_id
    self._server_execution_path = server_execution_path or MSCT.RULE_DEFAULT
    self._workers_location = workers_location
    self._workers_suffix = workers_suffix

    self._first_server_port = first_server_port or self._port + 1
    self._current_server_port = self._first_server_port

    self._config_endpoints = None
    
    self._start_time = time()
    
    self._servers = {}
    self._paths = None
    super(FlaskGateway, self).__init__(log=log, prefix_log='[GW]', **kwargs)
    return
    
  
  def get_response(self, data):
    if MSCT.DOWNLOAD_FILE_COMMAND in data:
      # MSCT.DOWNLOAD_FILE_COMMAND is a special field in responses that allows the creation of a file download from the
      # gateway directly to the client
      self.P("Received {} command:\n{}".format(MSCT.DOWNLOAD_FILE_COMMAND, json.dumps(data, indent=4)))
      dct_download = data[MSCT.DOWNLOAD_FILE_COMMAND]
      fn = dct_download[MSCT.DOWNLOAD_FILE_PATH]
      return flask.send_file(fn)
    else:
      if isinstance(data, dict):
        dct_result = data
      else:
        dct_result = {
          MSCT.DATA : data,        
        }
      dct_result[MSCT.APP_VER] = APP_VER
      dct_result[MSCT.FRM_VER] = LIB_VER
      dct_result[MSCT.TIME] = self.log.time_to_str()
      dct_result[MSCT.GW_UPTIME] = self._elapsed_to_str(time() - self._start_time)
      return flask.jsonify(dct_result)

  def _log_banner(self):
    _logo = "FlaskGateway v{} started on '{}:{}'".format(
      self.__version__, self._host, self._port
    )
    self.log.P(_logo, color='g', boxed=True)
    return

  def startup(self):
    super().startup()   
    self.show_env()
    self.load_gw_state_history() 
    self._log_banner()
    self._no_startup_wait = self.config_data.get(MSCT.NO_STARTUP_WAIT, False)
    self._config_endpoints = self.config_data.get(MSCT.CONFIG_ENDPOINTS, {})

    if self._start_server_names is None:
      self._start_server_names = list(self._config_endpoints.keys())

    if not self._server_execution_path.startswith('/'):
      self._server_execution_path = '/' + self._server_execution_path

    self.app = flask.Flask('FlaskGateway')

    self._start_basic_endpoints()

    self.start_servers(start_support=False)
    if self._paths is None:
      self.kill_servers()
      raise ValueError("Gateway cannot start because no paths were retrieved from endpoints.")

    self.app.json_encoder = NPJson
    for rule in self._paths:
      partial_view_func = partial(self._view_func_worker, rule)
      partial_view_func.__name__ = "partial_view_func_{}".format(rule.lstrip('/'))
      self.P("Registering {} on `{}`".format(rule, partial_view_func.__name__), color='g')
      self.app.add_url_rule(
        rule=rule,
        view_func=partial_view_func,
        methods=['GET', 'POST', 'OPTIONS']
      )
    #endfor
    

    self.P("Starting gateway server after all endpoints have been defined...", color='g')
    self._get_system_status(display=True)
    
    self.P("Starting support processes...", color='g')
    self.start_servers(start_support=True)    
    
    self.update_gw_state_history(state=StateCT.STARTUP)
    self.register_handlers()
    
    self.app.run(
      host=self._host,
      port=self._port,
      threaded=True
    )    
    return
    
  def _start_basic_endpoints(self):
    MANDATORY_RULES = [
      dict(
        rule=MSCT.RULE_START,
        endpoint='StartServerEndpoint',
        view_func=self._view_func_start_server,
        methods=['GET', 'POST']        
      ),
      dict(
        rule=MSCT.RULE_KILL,
        endpoint='KillServerEndpoint',
        view_func=self._view_func_kill_server,
        methods=['GET', 'POST']        
      ),
      dict(
        rule=MSCT.RULE_LIST,
        endpoint='ListServersEndpoint',
        view_func=self._view_list_servers,
        methods=['GET', 'POST']        
      ),
      dict(
        rule=MSCT.RULE_SYS,
        endpoint='SystemHealthStatus',
        view_func=self._view_system_status,
        methods=['GET', 'POST']        
      ),
      dict(
        rule=MSCT.RULE_SUPPORT,
        endpoint='SupportStatusEndpoint',
        view_func=self._view_support_status,
        methods=['GET', 'POST']        
      )
    ]

    ### THIS SHOULD BE USED WITH CARE IN PROD
    if True:
      MANDATORY_RULES.append(
        dict(
        rule=MSCT.RULE_SHUTDOWN,
        endpoint='ShutdownGateway',
        view_func=self._view_shutdown,
        methods=['GET', 'POST']
        )        
      )

    for dct_rule in MANDATORY_RULES:      
      rule = dct_rule['rule']
      partial_view_func = dct_rule['view_func']
      methods = dct_rule['methods']
      endpoint = dct_rule['endpoint']
      self.P("Registering {} on `{}`".format(rule, partial_view_func.__name__), color='g')
      self.app.add_url_rule(
        rule=rule,
        endpoint=endpoint,
        view_func=partial_view_func,
        methods=methods,
      )    
    return
  
  
  def _get_system_status(self, display=True):
    mem_total = round(self.log.get_machine_memory(gb=True),2)
    mem_avail = round(self.log.get_avail_memory(gb=True),2)
    mem_gateway = round(self.log.get_current_process_memory(mb=False),2)
    disk_total = round(self.log.get_total_disk(),2)
    disk_avail = round(self.log.get_avail_disk(),2)
    
    mem_servers = 0
    dct_servers = {
    }
    for svr in self._servers:
      proc = psutil.Process(self._servers[svr][MSCT.PROCESS].pid)
      proc_mem = round(proc.memory_info().rss / (1024**3), 2)
      mem_servers += proc_mem
      dct_servers[svr] = proc_mem
    #endfor calc mem
    mem_used = round(mem_gateway + mem_servers, 2)
    mem_sys = round((mem_total - mem_avail) - mem_used,2)
    server_name = self.config_data.get(MSCT.SERVER_NAME, 'base_ai_app')
    self.P("Information for server '{}':".format(server_name))
    self.P("  Total server memory:    {:>5.1f} GB".format(mem_total), color='g')
    self.P("  Total server avail mem: {:>5.1f} GB".format(mem_avail), color='g')
    self.P("  Total allocated mem:    {:>5.1f} GB".format(mem_used), color='g')
    self.P("  System allocated mem:   {:>5.1f} GB".format(mem_sys), color='g')
    self.P("  Disk free:   {:>5.1f} GB".format(disk_avail), color='g')
    self.P("  Disk total:  {:>5.1f} GB".format(disk_total), color='g')
    
    mem_alert = (mem_avail / mem_total) < MSCT.MEM_ALERT_THR
    disk_alert = (disk_avail / disk_total) < MSCT.DISK_ALERT_THR
    
    alerts = []
    if mem_alert:
      alerts.append("Memory below {} threshold.".format(MSCT.MEM_ALERT_THR))
    if disk_alert:
      alerts.append("Disk below {} threshold.".format(MSCT.DISK_ALERT_THR))
    dct_system_alert = dict(
      mem_alert=mem_alert,
      disk_alert=disk_alert,
      alerts=alerts,
    )
    
    dct_stats = dict(
      server_name=server_name,
      mem_total=mem_total,
      mem_avail=mem_avail,
      mem_gateway=mem_gateway,
      mem_used=mem_used,
      mem_sys=mem_sys,
      mem_servers=dct_servers,
      disk_avail=disk_avail,
      disk_total=disk_total,    
      system=platform.platform(),
      py=sys.version,
      monitored_packages=get_packages(monitored_packages=MONITORED_PACKAGES),
      info='Memory Size is in GB. Total and avail mem may be reported inconsistently in containers.'
    )
    return dct_stats, dct_system_alert


  def _start_server(self, server_name, port, execution_path, host=None, nr_workers=None, verbosity=1):
    config_endpoint = self._config_endpoints.get(server_name, {})
    
    is_support_process = False
    
    desc = config_endpoint.get(MSCT.DESCRIPTION)
    self.P('Attempting to start server with "SIGNATURE" : "{}"'.format(server_name))
    self.P('  Description: "{}"'.format(desc))
    
    if config_endpoint.get(MSCT.DISABLED):
      self.P("WARNING: Skipping server '{}' due to its {} status:\n {}".format(
        server_name, 
        MSCT.DISABLED, 
        json.dumps(config_endpoint, indent=4)), color='y'
      )
      return False
    
    if MSCT.SERVER_CLASS in config_endpoint:
      server_class = config_endpoint[MSCT.SERVER_CLASS]
      self.P("Found {} '{}' in endpoint '{}' definition - using this class as worker".format(
        MSCT.SERVER_CLASS, server_class, server_name,
      ))
    else:
      server_class = server_name

    if MSCT.HOST in config_endpoint:
      host = config_endpoint[MSCT.HOST]
    else:
      host = host or DEFAULT_HOST
      self.P("WARNING: '{}' not provided in endpoint configuration for {}.".format(MSCT.HOST, server_name), color='r')
    #endif
    

    if host == MSCT.SUPPORT_PROCESS_NO_HOST:
      fn = os.path.join(self._workers_location, server_name + '.py')
      if os.path.isfile(fn):
        msg  = "Creating SUPPORT process {}".format(fn)
        pad = 4
        pad = int(pad / 2) * 2
        self.P("*" * (len(msg) + pad), color='g')
        self.P(" " * int(pad/2) + msg + " " * int(pad/2), color='g')
        self.P("*" * (len(msg) + pad), color='g')
        self._create_notification(notif='log', msg=msg)
        config_data = {
          **config_endpoint,
          "SERVER" : "127.0.0.1",
          "SERVER_PORT" : self._port,
          "SERVER_PATH" : MSCT.RULE_SUPPORT, 
          "SUPPORT_NAME" : server_name,
        }
        popen_args = [
          'python',
          fn,
          '--config_endpoint', json.dumps(config_data),
          '--host_id', self.__host_id,
        ]     
        port = None
        is_support_process = True
      else:
        msg = "Could not find support process {}".format(fn)
        self.P(msg, color='r')
        self._create_notification(notif='log', msg=msg)
        return False
    else:     
      if MSCT.NR_WORKERS in config_endpoint:
        nr_workers = config_endpoint[MSCT.NR_WORKERS]
      else:
        nr_workers = nr_workers or DEFAULT_NR_WORKERS
        self.P("WARNING: MSCT.NR_WORKERS not provided in endpoint configuration for {}.".format(server_name), color='r')
      #endif
      
      
      msg = "Creating server `{} <{}>` at {}:{}{}".format(server_name, server_class, host, port, execution_path)
      self.P(msg, color='g')
      self._create_notification('log', msg)
      str_cmd = os.path.relpath(run_server_module.__file__)
      self.P("Running '{}'".format(str_cmd))
      popen_args = [
        'python',
        str_cmd,
        '--base_folder', self.log.root_folder,
        '--app_folder', self.log.app_folder,
        '--config_endpoint', json.dumps(config_endpoint),
        '--host', host,
        '--port', str(port),
        '--execution_path', execution_path,
        '--workers_location', self._workers_location,
        '--worker_name', server_class,
        '--worker_suffix', self._workers_suffix,
        '--microservice_name', server_name,
        '--nr_workers', str(nr_workers),
        '--host_id', self.__host_id,
        '--use_tf',
      ]
    #endif suport process or normal server
      
    process = subprocess.Popen(
      popen_args,
    )

    self.P(f"Waiting for process to {process.pid} warmup...")
    sleep(2)
    is_alive = process.poll() is None
    if not is_alive:
      msg = "**************** Process failed for {}:{}:{} *******************".format(process.args, host, port)
      self.P(msg, color='r')
      self._create_notification(notif='log', msg=msg)
      return False
    #endif
    
    self._servers[server_name] = {
      MSCT.PROCESS   : process,
      MSCT.HOST      : host,
      MSCT.PORT      : port,
      MSCT.START     : time(),
      MSCT.SUPPORT   : is_support_process, 
    }    
    
    result = None
    if host == MSCT.SUPPORT_PROCESS_NO_HOST:
      msg = "Successfully created SUPPORT process '{}' with PID={}".format(server_name, process.pid)
      result = False # no need to increment port nr
    else:
      msg = "Successfully created server '{}' with PID={}".format(server_name, process.pid)
      result = True
    self.P(msg, color='g')
    self._create_notification('log', msg)
    return result
  
  
  def _get_server_status(self, server_name):
    online = False
    urls = []
    _error = None
    paths = None
    if self._servers[server_name][MSCT.HOST] == MSCT.SUPPORT_PROCESS_NO_HOST:
      process = self._servers[server_name][MSCT.PROCESS]
      is_alive = process.poll() is None
      if is_alive:
        online = True
      paths = [process.args]
    else:
      try:
        url = 'http://{}:{}{}'.format(
          self._servers[server_name][MSCT.HOST],
          self._servers[server_name][MSCT.PORT],
          MSCT.RULE_PATHS
        )
        response = requests.get(url=url)
        paths = response.json()[MSCT.PATHS]
        urls = [url]
        for path in paths:
          url = 'http://{}:{}{}'.format(
            self._servers[server_name][MSCT.HOST],
            self._servers[server_name][MSCT.PORT],
            path
          )
          urls.append(url)
        online = True
      except Exception as exc:
        _error = str(exc)
    #endif support or normal server
  
    result = {
      MSCT.ONLINE  : online,
      MSCT.ERROR   : _error,
      MSCT.URLS    : urls,
      MSCT.PATHS   : paths,
      MSCT.PORT    : self._servers[server_name][MSCT.PORT],
      MSCT.UPTIME  : self._elapsed_to_str(time() - self._servers[server_name][MSCT.START])
    }
    return result

  def _get_paths_from_server(self, server_name):
    self.P("Requesting `get_paths` from server '{}' in order to map available paths...".format(server_name))
    
    resp = self._get_server_status(server_name)
    if not resp[MSCT.ONLINE]:
      raise ValueError('Server not yet online: {}'.format(resp[MSCT.ERROR]))
    else:
      self._paths = resp[MSCT.PATHS]
      self.P("  Responded with paths={}".format(self._paths), color='g')
    return


  def start_servers(self, start_support=False):
    for i,server_name in enumerate(self._start_server_names):
      config_endpoint = self._config_endpoints.get(server_name, {})
      is_support = config_endpoint.get(MSCT.HOST, None) == MSCT.SUPPORT_PROCESS_NO_HOST
      if is_support:
        if not start_support:
          continue
        else:
          self.P("  Starting support server '{}' ...".format(server_name), color='g')
      else:
        if start_support:
          continue
        else:
          self.P("  Starting microservice server '{}' ...".format(server_name), color='g')
      
      success = self._start_server(
        server_name=server_name,
        port=self._current_server_port,
        execution_path=self._server_execution_path,
        verbosity=1
      )
      if success:
        self._current_server_port += 1
    #endfor

    if self._no_startup_wait:
      self.P("Fast startup enabled, using default paths: {}".format(DEFAULT_SERVER_PATHS), color='g')
      self._paths = DEFAULT_SERVER_PATHS 
    else:
      nr_tries = 0    
      svr = self.config_data.get(MSCT.DEFAULT_SERVER,  self._start_server_names[0])
      self.P("")
      WAIT_ON_ERROR = 10
      while True:
        try:
          nr_tries += 1
          self._get_paths_from_server(svr)
          self.P("  Done getting paths.", color='g')
          break
        except Exception as exc:
          self.P("  Error: {}".format(exc), color='r')
          if nr_tries >= (120 / WAIT_ON_ERROR):
            raise ValueError("Could not get paths from server '{}'".format(svr))
          sleep(WAIT_ON_ERROR)
        #end try-except
      #endwhile
    #endif no startup wait or wait for paths

    return


  def _get_server_process(self, server_name):
    return self._servers[server_name][MSCT.PROCESS]

  def _server_exists(self, server_name):
    return server_name in self._servers

  @property
  def active_servers(self):
    return list(self._servers.keys())

  def _kill_server_by_name(self, server_name):
    TIMEOUT = 5
    process = self._get_server_process(server_name)
    process.terminate()
    process.wait(TIMEOUT)
    if process.returncode is None:
      self.P("Terminating '{}:{}' with kill signal after {}s".format(
        server_name, process.pid, TIMEOUT))
      process.kill()
      sleep(1)
    self.P("  '{}' terminated with code: {}".format(server_name, process.returncode))
    self._servers.pop(server_name)
    return

  def kill_servers(self):
    names = list(self._servers.keys())
    for server_name in names:
      self.P("Terminating server '{}' ...".format(server_name))
      self._kill_server_by_name(server_name)
      sleep(2)
      self.P("  Server '{}' deallocated.".format(server_name))
    return

  def register_handlers(self):
    # Register signal handlers
    self.P("Registering signal handler {} ...".format(signal.SIGINT))
    signal.signal(signal.SIGINT, self.__signal_handler)  # Intercept CTRL-C
    self.P("Registering signal handler {} ...".format(signal.SIGTERM))
    signal.signal(signal.SIGTERM, self.__signal_handler) # Intercept SIGTERM    
    self.P("Done registering signal handlers.", color='g')
    return
    
  
  def __signal_handler(self, sig, frame):
    """
    Handle the incoming signal and perform cleanup.

    Parameters:
    
      sig (int): The signal number.
      
      frame (frame): The current stack frame.
    """
    self.P('Signal received: {}. Performing safe shutdown...'.format(sig), color='r')
    # Perform your cleanup here
    # For example, close database connections, save necessary data, etc.
    self.gw_shutdown()
    
    
  def gw_shutdown(self):
    self.P("Running gateway v{}/{} shutdown...".format(APP_VER, LIB_VER), color='r')
    self.kill_servers()
    _pid = os.getpid()
    _signal = signal.SIGKILL
    
    self.update_gw_state_history(state=StateCT.SHUTDOWN)
    
    self.P("Terminating gateway server v{}/{} with pid {} with signal {}...".format(
      APP_VER, LIB_VER, _pid, _signal))
    os.kill(_pid, _signal)
    self.P("Running _exit() ...")
    os._exit(1)    