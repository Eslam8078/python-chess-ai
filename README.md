# Python Chess Game

A desktop chess game built with Python and Pygame, including a minimax-based AI opponent.

## Features

- Human vs AI gameplay
- Legal chess move generation
- Check, checkmate, and stalemate detection
- Castling
- En passant
- Pawn promotion to Queen, Rook, Bishop, or Knight
- Move undo and game reset
- Alpha-beta pruning in the AI search
- Automated tests
- GitHub Actions CI

## Requirements

- Python 3.10+
- Pygame 2.6+

## Setup

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

Linux or macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the game:

```bash
python main.py
```

## Development

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
```

## Controls

- Left click: select and move pieces
- Q, R, B, N: choose a promotion piece
- Backspace: undo the last move
- R: reset the game
- Esc: exit

## Project Structure

```text
python-chess-game/
├── assets/
│   └── chess/
├── chess_game/
│   ├── __init__.py
│   ├── ai.py
│   └── engine.py
├── tests/
│   └── test_engine.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── main.py
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```
