# Children's Video Content Evaluator API 🎥👶

REST API for evaluating YouTube videos for developmental appropriateness.

## 🚀 Quick Start

### 1. Start the API Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run the API
python api.py
```

The API will start on `http://localhost:5001`

### 2. Test the API

```bash
# Health check
curl http://localhost:5001/health

# Evaluate a video
curl "http://localhost:5001/evaluate?url=https://youtube.com/watch?v=jNQXAC9IVRw&age=4"
```

---

## 📡 API Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running.

**Response:**

```json
{
  "status": "healthy",
  "service": "Children's Video Content Evaluator API",
  "version": "1.0.0"
}
```

---

### 2. Evaluate Video (GET)

**GET** `/evaluate`

Evaluate a YouTube video for developmental appropriateness.

**Query Parameters:**

| Parameter         | Required | Type    | Description                               |
| ----------------- | -------- | ------- | ----------------------------------------- |
| `url`             | ✅ Yes   | string  | YouTube video URL                         |
| `age`             | ✅ Yes   | float   | Child's age in years (0-18)               |
| `skip_extraction` | ⚪ No    | boolean | Skip download/extraction (default: false) |

**Example Request:**

```bash
curl "http://localhost:5001/evaluate?url=https://youtube.com/watch?v=jNQXAC9IVRw&age=4"
```

**Example Response:**

```json
{
  "video_path": "/path/to/video.mp4",
  "child_age": 4.0,
  "age_band": "G3_3_5",
  "age_band_name": "Preschool",
  "duration_seconds": 318.1,
  "duration_minutes": 5.3,
  "dev_score": 68.4,
  "dev_interpretation": "Good - Generally appropriate with some areas for improvement",
  "brainrot_index": 20.5,
  "brainrot_interpretation": "Low Risk - Minor concerns, generally safe",
  "overall_recommendation": "Recommended",
  "dimension_scores": {
    "pacing": 83.3,
    "story": 100.0,
    "language": 70.5,
    "sel": 52.9,
    "fantasy": 100.0,
    "interactivity": 0.0
  },
  "metrics": {
    "cuts_per_minute": 8.3,
    "avg_shot_length": 7.1,
    "type_token_ratio": 0.46,
    "mean_utterance_length": 4.7,
    "question_rate": 5.0,
    "prosocial_rate": 0.2,
    "aggression_rate": 0.2,
    "adjacent_similarity": 1.0,
    "topic_jumps": 0.0
  },
  "strengths": [
    "Pacing: Excellent (83/100)",
    "Story: Excellent (100/100)",
    "Fantasy: Excellent (100/100)"
  ],
  "concerns": ["Interactivity: Needs improvement (0/100)"],
  "recommendations": [
    "Consider content with more direct viewer engagement",
    "Excellent narrative structure for this age group",
    "Pacing is well-suited for attention span"
  ]
}
```

**Status Codes:**

- `200` - Success
- `400` - Bad Request (missing or invalid parameters)
- `404` - Video not found
- `500` - Internal server error

---

### 3. Evaluate Video (POST)

**POST** `/evaluate`

⚠️ **Currently not implemented** - Placeholder for future use.

**Expected JSON Body:**

```json
{
  "url": "https://youtube.com/watch?v=VIDEO_ID",
  "age": 4.5,
  "options": {
    "skip_extraction": false,
    "detailed_analysis": true
  }
}
```

**Response:**

```json
{
  "error": "Not implemented",
  "message": "POST endpoint is not yet implemented. Please use GET /evaluate for now."
}
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
OPENROUTER_API_KEY=your-openrouter-api-key-here
```

### API Configuration

Edit `api.py` to change:

- Port: `app.run(port=5000)`
- Host: `app.run(host='0.0.0.0')`
- Debug mode: `app.run(debug=True)`

---

## 📊 Response Fields Explained

### Scores

- **`dev_score`** (0-100): Developmental value score

  - Higher is better
  - Based on age-appropriate metrics
  - Weighted across 6 dimensions

