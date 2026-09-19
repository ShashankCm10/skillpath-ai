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

def assistant_reply(message: str, profile: dict, analysis: dict | None) -> str:
    fallback = _assistant_fallback(message, profile, analysis)
    key = os.getenv("OPENAI_API_KEY")
    if not key: return fallback
    try:
        context = json.dumps({"profile": profile, "analysis": analysis}, default=str)
        prompt = ("You are SkillPath AI. Answer using only the supplied profile and analysis. "
                  "Be concise and factual. Never invent salaries, hiring claims, or numeric scores. "
                  f"Context: {context}\nUser: {message}")
        body = json.dumps({"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "messages":[{"role":"user","content":prompt}], "temperature":0.2}).encode()
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body, headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=8) as response: return json.loads(response.read())["choices"][0]["message"]["content"].strip()
    except Exception: return fallback

def _assistant_fallback(message: str, profile: dict, analysis: dict | None) -> str:
    if not analysis:
        return "Complete your profile and run an analysis so I can ground recommendations in your skills."
    target = analysis["target_job"]
    gaps = analysis["gap_analysis"]["missing_required_skills"]
    return f"Your current focus is {target['title']} at {target['company']}. Prioritize {', '.join(gaps[:3]) or 'a portfolio project'} and use the Learning Path for curated next steps."
