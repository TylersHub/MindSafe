# Children's Video Content Evaluator 🎥👶

**Complete automated system for evaluating YouTube videos for developmental appropriateness**

From YouTube URL to comprehensive evaluation in one command!

## 🚀 Quick Start

### Option 1: Command Line Interface

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run the complete pipeline
python main.py --url "https://youtube.com/watch?v=VIDEO_ID" --age 4
```

### Option 2: REST API

```bash
# 1. Start the API server
python api.py

# 2. Call the API endpoint
curl "http://localhost:5001/evaluate?url=YOUTUBE_URL&age=4"
```

**That's it!** The system will:

- ✅ Download the video from YouTube
- ✅ Extract and transcribe audio
- ✅ Analyze video content with AI
- ✅ Evaluate developmental appropriateness
- ✅ Generate comprehensive scores and recommendations

📖 **For API documentation, see [API_README.md](API_README.md)**

## 📊 What You Get

### Two Main Scores

1. **Development Score (0-100)**

   - Measures positive developmental value
   - Based on age-appropriate content
   - Higher is better

2. **Brainrot Index (0-100)**
   - Measures risk of negative impacts
   - Overstimulation, aggression, confusion
   - Lower is better

### Six Dimension Analysis

- **Pacing**: Visual cuts, motion, audio intensity
- **Story**: Narrative coherence and continuity
- **Language**: Vocabulary richness and complexity
- **SEL**: Social-emotional learning content
- **Fantasy**: Imagination vs reality balance
- **Interactivity**: Viewer engagement

### Complete Output Files

```
outputs/
├── video_with_audio.mp4          # Downloaded video
├── audio_only.m4a                # Audio track
├── speech_transcript.txt         # Speech transcription
├── video_llm_transcript.txt      # Visual analysis
├── dialogue_transcript.txt       # Dialogue breakdown
├── scene_summary.txt             # Scene analysis
└── evaluation_results.json       # ⭐ Final scores!
```

## 📖 Usage Examples

### Basic Evaluation

```bash
python main.py --url "https://youtube.com/watch?v=dQw4w9WgXcQ" --age 4
```

### Different Age Groups

```bash
# For a 3-year-old
python main.py --url "YOUTUBE_URL" --age 3

# For a 6-year-old
python main.py --url "YOUTUBE_URL" --age 6
```

### Custom Output Directory

```bash
python main.py --url "YOUTUBE_URL" --age 4 --output my_analysis
```

### Re-evaluate Existing Data

```bash
# Skip download/extraction, just re-evaluate
python main.py --url "YOUTUBE_URL" --age 5 --skip-extraction
```

## 🎯 Command-Line Arguments

| Argument            | Required | Description                           |
| ------------------- | -------- | ------------------------------------- |
| `--url`             | ✅ Yes   | YouTube video URL                     |
| `--age`             | ✅ Yes   | Child's age in years (e.g., 4, 5.5)   |
| `--output`          | ⚪ No    | Output directory (default: `outputs`) |
| `--skip-extraction` | ⚪ No    | Skip download, use existing data      |

## 💻 Installation

### Prerequisites

- Python 3.8+ (works with 3.14!)
- FFmpeg
- OpenAI API key

### Setup Steps

```bash
# 1. Clone/navigate to project
cd HackNYU

# 2. Create/activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install FFmpeg (if not already)
brew install ffmpeg  # macOS
# or
sudo apt-get install ffmpeg  # Ubuntu

# 5. Set up API key (OpenRouter / Gemini)
echo "OPENROUTER_API_KEY=your-openrouter-api-key-here" > .env
```

## 📊 Sample Output

```
======================================================================
              CHILDREN'S VIDEO CONTENT EVALUATOR
        Complete Pipeline: Download → Extract → Evaluate
======================================================================

📺 YouTube URL: https://youtube.com/watch?v=...
👶 Child Age: 4.0 years
📁 Output Directory: outputs

======================================================================
                    STEP 1: VIDEO DATA EXTRACTION
======================================================================

