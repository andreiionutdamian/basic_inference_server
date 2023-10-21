# Basic Inference Server: Streamlined Model Deployment



## General information

This section of documentation presents CI/CD aspects as well as basic API definitions. Extended API information can be found in below API section.

> **Note**
> Within this documentation you will see different `ver`, `worker_ver` and `time` in various example responses. This is due to the fact that the documentation has been completed gradually.

### Overall CI/CD aspects

All microservices are hosted under the same distributed gateway enabling multi-worker processing. Each microservice is defined by at least one property - i.e.`"SIGNATURE"`.
Failure to identify the microservice will yield an error. Main repo `push` operation will trigger autobuild of DockerHub repo.
Following automatic build a simple `http://<server>:5002/shutdown` command is required to restart and update the Docker container on the server.


On server a simple script is running the container with 
```bash
nohup ./run.sh &
```

The `run.sh` contains the following script:
```bash
#!/bin/bash

while true; do
  sudo docker run --pull=always -p 5002-5010:5002-5010 -v ai_vol:/aid_app/_cache <account>/<repo>
  sleep 5
done
```

As a result the data will be persistent from one session to another in the `sw_vol` usually found in `/var/lib/docker/volumes/sw_vol/_data`

A simple Azure or AWS Ubuntu 18+ VM is recommanded. See below the installation instructions.

### Development

#### Docker build

```bash
docker build -t <account>/<repo> .
```

...or a dev local build

```bash
docker build -t local_app .
```

> **Note**
> Place make sure env is prepared. Currently the env contains a couple neural word embeddings bundled within the env layer.

#### Docker run

```bash
docker run --pull=always -p 5002-5010:5002-5010 -v ai_vol:/aid_app/_cache <account>/<repo>
```

or run locally

```bash
docker run -p 5002-5010:5002-5010 local_app
```

> **Note**
> Always include volume `-v` and port forwarding `-p`.

### Usage

The engine itself works as a microservice gateway with multiple servers running their parallel workers. The list of active servers can be queried by running a `POST` on `<address>:5002/list_servers` resulting in a response similar with this 
```json
{
    "AVAIL_SERVERS": [
        "dummy_model_a",
        "test_01"
    ]
}
```

#### Restart/update all servers within automated container

Run `POST` on `<address>:5002/shutdown` with the following JSON:

```json
{
    "SIGNATURE" : "SAFE_KILL_SERVER_CMD"
}
```


#### Querying a microservice

Run a `POST` on `<address>:5002/run` with the following JSON:

```json
{
    "SIGNATURE" : "test_01",
    ...
}
```

While `SIGNATURE` is mandatory for any microservice the other fields are dependent of the particular endpoint.


For more information please see API section below.

#### Azure VM install

To install Docker on an Azure VM with Ubuntu, follow these steps:

1. Update the packages list:
```bash
sudo apt-get update
```
2. Install prerequisite packages:
```bash
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
```

3. Add Docker's official GPG key:
```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```

4. Set up the Docker repository:
```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

5. Update the packages list again:
```bash
sudo apt-get update
```

6. Install Docker:
```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

7. Verify the installation by checking the Docker version:
```bash
docker --version
```

8. Start the Docker service and enable it to start on boot:
```bash
sudo systemctl enable docker
sudo systemctl start docker
```

9. Create inbound rule with `*` as source and `5002-5010` as destination then make sure you `sudo docker login` on the VM


## AI API information

In this section specific information about various microservices is provided.


### API definition for utility features

Most of the endpoints have the following utility features

#### Get system health status

Getting system status requires a simple API call `POST <address>:5002/run`:

```json
{
    "SYSTEM_STATUS": {
        "info": "Memory Size is in GB. Total and avail mem may be reported inconsistently in containers.",
        "mem_avail": 22.88,
        "mem_gateway": 0.13,
        "mem_servers": {
            "basic_quiz_model": 0.56,
            "dummy_model_a": 0.14
        },
        "mem_sys": 1.14,
        "mem_total": 24.85,
        "mem_used": 0.83
    },
    "time": "2023-05-02 07:46:45",
    "ver": "2.3.2"
}
```

## Programmatic API information

Here is a quick start of the API. We assume we have a couple of dummy servers defined in the config_gateway.txt file:

