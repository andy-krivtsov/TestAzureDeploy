#!/bin/bash

TF_VER="1.7.3"
TFGRUNT_VER="v0.55.1"

cd $HOME

echo "Install Terraform $TF_VER"
curl -sLo terraform.zip https://releases.hashicorp.com/terraform/${TF_VER}/terraform_${TF_VER}_linux_amd64.zip
unzip terraform.zip
mv terraform /usr/local/bin
rm -f terraform.zip

echo "Install Terragrunt $TFGRUNT_VER"
curl -sLo /usr/local/bin/terragrunt "https://github.com/gruntwork-io/terragrunt/releases/download/${TFGRUNT_VER}/terragrunt_linux_amd64"
chmod +x /usr/local/bin/terragrunt

echo "Install TFLint latest"
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