Step 1/6: Downloading YouTube video...
✓ Video downloaded
Step 2/6: Extracting audio and video tracks...
✓ Audio extracted
Step 3/6: Transcribing audio...
✓ Audio transcribed (5.3 minutes)
Step 4/6: Analyzing video content...
✓ 11 segments analyzed
Step 5/6: Generating dialogue transcript...
✓ Dialogue structured
Step 6/6: Generating scene summary...
✓ Summary complete

✅ Video data extraction complete!
⏱️  Processing time: 180.5 seconds

======================================================================
                      STEP 2: CONTENT EVALUATION
======================================================================

🔧 Initializing LLM client...
✅ LLM client initialized

🚀 Starting evaluation...
👶 Child age: 4.0 years

Step 1: Preprocessing video...
  Found 45 shots (PySceneDetect)
  Using existing transcript
  Duration: 5.3 minutes

Step 2: Computing pacing and audio metrics...
  Cuts per minute: 8.3
  Motion: 2.34 (measured with OpenCV)

Step 3: Computing text metrics...
  Vocabulary diversity: 0.40

Step 4: Computing semantic metrics (LLM)...
  Prosocial content: 40%

Step 5: Computing narrative coherence...
  Story coherence: 87% (embeddings)

Step 6: Computing scores...

  DEVELOPMENTAL SCORE: 66.8/100
  BRAINROT INDEX: 21.0/100

============================================================
EVALUATION SUMMARY
============================================================

Video: video_with_audio.mp4
Age: 4.0 years (Preschool)
Duration: 5.3 minutes

SCORES
------------------------------------------------------------
  Developmental Score: 66.8/100
    → Good - Generally appropriate

  Brainrot Index: 21.0/100
    → Low Risk - Minor concerns

  Overall: Recommended

STRENGTHS
------------------------------------------------------------
  ✓ Excellent pacing (83/100)
  ✓ Perfect story coherence (100/100)
  ✓ Great fantasy balance (100/100)

======================================================================
💡 FINAL ASSESSMENT
======================================================================

✅ This content appears to be HIGH QUALITY and age-appropriate!
   Safe for regular viewing.

✨ Positive Aspects:
   • Excellent pacing (83/100)
   • Perfect story coherence (100/100)
   • Great fantasy balance (100/100)

======================================================================
📊 Full results saved to: outputs/evaluation_results.json
======================================================================

======================================================================
🎉 PIPELINE COMPLETE!
======================================================================

✅ Video downloaded and extracted
✅ Content analyzed and evaluated
✅ All files saved to: /path/to/outputs

📂 Generated files:
   • video_with_audio.mp4 - Full video
   • audio_only.m4a - Audio track
   • speech_transcript.txt - Speech transcription
   • video_llm_transcript.txt - Visual analysis
   • dialogue_transcript.txt - Dialogue breakdown
   • scene_summary.txt - Scene analysis
   • evaluation_results.json - ⭐ Final scores!

