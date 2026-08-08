import sys
import urllib.error

import argument_parsing
import command_contexts
import command_handlers


def main():
    arguments = argument_parsing.build_argument_parser().parse_args()
    context = command_contexts.build_context_for_command(arguments.command)
    handler = command_handlers.COMMAND_HANDLERS[arguments.command]
    try:
        handler(context, arguments)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
    except urllib.error.HTTPError as error:
        print(
            f"{error.code} from {error.url}: {error.read().decode(errors='replace')}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error
    except urllib.error.URLError as error:
        print(f"cannot reach media service: {error.reason}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
