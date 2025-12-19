# Contributing to CRML

Thank you for your interest in contributing to CRML! We welcome contributions from everyone.

---

## 🛠️ Development Setup

### Prerequisites

- Python 3.9+
- git
- pip

### 1. Fork and Clone

Fork the repository on GitHub, then clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/crml.git
cd crml
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

Install the packages in editable mode with dev dependencies:

```bash
pip install -e ./crml_lang -e ./crml_engine
```

---

## 🧪 Running Tests

We use `pytest` for testing. Ensure you have activated your virtual environment.

### Run All Tests

```bash
pytest
```

### Run Specific Tests

```bash
pytest tests/test_controls.py
```

### Check Coverage

```bash
pytest --cov=crml_lang --cov=crml_engine
```

---

## 💻 Code Style

We follow PEP 8 guidelines. Please ensure your code is formatted correctly.

- **Indent:** 4 spaces
- **Line Length:** 88 characters (Black default)
- **Docstrings:** Google style docstrings

### Running Linters

```bash
# Install linting tools if not already present
pip install black flake8 isort

# Format code
black .
isort .

# Check for issues
flake8 .
```

---

## 📝 Pull Request Process

1. **Create a Branch:**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make Changes:**
   - Write clear, concise code.
   - Add docstrings to new functions/classes.
   - Update `README.md` or documentation if needed.

3. **Add Tests:**
   - If adding a feature, add a test case in `tests/`.
   - Ensure all tests pass with `pytest`.

4. **Commit:**
   - Use clear commit messages (Conventional Commits preferred).
   - Example: `feat: add attack chain validation`

5. **Push and PR:**
   ```bash
   git push origin feature/my-new-feature
   ```
   - Go to GitHub and open a Pull Request against `main`.
   - Describe your changes and link any related issues.

---

## 📄 Documentation

- **Wiki:** If you are adding a major feature, please consider updating the Wiki.
- **Specification:** Changes to the language itself require updating `wiki/Reference/CRML-1.1.md`.

---

## 🐛 Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub:
[https://github.com/Faux16/crml/issues](https://github.com/Faux16/crml/issues)

**Please include:**
- CRML version
- Python version
- Operating system
- Steps to reproduce
- Example YAML model (if applicable)

---

## ⚖️ License

By contributing, you agree that your contributions will be licensed under the MIT License.
