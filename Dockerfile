FROM aidamian/base_env:x64

WORKDIR /aid_app

COPY  . /aid_app

ENV TZ Europe/Bucharest

ENV AID_APP_DOCKER Yes
ENV SHOW_PACKS Yes
ENV FORCE_CPU No
ENV AID_APP_ID BaseAidApp

# this variable should contain the path to the `basic_inference_server`
# repository directory, since the code contains a lot of magic tricks that
# rely on searching in the repository's directories 

# this variable is used as cwd when launching the server inside the container
ENV DEFAULT_PYTHON_PATH "."

EXPOSE 5001-5015/tcp

CMD python run_gateway.py --default_python_path $DEFAULT_PYTHON_PATH
