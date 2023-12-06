#!/bin/bash

set -e

CERT_PEM=$(cat - | jq -r .certBase64 | base64 -d | openssl x509)

jq -n --arg cert "$CERT_PEM"  '{ certPem: $cert }'
