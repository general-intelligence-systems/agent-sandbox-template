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
      # -- Manifests derivation -------------------------------------------
      #
      # Copies all Kubernetes manifests into the Nix store so they can be
      # referenced from other flakes or used in CI pipelines.
      #
      #   nix build .#manifests
      #   ls result/base/ result/examples/
      #
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
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

      # -- Dev shell ------------------------------------------------------
      #
      # Provides kubectl, k3d, k9s, and adds bin/ to $PATH.
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
            ];
            shellHook = ''
              export PATH="$PWD/bin:$PATH"
            '';
          };
        }
      );
    };
}
