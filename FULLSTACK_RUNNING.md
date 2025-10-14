# 🚀 ContractGuard AI - Full Stack Running Guide

## ✅ Current Status: FULLY OPERATIONAL

Both the backend API and frontend UI are now running!

---

## 🎯 Access Your Applications

### 🖥️ **Frontend (Streamlit UI)**
- **URL**: http://localhost:8501
- **Status**: ✅ Running
- **Features**:
  - 📤 Upload contracts (PDF/DOCX)
  - 🔍 View contract analysis
  - ⚠️ Risk assessment dashboard
  - 💬 Negotiation interface
  - 📊 Visual analytics

### 🔌 **Backend (FastAPI)**
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Status**: ✅ Running
- **Components**: API ✅ | Bedrock ✅ | DynamoDB ✅ | S3 ✅

---

## 📸 What You Should See

### Streamlit Frontend (Port 8501)
A beautiful web interface with:
- Contract upload section
- Analysis dashboard
- Negotiation workflow
- Risk visualization

### FastAPI Backend (Port 8000)
Interactive API documentation with all endpoints ready to test

---

## 🎮 Quick Start Guide

### 1. Upload a Contract
1. Open http://localhost:8501
2. Click **"Upload Contract"** in the sidebar
3. Select a PDF or DOCX file
4. Fill in contract details (industry, company size)
5. Click **"Analyze Contract"**

### 2. View Analysis Results
The system will show you:
- Overall risk score (0-10)
- High-risk clauses
- Detailed recommendations
- Alternative clause suggestions

### 3. Start Negotiation
- Click **"Start Negotiation"**
- Review AI-generated negotiation strategy
- Send negotiation email
- Track responses

---

## 🔧 Managing Your Applications

### Stop Both Services
```bash
# Stop using Ctrl+C in the terminals, or:
lsof -ti:8000 | xargs kill -9  # Kill API server
lsof -ti:8501 | xargs kill -9  # Kill Streamlit
```

### Restart Backend (API)
```bash
.venv/bin/uvicorn src.api.handlers:app --reload --port 8000
```

### Restart Frontend (Streamlit)
```bash
.venv/bin/streamlit run src/web/app.py --server.port 8501
```

### Start Both at Once
```bash
# Terminal 1 - Backend
.venv/bin/uvicorn src.api.handlers:app --reload --port 8000 &

# Terminal 2 - Frontend
.venv/bin/streamlit run src/web/app.py --server.port 8501
```

---

## 📋 Full Stack Architecture

```
┌─────────────────────────────────────────────────────┐
│                     Browser                         │
│                                                     │
│  Frontend: http://localhost:8501                   │
│  Backend:  http://localhost:8000                   │
└──────────────┬─────────────┬────────────────────────┘
               │             │
               │             │
       ┌───────▼──────┐ ┌────▼──────────┐
       │  Streamlit   │ │   FastAPI     │
       │  Frontend    │ │   Backend     │
       │  (Port 8501) │ │  (Port 8000)  │
       └───────┬──────┘ └────┬──────────┘
               │             │
               └─────────┬───┘
                         │
                         ▼
              ┌──────────────────┐
              │   AWS Services   │
              ├──────────────────┤
              │ • Bedrock        │
              │ • DynamoDB       │
              │ • S3             │
              │ • Lambda         │
              │ • API Gateway    │
              └──────────────────┘
```

---

## 🧪 Test the Full Stack

### Test 1: Health Check (Backend)
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "api": "UP",
    "bedrock": "UP",
    "dynamodb": "UP",
    "s3": "UP"
  }
}
```

### Test 2: Upload via API
```bash
curl -X POST http://localhost:8000/contracts/upload \
  -F "file=@test_contract.pdf" \
  -F "industry=SaaS" \
  -F "company_size=Small"
