"""[cyan][bold]Main command line interface for SWE-agent.[/bold][/cyan]

[cyan][bold]=== USAGE ===[/bold][/cyan]

[green]sweagent <command> [options][/green]

Display usage instructions for a specific command:

[green]sweagent <command> [bold]--help[/bold][/green]

[cyan][bold]=== SUBCOMMANDS TO RUN SWE-AGENT ===[/bold][/cyan]

[bold][green]run[/green][/bold] or [bold][green]r[/green][/bold]: Run swe-agent on a single problem statement, for example a github issue.
"""

import argparse
import sys

import rich


def get_cli():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "command",
        choices=["run"],
        nargs="?",
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    return parser


def main(args: list[str] | None = None):
    if args is None:
        args = sys.argv[1:]
    cli = get_cli()
    parsed_args, remaining_args = cli.parse_known_args(args)  # type: ignore
    command = parsed_args.command
    show_help = parsed_args.help
    if show_help:
        if not command:
            # Show main help
            rich.print(__doc__)
            sys.exit(0)
        else:
            # Add to remaining_args
            remaining_args.append("--help")
    elif not command:
        cli.print_help()
        sys.exit(2)
    # Defer imports to avoid unnecessary long loading times
    if command in ["run", "r"]:
        from sweagent.run.run_single import run_from_cli as run_single_main

        run_single_main(remaining_args)
    else:
        msg = f"Unknown command: {command}"
        raise ValueError(msg)


if __name__ == "__main__":
    sys.exit(main())
