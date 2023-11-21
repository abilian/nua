# Test app : Galene, use of internal galene TURN server

web site: https://galene.org/

  -   Not suitable for nua-orchestrator test suite



Example of deployment:

$ nua-orchestrator deploy gits/nua/apps/draft-real-apps/galene/sample_deploy.json
First launch: set Nua defaults in 'sqlite:////home/nua/db/nua.db'
Deploy apps from: /home/nua/gits/nua/apps/draft-real-apps/galene/sample_deploy.json
Image found: 'galene'
Installing App: galene 0.6.2, Galène videoconference server
Installing image:
    tags: nua-galene:0.6.2-6
    id: d4014f1b0d
    size: 308MB
    created: 2023-11-20 16:11:59
Deploy 'galene1': a new galene on 'test1.example.xyz'
Configure Nginx for domain 'test1.example.xyz'
Use HTTPS protocol (Certbot) for: test1.example.xyz
Docker run image: galene
        image id: d4014f1b0d40
    -> container of name: galene1-galene
            container id: 26a21689372c
Deployed apps:
Label: galene1
Image 'galene' deployed as https://test1.example.xyz
Deployment status: started
Container ID: 26a21689372c, status: running, created: 3.00s ago

Volumes used by current Nua configuration:
   type=managed driver=docker full_name=galene1-galene_groups
   domains: test1.example.xyz
   type=managed driver=docker full_name=galene1-galene_data
   domains: test1.example.xyz
