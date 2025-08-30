"""Streamlit dashboard to display application logs."""

from __future__ import annotations

import os
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import streamlit as st

DEFAULT_LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))


def iter_log_dirs(base: Path) -> Iterable[Path]:
    """Yield log directories contained in ``base`` sorted newest first."""
    if not base.exists():
        return []
    return sorted([p for p in base.iterdir() if p.is_dir()], reverse=True)


def load_logs(folder: Path) -> dict[str, str]:
    """Return mapping of filename to content for ``folder``."""
    logs: dict[str, str] = {}
    for file in sorted(folder.glob("*.log")):
        try:
            logs[file.name] = file.read_text()
        except OSError as e:  # pragma: no cover - unlikely
            logs[file.name] = f"<error reading file: {e}>"
    return logs


def main() -> None:
    """Render the log dashboard."""
    st.set_page_config(page_title="Log", layout="wide")
    st.title("Log dell'applicazione")

    with st.sidebar:
        st.subheader("Impostazioni")
        log_base = Path(st.text_input("Cartella dei log", value=str(DEFAULT_LOG_DIR)))

        if st.button("Aggiorna ora"):
            st.rerun()

    log_dirs = list(iter_log_dirs(log_base))
    if not log_dirs:
        st.info("Nessun log trovato.")
        return

    import time

    today = datetime.fromtimestamp(time.time(), tz=UTC).date().isoformat()

    for folder in log_dirs:
        with st.expander(folder.name, expanded=True):
            files = load_logs(folder)
            if not files:
                st.info("Nessun file di log.")
                continue
            tabs = st.tabs(list(files))
            for tab, fname in zip(tabs, files, strict=False):
                with tab:
                    st.code(files[fname] or "(empty)", language="text")


if __name__ == "__main__":
    main()
