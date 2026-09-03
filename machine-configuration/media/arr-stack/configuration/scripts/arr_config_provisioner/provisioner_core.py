from provisioner_logging import log
from provisioning_steps import (
    provision_host_login_step,
    provision_jellyseerr_sonarr_profile_step,
    provision_qbittorrent_preference_step,
    provision_quality_profile_step,
    provision_step,
)

RESOURCE_PLAN = [
    {
        "app": "radarr",
        "port": 7878,
        "resource": "downloadclient",
        "match": "name",
        "update": True,
        "force_save": True,
    },
    {
        "app": "radarr",
        "port": 7878,
        "resource": "rootfolder",
        "match": "path",
        "update": False,
        "force_save": False,
    },
    {
        "app": "radarr",
        "port": 7878,
        "resource": "customformat",
        "match": "name",
        "update": True,
        "force_save": False,
    },
    {
        "app": "sonarr",
        "port": 8989,
        "resource": "downloadclient",
        "match": "name",
        "update": True,
        "force_save": True,
    },
    {
        "app": "sonarr",
        "port": 8989,
        "resource": "rootfolder",
        "match": "path",
        "update": False,
        "force_save": False,
    },
    {
        "app": "sonarr",
        "port": 8989,
        "resource": "customformat",
        "match": "name",
        "update": True,
        "force_save": False,
    },
    {
        "app": "prowlarr",
        "port": 9696,
        "resource": "applications",
        "match": "name",
        "update": True,
        "force_save": True,
    },
    {
        "app": "prowlarr",
        "port": 9696,
        "resource": "indexer",
        "match": "name",
        "update": True,
        "force_save": True,
    },
]

QUALITY_PROFILE_PLAN = [
    {"app": "radarr", "port": 7878},
    {"app": "sonarr", "port": 8989},
]

JELLYSEERR_SONARR_PROFILE_PLAN = [{"app": "sonarr", "port": 8989}]

HOST_LOGIN_PLAN = [
    {"app": "radarr", "port": 7878},
    {"app": "sonarr", "port": 8989},
    {"app": "prowlarr", "port": 9696},
]

QBITTORRENT_PREFERENCE_PLAN = [{"app": "qbittorrent", "port": 8080}]


def run_plan(configuration, plan, step_runner, outcome_label, dry_run):
    failed_steps = 0
    for step in plan:
        try:
            step_runner(configuration, step, dry_run)
        except Exception as error:
            failed_steps += 1
            log(f"{step['app']}/{outcome_label}: skipped after error: {error}")
    return failed_steps


def provision_all(configuration, dry_run):
    plans = [
        (RESOURCE_PLAN, provision_step, "resource"),
        (QUALITY_PROFILE_PLAN, provision_quality_profile_step, "qualityprofile"),
        (
            JELLYSEERR_SONARR_PROFILE_PLAN,
            provision_jellyseerr_sonarr_profile_step,
            "jellyseerr-profile",
        ),
        (HOST_LOGIN_PLAN, provision_host_login_step, "host-login"),
        (
            QBITTORRENT_PREFERENCE_PLAN,
            provision_qbittorrent_preference_step,
            "preferences",
        ),
    ]
    total_steps = sum(len(plan) for plan, _, _ in plans)
    failed_steps = sum(
        run_plan(configuration, plan, step_runner, outcome_label, dry_run)
        for plan, step_runner, outcome_label in plans
    )
    if failed_steps:
        log(
            f"WARNING: {failed_steps} of {total_steps} steps could not be applied; "
            "config was not fully reconciled this run"
        )
    return failed_steps
