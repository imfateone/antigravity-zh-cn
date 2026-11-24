"""Assemble the offline Electron preload from packaged JavaScript modules."""

from pathlib import Path

_RENDERER_DIR = Path(__file__).with_name("renderer")


def _renderer_source(filename):
    return (_RENDERER_DIR / filename).read_text(encoding="utf-8")


# The marker also identifies an older injected block during a patch update.
DOM_TRANSLATOR_INJECTION = (
    "// Antigravity Chinese Localization Engine\n(() => {\n"
    + "\n".join(
        _renderer_source(name)
        for name in (
            "catalog.js",
            "formatters.js",
            "antigravity_dom.js",
            "mount_walk.js",
            "portal_registry.js",
            "engine.js",
        )
    )
    + "\n})();\n"
)
MENU_TRANSLATOR_INJECTION = _renderer_source("menu.js")
SYSTEM_PROXY_INJECTION = _renderer_source("system_proxy.js")
