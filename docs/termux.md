# Termux Quick Start

```sh
pkg update
pkg install python git
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
./scripts/termux-run.sh
```

Open `http://127.0.0.1:8010` on the Android device. Browser automation is optional and disabled by default.
