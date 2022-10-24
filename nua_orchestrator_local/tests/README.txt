Tests require existing docker images: run pytest on nua_build to generate those images.

Test with nginx and certbot require DNS known domain with subdomaine:
test, test1, test2

  - adapt content of REPLACE_DOMAIN for replacing example.com by your test domain

Also remove certbot/ssl:
    export NUA_CERTBOT_STRATEGY="none"
