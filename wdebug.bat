docker build -t local_bis .
docker run --rm --name local_bis_c -p 5002-5010:5002-5010 -v ai_vol:/aid_app/_cache local_bis