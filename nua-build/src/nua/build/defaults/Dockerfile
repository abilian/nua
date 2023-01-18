ARG nua_builder_tag
FROM ${nua_builder_tag}

# app build:
COPY . /nua/build
RUN app_builder

CMD ["python", "/nua/scripts/start.py"]
