From repo base folder (not from `./env`) run:

```
docker build -t aidamian/base_llm_env -f env/Dockerfile.env .
docker push aidamian/base_llm_env
```