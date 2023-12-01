import sys
import os
import platform
import uuid
import argparse

from time import sleep

from basic_inference_server import Logger
from basic_inference_server import FlaskGateway, get_packages

from app_ver import __VER__ as APP_VER
from basic_inference_server import LIB_VER


def runs_with_debugger():
  gettrace = getattr(sys, 'gettrace', None)
  if gettrace is None:
    return False
  else:
    return not gettrace() is None
  
def main():
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

  host_id = uuid.uuid4().hex[:6]
  ### Attention! config_file should contain the configuration for each endpoint; 'NR_WORKERS' and upstream configuration
  log = Logger(
    lib_name='APPv' + APP_VER,
    host_id=host_id,
    config_file='config_gateway.txt',
    base_folder=base_folder, app_folder=app_folder,
    TF_KERAS=False
  )

  in_debug = runs_with_debugger()
  running_in_docker = os.environ.get('AID_APP_DOCKER', False) == "Yes"
  app_id = os.environ.get('AID_APP_ID', 'aid_app_bare_metal')
  show_packs = os.environ.get('AID_APP_SHOW_PACKS')
  tz = os.environ.get('TZ', None)
  path = os.getcwd()
  hostname = os.environ.get('HOSTNAME', "uknown")
  log.P("Running in DEBUG mode" if in_debug else "Running in normal mode (NO debug enabled)")
  packs = get_packages()
  log.P("Running {} v{} on:\n  HostID: `{}` (hostname: {})\n  Path:   '{}'\n  TZ:     {}\n  Py:     {}\n  OS:     {}\n  Docker: {}".format(
    app_id,
    APP_VER,
    host_id, hostname,
    path, 
    tz,
    sys.version.split(' ')[0], 
    platform.platform(), 
    running_in_docker
    ), color='g'
  )
  log.P("Show packages: {}".format(show_packs))
  if isinstance(show_packs, str) and show_packs.lower() in ['yes', 'y', 'true', 't', '1']:
    log.P("Packages: \n{}".format("\n".join(packs)))
    
  sleep(3)

  gtw = FlaskGateway(
    log=log,
    host_id=host_id,
    # server_names=['get_micro_one', 'get_micro_two'],
    workers_location='endpoints',
    workers_suffix='Worker',
    host=host,
    port=port,
    #first_server_port=5020,
    server_execution_path='/run'
  )
  

if __name__ == '__main__':  
  pass