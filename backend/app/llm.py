"""Optional OpenAI reasoning hook with deterministic fallback."""
from __future__ import annotations
import json, os, urllib.request

def explain_gap(job_title: str, skill: str, fallback: str) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key: return fallback
    try:
        body = json.dumps({"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "messages":[{"role":"user","content":f"In one concise sentence, explain why {skill} matters for a {job_title} role. Do not give a number or make a guarantee."}], "temperature":0.2}).encode()
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body, headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=8) as response: return json.loads(response.read())["choices"][0]["message"]["content"].strip()
    except Exception: return fallback
