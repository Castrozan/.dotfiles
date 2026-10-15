from import_repair.repair import maybe_repair_blocked_imports
from import_repair.redundant_downloads.cleanup import maybe_cleanup_redundant_downloads


def maintain_blocked_imports(configuration, now_epoch, dry_run):
    maybe_cleanup_redundant_downloads(configuration, dry_run)
    maybe_repair_blocked_imports(configuration, now_epoch, dry_run)
