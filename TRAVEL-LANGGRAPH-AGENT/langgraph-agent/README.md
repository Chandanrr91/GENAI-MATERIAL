# ✈️ Travel LangGraph Agent (GenAI + AWS Ready)

A production-oriented **AI Travel Planning system** built using **LangGraph, OpenAI, Duffel API, and SerpAPI**, designed for multi-step agent orchestration and cloud deployment.

This project demonstrates how to evolve a **GenAI prototype → containerized microservice → CI/CD pipeline → AWS ECR → ECS-ready system**.

---

# 🚀 Features

- 🧠 Multi-agent orchestration using **LangGraph**
- ✈️ Real-time flight search using **Duffel API**
- 🏨 Hotel discovery using **SerpAPI**
- 🎯 Activity recommendations (SerpAPI)
- 💰 Budget-aware decision engine
- 🧩 Stateful graph execution with checkpointing
- 🐳 Dockerized for production deployment
- ☁️ AWS ECR + ECS deployment ready
- 🔁 CI/CD pipeline using GitHub Actions

---

# 🏗️ Architecture
User Input
↓
Processor Node (IATA + Date Normalization)
↓
Flight Agent (Duffel API)
↓
Hotel Agent (SerpAPI)
↓
Activity Agent (SerpAPI)
↓
Supervisor Node (Budget Recalculation)
↓
Conditional Routing
├── Budget OK → Activities → END
└── Budget Exceeded → Warning Node → END


---

# 📁 Project Structure
```
TRAVEL-LANGGRAPH-AGENT/
│
├── langgraph-agent/
│ ├── app/
│ │ ├── main.py # Entry point
│ │ ├── graph.py # LangGraph workflow
│ │ ├── nodes.py # Agent nodes (flight, hotel, etc.)
│ │ ├── state.py # TravelState definition
│ │ ├── config.py # API keys + LLM setup
│ │
│ ├── Dockerfile
│ ├── requirements.txt
│ ├── README.md
│
├── .github/workflows/
│ └── docker-ecr.yml # CI/CD pipeline

```
---

# ⚙️ Setup Instructions

## 1. Clone Repository

```bash
git clone <your-repo-url>
cd TRAVEL-LANGGRAPH-AGENT/langgraph-agent
```
## 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
```

## 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables

```bash
Create a .env file:
OPENAI_API_KEY=your_openai_key
SERPAPI_API_KEY=your_serpapi_key
DUFFEL_ACCESS_TOKEN=your_duffel_token
```
## 5. Run Application
```bash
python app/main.py
```

🐳 Docker Setup

## Build Image
```bash
docker build -t travel-langgraph-agent .
```

## Run Container
```bash
docker run -e OPENAI_API_KEY=xxx \
           -e SERPAPI_API_KEY=xxx \
           -e DUFFEL_ACCESS_TOKEN=xxx \
           travel-langgraph-agent
```
## ☁️ AWS ECR Deployment

```bash
1. Create ECR Repository
aws ecr create-repository \
  --repository-name travel-langgraph-agent \
  --region us-east-1
2. Login to ECR
aws ecr get-login-password --region us-east-1 \
| docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-east-1.amazonaws.com
3. Tag Docker Image
docker tag travel-langgraph-agent:latest \
<account_id>.dkr.ecr.us-east-1.amazonaws.com/travel-langgraph-agent:latest
4. Push Image
docker push <account_id>.dkr.ecr.us-east-1.amazonaws.com/travel-langgraph-agent:latest
```

🔁 CI/CD Pipeline (GitHub Actions)

On every push to main, the workflow will:

Build Docker image
Authenticate with AWS
Tag image
Push to ECR

Workflow file:

.github/workflows/docker-ecr.yml
🔐 GitHub Secrets Required

Add these in GitHub:

Secret Name	Description
AWS_ACCESS_KEY_ID	IAM access key
AWS_SECRET_ACCESS_KEY	IAM secret key
AWS_REGION	AWS region (e.g. us-east-1)
AWS_ACCOUNT_ID	AWS account ID
ECR_REPOSITORY	travel-langgraph-agent
