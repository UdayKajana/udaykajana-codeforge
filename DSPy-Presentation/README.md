# DSPy Presentation Demo

This folder contains a small interactive webpage demonstrating a comparison between a traditional prompt-based extraction pipeline (Pipeline A) and a simulated DSPy-based pipeline (Pipeline B).

Files added:
- `index.html` — interactive UI (two horizontal halves, pipelines A/B)
- `styles.css` — UI styling
- `app.js` — client-side interaction and simulated outputs
- `data/email.json` — sample Japanese bid email (human-like, with omissions)
- `dspy/dspy_demo.py` — illustrative DSPy demo module (Python)
- `dspy/golden_examples.json` — small golden set for optimizer
- `dspy/run_simulation.json` — simulated DSPy extraction output shown by UI

Run the backend server and open the page in a browser to view live pipeline output. The page shows stages for each pipeline; clicking any stage updates the shared email view and the two pipeline panels.

Start the server with:

```bash
python server.py
```

Then open:

```bash
http://127.0.0.1:8000/
```

The server executes both pipelines on the shared email input and returns actual output on demand. If `dspy` or `openai` are not installed, the backend falls back to the illustrative local demo implementation.

Real-time pipelines script
-------------------------
A helper script `run_pipelines.py` is included to run both pipelines from the command line.

Usage (fallback/mocked mode if dependencies are missing):
```bash
python run_pipelines.py --email data/email.json
```

If you have an OpenAI API key and a real `dspy` installation, set `OPENAI_API_KEY` in your environment and the script will attempt to run with the real services; otherwise it will fall back to the illustrative `dspy_demo.py` implementation.

Install suggested packages:
```bash
pip install -r requirements.txt
```

