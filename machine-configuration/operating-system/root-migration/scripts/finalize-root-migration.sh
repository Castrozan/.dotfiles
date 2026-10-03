#!/bin/sh
set -eu

source_filesystem_uuid=${1:?}
destination_filesystem_uuid=${2:?}
destination_directory=${3:?}
exclusion_file=${4:?}

fail_migration() {
	printf 'Root migration refused: %s\n' "$1" >&2
	exit 1
}

[ "$source_filesystem_uuid" != "$destination_filesystem_uuid" ] || fail_migration 'source and destination are identical'
mounted_filesystem_uuid=$(findmnt --noheadings --output UUID --mountpoint "$destination_directory")
[ "$mounted_filesystem_uuid" = "$destination_filesystem_uuid" ] || fail_migration 'destination mount has the wrong filesystem UUID'

migration_directory="$destination_directory/.root-migration"
migration_identity="$source_filesystem_uuid:$destination_filesystem_uuid"
completed_file="$migration_directory/completed"
prepared_file="$migration_directory/prepared"

if [ -e "$completed_file" ]; then
	[ "$(cat "$completed_file")" = "$migration_identity" ] || fail_migration 'completion marker belongs to another migration'
	exit 0
fi

[ -f "$prepared_file" ] || fail_migration 'the online copy has not been prepared'
[ "$(cat "$prepared_file")" = "$migration_identity" ] || fail_migration 'preparation marker belongs to another migration'

source_device="/dev/disk/by-uuid/$source_filesystem_uuid"
[ "$(blkid -s UUID -o value "$source_device")" = "$source_filesystem_uuid" ] || fail_migration 'source filesystem UUID does not match'
if findmnt --noheadings --source "$source_device" >/dev/null; then
	fail_migration 'source filesystem is already mounted'
fi

source_mount_directory=$(mktemp -d "${TMPDIR:-/run}/root-migration-source.XXXXXX")
source_is_mounted=false

cleanup_source_mount() {
	if [ "$source_is_mounted" = true ]; then
		umount "$source_mount_directory" || true
	fi
	rmdir "$source_mount_directory" || true
}

trap cleanup_source_mount EXIT
trap 'exit 1' HUP INT TERM

mount -t ext4 -o ro "$source_device" "$source_mount_directory"
source_is_mounted=true
source_mount_options=$(findmnt --noheadings --output OPTIONS --mountpoint "$source_mount_directory")
case ",$source_mount_options," in
*,ro,*) ;;
*) fail_migration 'source filesystem is not read-only' ;;
esac
[ -f "$source_mount_directory/etc/NIXOS" ] || fail_migration 'source is not a NixOS root'

printf 'Completing the root migration before starting services.\n'
rsync --archive --hard-links --acls --xattrs --numeric-ids --sparse \
	--one-file-system --modify-window=-1 --delete-delay --stats --info=progress2 \
	--exclude-from="$exclusion_file" --log-file="$migration_directory/final-sync.log" \
	"$source_mount_directory/" "$destination_directory/"

umount "$source_mount_directory"
source_is_mounted=false
sync
printf '%s\n' "$migration_identity" >"$completed_file.new"
mv "$completed_file.new" "$completed_file"
sync
printf 'Root migration synchronization completed. Starting the new root.\n'