======================================================================
```

## ⏱️ Processing Time & Cost

| Video Length | Processing Time | API Cost    |
| ------------ | --------------- | ----------- |
| 5 minutes    | ~3-5 minutes    | ~$0.10-0.20 |
| 15 minutes   | ~8-15 minutes   | ~$0.30-0.50 |
| 30 minutes   | ~15-30 minutes  | ~$0.50-1.00 |

**Tip**: Use `--skip-extraction` for faster re-evaluation with different ages!

## 🎓 How It Works

### Pipeline Steps

1. **Video Download** (yt-dlp)

   - Downloads video from YouTube
   - Handles quality selection

2. **Audio Extraction** (FFmpeg)

   - Separates audio track
   - Prepares for transcription

3. **Speech Transcription** (OpenAI Whisper)

   - Converts speech to text
   - Chunked processing for long videos

4. **Visual Analysis** (GPT-4 Vision)

   - Analyzes video frames
   - Describes visual content

5. **Content Evaluation** (Custom System)

   - Scene detection (PySceneDetect)
   - Motion analysis (OpenCV)
   - Text analysis (NLP)
   - Semantic analysis (GPT-3.5)
   - Narrative coherence (Embeddings)

6. **Score Computation** (Research-Based)
   - 22 metrics across 6 dimensions
   - Age-appropriate thresholds
   - Weighted scoring system

### Technologies Used

- **yt-dlp**: Video download
- **FFmpeg**: Media processing
- **OpenAI GPT**: LLM analysis
- **PySceneDetect**: Scene detection
- **OpenCV**: Motion analysis
- **PyTorch & Transformers**: Embeddings
- **Custom NLP**: Text metrics

## 📚 Project Structure

```
HackNYU/
├── main.py                    # CLI entry point
├── api.py                     # REST API server
├── requirements.txt           # Python dependencies
├── setup.sh                   # Setup script
├── README.md                  # This file
├── API_README.md              # API documentation
├── test_api.py                # API test script
├── evaluation/                # Evaluation system
│   ├── config.py             # Configuration & thresholds
│   ├── llm_client.py         # LLM integration
│   ├── video_preprocess.py   # Video preprocessing
│   ├── metrics_*.py          # Metric computation
│   ├── scoring.py            # Score calculation
│   ├── evaluate_video.py     # Main evaluator
│   ├── batch_evaluate.py     # Batch processing
│   └── utils.py              # Helper functions
├── video_data_extraction/     # Data extraction pipeline
│   ├── main.py               # Extraction orchestrator
│   ├── video_downloader.py   # YouTube download
│   ├── audio_processor.py    # Audio extraction
│   ├── video_processor.py    # Frame extraction
│   ├── ai_analyzer.py        # AI analysis
│   └── utils.py              # Helper functions
└── outputs/                   # Generated results
    └── evaluation_results.json
```

## 🔧 System Requirements

### Required

- ✅ Python 3.8+ (tested on 3.14)
- ✅ FFmpeg
- ✅ OpenAI API key
- ✅ NumPy

### Installed & Working

- ✅ PySceneDetect (advanced scene detection)
- ✅ OpenCV (motion analysis)
- ✅ Sentence-transformers (narrative coherence)
- ✅ PyTorch (ML backend)

### Optional

- ⚪ Librosa (detailed audio - not compatible with Python 3.14)

**Note**: System works at 95% capacity without librosa!

## 🎯 Age Bands

The system uses 4 age bands with different thresholds:

- **0-2 years**: Infant/Toddler

  - Very conservative limits
  - Emphasis on sensory regulation

- **2-3 years**: Early Preschool

  - Simple content focus
  - High interactivity preferred

- **3-5 years**: Preschool

  - Balanced evaluation
  - Story coherence matters

- **5-8 years**: Early Elementary
  - More complex content OK
  - Problem-solving valued

## 🐛 Troubleshooting

### API Key Issues (OpenRouter)

```bash
# Check if .env exists
cat .env

# If not, create it
echo "OPENROUTER_API_KEY=your-openrouter-api-key-here" > .env
```

### FFmpeg Not Found

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Verify installation
ffmpeg -version
```

### Module Not Found

```bash
# Make sure you're in venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Video Download Fails

- Check internet connection
- Verify YouTube URL is correct
- Try a different video
- Check yt-dlp is up to date: `pip install --upgrade yt-dlp`

## 🎓 Research Background

This system is based on research in:

- **American Academy of Pediatrics (AAP)**: Screen time guidelines
- **CASEL Framework**: Social-emotional learning
- **Piaget's Theory**: Cognitive development stages
- **CHILDES Corpus**: Language acquisition
- **Media Psychology**: Attention and engagement research

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional metrics
- More age bands
- Multi-language support
- Web interface
- Batch processing UI

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- OpenAI for GPT models
- PySceneDetect team
- FFmpeg developers
- Research community in child development

---

## 🎉 Get Started Now!

```bash
python main.py --url "YOUR_YOUTUBE_URL" --age 4
```

**One command. Complete analysis. Confident decisions.** 🚀

---

**Made with ❤️ for protecting children's development**

_HackNYU 2025_
