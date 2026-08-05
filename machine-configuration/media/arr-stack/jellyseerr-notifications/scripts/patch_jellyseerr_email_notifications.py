import json
import os
import subprocess
import tempfile


def required_environment_value(name):
    value = os.environ.get(name)
    if value is None or value == "":
        raise SystemExit(f"missing required environment value {name}")
    return value


def read_configured_app_password(app_password_secret_file, app_password_sentinel):
    try:
        with open(app_password_secret_file, "r", encoding="utf-8") as handle:
            app_password = handle.read().strip()
    except FileNotFoundError:
        return None
    if not app_password or app_password == app_password_sentinel:
        return None
    return app_password


def desired_email_agent(existing_email_agent, app_password, configuration):
    uses_implicit_tls = configuration["smtp_port"] == 465
    options = dict(existing_email_agent.get("options", {}))
    options["emailFrom"] = configuration["sender_address"]
    options["senderName"] = configuration["sender_name"]
    options["smtpHost"] = configuration["smtp_host"]
    options["smtpPort"] = configuration["smtp_port"]
    options["authUser"] = configuration["smtp_username"]
    options["authPass"] = app_password
    options["secure"] = uses_implicit_tls
    options["requireTls"] = not uses_implicit_tls
    options["ignoreTls"] = False
    options["allowSelfSigned"] = False
    return {
        **existing_email_agent,
        "enabled": True,
        "types": configuration["notification_types_bitmask"],
        "options": options,
    }


def load_settings(settings_file):
    with open(settings_file, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_settings_atomically(settings_file, settings):
    settings_directory = os.path.dirname(settings_file)
    temporary_handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=settings_directory, delete=False
    )
    with temporary_handle:
        json.dump(settings, temporary_handle, indent=2)
        temporary_handle.write("\n")
    os.chmod(temporary_handle.name, 0o644)
    os.replace(temporary_handle.name, settings_file)


def restart_jellyseerr_best_effort(docker_binary, container_name):
    completed = subprocess.run(
        [docker_binary, "restart", container_name],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        print(
            "jellyseerr container restart skipped, it will read the patched settings on its next start: "
            f"{completed.stderr.strip()}"
        )


def apply_email_notification_configuration(configuration):
    app_password = read_configured_app_password(
        configuration["app_password_secret_file"],
        configuration["app_password_sentinel"],
    )
    if app_password is None:
        print(
            "gmail app password not configured yet, leaving the jellyseerr email agent untouched"
        )
        return False
    settings = load_settings(configuration["settings_file"])
    agents = settings.setdefault("notifications", {}).setdefault("agents", {})
    existing_email_agent = agents.get("email", {})
    updated_email_agent = desired_email_agent(
        existing_email_agent, app_password, configuration
    )
    if updated_email_agent == existing_email_agent:
        print("jellyseerr email agent already matches the desired configuration")
        return False
    agents["email"] = updated_email_agent
    write_settings_atomically(configuration["settings_file"], settings)
    print("patched the jellyseerr email agent, restarting the container to load it")
    restart_jellyseerr_best_effort(
        configuration["docker_binary"], configuration["container_name"]
    )
    return True


def resolve_configuration():
    return {
        "settings_file": required_environment_value("JELLYSEERR_SETTINGS_FILE"),
        "app_password_secret_file": required_environment_value(
            "JELLYSEERR_SMTP_APP_PASSWORD_FILE"
        ),
        "app_password_sentinel": required_environment_value(
            "JELLYSEERR_SMTP_APP_PASSWORD_SENTINEL"
        ),
        "sender_address": required_environment_value("JELLYSEERR_EMAIL_SENDER_ADDRESS"),
        "sender_name": required_environment_value("JELLYSEERR_EMAIL_SENDER_NAME"),
        "smtp_host": required_environment_value("JELLYSEERR_SMTP_HOST"),
        "smtp_port": int(required_environment_value("JELLYSEERR_SMTP_PORT")),
        "smtp_username": required_environment_value("JELLYSEERR_SMTP_USERNAME"),
        "notification_types_bitmask": int(
            required_environment_value("JELLYSEERR_NOTIFICATION_TYPES_BITMASK")
        ),
        "docker_binary": required_environment_value("DOCKER_BINARY"),
        "container_name": required_environment_value("JELLYSEERR_CONTAINER_NAME"),
    }


def main():
    apply_email_notification_configuration(resolve_configuration())


if __name__ == "__main__":
    main()
