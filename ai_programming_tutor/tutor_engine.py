"""Pedagogical hinting and restricted educational Python execution."""
import ast, os, subprocess, sys, tempfile
from pathlib import Path
import requests

BLOCKED_NAMES={"eval","exec","compile","open","__import__","globals","locals","input"}
BLOCKED_MODULES={"os","sys","subprocess","socket","pathlib","shutil","requests","urllib"}
class SafetyError(ValueError): pass

def validate_code(code):
    if len(code)>8000: raise SafetyError("Code is too long for this learning workspace.")
    try: tree=ast.parse(code)
    except SyntaxError: return
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            names=[a.name.split('.')[0] for a in node.names] if isinstance(node,ast.Import) else [(node.module or '').split('.')[0]]
            if any(n in BLOCKED_MODULES for n in names): raise SafetyError("System, network and file modules are disabled.")
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in BLOCKED_NAMES: raise SafetyError(f"{node.func.id}() is disabled.")
        if isinstance(node,ast.Attribute) and node.attr.startswith('__'): raise SafetyError("Private runtime attributes are disabled.")

def run_python(code,timeout=3):
    validate_code(code)
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"solution.py"; path.write_text(code,encoding="utf-8")
        try:
            cp=subprocess.run([sys.executable,"-I",str(path)],capture_output=True,text=True,timeout=timeout,cwd=td,env={"PYTHONIOENCODING":"utf-8"})
            return {"status":"ok" if cp.returncode==0 else "error","stdout":cp.stdout[:5000],"stderr":cp.stderr[:3000]}
        except subprocess.TimeoutExpired: return {"status":"timeout","stdout":"","stderr":"Execution stopped: check for an infinite loop."}

def normalize(text): return "\n".join(line.rstrip() for line in text.strip().splitlines())
def test_submission(code,tests,timeout=3):
    execution=run_python(code,timeout)
    if execution["status"]!="ok": return {**execution,"passed":0,"total":len(tests),"details":[]}
    actual=normalize(execution["stdout"]); details=[]
    for test in tests:
        expected=normalize(test["expected"]); ok=actual==expected
        details.append({"name":test.get("name","Output test"),"passed":ok,"expected":expected if test.get("visible",True) else "Hidden","actual":actual})
    return {**execution,"passed":sum(x["passed"] for x in details),"total":len(details),"details":details}

def local_hint(exercise,result,level):
    if result.get("status")=="timeout": return "Your program did not finish. Check whether the loop variable changes toward termination."
    if result.get("status")=="error":
        last=(result.get("stderr") or "Python reported an error.").strip().splitlines()[-1]
        return f"Python reported: {last} Start at the indicated line and explain what Python expected."
    if result.get("passed")==result.get("total") and result.get("total",0): return "All tests passed. Explain why the solution works and name one boundary case."
    return [exercise.hint1,exercise.hint2,exercise.hint3][min(max(level-1,0),2)]

def ai_hint(exercise,code,result,level):
    fallback=local_hint(exercise,result,level); url=os.getenv("AI_API_URL"); key=os.getenv("AI_API_KEY"); model=os.getenv("AI_MODEL")
    if not (url and key and model): return fallback
    prompt=(f"You are a patient introductory Python tutor. Give hint level {level}/3 only. Never provide a complete solution. "
            f"Use beginner Python and end with one question. Objective: {exercise.objective}. Exercise: {exercise.prompt}. "
            f"Verified status: {result}. Student code:\n{code[:4000]}")
    try:
        r=requests.post(url,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json={"model":model,"messages":[{"role":"user","content":prompt}],"temperature":.2,"max_tokens":220},timeout=12)
        r.raise_for_status(); content=r.json()["choices"][0]["message"]["content"].strip()
        return content if content and len(content)<1800 else fallback
    except Exception: return fallback

