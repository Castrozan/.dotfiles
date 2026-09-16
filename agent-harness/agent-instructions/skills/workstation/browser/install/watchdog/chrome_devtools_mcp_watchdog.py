from __future__ import annotations

import kill_runaway_chrome_devtools_mcp_instances
import reap_orphaned_chrome_devtools_mcp_instances


def main():
    reap_orphaned_chrome_devtools_mcp_instances.main()
    kill_runaway_chrome_devtools_mcp_instances.main()


if __name__ == "__main__":
    main()
