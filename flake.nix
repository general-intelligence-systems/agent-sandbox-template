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
          # nix build .#image --impure && docker load < result
          image = pkgs.runCommand "agent-sandbox-image" {
            __impure = true;
            nativeBuildInputs = [ pkgs.docker ];
            src = self;
          } ''
            cd $src
            docker build -t agent-sandbox:local .
            docker save agent-sandbox:local -o $out
          '';

          # nix build .#manifests
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

          # nix build .#examples-langchain-image --impure && docker load < result
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

          # nix build .#examples-langchain-manifests
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
            ];
            shellHook = ''
              export PATH="$PWD/bin:$PATH"
            '';
          };
        }
      );
    };
}
