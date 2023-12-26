ARG base_image=python
ARG base_image_tag=3.11-slim-bookworm

FROM ${base_image}:${base_image_tag}

ARG git_commit

RUN apt update \
    && apt -y upgrade \
    && apt -y install curl wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt -y clean \
    && apt -y autoclean

COPY /requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt --no-cache-dir

COPY /demoapp /demoapp/
COPY /contrib /contrib/

ENV GIT_COMMIT_SHA=${git_commit}
ENV PYTHONPATH=/contrib

EXPOSE 8000/tcp

ENTRYPOINT [ "/usr/local/bin/uvicorn" ]

CMD ["--host", "0.0.0.0", "demoapp.front_main:app"]

