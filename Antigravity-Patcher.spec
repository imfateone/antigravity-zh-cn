# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH)
package = root / "antigravity_localization"
analysis = Analysis(
    [str(root / "Antigravity-Patcher.py")],
    pathex=[str(root)],
    datas=[(str(package / "renderer"), "antigravity_localization/renderer")],
)
archive = PYZ(analysis.pure)
exe = EXE(
    archive,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    name="Antigravity-Patcher",
    console=True,
)
