"""
CLI interface - Argument parsing and command dispatch.
"""

import sys
import argparse

#from ..common import ensure_correct_kernel
from .rclone import push_rclone, pull_rclone, generate_diff_report, transfer_between_remotes, install_rclone
from .remotes import (
    setup_rclone,
    list_remotes,
    delete_remote,
    list_supported_remote_types,
    set_host_port,
    _detect_remote_type,
    check_lumi_o_credentials,
)


#@ensure_correct_kernel
def main():
    """Main CLI entry point."""
    if not install_rclone("./bin"):
        print("Error: rclone installation/verification failed.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Backup manager CLI using rclone")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Global arguments
    parser.add_argument("--dry-run", action="store_true", help="Do not modify remote; show actions.")
    parser.add_argument("-v", "--verbose", action="count", default=1, help="Increase verbosity (-v, -vv, -vvv).")

    # List command
    subparsers.add_parser("list", help="List rclone remotes and mapped folders")
    
    # Types command
    subparsers.add_parser("types", help="List supported remote types")

    # Add command
    add = subparsers.add_parser("add", help="Add a remote and folder mapping")
    add.add_argument("--remote", required=True, help="Remote name")
    add.add_argument("--local-path", help="Specific local path to backup")

    # Push command
    push = subparsers.add_parser("push", help="Push/backup to remote")
    push.add_argument("--remote", required=True, help="Remote name")
    push.add_argument("--mode", choices=["sync", "copy", "move"], default="sync",
                     help="sync: mirror (default), copy: no deletes, move: delete source after")
    push.add_argument("--remote-path", help="remote path to backup")

    # Pull command
    pull = subparsers.add_parser("pull", help="Pull/restore from remote")
    pull.add_argument("--remote", required=True, help="Remote name")
    pull.add_argument("--mode", choices=["sync", "copy", "move"], default="sync",
                     help="sync: mirror (default), copy: no deletes, move: delete source after")
    pull.add_argument("--local-path", help="Override destination path")

    # Delete command
    delete = subparsers.add_parser("delete", help="Delete a remote and its mapping")
    delete.add_argument("--remote", required=True, help="Remote name")

    # Diff command
    diff = subparsers.add_parser("diff", help="Generate a diff report for a remote")
    diff.add_argument("--remote", required=True, help="Remote name")

    # Transfer command (remote-to-remote)
    transfer = subparsers.add_parser("transfer", help="Transfer data between two remotes")
    transfer.add_argument("--source", required=True, help="Source remote name")
    transfer.add_argument("--destination", required=True, help="Destination remote name")
    transfer.add_argument("--mode", choices=["copy", "sync"], default="copy", help="Operation: copy or sync")
    transfer.add_argument("--confirm", action="store_true", help="Confirm execution (otherwise dry-run)")

    args = parser.parse_args()

    # Handle commands
    if hasattr(args, "remote") and args.remote:
        remote = args.remote.strip().lower()
        
        # Handle LUMI credentials
        if "lumi" in remote:
            remote = check_lumi_o_credentials(remote_name=remote, command=args.command)
            if remote is None:
                return

        # Set host/port for SFTP remotes
        if args.command in {"add", "push", "pull"}:
            remote_type = _detect_remote_type(remote)
            if remote_type in ["erda", "ucloud"]:
                set_host_port(remote)

        # Dispatch commands
        if args.command == "add":
            setup_rclone(remote, local_backup_path=args.local_path)
            
        elif args.command == "push":
            mode = getattr(args, "mode", "sync")
            push_rclone(
                remote_name=remote,
                new_path=args.remote_path,
                operation=mode,
                dry_run=args.dry_run,
                verbose=args.verbose
            )
            
        elif args.command == "pull":
            mode = getattr(args, "mode", "sync")
            pull_rclone(
                remote_name=remote,
                new_path=args.local_path,
                operation=mode,
                dry_run=args.dry_run,
                verbose=args.verbose
            )
            
        elif args.command == "delete":
            delete_remote(remote_name=remote, verbose=args.verbose)
            
        elif args.command == "diff":
            generate_diff_report(remote_name=remote)

    elif args.command == "transfer":
        # Remote-to-remote transfer
        operation = getattr(args, "mode", "copy")
        dry_run = not args.confirm  # If not confirmed, run in dry-run
        transfer_between_remotes(
            source_remote=args.source.strip().lower(),
            dest_remote=args.destination.strip().lower(),
            operation=operation,
            dry_run=dry_run,
            verbose=args.verbose
        )

    else:
        # Commands without a remote
        if args.command == "list":
            list_remotes()
        elif args.command == "types":
            list_supported_remote_types()
        else:
            parser.print_help()
            sys.exit(2)


if __name__ == "__main__":
    main()