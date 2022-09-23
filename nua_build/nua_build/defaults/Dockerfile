ARG nua_builder_tag
FROM ${nua_builder_tag}

# app build:
COPY . /nua/build
RUN nua_build_setup_app

CMD ["python", "/nua/scripts/start.py"]
