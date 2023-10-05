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

import traceback
from ..public_logger import Logger
import os

class MSCT:
  NO_STARTUP_WAIT = 'NO_STARTUP_WAIT'
  CONFIG_ENDPOINTS = 'CONFIG_ENDPOINTS'
  
  SERVER_NAME = 'SERVER_NAME'
  
  SIGNATURE = 'SIGNATURE'
  
  PROCESS = 'PROCESS'
  DISABLED = 'DISABLED'
  DATA = 'data'
  VER = 'ver'
  GW_UPTIME = 'gw-uptime'
  TIME = 'time'
  SERVER_CLASS = 'SERVER_CLASS'
  HOST = 'HOST'
  DESCRIPTION = 'DESCRIPTION'
  NR_WORKERS = 'NR_WORKERS'
  SUPPORT_PROCESS_NO_HOST = "NO_HOST"
  PATHS = 'PATHS'
  ONLINE = 'ONLINE'
  PORT = 'PORT'
  ERROR = 'ERROR'
  URLS = 'URLS'
  UPTIME = 'UPTIME'
  START = 'START'
  SUPPORT = 'SUPPORT'
  
  SYSTEM_STATUS = 'SYSTEM_STATUS'
  SYSTEM_ALERTS = 'SYSTEM_ALERTS'
  
  DEFAULT_SERVER = 'DEFAULT_SERVER'
  AVAIL_SERVERS = 'AVAIL_SERVERS'
  
  NOTIF_NOTIFICATION_TYPE = 'NOTIFICATION_TYPE'
  NOTIF_MODULE = 'MODULE'
  NOTIF_TIME = 'TIMESTAMP'
  
  DOWNLOAD_FILE_COMMAND = 'DOWNLOAD'  
  DOWNLOAD_FILE_PATH = 'DOWNLOAD_FILE_PATH'
  
  RULE_LIST = '/list_servers'
  RULE_SHUTDOWN = '/shutdown'
  RULE_DEFAULT = '/analyze'
  RULE_START = '/start_server'
  RULE_KILL = '/kill_server'
  RULE_SYS = '/system_status'
  RULE_SUPPORT = '/support_update_status'
  
  RULE_NOTIF = '/notifications'
  RULE_RUN = '/run'
  RULE_UPDATE_WORKERS = '/update_workers'
  RULE_PATHS = '/get_paths'
  
  KILL_CMD = 'SAFE_KILL_SERVER_CMD' 
  
  MEM_ALERT_THR = 0.15
  DISK_ALERT_THR = 0.10

def get_api_request_body(request, log : Logger, sender=None):
  params = {}
  try:
    method = request.method
    args_data = request.args
    form_data = request.form
    json_data = request.json

    if method == 'GET':
      # parameters in URL
      base_params = args_data
    else:
      # parameters in form
      base_params = form_data
      if len(base_params) == 0:
        # params in json?
        base_params = json_data
    #endif

    if base_params is not None:
      params = dict(base_params)
    else:
      params = {}
    #endif
  except Exception as e:
    s = 'sender={}\n\ntraceback={}\n\nrequest.data={}'.format(sender, traceback.format_exc(), str(request.data))
    fn = 'error_{}'.format(log.now_str())
    log.P("Error:\n{}".format(s), color='r')

  return params
