# 📊 WebAPI CLI Tool

A simple and powerful CLI tool to turn your local **CSV/XLSX files** into a **FastAPI-powered web API** — instantly!

Serve your data locally and access:
- All rows: `http://localhost:3000`
- Specific column: `http://localhost:3000/column_name`
- Specific row & column: `http://localhost:3000/column_name?row_id=2`

---

## 🚀 Features

- 📁 Load `.csv` or `.xlsx` files
- 🌐 Serve data as a local API
- ✅ CLI control: `serve`, `terminate`, `check`
- 🧠 Auto-setup dependencies and virtual environments
- 💡 Built with FastAPI + Typer

---

## 📦 Installation

### Option 1: From Source

Clone this repo and install it:

```bash
git clone https://github.com/yourusername/webapi-cli.git
cd webapi-cli
pip install "fastapi[standard]" typer pandas pydantic
```
## Uses(Make sure you are in the main.py project directory in terminal)
1. ```python main.py webapi check``` to check the installed packages
2. ```python main.py webapi serve file="D:\Python_Space\FastAPI\data\sample.csv"``` to run the server if passed from check command.
3. **Ctrl+C** OR **q and Enter** OR ```python main.py webapi termintate``` to terminate the running server.