```json
{
    "DEFAULT_SERVER" : "dummy_model_demo1",
    "NO_STARTUP_WAIT" : true,
    "SERVER_NAME" : "base_server",
    
    "CONFIG_ENDPOINTS": {                
        "dummy_model_demo1": {
            "NR_WORKERS"    : 2,
            "HOST"          : "127.0.0.1",
            "DESCRIPTION"   : "Test_01 server #1"
        },

        "dummy_model_demo1-bis": {
            "SERVER_CLASS"  : "dummy_model_demo1",
            "NR_WORKERS"    : 2,
            "HOST"          : "127.0.0.1",
            "DISABLED"      : true,
            "DESCRIPTION"   : "dummy_model_a server #2. Redundancy server for dummy_model_a"
        },
        
        
        "dummy_model_demo2": {
            "NR_WORKERS"    : 2,
            "HOST"          : "127.0.0.1",
            "DESCRIPTION"   : "dummy_model_demo2 server #1"
        },
        
        "support_process"  : {
            "HOST"          : "NO_HOST",
            "PING_INTERVAL" : 10,
            "DESCRIPTION"   : "Basic support process."
        }
    }
}
```

The above configuration will result in the following servers: `dummy_model_demo1`, `dummy_model_demo2` and `support_process`. The `dummy_model_demo1-bis` is disabled and will not be started. The `support_process` is a special server that will be started automatically and will be used to monitor the other servers. 

Furthermore lets define in the `endpoints` folder the following files:

```python
#file: endpoints/dummy_model_demo1.py

from basic_inference_server import FlaskWorker

_CONFIG = {
  'WEIGHT'     : 0,
  'BIAS'       : 0,
  'PLACEHOLDER_MODEL' : True,
}

__WORKER_VER__ = '1.2.1'

class PlaceholderModel():
  def __init__(self, log):
    self.log = log
    self.log.P("******** Using a model placeholder *********", color='r')
    return 
  
  def get_similar(self, **kwargs):
    return "same-word-always"

class DummyModelDemo1Worker(FlaskWorker):

  def __init__(self, **kwargs):
    super(DummyModelDemo1Worker, self).__init__(prefix_log='[DUMA]', **kwargs)
    return


  def _load_model(self):
    self.nlp_model = PlaceholderModel(log=self.log)
    return

  def _pre_process(self, inputs):
    s = inputs['INPUT_VALUE']
    lang = inputs.get('LANGUAGE', inputs.get('language', 'en'))
    return s, lang

  def _predict(self, prep_inputs):
    word, lang = prep_inputs
    res = self.nlp_model.get_similar(word=word, lang=lang)
    return res, prep_inputs

  def _post_process(self, pred):
    result = {
      'dummy_model_a_predict' : pred[0], 
    }
    return result

```

then the `dummy_model_demo2.py` file:

```python

from basic_inference_server import FlaskWorker

_CONFIG = {
  'WEIGHT'    : 0,
  'BIAS'      : 0,
}

class DummyModelDemo2Worker(FlaskWorker):
  def __init__(self, **kwargs):
    super(DummyModelDemo2Worker, self).__init__(prefix_log='[DUMB]', **kwargs)
    return


  def _load_model(self):
    return

  def _pre_process(self, inputs):
    s = inputs['INPUT_VALUE']
    return s

  def _predict(self, prep_inputs):
    val = int(prep_inputs)
    res = '{}*{} + {} = {} PREDICTED'.format(prep_inputs, self.cfg_weight, self.cfg_bias, val * self.cfg_weight + self.cfg_bias)
    return res

  def _post_process(self, pred):
    return {'dummy_model_predict' : pred}

```

... and finally the `support_process.py` file:

```python


__VERSION__ = '0.2.1'

class ServerMonitor:
  def __init__(self, name, log, interval=None, debug=False):
    ...
    return
  
  def _collect_system_metrics(self):
    ...
    return metrics

  def _send_data(self, data):
    ...
    return
    
  def execute(self):    
    ...
    return

if __name__ == '__main__':
  ...

  engine = ServerMonitor(name=name, log=log) 
  engine.run()

```

Now lets put everything together in a `run_gateway.py` file:

```python

# file: ./run_gateway.py

if __name__ == '__main__':  
  ...

  gtw = FlaskGateway(
    log=log,
    workers_location='endpoints',
    workers_suffix='Worker',
    host=host,
    port=port,
    server_execution_path='/run'
  )
  
```

## Author

- Name: Andrei Ionut Damian
- Email: andrei.damian@me.com
- ORCID: [Andrei Ionut Damian](https://orcid.org/0000-0002-5294-6223)

## Citations

If you use this project in your research, please cite the following papers:

```bibtex
@article{ciobanu2021solis,
  title={SOLIS--The MLOps journey from data acquisition to actionable insights},
  author={Ciobanu, Razvan and Purdila, Alexandru and Piciu, Laurentiu and Damian, Andrei},
  journal={arXiv preprint arXiv:2112.11925},
  year={2021}
}

@article{milik2023aixpand,
  title={AiXpand AI OS--Decentralized ubiquitous computing MLOps execution engine},
  author={Milik, Beatrice and Saraev, Stefan and Bleotiu, Cristian and Lupaescu, Radu and Hobeanu, Bogdan and Damian, Andrei Ionut},
  journal={arXiv preprint arXiv:2306.08708},
  year={2023}
}
```