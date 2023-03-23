To install and run in docker

```bash
$ docker build -t zerotrigger .
$ docker run -p 10001:10001 -p 10002:10002 -it --rm --name zerotrigger_service zerotrigger
```
