#!/bin/sh

# This script installs the Nix package manager on your system by
# downloading a binary distribution and running its installer script
# (which in turn creates and populates /nix).

{ # Prevent execution if this script was only partially downloaded
    oops() {
        echo "$0:" "$@" >&2
        exit 1
    }

    umask 0022

    tmpDir="$(mktemp -d -t nix-binary-tarball-unpack.XXXXXXXXXX ||
        oops "Can't create temporary directory for downloading the Nix binary tarball")"
    cleanup() {
        rm -rf "$tmpDir"
    }
    trap cleanup EXIT INT QUIT TERM

    require_util() {
        command -v "$1" >/dev/null 2>&1 ||
            oops "you do not have '$1' installed, which I need to $2"
    }

    case "$(uname -s).$(uname -m)" in
    Linux.x86_64)
        hash=f66ee75b9107bac599de6b7516a3f8e0f808c30d6fe56693d4972152d6fc5dc3
        path=i9fy0pvnm9p78wv779jml81g8pn901y5/nix-2.25.3-x86_64-linux.tar.xz
        system=x86_64-linux
        ;;
    Linux.i?86)
        hash=892c42f51bf180eb4f034f856fd4b5d7cd72555ebf9aeaff99c5af460bf65a8e
        path=ig5zbxdwjnkil72gm5an9fj4nam6rmk2/nix-2.25.3-i686-linux.tar.xz
        system=i686-linux
        ;;
    Linux.aarch64)
        hash=407978c9eeb850e7c1370b6d7784814b65e50af4b82677a479d38dead8151f49
        path=6yshvjjfaaxiqr5026vs7b0y2w7shnm1/nix-2.25.3-aarch64-linux.tar.xz
        system=aarch64-linux
        ;;
    Linux.armv6l)
        hash=1e82ac4437b753d6f5e44e7926e3cf3eb24c2e751c21224db237fe167f09cf70
        path=v56sdm0ic3crw2yi3wz7d9b5f482i03k/nix-2.25.3-armv6l-linux.tar.xz
        system=armv6l-linux
        ;;
    Linux.armv7l)
        hash=80c658c4ab81c768f3e504f6efb6ba2debc6f29bf22efdf4d15393da8637cdab
        path=9rj2a7yclqlkqyrcpqn6wgwc567g6c8j/nix-2.25.3-armv7l-linux.tar.xz
        system=armv7l-linux
        ;;
    Linux.riscv64)
        hash=5c049986d600e58f76cbac81aa7d60503f33d665be0477fbba7e2774dd913d7a
        path=ja0j1v67jp9i8jfr2fg29zgkawiclpz4/nix-2.25.3-riscv64-linux.tar.xz
        system=riscv64-linux
        ;;
    Darwin.x86_64)
        hash=5d41ad5203724a56bea5a1b61f436a22839d82126680ec00e78c27765d99b252
        path=g3ydmarap98zfj4j286dgrwzpc8agllf/nix-2.25.3-x86_64-darwin.tar.xz
        system=x86_64-darwin
        ;;
    Darwin.arm64 | Darwin.aarch64)
        hash=9d3b7eadd1c9b71ae43c3244e88fc3dd89ba59f1c78ee6c7d22800c562b7e66e
        path=fg8haq4wkgm320cffnib91f6lv2i28g6/nix-2.25.3-aarch64-darwin.tar.xz
        system=aarch64-darwin
        ;;
    *) oops "sorry, there is no binary distribution of Nix for your platform" ;;
    esac

    # Use this command-line option to fetch the tarballs using nar-serve or Cachix
    if [ "${1:-}" = "--tarball-url-prefix" ]; then
        if [ -z "${2:-}" ]; then
            oops "missing argument for --tarball-url-prefix"
        fi
        url=${2}/${path}
        shift 2
    else
        url=https://releases.nixos.org/nix/nix-2.25.3/nix-2.25.3-$system.tar.xz
    fi

    tarball=$tmpDir/nix-2.25.3-$system.tar.xz

    require_util tar "unpack the binary tarball"
    if [ "$(uname -s)" != "Darwin" ]; then
        require_util xz "unpack the binary tarball"
    fi

    if command -v curl >/dev/null 2>&1; then
        fetch() { curl --fail -L "$1" -o "$2"; }
    elif command -v wget >/dev/null 2>&1; then
        fetch() { wget "$1" -O "$2"; }
    else
        oops "you don't have wget or curl installed, which I need to download the binary tarball"
    fi

    echo "downloading Nix 2.25.3 binary tarball for $system from '$url' to '$tmpDir'..."
    fetch "$url" "$tarball" || oops "failed to download '$url'"

    if command -v sha256sum >/dev/null 2>&1; then
        hash2="$(sha256sum -b "$tarball" | cut -c1-64)"
    elif command -v shasum >/dev/null 2>&1; then
        hash2="$(shasum -a 256 -b "$tarball" | cut -c1-64)"
    elif command -v openssl >/dev/null 2>&1; then
        hash2="$(openssl dgst -r -sha256 "$tarball" | cut -c1-64)"
    else
        oops "cannot verify the SHA-256 hash of '$url'; you need one of 'shasum', 'sha256sum', or 'openssl'"
    fi

    if [ "$hash" != "$hash2" ]; then
        oops "SHA-256 hash mismatch in '$url'; expected $hash, got $hash2"
    fi

    unpack=$tmpDir/unpack
    mkdir -p "$unpack"
    tar -xJf "$tarball" -C "$unpack" || oops "failed to unpack '$url'"

    script=$(echo "$unpack"/*/install)

    [ -e "$script" ] || oops "installation script is missing from the binary tarball!"
    export INVOKED_FROM_INSTALL_IN=1
    "$script" "$@"

} # End of wrapping

# 0: Indicates the script or shell is running as the superuser (root).
# Non-zero: A regular user ID (e.g., 1000 for the first user on most Linux systems).
is_root() {
    if [ "$EUID" -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

_SERIOUS_BUSINESS="${RED}%s:${ESC} "
password_confirm() {
    local do_something_consequential="$1"
    if ui_confirm "Can I $do_something_consequential?"; then
        # shellcheck disable=SC2059
        sudo -kv --prompt="$(printf "${_SERIOUS_BUSINESS}" "Enter your password to $do_something_consequential")"
    else
        return 1
    fi
}

__sudo() {
    local expl="$1"
    local cmd="$2"
    shift
    header "sudo execution"

    echo "I am executing:"
    echo ""
    printf "    $ sudo %s\\n" "$cmd"
    echo ""
    echo "$expl"
    echo ""

    return 0
}

_sudo() {
    local expl="$1"
    shift
    if ! headless || is_root; then
        __sudo "$expl" "$*" >&2
    fi

    if is_root; then
        env "$@"
    else
        sudo "$@"
    fi
}

sh <(curl -L https://nixos.org/nix/install) --no-daemon --yes --no-channel-add