# ✨ Backend Setup

Clone this repo:

```bash
git clone https://github.com/yourusername/yourrepo.git
```

**You do not need Python installed on your computer!** `uv` will handle it for us :)

> [!CAUTION]
> NEVER EVER RUN `pip install` MANUALLY.

### 1. Install `uv`

`uv` manages Python versions, virtual environments, and dependencies all in one place. Install `uv` with brew (Mac only) or run this in your terminal (Windows & Mac):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your terminal. You can verify the install with `uv --version`.

### 2. Sync dependencies

In the `backend` folder, run:

```bash
uv sync
uv run pre-commit install
```

This will install the correct Python version, create a local virtual environment, and install the dependencies in `pyproject.toml`.

**You may need to re-sync periodically, when others add new dependencies.**

### 3. Run the server

To start the backend, run:

```bash
uv run uvicorn app.main:app --reload
```

Our backend server will be available at [localhost:8000](http://localhost:8000) 🤩🎉💃

Our API documentation + sandbox is also available at [localhost:8000/docs](http://localhost:8000/docs) 🤓

## 🐍 Development

### CV, ML, and Hardware

There are specific folders for you! Please write your code & keep your files in the right place so the codebase can stay organized :)

To run a specific Python file:

```bash
uv run python file_with_code.py
```

(Make sure you're in the right directory!)

Your functions will be imported and used in the FastAPI endpoints 😎

### Adding a new dependency

```bash
uv add package_name_here
```

No need to re-sync as `uv` will do it for you.

### Code Formatting

If you get an error `Git: black....................................................................Failed`, this is the formatter doing its job ;3 It will automatically format your file, just stage the update and commit again.
