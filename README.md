# SkillPath AI

Agentic skill-gap-to-job matching platform built from the supplied dark career-intelligence reference.

## Run locally

```powershell
# backend
cd backend
python -m pip install -r requirements.txt
$env:PYTHONPATH='.'
python -m uvicorn app.main:app --reload --port 8000

# frontend (separate terminal)
cd frontend
npm install
npm run dev
```

The demo works without `OPENAI_API_KEY`. The matching engine uses Sentence-Transformers when the model stack is available and a deterministic lexical fallback otherwise. The workflow is LangGraph-backed when installed, with a compatible deterministic fallback for lightweight environments.

The default demo path is: Try Demo Profile → Analyze → Agent Activity → Skill Analysis → Learning Path → FREE ONLY → AI Assistant.
