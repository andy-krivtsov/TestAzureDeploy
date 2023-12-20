ARG base_image=python
ARG base_image_tag=3.11-slim-bookworm

FROM ${base_image}:${base_image_tag}

RUN apt update \
    && apt -y upgrade \
    && apt -y install curl wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt -y clean \
    && apt -y autoclean

COPY /requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt --no-cache-dir

COPY /demoapp /demoapp/
COPY /fastapi_msal /fastapi_msal

EXPOSE 8000/tcp

ENTRYPOINT [ "/usr/local/bin/uvicorn" ]

CMD ["--host", "0.0.0.0", "demoapp.front:app"]

