FROM aidamian/base_env:x64


WORKDIR /aid_app

COPY  . /aid_app

ENV TZ Europe/Bucharest

ENV AID_APP_DOCKER Yes
ENV SHOW_PACKS Yes
ENV FORCE_CPU No
ENV AID_APP_ID BaseAidApp

ENV PYTHONPATH .

EXPOSE 5001-5015/tcp

CMD ["python", "run_gateway.py"]
