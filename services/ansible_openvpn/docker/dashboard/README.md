Derived from this work
https://github.com/docker/awesome-compose/tree/c2f8036fd353dae457eba7b9b436bf3a1c85d937/flask

To test locally

docker build -t flasktest .
docker run --name flasktest -p 8000:8000 flasktest
