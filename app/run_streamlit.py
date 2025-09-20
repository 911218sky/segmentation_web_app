import sys

try:
    from streamlit import cli as stcli
except Exception:
    try:
        from streamlit.web import cli as stcli
    except Exception:
        stcli = None

if __name__ == "__main__":
    if stcli is None:
        print("Cannot import streamlit.cli")
        sys.exit(1)

    sys.argv = ["streamlit", "run", "app/main.py"]
    sys.exit(stcli.main())