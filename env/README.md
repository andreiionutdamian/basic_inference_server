From repo base folder (not from `./env`) run:

```
docker build -t aidamian/base_env:x64 -f env/Dockerfile.env .
docker push aidamian/base_env:x64
```