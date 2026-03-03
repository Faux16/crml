#!/bin/bash
# CRML Code for Cyber Risk - Enhanced Installation Script

set -e

echo "🚀 Installing CRML Code for Cyber Risk..."

# 1. Flexible Python Detection
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Verify if 'python' is actually version 3
    if python --version 2>&1 | grep -q "Python 3"; then
        PYTHON_CMD="python"
    else
        echo "❌ Error: Python 3 is not installed or not in PATH."
        exit 1
    fi
else
    echo "❌ Error: python3/python is not installed."
    exit 1
fi

echo "✅ Found: $($PYTHON_CMD --version)"

# 2. Handle Remote Installation (Download Source)
if [ ! -d "crml_lang" ] || [ ! -d "crml_engine" ]; then
    echo "🌐 Remote session detected. Downloading source files..."
    
    # Try to infer host from command if possible, or ask
    DEFAULT_HOST="192.168.1.18"
    echo "Host IP required to download source bundle."
    printf "Enter the Host IP [%s]: " "$DEFAULT_HOST"
    read -r HOST_IP < /dev/tty
    HOST_IP=${HOST_IP:-$DEFAULT_HOST}
    
    # Create directory and move into it
    mkdir -p crml_install
    cd crml_install
    
    echo "📥 Fetching source from http://$HOST_IP:8000/crml_source.tar.gz..."
    # Use curl or wget
    if command -v curl &> /dev/null; then
        curl -L "http://$HOST_IP:8000/crml_source.tar.gz" -o crml_source.tar.gz
    else
        wget "http://$HOST_IP:8000/crml_source.tar.gz"
    fi
    
    tar -xzf crml_source.tar.gz
    echo "📦 Source extracted successfully."
fi

# 3. Setup Virtual Environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
fi

source .venv/bin/activate

# 4. Install Dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -e ./crml_lang -e ./crml_engine
pip install openai python-dotenv pyyaml rich

# 5. Create executable link
echo "🔗 Linking crml-cli command..."
INSTALL_DIR="/usr/local/bin"
if [ -w "$INSTALL_DIR" ] && [ "$EUID" -eq 0 ]; then
    cat <<EOF > "$INSTALL_DIR/crml-cli"
#!/bin/bash
source "$(pwd)/.venv/bin/activate"
python3 "$(pwd)/scripts/crml_cli.py" "\$@"
EOF
    chmod +x "$INSTALL_DIR/crml-cli"
    echo "✅ Success! You can now run 'crml-cli' from anywhere."
else
    echo "⚠️  Warning: Creating local runner instead."
    cat <<EOF > "crml-cli"
#!/bin/bash
source "$(pwd)/.venv/bin/activate"
python3 "$(pwd)/scripts/crml_cli.py" "\$@"
EOF
    chmod +x "crml-cli"
    echo "✅ Success! Run the tool using './crml-cli'"
fi

echo "---"
echo "🛠️  Setup complete."
echo "👉 Start modeling: ./crml-cli"
