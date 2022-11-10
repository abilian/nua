Tests require existing docker images: run pytest on nua_build to generate those images.

Test with nginx and certbot require DNS known domain with subdomaine:
test, test1, test2

  - adapt content of REPLACE_DOMAIN for replacing example.com by your test domain
  - or, simply do something like:
       perl -pi -e 's/example.com/my-test-domain.com/g' *.toml

s
Also remove certbot/ssl:
    export NUA_CERTBOT_STRATEGY="none"


If something goes really wrong:
    docker ps -a
    docker container rm -f $(docker ps -qa)
    docker network prune
    docker volume prune
    docker system prune -a

docker run -p 8101:80 -e DB_NAME=flask_db_2 -e DB_USER=bob2 -e DB_USER_PWD=bob_pwd_2 --add-host host.docker.internal:172.17.0.1 --name test sha256:b414517f8b952f8ac77896136b9f7a0b2c179721574f87f082fe05c11c6eba9f bash
