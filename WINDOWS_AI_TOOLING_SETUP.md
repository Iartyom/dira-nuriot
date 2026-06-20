# Windows AI Tooling Setup

Use this guide when preparing a new project for Codex or another coding agent on Windows.

## Instructions for the agent

1. Run commands from PowerShell.
2. Check whether each tool is already installed before installing it.
3. Use exact Winget package IDs.
4. Install Python packages inside the project's virtual environment, never globally.
5. Do not assume that installing Repomix, Tiktoken, or ChromaDB makes the agent use them automatically.
6. Never include secrets, `.env` files, credentials, build output, or dependency folders in generated context bundles.

## What is actually needed?

Do not install every tool blindly. The right set depends on the project and task.

| Tool | Required? | Install when | Skip when | Automatic after installation? |
|---|---|---|---|---|
| Node.js LTS | Project-dependent | The project uses JavaScript/TypeScript, npm, or Repomix | The project needs none of those | No; it provides the `node`, `npm`, and `npx` runtimes |
| Python 3.11 | Project-dependent | The project uses Python, Tiktoken, or ChromaDB | The project is not Python-based and does not need those libraries | No; it provides the Python runtime |
| Ripgrep (`rg`) | Strongly recommended | Almost every code repository | Only when it is already supplied by the environment | Usually yes; coding agents commonly choose it for searches |
| fd | Optional | The repository is large or frequent filename searches are needed | Built-in file search or `rg --files` is sufficient | Not necessarily; the agent must choose to call it |
| jq | Optional | JSON files or API responses need filtering | The task does not process JSON | No; it must be called explicitly |
| Repomix | Optional | A repository snapshot must be sent to a model or archived as model context | The agent can inspect the repository directly, or only a few files matter | No; run it explicitly |
| Tiktoken | Optional | A script needs approximate OpenAI-model token counts | No token measurement is required | No; application or utility code must import it |
| ChromaDB | Advanced and optional | The project is implementing local semantic search or RAG over many documents | Normal code search is sufficient, or no embedding/indexing pipeline exists | No; it requires indexing, embeddings, storage, and retrieval code |

### Recommended minimal installation

For ordinary Codex work, the useful minimum is:

```text
Ripgrep
Node.js LTS only for Node projects or Repomix
Python only for Python projects
```

`rg --files` can often replace `fd`, so `fd` is a convenience rather than a requirement. `jq` is valuable only for JSON-heavy work. Repomix, Tiktoken, and ChromaDB solve specialized problems and should not be treated as mandatory setup.

### Important distinction

Installation only makes a tool available. It does not add the tool to Codex's context and does not force Codex to use it. CLI tools can be invoked by an agent when appropriate; Python libraries require code that imports and integrates them.

## 1. Install global prerequisites

Check the existing installations:

```powershell
node --version
npm --version
python --version
py -0p
rg --version
fd --version
jq --version
repomix --version
```

Install only missing tools:

```powershell
winget install --id OpenJS.NodeJS.LTS --exact
winget install --id Python.Python.3.11 --exact
winget install --id BurntSushi.ripgrep.MSVC --exact
winget install --id sharkdp.fd --exact
winget install --id jqlang.jq --exact
npm install --global repomix
```

Close and reopen PowerShell after installing Node.js or Python so that updated PATH entries are loaded.

## 2. Create the project Python environment

From the project root, prefer Python 3.11 explicitly:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

If an old Windows Python Launcher misidentifies Python 3.11 or `py -3.11` fails, locate it with:

```powershell
py -0p
```

Then invoke the Python 3.11 executable directly. A common per-user installation path is:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

The version must report `Python 3.11.x`. If `.venv` was accidentally created with an older Python, deactivate and recreate it:

```powershell
deactivate
Remove-Item -Recurse -Force .venv
& "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Install project Python packages

With `(.venv)` visible in the PowerShell prompt:

```powershell
python -m pip install --upgrade pip
python -m pip install tiktoken chromadb
```

Verify the installation:

```powershell
python -c "import tiktoken, chromadb; print('Tiktoken and ChromaDB are ready')"
```

If the project should reproduce these dependencies elsewhere, add them to its dependency file, such as `requirements.txt` or `pyproject.toml`, using the project's existing dependency-management convention.

## 4. How the tools should be used

### Ripgrep (`rg`)

Use it as the default tool for targeted code searches. It respects `.gitignore` and avoids reading unrelated files.

```powershell
rg -n -C 3 "loadConfig" .\src
```

### fd

Use it to locate relevant files quickly:

```powershell
fd "config" .\src
fd --extension json
```

### jq

Use it to reduce large JSON documents before placing them in model context:

```powershell
Get-Content .\package.json | jq '{name, scripts, dependencies}'
```

Normal `rg` output is plain text and must not be piped directly into `jq`. Request JSON output first:

```powershell
rg --json "loadConfig" .\src |
  jq 'select(.type == "match") | {file: .data.path.text, line: .data.line_number, text: .data.lines.text}'
```

### Repomix

Run Repomix only when a consolidated repository snapshot is genuinely useful. Prefer a narrow include pattern over bundling the whole repository:

```powershell
repomix --include "src/**,README.md"
```

Exclude generated and sensitive content as needed:

```powershell
repomix --ignore "**/*.lock,dist/**,coverage/**,.env*,**/node_modules/**,.venv/**"
```

Inspect `repomix-output.xml` before sharing it with any model or external service.

### Tiktoken

Tiktoken is a Python library, not an automatic Codex feature. Use it from a script when token measurement is needed.

### ChromaDB

ChromaDB is also not used automatically. It becomes useful only after the project implements a local indexing and retrieval workflow, including document chunking and embeddings. Do not create a Chroma index unless the task actually benefits from RAG.

## 5. Completion checklist

The setup is complete when:

- `node`, `npm`, `rg`, `fd`, `jq`, and `repomix` return version information.
- `.venv` uses Python 3.11 or another currently supported project version.
- `tiktoken` and `chromadb` import successfully inside `.venv`.
- `.venv/`, Repomix output, local databases, and secrets are excluded from version control when appropriate.
