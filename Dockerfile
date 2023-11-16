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

COPY /demoapp /app/

EXPOSE 8000/tcp

CMD ["/usr/local/bin/uvicorn", "--host", "0.0.0.0", "app.app:app"]

