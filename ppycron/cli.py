"""
PPyCron CLI - Cross-platform command-line interface for managing cronjobs.

Usage:
    ppycron add --command "echo hello" --interval "*/5 * * * *"
    ppycron list
    ppycron get --id <cron_id>
    ppycron edit --id <cron_id> --command "new command"
    ppycron delete --id <cron_id>
    ppycron clear
    ppycron validate --interval "* * * * *"
    ppycron count
    ppycron search --command "echo" | --interval "* * * * *"
    ppycron duplicate --id <cron_id> [--interval "0 3 * * *"]
"""

import sys
import json
import platform
import logging

import click

from ppycron.src.base import Cron


def _get_interface():
    """Get the appropriate interface for the current operating system."""
    if platform.system() == "Windows":
        from ppycron.src.windows import WindowsInterface
        return WindowsInterface()
    else:
        from ppycron.src.unix import UnixInterface
        return UnixInterface()


def _format_cron(cron: Cron, output_format: str = "table") -> str:
    """Format a Cron object for display."""
    if output_format == "json":
        return json.dumps(cron.to_dict(), indent=2)
    else:
        return (
            f"  ID:       {cron.id}\n"
            f"  Command:  {cron.command}\n"
            f"  Interval: {cron.interval}"
        )


def _format_cron_list(crons: list, output_format: str = "table") -> str:
    """Format a list of Cron objects for display."""
    if not crons:
        return "No cronjobs found."

    if output_format == "json":
        return json.dumps([c.to_dict() for c in crons], indent=2)
    else:
        lines = []
        for i, cron in enumerate(crons, 1):
            lines.append(f"[{i}] {cron.id}")
            lines.append(f"    Command:  {cron.command}")
            lines.append(f"    Interval: {cron.interval}")
            if i < len(crons):
                lines.append("")
        return "\n".join(lines)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging output.")
@click.version_option(version="1.1.0", prog_name="ppycron")
@click.pass_context
def cli(ctx, verbose):
    """PPyCron - Cross-platform cronjob management CLI.

    Manage scheduled tasks on Unix/Linux (cron) and Windows (Task Scheduler)
    using a unified command-line interface.
    """
    ctx.ensure_object(dict)
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


@cli.command()
@click.option("--command", "-c", required=True, help="Command to execute.")
@click.option("--interval", "-i", required=True, help="Cron interval (e.g. '*/5 * * * *').")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json"]), default="table",
              help="Output format.")
def add(command, interval, output_format):
    """Add a new cronjob.

    Examples:

        ppycron add -c "echo hello" -i "*/5 * * * *"

        ppycron add --command "python script.py" --interval "0 2 * * *"
    """
    try:
        interface = _get_interface()
        cron = interface.add(command=command, interval=interval)
        click.echo(click.style("✓ Cronjob created successfully!", fg="green", bold=True))
        click.echo()
        click.echo(_format_cron(cron, output_format))
    except ValueError as e:
        click.echo(click.style(f"✗ Validation error: {e}", fg="red"), err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(click.style(f"✗ Runtime error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command("list")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json"]), default="table",
              help="Output format.")
def list_jobs(output_format):
    """List all cronjobs.

    Examples:

        ppycron list

        ppycron list --format json
    """
    try:
        interface = _get_interface()
        crons = interface.get_all()
        if crons:
            click.echo(click.style(f"Found {len(crons)} cronjob(s):", fg="cyan", bold=True))
            click.echo()
        click.echo(_format_cron_list(crons, output_format))
    except RuntimeError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option("--id", "-i", "cron_id", required=True, help="Cronjob ID.")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json"]), default="table",
              help="Output format.")
def get(cron_id, output_format):
    """Get a cronjob by its ID.

    Examples:

        ppycron get --id abc123

        ppycron get -i abc123 --format json
    """
    try:
        interface = _get_interface()
        cron = interface.get_by_id(cron_id)
        if cron:
            click.echo(_format_cron(cron, output_format))
        else:
            click.echo(click.style(f"✗ Cronjob with ID '{cron_id}' not found.", fg="yellow"), err=True)
            sys.exit(1)
    except ValueError as e:
        click.echo(click.style(f"✗ Validation error: {e}", fg="red"), err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option("--id", "-i", "cron_id", required=True, help="Cronjob ID to edit.")
@click.option("--command", "-c", default=None, help="New command to execute.")
@click.option("--interval", "-I", default=None, help="New cron interval.")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json"]), default="table",
              help="Output format.")
