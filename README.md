# Basic full inference server based on microservice-gateway architecture

## General information

This section of documentation presents CI/CD aspects as well as basic API definitions. Extended API information can be found in below API section.

> **Note**
> Within this documentation you will see different `ver`, `worker_ver` and `time` in various example responses. This is due to the fact that the documentation has been completed gradually.

### Overall CI/CD aspects

All microservices are hosted under the same distributed gateway enabling multi-worker processing. Each microservice is defined by at least one property - i.e.`"SIGNATURE"`.
Failure to identify the microservice will yield an error. Main repo `push` operation will trigger autobuild of DockerHub repo.
Following automatic build a simple `http://<server>:5002/shutdown` command is required to restart and update the Docker container on the server.


On server a simple script is running the container with 
```
nohup ./run.sh &
```

The `run.sh` contains the following script:
```
#!/bin/bash

while true; do
  sudo docker run --pull=always -p 5002-5010:5002-5010 -v sw_vol:/safeweb_ai/output safeweb/ai
  sleep 5
done
```

As a result the data will be persistent from one session to another in the `sw_vol` usually found in `/var/lib/docker/volumes/sw_vol/_data`

A simple Azure or AWS Ubuntu 18+ VM is recommanded. See below the installation instructions.

### Development

#### Docker build

```
docker build -t org/repo .
```

...or a dev local build

```
docker build -t localsw .
```

> **Note**
> Place make sure env is prepared. Currently the env contains a couple neural word embeddings bundled within the env layer.

#### Docker run

```
docker run --pull=always -p 5002-5010:5002-5010 -v ai_vol:/aid_app/_cache org/repo
```

or run locally

```
docker run -p 5002-5010:5002-5010 localsw
```

> **Note**
> Always include volume `-v` and port forwarding `-p`.

### Usage

The engine itself works as a microservice gateway with multiple servers running their parallel workers. The list of active servers can be queried by running a `POST` on `<address>:5002/list_servers` resulting in a response similar with this 
```
{
    "AVAIL_SERVERS": [
        "dummy_model_a",
        "test_01"
    ]
}
```

#### Restart/update all servers within automated container

Run `POST` on `<address>:5002/shutdown` with the following JSON:

```
{
    "SIGNATURE" : "SAFE_KILL_SERVER_CMD"
}
```


#### Querying a microservice

Run a `POST` on `<address>:5002/run` with the following JSON:

```
{
    "SIGNATURE" : "test_01",
    ...
}
```

While `SIGNATURE` is mandatory for any microservice the other fields are dependent of the particular endpoint.

In this case as well as in other quiz-like responses we will obtain something like:
```
{
    "call_id": 1,
    "quizzes" : [
        {
            "answer": "spațiul_încercărilor",
            "max_given_time": 7,
            "options": [
                "spațiul_încercărilor",
                "distribuție",
                "variabilă"
            ],
            "question": "Mulțimea tuturor rezultatelor posibile într-un experiment de probabilitate se numește _______."
        }
    ],
    "signature": "BasicQuizWorker:1",
    "ver": "0.2.2",
    "worker_ver": "1.0.8"
}
```

For more information please see API section below.

#### Azure VM install

To install Docker on an Azure VM with Ubuntu, follow these steps:

1. Update the packages list:
```
sudo apt-get update
```
2. Install prerequisite packages:
```
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
```

3. Add Docker's official GPG key:
```
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```

4. Set up the Docker repository:
```
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

5. Update the packages list again:
```
sudo apt-get update
```

6. Install Docker:
```
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

7. Verify the installation by checking the Docker version:
```
docker --version
```

8. Start the Docker service and enable it to start on boot:
```
sudo systemctl enable docker
sudo systemctl start docker
```

9. Create inbound rule with `*` as source and `5002-5010` as destination


## SafeWeb AI API information

In this section specific information about various microservices is provided.


### API definition for utility features

Most of the endpoints have the following utility features

#### Get system health status

Getting system status requires a simple API call `POST <address>:5002/run`:

```
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

