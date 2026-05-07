# 🚀 Quick API Setup Guide

## Start the API in 3 Steps

### 1. Activate Virtual Environment

```bash
cd /Users/mateicoldea/Documents/Projects/Hackathons/HackNYU
source venv/bin/activate
```

### 2. Start the Server

```bash
python api.py
```

You should see:

```
======================================================================
  Children's Video Content Evaluator API
======================================================================

API Endpoints:
  GET  /health              - Health check
  GET  /evaluate?url=...    - Evaluate video (requires url and age params)
  POST /evaluate            - Placeholder (not yet implemented)

Example usage:
  curl "http://localhost:5001/evaluate?url=YOUTUBE_URL&age=4"

Starting server...
======================================================================

 * Running on http://0.0.0.0:5001
```

### 3. Test the API

Open a **new terminal** and run:

```bash
# Health check
curl http://localhost:5001/health

# Expected output:
# {
#   "status": "healthy",
#   "service": "Children's Video Content Evaluator API",
#   "version": "1.0.0"
# }
```

## 🎯 Evaluate a Video

```bash
curl "http://localhost:5001/evaluate?url=https://www.youtube.com/watch?v=jNQXAC9IVRw&age=4"
```

**Note:** This will take 3-10 minutes depending on video length.

## 📖 Full Documentation

See [API_README.md](API_README.md) for:

- Complete endpoint documentation
- Request/response examples
- Error handling
- Testing examples in Python, JavaScript, cURL
- Production deployment guide

## 🧪 Run Automated Tests

```bash
# In a new terminal (keep API running)
python test_api.py
```

This will test:

- ✅ Health check endpoint
- ✅ Error handling
- ✅ Video evaluation (optional)

## 🛑 Stop the Server

Press `Ctrl+C` in the terminal running the API.

---

## Quick Reference

| Action         | Command                                               |
| -------------- | ----------------------------------------------------- |
| Start API      | `python api.py`                                       |
| Health check   | `curl http://localhost:5001/health`                   |
| Evaluate video | `curl "http://localhost:5001/evaluate?url=URL&age=4"` |
| Run tests      | `python test_api.py`                                  |
| Stop API       | `Ctrl+C`                                              |

---

**API Server:** `http://localhost:5001`
**Documentation:** See [API_README.md](API_README.md)
