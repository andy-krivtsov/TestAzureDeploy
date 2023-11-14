#!/bin/bash

echo "Installs Azure CLI bash autocompletion"
curl https://raw.githubusercontent.com/Azure/azure-cli/dev/az.completion --output /etc/bash_completion.d/az.completion

