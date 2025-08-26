# mini_resume_extract.py
from __future__ import annotations
from typing import Any, Dict, Union
from io import BytesIO
import json, re
from pypdf import PdfReader
from openai import OpenAI

SCHEMA_SHAPE = {
    "first_name": "", "last_name": "", "job_position": "", "years_experience": "",
    "professional_summary": "",
    "languages": [{"name": "", "level": ""}],
    "experiences": [{
        "company_name": "", "position": "",
        "start_month": "", "start_year": "", "end_month": "", "end_year": "",
        "responsibilities": []
    }],
    "skills": [{"name": ""}],
    "softwares": [{"name": ""}],
    "standards": [],
    "educations": [{"name": "", "field_of_study": "", "university_name": "", "graduation_year": ""}],
    "certifications": [{"name": ""}]
}

SYSTEM_PROMPT = """You are an expert résumé extractor.
Return ONLY one valid JSON object that matches the provided schema.
Unknown fields => "" (strings) or [] (lists). Do not invent facts.
Months must be '01'..'12' or "".
Responsibilities: list of short strings without bullets.
'softwares' and 'skills' must be [{ "name": "<value>" }].
"""

def _to_bytes(file_or_bytes: Union[bytes, Any]) -> bytes:
    if isinstance(file_or_bytes, bytes):
        return file_or_bytes
    if hasattr(file_or_bytes, "read"):
        return file_or_bytes.read()
    raise TypeError("Expected bytes or a file-like object with .read()")

def pdf_to_text(file_or_bytes: Union[bytes, Any]) -> str:
    data = _to_bytes(file_or_bytes)
    reader = PdfReader(BytesIO(data))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) < 100:
        raise ValueError("PDF text too short; likely scanned or empty.")
    return text

def _json_chat(client: OpenAI, model: str, resume_text: str) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",
         "content": "Extract the résumé below into the exact JSON schema. Return ONLY JSON.\n\n"
                    "----- SCHEMA (shape example) -----\n"
                    + json.dumps(SCHEMA_SHAPE, ensure_ascii=False, indent=2)
                    + "\n\n----- RÉSUMÉ TEXT -----\n"
                    + resume_text}
    ]
    resp = client.chat.completions.create(
        model=model, temperature=0,
        messages=messages,
        response_format={"type": "json_object"},
        max_tokens=4000,
    )
    txt = resp.choices[0].message.content
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        cleaned = re.sub(r"^```json|```$", "", txt.strip(), flags=re.MULTILINE)

        return json.loads(cleaned)

def _normalize_named_list(items):
    out = []
    for it in (items or []):
        if isinstance(it, dict) and "name" in it:
            out.append({"name": f"{it.get('name','')}".strip()})
        elif isinstance(it, str):
            out.append({"name": it.strip()})
    return out

def _normalize_langs(items):
    res = []
    for it in (items or []):
        if isinstance(it, dict):
            res.append({"name": f"{it.get('name','')}".strip(),
                        "level": f"{it.get('level','')}".strip()})
        else:
            s = f"{it}"
            m = re.match(r"^\s*([^(]+?)\s*(?:\(([^)]+)\))?\s*$", s)
            name = (m.group(1) if m else s).strip()
            level = (m.group(2) if m and m.group(2) else "").strip()
            res.append({"name": name, "level": level})
    return res

def _normalize_exps(items):
    def mm(v):
        v = f"{v}".strip()
        return f"{int(v):02d}" if re.fullmatch(r"\d{1,2}", v or "") and 1 <= int(v) <= 12 else (v or "")
    out = []
    for e in (items or []):
        if not isinstance(e, dict): 
            continue
        resp = e.get("responsibilities", [])
        if isinstance(resp, str):
            resp = [s.strip("•- \t") for s in resp.split("\n") if s.strip()]
        else:
            resp = [f"{s}".strip("•- \t") for s in (resp or []) if f"{s}".strip()]
        out.append({
            "company_name": f"{e.get('company_name','')}".strip(),
            "position": f"{e.get('position','')}".strip(),
            "start_month": mm(e.get("start_month","")),
            "start_year": f"{e.get('start_year','')}".strip(),
            "end_month": mm(e.get("end_month","")),
            "end_year": f"{e.get('end_year','')}".strip(),
            "responsibilities": resp
        })
    return out

def ensure_schema(d: Dict[str, Any]) -> Dict[str, Any]:
    out = {**SCHEMA_SHAPE, **(d or {})}
    # strings
    for k in ["first_name","last_name","job_position","years_experience","professional_summary"]:
        out[k] = f"{out.get(k,'')}".strip()
    # lists
    out["languages"] = _normalize_langs(out.get("languages"))
    out["skills"] = _normalize_named_list(out.get("skills"))
    out["softwares"] = _normalize_named_list(out.get("softwares"))
    out["experiences"] = _normalize_exps(out.get("experiences"))
    out["educations"] = [
        {
            "name": f"{e.get('name','')}".strip(),
            "field_of_study": f"{e.get('field_of_study','')}".strip(),
            "university_name": f"{e.get('university_name','')}".strip(),
            "graduation_year": f"{e.get('graduation_year','')}".strip(),
        } for e in (out.get("educations") or []) if isinstance(e, dict)
    ]
    out["certifications"] = [
        {"name": f"{c.get('name','')}".strip()} if isinstance(c, dict) else {"name": f"{c}".strip()}
        for c in (out.get("certifications") or [])
    ]
    out["standards"] = [
        {"name": f"{s.get('name','')}".strip()} if isinstance(s, dict) else {"name": f"{s}".strip()}
        for s in (out.get("standards") or [])
    ]
    return out

def extract_resume_json(
    uploaded_file_or_bytes: Union[bytes, Any],
    api_key: str,
    base_url: str = 'http://localhost:11434/v1',   # <— default to ollama
    model: str = "llama3.1:latest",
) -> Dict[str, Any]:
    """
    Pass Streamlit's st.file_uploader() return value (or raw bytes).
    Returns a Python dict matching the target schema.
    """
    text = pdf_to_text(uploaded_file_or_bytes)
    client = OpenAI(base_url=base_url, api_key=api_key)  # LiteLLM/OpenAI-compatible proxy
    raw = _json_chat(client, model=model, resume_text=text)
    return ensure_schema(raw)
