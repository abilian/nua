Testing:

-   DB resource is defined directly with tag "docker" and explicit docker image. Not the prefered way, but should still work.
-   we use the feature of no build.py but project auto detection
-   also tested: meta package with wrong double declaration (double aliases for 'postgres-client')
