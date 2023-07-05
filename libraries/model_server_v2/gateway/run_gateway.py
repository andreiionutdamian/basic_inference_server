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

import argparse

from libraries import Logger
from libraries.model_server_v2.gateway import FlaskGateway

### Example for running a gateway
if __name__ == '__main__':
  parser = argparse.ArgumentParser()

  parser.add_argument(
    '-b', '--base_folder',
    type=str, default='libraries',
    help='Logger base folder'
  )

  parser.add_argument(
    '-a', '--app_folder',
    type=str, default='_logger_cache',
    help='Logger app folder'
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

  try:
    ### Attention! config_file should contain the configuration for each endpoint; 'NR_WORKERS' and upstream configuration
    log = Logger(
      lib_name='GTW',
      config_file='libraries/model_server_v2/gateway/config_gateway.txt',
      base_folder=base_folder, app_folder=app_folder,
      TF_KERAS=False
    )

    gtw = FlaskGateway(
      log=log,
      server_names=['fake'],
      workers_location='libraries.model_server_v2.example_endpoints',
      workers_suffix='Worker',
      host=host,
      port=port,
      first_server_port=port+1,
      server_execution_path='/analyze'
    )
  except Exception as exc:
    print("FAILED to load config_gateway.txt: {}".format(exc))
