# -*- coding: utf-8 -*-
"""
Template for a support process that can be used to monitor the server.
"""

import json
import argparse
import requests
import psutil

from time import sleep, time

import basic_inference_server as BIS

__VERSION__ = '0.0.1'

class ServerMonitor:
  def __init__(self, name, log, interval=None, debug=False):
    self.log = log
    self.__debug = debug
    self.__name = name
    if interval is None:
      interval = self.log.config_data.get('PING_INTERVAL', 1)
    self.__interval = interval
    self.__run_cnt = 0
    self.__server = self.log.config_data['SERVER']
    self.__port = self.log.config_data['SERVER_PORT']
    self.__path = self.log.config_data['SERVER_PATH']
    self.P("ServerMonitor v{} initialized on {}s interval".format(__VERSION__, self.__interval), color='g')
    return
  
  def P(self, s, color=None):
    self.log.P(s, color=color)
    return

  def _collect_system_metrics(self, as_gb=True):
    """
    Collect system and application metrics including memory and disk usage.

    Parameters:
      as_gb (bool): Whether to return the metrics in GB.

    Returns:
      dict: Dictionary containing metrics about system and application.
    """
    metrics = {}
    
    # Conversion factor for bytes to GB
    to_gb = 1 if not as_gb else (1024 ** 3)
    
    # Memory Metrics
    memory_info = psutil.virtual_memory()
    metrics['total_memory'] = memory_info.total / to_gb
    metrics['available_memory'] = memory_info.available / to_gb
    metrics['system_used_memory'] = memory_info.used / to_gb
    metrics['app_used_memory'] = psutil.Process().memory_info().rss / to_gb
    
    # Disk Metrics
    disk_info = psutil.disk_usage('/')
    metrics['total_disk'] = disk_info.total / to_gb
    metrics['available_disk'] = disk_info.free / to_gb
    
    return metrics

  
  
  def _send_data(self, data):
    url = None
    try:
      assert isinstance(data, dict)
      url = 'http://{}:{}{}'.format(
        self.__server,
        self.__port,
        self.__path,
      )
      data['SIGNATURE'] = self.__name
      if self.__debug:
        self.P("Sending data to {}".format(url), color='m')
      r = requests.post(url, json=data)
      if self.__debug:
        self.P("Response: {}".format(r.text), color='m')
    except Exception as e:
      self.P("Error while trying to deliver to {}: {}".format(url, e), color='r')
    return
      
      
    
  def execute(self):    
    self.__run_cnt += 1
    metrics = self._collect_system_metrics()
    msg = (
      "{} v{} Total Mem: {:.1f}GB, Avail Mem: {:.1f}GB, "
      "Sys Used Mem: {:.1f}GB, App Used Mem: {:.1f}GB, Total Disk: {:.1f}GB, Avail Disk: {:.1f}GB"
    ).format(
      self.__name, __VERSION__,
      metrics['total_memory'], metrics['available_memory'],
      metrics['system_used_memory'], metrics['app_used_memory'],
      metrics['total_disk'], metrics['available_disk']
    )
  
    data = dict(
      msg=msg,
      **metrics,      
    )
    self._send_data(data)
    return

  def run(self):
    tick = time()
    while True:
      while (time() - tick) < self.__interval:
        sleep(0.1)
      self.execute()
      tick = time()
    return
      
    

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  
  parser.add_argument(
    '--config_endpoint', type=str, default='{}',
    help='JSON configuration of the endpoint'
  )
  
  parser.add_argument(
    '--host_id', type=str,
    help='The host id'
  )
  
  args = parser.parse_args()
  host_id = args.host_id
  str_config_data = args.config_endpoint

  print("Using --config_endpoint: {}".format(str_config_data))
  config_data = json.loads(str_config_data)
  name = config_data.get("SUPPORT_NAME", "SUPPORT")
  
  log = BIS.Logger(
    lib_name="TSPRC",
    host_id=host_id,
    base_folder=".",
    app_folder="_cache",
    TF_KERAS=False, # use_tf
    max_lines=3000
  )  
  
  log.update_config_data(config_data)
  
  
  log.P("Using config_data: \n{}".format(json.dumps(log.config_data, indent=2)))
  
  engine = ServerMonitor(name=name, log=log) 
  engine.run()

