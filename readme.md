# install
- install nix with flakes
- create .env
- enable direnv or load .env file into shell
- create bucket in scaleway for state
- ./tofu.sh apply
- nix run .#pushall

# IMPORTANT NOTE
The current implementation of encryption is flawed and must not be relied upon