```

### Test 3: Use the Streamlit UI
1. Visit http://localhost:8501
2. Upload a contract
3. See the magic happen! ✨

---

## 🐛 Troubleshooting

### Frontend Not Loading
```bash
# Check if Streamlit is running
lsof -i:8501

# Restart Streamlit
.venv/bin/streamlit run src/web/app.py --server.port 8501
```

### Backend Not Responding
```bash
# Check if API is running
curl http://localhost:8000/health

# Restart API
.venv/bin/uvicorn src.api.handlers:app --reload --port 8000
```

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 8501
lsof -ti:8501 | xargs kill -9
```

### AWS Connection Issues
```bash
# Verify AWS credentials
.venv/bin/python scripts/get_account_id.py

# Check Bedrock access
.venv/bin/python scripts/check_bedrock.py
```

---

## 📊 Running Processes

Your current setup has:

1. **Backend API** (Background Process)
   - Command: `uvicorn src.api.handlers:app --reload --port 8000`
   - Port: 8000
   - Auto-reload: ✅ Enabled

2. **Frontend UI** (Background Process)
   - Command: `streamlit run src/web/app.py --server.port 8501`
   - Port: 8501
   - Hot-reload: ✅ Enabled

Both processes are running in the background with auto-reload, so code changes will automatically update!

---

## 🎨 Frontend Features

### 📤 Contract Upload
- Drag & drop PDF/DOCX files
- Industry selection (SaaS, Healthcare, Finance, etc.)
- Company size selection
- Instant upload feedback

### 🔍 Analysis Dashboard
- Overall risk score with color coding
- Clause-by-clause breakdown
- Risk level indicators
- Detailed recommendations

### 💬 Negotiation Interface
- AI-generated negotiation strategy
- Email template generation
- Multi-round tracking
- Response management

### 📊 Analytics & Reports
- Risk distribution charts
- Historical analysis
- Comparison views
- Export functionality

---

## 🔑 Key URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Streamlit UI** | http://localhost:8501 | Main user interface |
| **API Root** | http://localhost:8000 | API service info |
| **API Docs** | http://localhost:8000/docs | Interactive API docs (Swagger) |
| **ReDoc** | http://localhost:8000/redoc | Alternative API docs |
| **Health Check** | http://localhost:8000/health | System status |
| **AWS API** | https://3hwwidtpj1.execute-api.us-east-2.amazonaws.com/prod/ | Production API |

---

## 💡 Usage Tips

### For Development
- Both services auto-reload on code changes
- Check terminal output for errors
- Use browser DevTools for debugging
- API docs at http://localhost:8000/docs for testing

### For Testing
- Use Streamlit UI for end-to-end testing
- Use API docs for individual endpoint testing
- Check health endpoint to verify all services
- Monitor CloudWatch logs for Lambda functions

### For Production
- Deploy frontend to Streamlit Cloud or similar
- API already deployed to AWS API Gateway
- Configure custom domain names
- Enable authentication/authorization

---

## 📚 Additional Resources

- **Full Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **API Documentation**: [RUNNING.md](RUNNING.md)
- **Project README**: [README.md](README.md)
- **AWS Console**: https://console.aws.amazon.com/
- **Streamlit Docs**: https://docs.streamlit.io/

---

## 🎉 You're All Set!

Your full-stack ContractGuard AI application is now running:

✅ Backend API on http://localhost:8000
✅ Frontend UI on http://localhost:8501
✅ AWS Infrastructure deployed
✅ All services healthy

**Start by uploading a contract at http://localhost:8501!** 🚀

---

## 📞 Quick Commands Reference

```bash
# Check what's running
lsof -i:8000  # Backend
lsof -i:8501  # Frontend

# View logs
# Backend logs appear in terminal
# Frontend logs appear in Streamlit terminal

# Stop services
Ctrl+C in respective terminals

# Restart everything
.venv/bin/uvicorn src.api.handlers:app --reload --port 8000 &
.venv/bin/streamlit run src/web/app.py --server.port 8501
```

Happy analyzing! 🎊
