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
          # Builds the agent container image using docker build (impure).
          #
          #   nix build .#image --impure
          #   docker load < result
          #
          image = pkgs.runCommand "agent-sandbox-image" {
            __impure = true;
            nativeBuildInputs = [ pkgs.docker ];
            src = self;
          } ''
            cd $src
            docker build -t agent-sandbox:local .
            docker save agent-sandbox:local -o $out
          '';

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

          # -- Examples -----------------------------------------------------

          # LangChain coding agent image (impure).
          #
          #   nix build .#examples-langchain-image --impure
          #   docker load < result
          #
          examples-langchain-image = pkgs.runCommand "langchain-coding-agent-image" {
            __impure = true;
            nativeBuildInputs = [ pkgs.docker ];
            src = self;
          } ''
            cd $src
            docker build -t langchain-coding-agent:local \
              -f examples/langchain/Dockerfile examples/langchain/
            docker build -t langchain-model-downloader:local \
              -f examples/langchain/Dockerfile.init examples/langchain/
            docker save langchain-coding-agent:local \
              langchain-model-downloader:local -o $out
          '';

          # LangChain manifests.
          #
          #   nix build .#examples-langchain-manifests
          #   ls result/
          #
          examples-langchain-manifests = pkgs.stdenvNoCC.mkDerivation {
            pname = "langchain-example-manifests";
            version = "0.1.0";
            src = ./examples/langchain/manifests;
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
