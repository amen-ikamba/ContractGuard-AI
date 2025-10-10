# ContractGuard AI ⚖️

**Autonomous AI Agent for Contract Review & Negotiation**

ContractGuard AI is an intelligent contract analysis system built on AWS Bedrock that autonomously reviews contracts, identifies risks, and assists with negotiations. Powered by Claude 3.5 Sonnet and AWS infrastructure, it provides enterprise-grade contract intelligence.

## 🌟 Features

### Automated Contract Analysis
- 📄 **Document Parsing**: Extracts text from PDF/DOCX using AWS Textract
- 🔍 **Clause Identification**: Automatically identifies key contract clauses
- ⚠️ **Risk Assessment**: AI-powered risk scoring (0-10 scale)
- 💡 **Smart Recommendations**: Suggests alternative clause language from knowledge base

### Intelligent Negotiation
- 🤖 **Autonomous Strategy**: Generates negotiation strategies based on risk analysis
- ✉️ **Email Drafting**: Creates professional negotiation emails
- 📊 **Multi-Round Tracking**: Manages iterative negotiation cycles
- 🎯 **Success Metrics**: Tracks acceptance rates and outcomes

### Enterprise Ready
- 🔐 **AWS Cognito Auth**: Secure user authentication
- 📈 **CloudWatch Monitoring**: Full observability
- 🗄️ **DynamoDB Storage**: Scalable data persistence
- 📦 **S3 Document Storage**: Secure file management
- 🚀 **FastAPI Backend**: High-performance REST API

---

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   API Gateway       │
│  (FastAPI/ALB)      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐      ┌──────────────────┐
│  Bedrock Agent      │◄────►│  Knowledge Base  │
│  (Orchestrator)     │      │  (OpenSearch)    │
└──────┬──────────────┘      └──────────────────┘
       │
       ├─────────┬─────────┬──────────┐
       ▼         ▼         ▼          ▼
   ┌────────┐ ┌─────┐ ┌─────────┐ ┌────────┐
   │Parser  │ │Risk │ │Recommend│ │Negotia-│
   │Tool    │ │Tool │ │er Tool  │ │tor Tool│
   └────────┘ └─────┘ └─────────┘ └────────┘
       │
       ▼
┌─────────────────────┐
│   AWS Services      │
│ • DynamoDB          │
│ • S3                │
│ • Textract          │
│ • SES (Email)       │
└─────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- **AWS Account** with Bedrock access enabled
- **Python 3.11+** (tested with 3.12/3.13)
- **Node.js 18+** (for AWS CDK)
- **AWS CLI** configured with credentials

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/amen-ikamba/contractguard-ai.git
cd contractguard-ai
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -e .
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your AWS credentials and configuration
```

5. **Deploy infrastructure** (optional for local dev)
```bash
cd infrastructure/cdk
npm install
cdk deploy --all
```

6. **Run the API server**
```bash
uvicorn src.api.handlers:app --reload --port 8000
```

7. **Run the Streamlit UI** (alternative)
```bash
streamlit run src/web/app.py
```

---

## 📖 Usage

### API Examples

#### Upload a Contract
```bash
curl -X POST "http://localhost:8000/contracts/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@contract.pdf" \
  -F "industry=SaaS" \
  -F "company_size=Small"
```

#### Get Contract Analysis
```bash
curl "http://localhost:8000/contracts/{contract_id}"
```

#### Start Negotiation
```bash
curl -X POST "http://localhost:8000/contracts/{contract_id}/negotiate"
```

### Python SDK Example
```python
from src.agent.orchestrator import ContractGuardAgent

agent = ContractGuardAgent()

# Process a contract
result = agent.process_contract(
    contract_id="contract-123",
    user_id="user-456"
)

print(f"Risk Level: {result['risk_level']}")
print(f"High Risk Clauses: {len(result['high_risk_clauses'])}")
```

---

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | `us-east-1` |
| `BEDROCK_MODEL_ID` | Claude model ID | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `BEDROCK_AGENT_ID` | Bedrock Agent ID | - |
| `BEDROCK_KB_ID` | Knowledge Base ID | - |
| `CONTRACTS_TABLE` | DynamoDB table name | `ContractGuard-Contracts` |
| `CONTRACTS_BUCKET` | S3 bucket name | `contractguard-contracts-bucket` |
| `APP_ENV` | Environment (dev/prod) | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

See [.env.example](.env.example) for complete list.

---

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md) - System design and components
- [API Reference](docs/API.md) - Complete API documentation
- [Setup Guide](docs/SETUP.md) - Detailed installation instructions
- [Contributing](CONTRIBUTING.md) - How to contribute

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_parser.py

# Run integration tests
pytest tests/integration/
```

