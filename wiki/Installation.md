# Installation Guide

CRML is split into two Python packages:

- `crml-lang` (language/spec): models + schema + validation + YAML IO
- `crml-engine` (engine): simulation runtime + `crml` CLI

## Quick install

If you want the CLI:

```bash
pip install crml-engine
```

If you only want the language library:

```bash
pip install crml-lang
```

Verify the CLI install with:

```bash
crml --help
```

---

## Platform-Specific Instructions

### macOS

**Option 1: Using pip (Recommended)**
```bash
# Install Python 3.9+ if needed
brew install python3

# Install CRML engine + CLI
pip3 install crml-engine

# Verify
crml --help
```

**Option 2: Using pipx (Isolated)**
```bash
# Install pipx
brew install pipx
pipx ensurepath

# Install CRML engine + CLI
pipx install crml-engine

# Verify
crml --help
```

---

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python 3.9+
sudo apt install python3 python3-pip

# Install CRML engine + CLI
pip3 install crml-engine

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify
crml --help
```

---

### Windows

**Option 1: Using pip**
```powershell
# Install Python 3.9+ from python.org

# Install CRML engine + CLI
pip install crml-engine

# Verify
crml --help
```

**Option 2: Using Windows Terminal**
```powershell
# Install Python from Microsoft Store
# Then:
pip install crml-engine
```

---

## CRML Studio Setup

### Prerequisites
- Node.js 18+ and npm
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/Faux16/crml.git
cd crml/web

# Install dependencies
npm install

# Run development server
npm run dev
```

Visit http://localhost:3000

---

## Troubleshooting

See [Troubleshooting Guide](Reference/Troubleshooting) for common issues.
