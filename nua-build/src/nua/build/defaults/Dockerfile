ARG nua_builder_tag
FROM ${nua_builder_tag}

# app build:
COPY . /nua/build
ARG nua_verbosity
RUN app-builder

CMD ["python", "/nua/scripts/start.py"]