---

## 📊 Project Structure

```
contractguard-ai/
├── src/
│   ├── agent/           # Agent orchestration
│   │   ├── orchestrator.py
│   │   ├── prompts.py
│   │   └── agent_config.py
│   ├── tools/           # Lambda tools
│   │   ├── contract_parser.py
│   │   ├── risk_analyzer.py
│   │   ├── clause_recommender.py
│   │   ├── negotiation_strategist.py
│   │   ├── redline_creator.py
│   │   └── email_generator.py
│   ├── models/          # Pydantic data models
│   │   ├── contract.py
│   │   └── negotiation.py
│   ├── api/             # FastAPI handlers
│   │   └── handlers.py
│   ├── utils/           # Utilities
│   │   ├── s3_helper.py
│   │   ├── dynamodb_helper.py
│   │   ├── textract_helper.py
│   │   └── logger.py
│   └── web/             # Streamlit UI
│       └── app.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── infrastructure/
│   └── cdk/             # AWS CDK stacks
├── docs/                # Documentation
├── knowledge_base/      # KB content
└── scripts/             # Deployment scripts
```

---

## 🎯 Key Components

### 1. Contract Parser Tool
- Extracts text using AWS Textract
- Identifies contract type (NDA, MSA, SaaS, etc.)
- Extracts parties, dates, terms
- Segments clauses by type

### 2. Risk Analyzer Tool
- Scores each clause (0-10)
- Identifies specific concerns
- Calculates overall contract risk
- Generates executive summary

### 3. Clause Recommender Tool
- Queries knowledge base for alternatives
- Generates 3-tier recommendations (aggressive/moderate/minimal)
- Provides likelihood of acceptance
- Includes business rationale

### 4. Negotiation Strategist
- Creates negotiation strategy
- Prioritizes requests
- Defines walk-away conditions
- Tracks multi-round negotiations

### 5. Email Generator
- Drafts professional emails
- Maintains appropriate tone
- Includes all key points
- Follows email best practices

---

## 🔒 Security

- ✅ AWS Cognito authentication
- ✅ S3 server-side encryption
- ✅ DynamoDB encryption at rest
- ✅ VPC deployment support
- ✅ IAM role-based access
- ✅ Secrets Manager integration
- ✅ API rate limiting
- ✅ Input validation with Pydantic

---

## 💰 Cost Optimization

**Estimated Monthly Costs (1000 contracts/month):**

| Service | Estimated Cost |
|---------|---------------|
| Bedrock (Claude 3.5) | $80-120 |
| DynamoDB | $5-10 |
| S3 | $2-5 |
| Textract | $15-25 |
| Knowledge Base | $10-20 |
| **Total** | **~$112-180/month** |

**Cost Reduction Tips:**
- Use caching for repeated analyses
- Batch Textract jobs
- Enable DynamoDB auto-scaling
- Use S3 Intelligent-Tiering
- Set Bedrock token limits

---

## 🚦 Roadmap

- [x] Core contract parsing
- [x] Risk analysis
- [x] Clause recommendations
- [x] Negotiation workflow
- [ ] Multi-language support
- [ ] Batch processing
- [ ] Advanced analytics dashboard
- [ ] Contract templates library
- [ ] Slack/Teams integration
- [ ] Mobile app

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Amen Ikamba** - [GitHub](https://github.com/amen-ikamba)

---

## 🙏 Acknowledgments

- Built with [AWS Bedrock](https://aws.amazon.com/bedrock/)
- Powered by [Anthropic Claude](https://www.anthropic.com/)
- UI framework: [Streamlit](https://streamlit.io/)
- API framework: [FastAPI](https://fastapi.tiangolo.com/)

---

## 📞 Support

- 📧 Email: support@contractguard.ai
- 💬 Discussions: [GitHub Discussions](https://github.com/amen-ikamba/contractguard-ai/discussions)
- 🐛 Issues: [GitHub Issues](https://github.com/amen-ikamba/contractguard-ai/issues)
- 📖 Docs: [Documentation Site](https://docs.contractguard.ai)

---

## ⚡ Performance

- Average contract analysis: **15-30 seconds**
- Concurrent requests supported: **100+**
- Max file size: **25 MB**
- Supported formats: **PDF, DOCX**

---

## 🌐 Deployment Options

### 1. AWS Lambda + API Gateway
```bash
cd infrastructure/cdk
cdk deploy ContractGuardApiStack
```

### 2. ECS Fargate
```bash
cd infrastructure/cdk
cdk deploy ContractGuardECSStack
```

### 3. Local Development
```bash
uvicorn src.api.handlers:app --reload
```

---

Made with ❤️ by the ContractGuard Team