def edit(cron_id, command, interval, output_format):
    """Edit an existing cronjob.

    At least one of --command or --interval must be provided.

    Examples:

        ppycron edit --id abc123 --command "new_command.sh"

        ppycron edit --id abc123 --interval "0 3 * * *"

        ppycron edit --id abc123 -c "cmd.sh" -I "*/10 * * * *"
    """
    if command is None and interval is None:
        click.echo(click.style("✗ At least one of --command or --interval must be provided.", fg="red"), err=True)
        sys.exit(1)

    try:
        interface = _get_interface()
        kwargs = {}
        if command is not None:
            kwargs["command"] = command
        if interval is not None:
            kwargs["interval"] = interval

        success = interface.edit(cron_id=cron_id, **kwargs)
        if success:
            click.echo(click.style("✓ Cronjob updated successfully!", fg="green", bold=True))
            # Show updated job
            updated = interface.get_by_id(cron_id)
            if updated:
                click.echo()
                click.echo(_format_cron(updated, output_format))
        else:
            click.echo(click.style(f"✗ Cronjob with ID '{cron_id}' not found.", fg="yellow"), err=True)
            sys.exit(1)
    except ValueError as e:
        click.echo(click.style(f"✗ Validation error: {e}", fg="red"), err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option("--id", "-i", "cron_id", required=True, help="Cronjob ID to delete.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
def delete(cron_id, yes):
    """Delete a cronjob by its ID.

    Examples:

        ppycron delete --id abc123

        ppycron delete --id abc123 --yes
    """
    if not yes:
        click.confirm(f"Are you sure you want to delete cronjob '{cron_id}'?", abort=True)

    try:
        interface = _get_interface()
        success = interface.delete(cron_id=cron_id)
        if success:
            click.echo(click.style("✓ Cronjob deleted successfully!", fg="green", bold=True))
        else:
            click.echo(click.style(f"✗ Cronjob with ID '{cron_id}' not found.", fg="yellow"), err=True)
            sys.exit(1)
    except ValueError as e:
        click.echo(click.style(f"✗ Validation error: {e}", fg="red"), err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
def clear(yes):
    """Clear all cronjobs.

    Examples:

        ppycron clear

        ppycron clear --yes
    """
    if not yes:
        click.confirm("Are you sure you want to delete ALL cronjobs? This cannot be undone.", abort=True)

    try:
        interface = _get_interface()
        success = interface.clear_all()
        if success:
            click.echo(click.style("✓ All cronjobs cleared successfully!", fg="green", bold=True))
        else:
            click.echo(click.style("✗ Failed to clear cronjobs.", fg="red"), err=True)
            sys.exit(1)
    except RuntimeError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option("--interval", "-i", required=True, help="Cron interval to validate.")
def validate(interval):
    """Validate a cron interval format.

    Examples:

        ppycron validate --interval "*/5 * * * *"

        ppycron validate -i "60 * * * *"
    """
    try:
        interface = _get_interface()
        is_valid = interface.is_valid_cron_format(interval)
        if is_valid:
            click.echo(click.style(f"✓ '{interval}' is a valid cron format.", fg="green", bold=True))
        else:
            click.echo(click.style(f"✗ '{interval}' is NOT a valid cron format.", fg="red"))
            sys.exit(1)
    except RuntimeError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
def count():
    """Count the total number of cronjobs.

    Examples:

        ppycron count
    """
    try:
        interface = _get_interface()
        total = interface.count()
        click.echo(click.style(f"Total cronjobs: {total}", fg="cyan", bold=True))
    except RuntimeError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option("--command", "-c", default=None, help="Search by command string.")
@click.option("--interval", "-i", default=None, help="Search by interval string.")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json"]), default="table",
              help="Output format.")
def search(command, interval, output_format):
    """Search cronjobs by command or interval.

    At least one of --command or --interval must be provided.

    Examples:

        ppycron search --command "backup.sh"

        ppycron search --interval "0 2 * * *"
    """
    if command is None and interval is None:
        click.echo(click.style("✗ At least one of --command or --interval must be provided.", fg="red"), err=True)
        sys.exit(1)

    try:
        interface = _get_interface()
        results = []

        if command is not None:
            results.extend(interface.get_by_command(command))
        if interval is not None:
            # Avoid duplicates
            interval_results = interface.get_by_interval(interval)
            existing_ids = {c.id for c in results}
            results.extend([c for c in interval_results if c.id not in existing_ids])

        if results:
            click.echo(click.style(f"Found {len(results)} matching cronjob(s):", fg="cyan", bold=True))
            click.echo()
        click.echo(_format_cron_list(results, output_format))
    except RuntimeError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option("--id", "-i", "cron_id", required=True, help="Cronjob ID to duplicate.")
@click.option("--interval", "-I", default=None, help="New interval for the duplicated cronjob.")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json"]), default="table",
              help="Output format.")
def duplicate(cron_id, interval, output_format):
    """Duplicate an existing cronjob.

    Examples:

        ppycron duplicate --id abc123

        ppycron duplicate --id abc123 --interval "0 4 * * *"
    """
    try:
        interface = _get_interface()
        new_cron = interface.duplicate(cron_id, new_interval=interval)
        if new_cron:
            click.echo(click.style("✓ Cronjob duplicated successfully!", fg="green", bold=True))
            click.echo()
            click.echo(_format_cron(new_cron, output_format))
        else:
            click.echo(click.style(f"✗ Cronjob with ID '{cron_id}' not found.", fg="yellow"), err=True)
            sys.exit(1)
    except ValueError as e:
        click.echo(click.style(f"✗ Validation error: {e}", fg="red"), err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
