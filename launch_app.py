# launch_app.py
import os, sys, traceback, shutil
from datetime import datetime

ENTRY = "Automatisation_RH.py"   #  Streamlit entry file

def project_dir():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))

def ensure_dir(p):
    os.makedirs(p, exist_ok=True); return p

def log_and_pause(e):
    out_dir = ensure_dir(os.path.join(project_dir(), "output_documents"))
    with open(os.path.join(out_dir, "launch_error.log"), "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] {e}\n")
        f.write(traceback.format_exc() + "\n")
    if getattr(sys, "frozen", False):
        os.system("pause")

def main():
    base = project_dir()
    run_base = getattr(sys, "_MEIPASS", base)

    # Work from bundled resources so data/ works as-is
    os.chdir(run_base)
 
    # Copy ENTRY (and pages/) to a local, writable folder next to the exe
    run_src = ensure_dir(os.path.join(base, "_run_src"))
    entry_src = os.path.join(run_base, ENTRY)
    entry_dst = os.path.join(run_src, ENTRY)
    shutil.copy2(entry_src, entry_dst)

    pages_src = os.path.join(run_base, "pages")
    pages_dst = os.path.join(run_src, "pages")
    if os.path.isdir(pages_src):
        # fresh copy to keep it in sync
        if os.path.exists(pages_dst):
            shutil.rmtree(pages_dst, ignore_errors=True)
        shutil.copytree(pages_src, pages_dst)

    # Force production mode & normal UI port
    # os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    # os.environ.setdefault("STREAMLIT_SERVER_PORT", "8501")
    # os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", "127.0.0.1")  # or "0.0.0.0" for LAN

    # Run Streamlit on the copied script (safe path)
    from streamlit.web import cli as stcli
    sys.argv = [
        "streamlit", "run", entry_dst,
        "--server.port", "8501",
        "--server.address", "127.0.0.1",
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false",
        "--global.developmentMode", "false",
    ]
    raise SystemExit(stcli.main())

if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        log_and_pause(e)
        raise
