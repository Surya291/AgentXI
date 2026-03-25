# Hermes Setup via LiteLLM (Gemini API Key)

This setup routes Hermes through a local LiteLLM proxy and authenticates with a Google AI Studio API key (`GEMINI_API_KEY`), so you do not need to manually refresh OAuth tokens.

Flow:

`Hermes -> LiteLLM (localhost:4000) -> Gemini API (AI Studio key)`

## 1) Prerequisites

- Linux VM with shell access
- Hermes already installed and working
- Python 3 + pip available
- A valid Google AI Studio API key

## 2) Create `.env` (Gemini key + local proxy password)

```bash
cd /home/ubuntu/misc/AgentXI/hermes-setup
cp -n .env.example .env   # skip if .env already exists
```

Edit `.env`:

- `GEMINI_API_KEY` — from [Google AI Studio](https://aistudio.google.com/) (`AIza...`).
- `LITELLM_MASTER_KEY` — any long random string; Hermes will use this as `OPENAI_API_KEY` when talking to LiteLLM (not sent to Google).

Optional: `LITELLM_PORT=4000` if you change the port.

After editing, ensure `litellm_config.yaml` exists (created automatically on first `./start_litellm.sh` from `litellm_config.yaml.example`). To change the Gemini model, edit `model:` under `litellm_params` (e.g. `gemini/gemini-3-flash-preview`) and add a matching `model_name` alias if you want a second Hermes model id.

## 3) Install LiteLLM proxy (venv, recommended)

Use the bundled installer so `litellm` is always available to `start_litellm.sh`:

```bash
cd /home/ubuntu/misc/AgentXI/hermes-setup
chmod +x install_litellm.sh start_litellm.sh
./install_litellm.sh
```

This creates `./.venv` and installs `litellm[proxy]` from PyPI.

**Security note:** PyPI `litellm==1.82.8` was reported compromised ([issue #24512](https://github.com/BerriAI/litellm/issues/24512)). After reinstalling, run ` .venv/bin/pip show litellm` and confirm you are on a **maintainer-published safe version** (not 1.82.8). If in doubt, pin in `install_litellm.sh` to an explicit version your team trusts.

Alternative (global user install):

```bash
python3 -m pip install --user "litellm[proxy]"
export PATH="$HOME/.local/bin:$PATH"
```

## 4) Create LiteLLM config

Copy the bundled example (or let `./start_litellm.sh` create `litellm_config.yaml` on first run):

```bash
cp litellm_config.yaml.example litellm_config.yaml
```

Edit `master_key` to match `LITELLM_MASTER_KEY` in `.env` (or rely on `start_litellm.sh` to sync that line).

The example lists four routes with OpenRouter-style client ids: `google/gemini-3-flash-preview`, etc. See `litellm_config.yaml.example` for the full `model_list`.

Notes:
- `model_name` is what Hermes sends as the OpenAI `model` string.
- `master_key` is the local auth key Hermes uses to call LiteLLM.

## 5) Start LiteLLM in background (tmux)

```bash
tmux new -s litellm
cd /home/ubuntu/misc/AgentXI/hermes-setup
./start_litellm.sh
```

`start_litellm.sh` loads `.env`, syncs `master_key`, and runs `.venv/bin/litellm` when the venv exists.

Detach tmux: `Ctrl+b`, then `d`

Reattach later:

```bash
tmux attach -t litellm
```

## 6) Test LiteLLM + Gemini

With `./start_litellm.sh` running in another terminal/tmux:

```bash
cd /home/ubuntu/misc/AgentXI/hermes-setup
chmod +x test_litellm.sh
./test_litellm.sh
```

Or set a different routed model for the test:

```bash
TEST_MODEL=google/gemini-3.1-pro-preview ./test_litellm.sh
```

Manual `curl` (replace `MASTER` with your `LITELLM_MASTER_KEY`):

```bash
curl -sS http://127.0.0.1:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer MASTER" \
  -d '{"model":"google/gemini-3-flash-preview","messages":[{"role":"user","content":"Reply with: LiteLLM OK"}]}'
```

You should see a JSON completion from Gemini. If you get a Gemini/model error, check the `model:` value in `litellm_config.yaml` matches a model your API key can use.

## 7) Point Hermes to LiteLLM

Set these for Hermes:

- `OPENAI_BASE_URL=http://127.0.0.1:4000/v1`
- `OPENAI_API_KEY=<your litellm master_key>`
- Model/provider should use custom endpoint; default model id: `google/gemini-3-flash-preview`

Example:

```bash
export OPENAI_BASE_URL="http://127.0.0.1:4000/v1"
export OPENAI_API_KEY="change-this-to-a-strong-local-key"
```

Then in Hermes:
- Run `hermes chat`
- Default model id: `google/gemini-3-flash-preview`

### Switch models in Hermes

In interactive chat, the slash command is:

```text
/model <model-name>
```

Examples (must match `model_name` in `litellm_config.yaml`):

```text
/model google/gemini-3-flash-preview
/model google/gemini-3.1-pro-preview
/model google/gemini-3.1-flash-image-preview
/model google/gemini-3.1-flash-lite-preview
```

You can also pass a one-off model on the CLI:

```bash
hermes chat --model google/gemini-3.1-pro-preview
```

Provider-prefixed form works when multiple providers are configured:

```text
/model custom:google/gemini-3-flash-preview
```

## 8) Telegram gateway (optional)

Run Hermes gateway in a separate tmux session:

```bash
tmux new -s hermes-tg
export OPENAI_BASE_URL="http://127.0.0.1:4000/v1"
export OPENAI_API_KEY="change-this-to-a-strong-local-key"
hermes gateway telegram
```

Detach with `Ctrl+b`, then `d`.

Recommended:
- Session 1: `litellm`
- Session 2: `hermes-tg`

## 9) Quick troubleshooting

- `401 Unauthorized` from LiteLLM:
  - Check `OPENAI_API_KEY` in Hermes matches LiteLLM `master_key`.
- Gemini auth errors:
  - Verify `GEMINI_API_KEY` is exported in the LiteLLM process environment.
- Connection refused on `127.0.0.1:4000`:
  - LiteLLM is not running, wrong port, or crashed.
- Model not found:
  - Confirm the `model` string matches a `model_name` in `litellm_config.yaml` (e.g. `google/gemini-3-flash-preview`).
