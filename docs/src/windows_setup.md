# Windows Setup (Running Locally)

## Introduction

This guide explains how to run VulcanLab locally on Windows. You might want to run it locally if you're:

* Contributing to VulcanLab development
* Already running a PostgreSQL database (with pgvector) that you'd like to use
* Experimenting with the source code for optimizations or customizations
* Troubleshooting issues with the Docker version

**Note:** If you just want to get VulcanLab up and running quickly on Windows (or any other OS), we recommend using the [Docker installation](./docker_setup.md) instead.

## Why Use WSL?

We strongly recommend running VulcanLab through Windows Subsystem for Linux (WSL) rather than directly on Windows:

* AI coding assistants (Cursor, Claude, Antigravity, Codex) perform significantly better in Linux environments
* All recent tests and Python code are optimized for Linux
* You'll have a smoother development experience overall

## Step 1: Install WSL on Windows

**Recommended:** Install Ubuntu 24.04 LTS (or the latest 24.xx version). This is the version we actively use and test with.

**Avoid:** Older Ubuntu versions (like 18.04) may cause compatibility issues due to outdated Python versions.

**Installation:**
Follow Microsoft's official WSL installation guide: [Install WSL](https://learn.microsoft.com/en-us/windows/wsl/install)

Quick installation (run in PowerShell as Administrator):
```powershell
wsl --install -d Ubuntu-24.04
```

After installation, restart your computer and launch Ubuntu from your Start menu.

## Step 2: Install Prerequisites in WSL

Once you're in your WSL Ubuntu terminal, install the following prerequisites:

### 1. Python 3.10 or Higher

Ubuntu 24.04 comes with Python 3.12 by default, which is perfect for VulcanLab. You may want to create a convenient alias so you can use `python` instead of `python3`:

```bash
# Install the python-is-python3 package (optional but recommended)
sudo apt install python-is-python3

# Verify Python version (should be 3.10 or higher)
python --version
```

### 2. Pip and Venv

Ubuntu may not include pip and venv by default. Install them with:

```bash
sudo apt update
sudo apt install python3-pip python3-venv
```

### 3. Node.js and npm

VulcanLab's frontend requires Node.js and npm. We **strongly recommend** using `nvm` (Node Version Manager) instead of the Ubuntu package, as it gives you better version control and typically includes `npx` by default.

#### Option A: Install via nvm (Recommended)

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Close and reopen your terminal, or run:
source ~/.bashrc

# Install the latest LTS version of Node.js
nvm install --lts

# Verify installation
node --version
npm --version
npx --version
```

#### Option B: Install via apt (if you prefer)

If you choose to use Ubuntu's package manager, you'll need to ensure `npx` is properly configured:

```bash
# Install Node.js and npm
sudo apt update
sudo apt install nodejs npm

# Install npx globally (STRONGLY RECOMMENDED)
sudo npm install -g npx

# Verify installation
node --version
npm --version
npx --version
```

**Important:** If `npx` doesn't work after installation, you need to add npm's global bin directory to your PATH:

```bash
# Add to your shell configuration file
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.zshrc

# Configure npm to use a different directory for global packages
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'

# Reload your shell configuration
source ~/.bashrc  # or source ~/.zshrc if using zsh

# Reinstall npx to the new location
npm install -g npx

# Verify npx is now in your PATH
which npx
npx --version
```

If you're using `zsh` as your shell (check with `echo $SHELL`), make sure to reload `.zshrc`:
```bash
source ~/.zshrc
```

### 4. Additional Utilities (Optional)

Some helpful tools for development:

```bash
# Git (usually pre-installed, but just in case)
sudo apt install git

# Build tools (may be needed for some Python packages)
sudo apt install build-essential
```

## Step 3: Access Your VulcanLab Code

You have two options for accessing your VulcanLab code in WSL:

### Option A: Clone Directly in WSL (Recommended)

Clone the repository directly into your WSL file system for better performance:

```bash
# Navigate to your home directory
cd ~

# Create a projects folder
mkdir -p projects
cd projects

# Clone VulcanLab
git clone https://github.com/yourusername/vulcanlab.git
cd vulcanlab
```

### Option B: Access Windows Files from WSL

If you already have VulcanLab cloned in Windows, you can access it from WSL:

```bash
# Windows drives are mounted at /mnt/
cd /mnt/c/path/to/your/vulcanlab
```

**Note:** Option A is recommended for better performance, as accessing Windows files from WSL can be slower.

## Next Steps: Running VulcanLab

Now that WSL is set up with all the prerequisites, you're ready to run VulcanLab!

Follow the complete setup instructions in [Running Locally](./running_locally.md), which covers:

* Setting up PostgreSQL (Docker or local)
* Configuring your Python virtual environment
* Installing dependencies
* Setting up environment variables
* Initializing the database
* Running the backend and frontend servers

The instructions in [running_locally.md](./running_locally.md) work perfectly in WSL—just follow them as if you were on a native Linux system.

## Accessing VulcanLab from Windows

Once VulcanLab is running in WSL, you can access it from your Windows browser:

* **Frontend:** http://localhost:3000
* **Backend API:** http://localhost:8000
* **API Docs:** http://localhost:8000/docs

WSL automatically forwards ports, so services running in WSL are accessible from Windows!

## Tips for Working with WSL

### File System Access

* Access WSL files from Windows File Explorer: `\\wsl$\Ubuntu-24.04\home\yourusername`
* Access Windows files from WSL: `/mnt/c/Users/YourUsername`

### VS Code Integration

Install the "WSL" extension in VS Code to seamlessly edit files and run terminals in WSL:

```bash
# From WSL terminal, in your project directory
code .
```

This opens VS Code with direct WSL integration.

### Restart WSL

If you need to restart WSL:

```powershell
# In PowerShell
wsl --shutdown
```

Then relaunch Ubuntu from your Start menu.

---

**Ready to continue?** Head over to [Running Locally](./running_locally.md) to complete your VulcanLab setup!