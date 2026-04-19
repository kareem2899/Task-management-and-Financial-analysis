# 🤖 AI Assistant Setup Guide (Free — No API Key Needed)

The AI chat uses **Ollama** — a free tool that runs AI models
100% locally on your Mac. No internet, no subscription, no API key.

---

## Step 1 — Install Ollama

Go to https://ollama.com and download the macOS app,
OR run this in Terminal:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

## Step 2 — Pull the AI model (one-time download ~2 GB)

```bash
ollama pull llama3.2
```

`llama3.2` is Meta's fast 3B model — great for Q&A.
It downloads once and runs offline forever after.

**Alternative models (if you want a different one):**
| Model | Size | Speed | Quality |
|---|---|---|---|
| `llama3.2`  | ~2 GB | ⚡ Fast   | ✅ Good (default) |
| `mistral`   | ~4 GB | 🔁 Medium | ✅ Good |
| `llama3`    | ~5 GB | 🐢 Slower | ⭐ Best  |
| `phi3`      | ~2 GB | ⚡ Fast   | ✅ Good  |

To switch models, open `ai_chat_tab.py` and change line:
```python
OLLAMA_MODEL = "llama3.2"   # ← change this
```

---

## Step 3 — Start Ollama before using TaskFlow

**Option A:** Open the Ollama app from Applications (it runs in the menu bar).

**Option B:** Run in Terminal:
```bash
ollama serve
```

Keep this Terminal window open while using TaskFlow.

---

## Step 4 — Run TaskFlow normally

```bash
cd ~/Desktop/taskflow
source venv/bin/activate
python3 main.py
```

Click **🤖 AI Assistant** in the sidebar and start chatting!

---

## Troubleshooting

**"Cannot reach Ollama"** error in chat:
→ Ollama is not running. Start it: `ollama serve`

**Model is slow the first message:**
→ Normal — it loads into memory. Subsequent replies are faster.

**Want to check Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```
Should return a JSON list of your downloaded models.

---

## Privacy

Everything runs **100% on your Mac**. Your task data, financial data,
and questions never leave your computer. No cloud, no logging.
