{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
  };

  outputs = { self, nixpkgs, ... }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs supportedSystems f;
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          # -- Docker image -----------------------------------------------
          #
          # Builds the agent container image via Nix.
          #
          #   nix build .#image
          #   docker load < result
          #
          image = pkgs.dockerTools.buildLayeredImage {
            name = "agent-sandbox";
            tag = "local";
            contents = [
              pkgs.python312
              pkgs.coreutils
              pkgs.curl
              pkgs.bashInteractive
            ];
            config = {
              WorkingDir = "/app";
              Cmd = [ "${pkgs.python312}/bin/python" "main.py" ];
              ExposedPorts."8080/tcp" = {};
            };
            extraCommands = ''
              mkdir -p app
              cp ${./src/agent/main.py} app/main.py
            '';
          };

          # -- Manifests --------------------------------------------------
          #
          # Copies all Kubernetes manifests into the Nix store.
          #
          #   nix build .#manifests
          #   ls result/base/
          #
          manifests = pkgs.stdenvNoCC.mkDerivation {
            pname = "agent-sandbox-manifests";
            version = "0.1.0";
            src = ./manifests;
            phases = [ "installPhase" ];
            installPhase = ''
              mkdir -p $out
              cp -r $src/* $out/
            '';
          };
        }
      );

      # -- Dev shell ----------------------------------------------------
      #
      # Provides kubectl, k3d, k9s and adds bin/ to $PATH.
      #
      #   nix develop
      #
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              kubectl
              k3d
              k9s
              python312
            ];
            shellHook = ''
              export PATH="$PWD/bin:$PATH"
            '';
          };
        }
      );
    };
}
