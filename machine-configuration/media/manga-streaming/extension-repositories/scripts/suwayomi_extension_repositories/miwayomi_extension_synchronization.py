from dataclasses import dataclass


@dataclass(frozen=True)
class ExtensionPolicy:
    removed_packages: tuple[str, ...]


def installed_package_names(base_url, client):
    return {
        extension["pkg"]
        for extension in client.read_installed_extensions(base_url)
        if isinstance(extension.get("pkg"), str)
    }


def synchronize_extensions(base_url, policy, client):
    installed_packages = installed_package_names(base_url, client)
    removed_packages = []
    for package_name in policy.removed_packages:
        if package_name not in installed_packages:
            continue
        client.uninstall_extension(base_url, package_name)
        removed_packages.append(package_name)
    remaining_packages = installed_package_names(base_url, client).intersection(
        policy.removed_packages
    )
    if remaining_packages:
        remaining_names = ", ".join(sorted(remaining_packages))
        raise ValueError(
            f"Miwayomi still reports forbidden extension packages: {remaining_names}"
        )
    return {"removed_packages": removed_packages}
