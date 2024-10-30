{
  description = "Remote wipe solution with secure communication and Dell BIOS integration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
      };
      pythonEnv = pkgs.python313.withPackages (ps: [
        ps.pyyaml
        ps.pip
        ps.requests
      ]);
    in {
      devShells.${system} = {
        serverApp = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.openssl
            pkgs.nss
            pkgs.sops
          ];
          shellHook = ''
            #!/bin/bash

            # Set a writable directory for pip installations
            export PIP_TARGET="$PWD/.local/lib/python3.13/site-packages"
            mkdir -p $PIP_TARGET

            # Install additional pip packages into the local directory
            python -m pip install python-fasthtml --no-warn-script-location

            # Add the local directory to PYTHONPATH
            export PYTHONPATH=$PIP_TARGET:$PYTHONPATH

            echo "Starting the Remote Wipe Server"
            python main.py
          '';
        };

        clientApp = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.openssl
            pkgs.nss
            pkgs.sops
          ];
          shellHook = ''
            #!/bin/bash

            # Set a writable directory for pip installations
            export PIP_TARGET="$PWD/.local/lib/python3.13/site-packages"
            mkdir -p $PIP_TARGET

            # Install additional pip packages into the local directory
            python -m pip install python-fasthtml --no-warn-script-location

            # Add the local directory to PYTHONPATH
            export PYTHONPATH=$PIP_TARGET:$PYTHONPATH

            echo "Starting the Remote Wipe Client Agent"
            python client.py
          '';
        };
      };
    };
}