- **`brainrot_index`** (0-100): Risk assessment score
  - Lower is better
  - Measures overstimulation, confusion, harmful content
  - Inverse weighting of developmental factors

### Dimension Scores

- **`pacing`**: Visual cuts, motion, audio intensity
- **`story`**: Narrative coherence and continuity
- **`language`**: Vocabulary richness and complexity
- **`sel`**: Social-emotional learning content
- **`fantasy`**: Imagination vs reality balance
- **`interactivity`**: Viewer engagement elements

### Metrics

Detailed measurements including:

- Shot length and cut frequency
- Text complexity (TTR, utterance length)
- Content analysis (prosocial, aggression)
- Narrative coherence (similarity, topic jumps)

---

## 🧪 Testing Examples

### Python (requests)

```python
import requests

# Evaluate video
response = requests.get(
    'http://localhost:5001/evaluate',
    params={
        'url': 'https://youtube.com/watch?v=jNQXAC9IVRw',
        'age': 4
    }
)

results = response.json()
print(f"Dev Score: {results['dev_score']}")
print(f"Brainrot Index: {results['brainrot_index']}")
```

### JavaScript (fetch)

```javascript
const url = "http://localhost:5001/evaluate?url=YOUTUBE_URL&age=4";

fetch(url)
  .then((response) => response.json())
  .then((data) => {
    console.log("Dev Score:", data.dev_score);
    console.log("Brainrot Index:", data.brainrot_index);
  });
```

### cURL

```bash
# Basic evaluation
curl "http://localhost:5001/evaluate?url=https://youtube.com/watch?v=jNQXAC9IVRw&age=4"

# Pretty print JSON
curl -s "http://localhost:5001/evaluate?url=https://youtube.com/watch?v=jNQXAC9IVRw&age=4" | python -m json.tool

# Save to file
curl "http://localhost:5001/evaluate?url=https://youtube.com/watch?v=jNQXAC9IVRw&age=4" > results.json
```

---

## ⏱️ Processing Time

| Video Length | API Response Time | API Cost    |
| ------------ | ----------------- | ----------- |
| 5 minutes    | ~3-5 minutes      | ~$0.10-0.20 |
| 15 minutes   | ~8-15 minutes     | ~$0.30-0.50 |
| 30 minutes   | ~15-30 minutes    | ~$0.50-1.00 |

**Note:** Processing happens synchronously. Consider implementing async/queue for production.

---

## 🔒 Security Considerations

### For Production Deployment:

1. **Add authentication**: Implement API keys or OAuth
2. **Rate limiting**: Prevent abuse
3. **Input validation**: Sanitize URLs and parameters
4. **CORS**: Configure allowed origins
5. **HTTPS**: Use SSL/TLS certificates
6. **Environment**: Use production WSGI server (gunicorn, uwsgi)

Example with gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api:app
```

---

## 🐛 Troubleshooting

### API won't start

```bash
# Check if port 5000 is in use
lsof -i :5000

# Use a different port
python api.py  # Edit port in api.py
```

### API key errors (OpenRouter)

```bash
# Verify .env file exists
cat .env

# Check environment variable
echo $OPENROUTER_API_KEY
```

### Module not found

```bash
# Activate venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 🚀 Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 600 api:app
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "600", "api:app"]
```

### Environment Variables for Production

```bash
OPENROUTER_API_KEY=your-openrouter-api-key-here
FLASK_ENV=production
FLASK_DEBUG=0
```

---

## 📈 Future Enhancements

- [ ] Async processing with task queues (Celery, RQ)
- [ ] WebSocket support for real-time progress
- [ ] Batch evaluation endpoint
- [ ] Caching layer (Redis)
- [ ] Rate limiting
- [ ] API authentication
- [ ] Webhook notifications
- [ ] Video ID-based result caching

---

## 📝 API Versioning

Current version: **v1.0.0**

Future versions will use URL versioning:

- `/v1/evaluate`
- `/v2/evaluate`

---

**Made with ❤️ for protecting children's development**

_HackNYU 2025_
