## MindSafe

MindSafe is a full-stack system and Chrome extension that analyzes YouTube and YouTube Kids videos to estimate how healthy they are for a child’s mental and emotional development. It turns a complex AI pipeline into a simple 1–10 score and rich breakdown that parents can see directly on YouTube.

---

## Why MindSafe Exists

Online video is a huge part of childhood today. It can be:

- **Deeply positive**: calm pacing, clear stories, kind language, strong social–emotional modeling.
- **Quietly harmful**: hyper-fast cuts, constant shouting, manipulative hooks, “brainrot” humor, or themes that are confusing or emotionally intense for young kids.

Most platforms focus on **content category** (kid vs. not kid) but **not** on the _developmental quality_ of what a child is watching. A video can be “kid-friendly” and still be:

- Overstimulating for a 4‑year‑old.
- Emotionally confusing or scary.
- Teaching social dynamics that are harsh, sarcastic, or unkind.

MindSafe tries to fill that gap. It doesn’t replace parenting or clinical judgment, but it gives families a **fast, evidence‑inspired signal** about how a video might impact a young mind.

---

## What MindSafe Does

- **Analyzes YouTube / YouTube Kids videos** given a URL and a child’s age.
- **Downloads and processes the video** (audio + visuals) locally for privacy.
- **Transcribes the audio** with a local Whisper model (no cloud upload of raw audio).
- **Computes a set of metrics**, including:
  - Overall **Developmental Score (0–100)** – higher is better.
  - **Brainrot Index (0–100)** – higher means more risk of negative impact (overstimulation, low-quality engagement).
  - **Dimension scores**:
    - Pacing (calm vs. chaotic)
    - Story / Narrative coherence
    - Language (kind vs. harsh/explicit)
    - Social‑Emotional Learning (SEL)
    - Fantasy balance (imagination vs. confusion)
    - Interactivity / call‑to‑action style
- **Maps everything into a 1–10 MindSafe rating** with an interpretation label like “Highly suitable”, “Moderately suitable”, or “Not recommended”.
- **Displays the score directly in YouTube** via a Chrome extension sidebar card and popup.

The goal is **speed + decent accuracy**: fast enough to use in real time, but grounded in real signals (transcripts, pacing metrics, heuristics, and optional LLM semantics) instead of random guesses.

---

## High-Level Architecture

MindSafe consists of several coordinated parts:

- **Chrome extension (`chrome_extension/`)**

  - Injects a **MindSafe card** into YouTube / YouTube Kids watch pages.
  - Sends the current video URL to the local API.
  - Polls for the latest evaluation and renders:
    - Big 1–10 score badge (color‑coded green/orange/red).
    - Label (e.g., “Highly suitable”).
    - Expanded breakdown with all dimension scores.

- **AI evaluation API (`ai-agents/`)**

  - Flask API on `http://localhost:5001` with endpoints like `GET /evaluate?url=...&age=...`.
  - Downloads the video (via `yt-dlp`), extracts audio/video tracks, and runs the evaluation pipeline.
  - Uses **local Whisper** for transcription and a combination of:
    - Heuristic metrics (keyword patterns, pacing, structure).
    - Embeddings / semantic metrics (optionally via OpenRouter + Gemini models).
  - Returns a structured JSON object with all scores and metrics.

- **Frontend + backend web app (`frontend/` + `backend/`)**
  - Minimal Flask app that serves a landing page and basic UI.
  - Useful for demos outside the browser extension context.

---

## Technical Stack

- **Languages & Frameworks**

  - Python (Flask API, AI pipeline)
  - JavaScript (Chrome extension, frontend behavior)
  - HTML/CSS (popup UI, sidebar styling)

- **AI / Data Processing**

  - **Whisper (local)** for speech‑to‑text transcription (no raw audio sent to the cloud).
  - **yt-dlp** for reliable YouTube / YouTube Kids video download.
  - **FFmpeg** for audio and video track extraction.
  - **Heuristic and embedding‑based metrics** for semantics and narrative coherence.
  - **OpenRouter + Gemini** (optional, via `evaluation/llm_client.py`) for deeper semantic labeling.

- **Infrastructure / Integrations**
  - **Snowflake (optional)** for logging evaluation results at scale (video URL, scores, full JSON result) so you can build dashboards or run research on how kids’ content has changed.
  - **Vultr cloud (optional)** as a remote worker target:
    - You can run a copy of the `ai-agents` API on a powerful Vultr instance.
    - A local API can **forward evaluations** to the Vultr worker when configured, speeding up scoring for heavier models.

---

## End-to-End Workflow

### 1. User watches a video

- The user opens a **YouTube** or **YouTube Kids** watch page.
- The MindSafe **content script** detects that this is a `/watch` page and:
  - Injects the MindSafe card into the right column.
  - Sends a `NEW_VIDEO` message with the video URL to the background service worker.

