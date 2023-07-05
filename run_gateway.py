# -*- coding: utf-8 -*-
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
import os
import platform


import argparse

from libraries import Logger
from libraries.model_server_v2.gateway import FlaskGateway, get_packages

from time import sleep



from ver import __VER__


def runs_with_debugger():
  gettrace = getattr(sys, 'gettrace', None)
  if gettrace is None:
    return False
  else:
    return not gettrace() is None
  

  
if __name__ == '__main__':  
  parser = argparse.ArgumentParser()

  parser.add_argument(
    '-b', '--base_folder',
    type=str, default='.',
    help='Local cache base folder'
  )

  parser.add_argument(
    '-a', '--app_folder',
    type=str, default='_cache',
    help='Local cache app folder'
  )

  parser.add_argument(
    '--host', type=str, default='0.0.0.0'
  )

  parser.add_argument(
    '--port', type=int, default=5002
  )

  args = parser.parse_args()
  base_folder = args.base_folder
  app_folder = args.app_folder
  host = args.host
  port = args.port

  ### Attention! config_file should contain the configuration for each endpoint; 'NR_WORKERS' and upstream configuration
  log = Logger(
    lib_name='AIAPP',
    config_file='config_gateway.txt',
    base_folder=base_folder, app_folder=app_folder,
    TF_KERAS=False
  )

  in_debug = runs_with_debugger()
  running_in_docker = os.environ.get('AID_APP_DOCKER', False) == "Yes"
  ee_id = os.environ.get('AID_APP_ID', 'aid_app_bare_metal')
  show_packs = os.environ.get('SHOW_PACKS')
  tz = os.environ.get('TZ', None)
  path = os.getcwd()
  log.P("Running in DEBUG mode" if in_debug else "Running in normal mode (NO debug enabled)")
  packs = get_packages()
  log.P("Running {} test v{} '{}', TZ: {}, py: {}, OS: {}, Docker: {}".format(
    ee_id,
    __VER__,
    path, 
    tz,
    sys.version.split(' ')[0], 
    platform.platform(), 
    running_in_docker
    ), color='g'
  )  
  log.P("Show packages: {}".format(show_packs))
  if show_packs in ['Yes', 'YES', 'yes']:
    log.P("Packages: \n{}".format("\n".join(packs)))
    
  sleep(3)

  gtw = FlaskGateway(
    log=log,
    # server_names=['get_tags', 'get_qa', 'get_sim', 'get_aprox', 'get_conf'],
    workers_location='endpoints',
    workers_suffix='Worker',
    host=host,
    port=port,
    #first_server_port=5020,
    server_execution_path='/run'
  )
  