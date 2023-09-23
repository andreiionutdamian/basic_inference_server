docker build -t localsw .
docker run --rm --name basic_serving_debug -p 5002-5010:5002-5010 localsw