### 2. Background service worker calls the API

- The background script:
  - Stores a **pending** `lastScore` (status `pending`) in memory and in `chrome.storage.local` so the UI can immediately show “Analyzing…”.
  - Calls `http://localhost:5001/evaluate?url=...&age=...` with the configured child age.

### 3. AI pipeline runs (locally or on Vultr)

Inside `ai-agents/api.py` and `evaluation/`:

- **Download & extract**

  - `yt-dlp` downloads the video.
  - `ffmpeg` extracts:
    - `video_with_audio.mp4`
    - `audio_only.m4a`
    - `video_no_audio.mp4` (muted video)

- **Transcription (Whisper)**

  - The audio is chunked and transcribed locally using Whisper.
  - Chunks are combined into a full transcript for downstream analysis.

- **Metrics & scoring**

  - Audio pacing and rhythm features.
  - Simple shot/segment structure (time‑based segmentation).
  - Heuristic metrics on the transcript (e.g., intensity, language style, SEL cues).
  - Optional LLM‑based semantics via OpenRouter if enabled.
  - All metrics are combined into:
    - `dev_score` (0–100).
    - `brainrot_index` (0–100).
    - `dimension_scores` for Pacing, Story, Language, SEL, Fantasy, Interactivity.
    - A 1–10 MindSafe rating + human‑readable label.

- **Optional: Cloud acceleration & logging**
  - If configured, a remote Vultr worker can handle the heavy evaluation instead of your local machine.
  - Snowflake can asynchronously receive a copy of each result for analytics and research.

### 4. Results flow back to the extension

- The API returns JSON to the background service worker.
- The background script:

  - Enriches the result with label + reasons.
  - Stores it as the new `lastScore` (in memory + `chrome.storage.local`).
  - Broadcasts a `SCORE_UPDATED` message to all YouTube tabs.

- The **content script**:

  - Receives `SCORE_UPDATED` and re‑renders the MindSafe card.
  - Shows a big **X / 10** score badge with colors:
    - Green: generally very supportive and age‑appropriate.
    - Orange: mixed, good with some caution or supervision.
    - Red: likely overstimulating, confusing, or emotionally intense for young kids.
  - On click, it expands to show all dimension scores and context.

- The **popup**:
  - Reads `lastScore` from storage and shows a **compact dashboard** for the last analyzed video.

---

## Why This Matters for Children’s Mental Health

Children’s brains are still wiring up their attention, emotion regulation, and understanding of relationships. Video content can either:

- Support that development: gentle pacing, clear cause‑and‑effect, kind language, healthy problem‑solving.
- Undermine it: constant dopamine spikes, aggressive or mocking social dynamics, confusing fantasy vs. reality, or “always on” stimulation with no downtime.

MindSafe is built around that reality:

- It does **not** just ask “Is this kid content?” but “**Is this likely to be mentally healthy for this specific age?**”
- It treats **brainrot** not as a joke but as a rough index of:
  - Overstimulation and frenetic pacing.
  - Low‑quality engagement vs. learning or reflection.
  - Repeated patterns that may encourage addictive viewing rather than balanced habits.

This tool is not a diagnosis or a replacement for parenting, but it can:

- Help parents quickly triage what kids are watching.
- Start better conversations about “why this video feels good or not‑so‑good”.
- Provide researchers and clinicians (via logs, if enabled) with a starting point for studying the impact of modern kids’ media.

---

## Getting Started (High-Level)

At a high level you will:

1. **Set up the AI API** (`ai-agents/`)

   - Create and activate a Python virtual environment.
   - Install dependencies from `ai-agents/requirements.txt`.
   - Configure `.env` (OpenRouter key if using LLM, optional Snowflake / Vultr envs).
   - Run `python api.py` to start the Flask server on `http://localhost:5001`.

2. **Load the Chrome extension** (`chrome_extension/`)

   - Go to `chrome://extensions` → enable **Developer mode**.
   - Click **Load unpacked** and select the `chrome_extension` folder.

3. **Open YouTube / YouTube Kids and watch a video**
   - The MindSafe card appears in the right column.
   - After processing, you’ll see the 1–10 score and can expand the details.

For more technical detail and API usage, see the documentation inside `ai-agents/` (e.g., `API_README.md`, `RUN_API.md`, and `MINDSAFE_SCORES.md`).

---

## Future Potential

MindSafe is intentionally modular and has room to grow:

- **Smarter models**: swap in stronger LLMs or domain‑specific models as they emerge.
- **Personalized profiles**: tune thresholds for specific ages, sensitivities, or neurodivergent kids.
- **Richer dashboards**: leverage Snowflake logs to build visuals showing trends over time.
- **Cross‑platform support**: extend the extension and pipeline beyond YouTube / YouTube Kids.

Most importantly, it is a step toward treating kids’ mental health as **first‑class** in product design—not an afterthought.
