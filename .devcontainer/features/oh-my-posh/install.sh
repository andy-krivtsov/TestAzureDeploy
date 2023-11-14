#!/bin/bash

echo "Install Oh-my-posh for Linux/bash"

curl -s https://ohmyposh.dev/install.sh | bash -s

mkdir -p ~/.poshthemes
curl https://raw.githubusercontent.com/JanDeDobbeleer/oh-my-posh/main/themes/agnoster.omp.json --output  ~/.poshthemes/agnoster.omp.json

echo -e '#\n# Oh-my-posh prompt' >> ~/.bashrc
echo 'eval "$(oh-my-posh init bash --config ~/.poshthemes/agnoster.omp.json)"' >> ~/.bashrc
