"""Local browser dashboard for training and testing nanoGPT."""
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, request, render_template_string

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
process = None
process_lock = threading.Lock()
log_lock = threading.Lock()
log_path = ROOT / "training.log"

PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LLM Studio</title>
<style>
:root{--bg:#0b1020;--panel:#121a2e;--panel2:#17213a;--line:#25314d;--text:#edf2ff;--muted:#9aa8c2;--accent:#8b9dff;--green:#73e0b0;--red:#ff8294}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 15% 0%,#1c2850 0,transparent 36%),var(--bg);color:var(--text);font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}main{max-width:1160px;margin:auto;padding:32px 24px 60px}.top{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:26px}.brand{display:flex;align-items:center;gap:14px}.mark{width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,#758cff,#a879f4);display:grid;place-items:center;font-size:23px;box-shadow:0 8px 28px #667aff33}.eyebrow{color:#aab6ff;text-transform:uppercase;letter-spacing:.16em;font-weight:700;font-size:11px}.brand h1{font-size:23px;letter-spacing:-.04em;margin:1px 0 0}.status{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:13px}.dot{width:8px;height:8px;border-radius:100%;background:#74829f}.dot.live{background:var(--green);box-shadow:0 0 12px #73e0b0}.tabs{display:flex;gap:8px;border-bottom:1px solid var(--line);margin-bottom:22px}.tab{color:var(--muted);border:0;background:none;padding:12px 16px;cursor:pointer;font:inherit;border-bottom:2px solid transparent}.tab.active{color:var(--text);border-color:var(--accent)}.view{display:none}.view.active{display:block}.grid{display:grid;grid-template-columns:1.05fr .95fr;gap:18px}.card{background:linear-gradient(180deg,#141d33,#11192c);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 14px 38px #02061230}.card h2{font-size:16px;margin:0 0 4px}.sub{color:var(--muted);font-size:13px;margin:0 0 18px}.field{margin:15px 0}.field label{display:block;color:#ccd6eb;font-size:13px;font-weight:600;margin:0 0 7px}.field small{display:block;color:var(--muted);font-size:12px;margin-top:6px}input,select,textarea{width:100%;border:1px solid #2c3958;background:#0c1427;color:var(--text);border-radius:10px;padding:11px 12px;font:inherit;outline:none}input:focus,select:focus,textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px #8797ff20}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}.button{border:0;border-radius:10px;padding:11px 16px;background:linear-gradient(120deg,#7489ff,#9a75f4);color:white;font-weight:700;font-size:14px;cursor:pointer}.button:hover{filter:brightness(1.08)}.button.secondary{background:#263452;border:1px solid #354665}.button.danger{background:#512b3b;border:1px solid #724052}.button:disabled{opacity:.45;cursor:not-allowed}.actions{display:flex;gap:10px;align-items:center;margin-top:18px}.notice{border:1px solid #655632;background:#292516;color:#eddda5;border-radius:12px;padding:12px 14px;font-size:13px;margin-top:14px}.notice.info{border-color:#30446c;background:#15223b;color:#c5d4fa}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.metric{padding:14px;background:#0d1528;border:1px solid #202d49;border-radius:12px}.metric b{display:block;font-size:20px;letter-spacing:-.03em}.metric span{color:var(--muted);font-size:12px}.bar{height:7px;background:#222d48;border-radius:8px;overflow:hidden;margin-top:12px}.bar i{height:100%;display:block;background:linear-gradient(90deg,#758aff,#69deb4);width:0;transition:width .3s}.console{height:300px;overflow:auto;white-space:pre-wrap;background:#080e1b;border:1px solid #202a42;border-radius:12px;padding:14px;color:#b8c7e4;font:12px/1.65 ui-monospace,SFMono-Regular,Consolas,monospace}.full{grid-column:1/-1}.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}.pill{display:inline-flex;padding:4px 9px;border-radius:99px;background:#1e2d4e;color:#b9c9ff;font-size:11px;font-weight:700}.output{min-height:180px;white-space:pre-wrap;background:#0b1324;border:1px solid #273451;padding:15px;border-radius:12px;color:#d5e0f6}.chatbox{height:390px;overflow:auto;background:#0b1324;border:1px solid #273451;border-radius:12px;padding:14px}.bubble{max-width:90%;padding:11px 14px;margin:8px 0;border-radius:14px;white-space:pre-wrap;overflow-wrap:anywhere}.bubble.user{margin-left:auto;background:#27365b;color:#eef1ff}.bubble.assistant{background:#17233b;color:#d9e4f8}.chatform{display:flex;gap:9px;margin-top:12px;align-items:flex-end}.chatform textarea{resize:vertical;min-height:48px;max-height:130px}.filelist{max-height:235px;overflow:auto;border:1px solid #2c3958;border-radius:10px;background:#0c1427}.fileitem{display:flex;align-items:center;gap:10px;padding:9px 11px;border-bottom:1px solid #202d49;color:#d5e0f6;font-size:13px}.fileitem:last-child{border-bottom:0}.fileitem input{width:auto;margin:0;accent-color:#8b9dff}.filemeta{margin-left:auto;color:#91a0bc;font-size:11px;white-space:nowrap}.filetools{display:flex;gap:8px;margin:8px 0}.filetools button{padding:5px 9px;font-size:12px}.foot{color:#8290aa;text-align:center;font-size:12px;margin-top:25px}@media(max-width:760px){main{padding:22px 14px}.grid,.two{grid-template-columns:1fr}.full{grid-column:auto}.top{align-items:flex-start;flex-direction:column}.metrics{grid-template-columns:1fr 1fr}}
</style></head><body><main>
<header class="top"><div class="brand"><div class="mark">✳</div><div><div class="eyebrow">Local language model lab</div><h1>LLM Studio</h1></div></div><div class="status"><i class="dot" id="dot"></i><span id="topstatus">Checking runtime…</span></div></header>
<nav class="tabs"><button class="tab active" data-tab="training">Training</button><button class="tab" data-tab="testing">Testing</button><button class="tab" data-tab="settings">Settings</button></nav>
<section id="training" class="view active"><div class="grid">
<div class="card"><h2>Train or fine-tune</h2><p class="sub">Start with the included CC0 books, or continue training a model you already have.</p>
<div class="field"><label>Training mode</label><select id="mode"><option value="scratch">Train from scratch</option><option value="finetune">Fine-tune a saved model</option></select></div>
<div id="scratch-options" class="field"><label>Model size</label><select id="size"><option value="2M">~2M parameters — recommended start</option><option value="8M">~8M parameters — richer small model</option><option value="100M">~100M parameters — needs substantial memory</option></select><small>100M is an approximate architecture size; 4 GB VRAM does not guarantee it fits. Reduce batch/context or use CPU if memory runs out.</small></div>
<div id="finetune-options" class="field" style="display:none"><label>Base model to fine-tune</label><select id="base-model"></select><small>Fine-tune a scratch checkpoint or either downloaded model. Pretrained fine-tuning updates only the final Transformer block and norm to reduce memory use; the original stays unchanged. CPU training can be slow.</small></div>
<div class="field"><label>Training text files</label><div class="filetools"><button class="button secondary" id="selectAllData" type="button">Select all</button><button class="button secondary" id="clearData" type="button">Clear</button><span class="pill" id="dataCount">0 selected</span></div><div class="filelist" id="dataFiles">Loading files from Training_Data…</div><small>Select one or more UTF-8 .txt files. The combined books corpus is selected by default. Selecting it together with individual books repeats that text.</small></div>
<div class="row"><div class="field"><label>Training steps</label><input id="steps" type="number" min="10" max="1000000" value="500"></div><div class="field"><label>Batch size</label><input id="batch" type="number" min="1" max="256" value="8"></div></div>
<div class="row"><div class="field"><label>Context length</label><select id="context"><option>64</option><option selected>128</option><option>256</option><option>512</option></select></div><div class="field"><label>Learning rate</label><input id="lr" type="number" min="0.000001" max="0.1" step="0.0001" value="0.0003"></div></div>
<div class="field"><label>Model name</label><input id="name" value="my_first_model" maxlength="40"></div>
<div class="notice">Reality check: scratch models are learning demos and may produce garbled text. The downloaded small Transformers models produce more readable English than the scratch demos. TinyStories is strongest on simple short-story continuations; Pythia is a broader base text model. Neither is instruction-tuned or fact-checked, and both can still be wrong or nonsensical. Fine-tuning quality depends on your text. Training-time estimates are rough.</div>
<div class="actions"><button class="button" id="start">Start training</button><button class="button danger" id="stop" disabled>Stop</button><span class="pill" id="estimate">Estimated time: —</span></div>
</div>
<div class="card"><h2>Live resources</h2><p class="sub">Local machine usage while the dashboard is open.</p><div class="metrics"><div class="metric"><b id="cpu">—</b><span>CPU usage</span></div><div class="metric"><b id="ram">—</b><span>System memory</span></div><div class="metric"><b id="gpu">—</b><span>GPU / VRAM</span></div></div><div class="field"><label>Training progress</label><div class="bar"><i id="progress"></i></div><small id="progresslabel">Waiting for a run</small></div><div class="field"><label>Runtime</label><div id="runtime" class="output" style="min-height:90px">Detecting Python, PyTorch and device…</div></div></div>
<div class="card full"><h2>Training output</h2><p class="sub">Recent messages from the trainer.</p><div class="console" id="console">Ready. Choose settings and start a run.</div></div>
</div></section>
<section id="testing" class="view"><div class="card"><h2>Chat with a model</h2><p class="sub">Choose TinyStories for simple, more coherent English story continuations or Pythia-70M for broader text completion. Neither is instruction-tuned or fact-checked; both run locally.</p><div class="row"><div class="field"><label>Model</label><select id="models"></select></div><div class="field"><label>Temperature</label><input id="temperature" type="number" value="0.8" min="0.1" max="2" step="0.1"></div></div><div class="chatbox" id="chatbox"><div class="bubble assistant">Try TinyStories for a short, simple English story, or Pythia-70M for broader text continuation. Neither is chat-tuned or fact-checked. Scratch nanoGPT models are learning demos and may be garbled.</div></div><div class="chatform"><textarea id="chatPrompt" rows="2" placeholder="Write a message…"></textarea><button class="button" id="send">Send</button></div><div class="actions"><label class="sub" style="margin:0">New tokens per reply</label><input id="newtokens" type="number" value="160" min="1" max="1000" style="max-width:130px"><button class="button secondary" id="clearChat">Clear chat</button></div><div class="notice info">TinyStories is tuned for simple short-story continuations and the downloaded weights contain about 68.5M parameters (the upstream repo name says 33M). Pythia-70M is a broader English base model. Neither is instruction-tuned or fact-checked; outputs can still be repetitive, incorrect, or nonsensical. Fine-tuning and generation run locally.</div></div></section>
<section id="settings" class="view"><div class="card" style="max-width:760px"><h2>Runtime & portability</h2><p class="sub">This app runs locally in your browser; no API keys or external model services are used.</p><div id="settingsinfo" class="output" style="min-height:130px">Loading system details…</div><div class="notice info">Checkpoints contain CPU-compatible PyTorch weights plus their tokenizer and config. Fine-tuned models can be copied between Windows and Linux with compatible Python and PyTorch installed. GPU availability and speed vary by machine.</div><h2 style="margin-top:22px">Training data</h2><p class="sub">Training_Data includes five public-domain books and a larger combined training_corpus.txt, with provenance and license notes in its README. Small models still learn only weak language patterns.</p></div></section>
<div class="foot">Runs on your computer · No API keys · Checkpoints stay in this project folder</div></main>
<script>
const $=id=>document.getElementById(id);let running=false,chats=[];
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tab,.view').forEach(x=>x.classList.remove('active'));b.classList.add('active');$(b.dataset.tab).classList.add('active');if(b.dataset.tab==='testing')loadModels()});
async function api(path,opts){const r=await fetch(path,opts);const j=await r.json();if(!r.ok)throw Error(j.error||'Request failed');return j}
function estimate(){const size=$('size').value,steps=+$('steps').value,batch=+$('batch').value,ctx=+$('context').value;let secPer=size==='2M'?0.035:size==='8M'?0.18:2.6;if($('mode').value==='finetune')secPer=0.35;let gpu=$('gpu').textContent.toLowerCase();if(gpu==='none'||gpu.includes('unavailable'))secPer*=5;let secs=steps*secPer*(batch/8)*(ctx/128);let txt=secs<60?`${Math.ceil(secs)} sec`:secs<3600?`${Math.ceil(secs/60)} min`:`${(secs/3600).toFixed(1)} hr`;$('estimate').textContent='Estimated time: ~'+txt}
['size','steps','batch','context','mode'].forEach(id=>$(id).addEventListener('input',estimate));$('mode').addEventListener('change',()=>{const fine=$('mode').value==='finetune';$('scratch-options').style.display=fine?'none':'block';$('finetune-options').style.display=fine?'block':'none';if(fine)$('lr').value='0.0001';else $('lr').value='0.0003';estimate()});$('size').addEventListener('change',()=>{if($('size').value==='100M'&&+$('batch').value>2)$('batch').value=2;if($('size').value==='8M'&&+$('batch').value>4)$('batch').value=4;estimate()});
async function refresh(){try{const s=await api('/api/status');running=s.running;$('dot').className='dot'+(running?' live':'');$('topstatus').textContent=running?'Training active':'Ready';$('cpu').textContent=s.cpu+'%';$('ram').textContent=s.ram+'%';$('gpu').textContent=s.gpu||'None';$('runtime').textContent=s.summary;$('settingsinfo').textContent=s.details;$('start').disabled=running;$('stop').disabled=!running;const log=s.log||'';$('console').textContent=log||'Ready. Choose settings and start a run.';$('console').scrollTop=$('console').scrollHeight;let m=log.match(/STEP (\d+)\/(\d+)/g),last=m&&m.length?m[m.length-1].match(/STEP (\d+)\/(\d+)/):null;if(last){const p=Math.round(+last[1]/+last[2]*100);$('progress').style.width=p+'%';$('progresslabel').textContent=`Step ${last[1]} of ${last[2]} · ${p}%`}else if(!running){$('progress').style.width='0%';$('progresslabel').textContent='Waiting for a run'}}catch(e){$('topstatus').textContent='Dashboard error: '+e.message}}
$('start').onclick=async()=>{try{const body={mode:$('mode').value,size:$('size').value,base_model:$('base-model').value,data_files:selectedDataFiles(),steps:+$('steps').value,batch_size:+$('batch').value,context:+$('context').value,learning_rate:+$('lr').value,name:$('name').value};await api('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});refresh()}catch(e){alert(e.message)}};
$('stop').onclick=async()=>{try{await api('/api/stop',{method:'POST'});refresh()}catch(e){alert(e.message)}};
async function loadModels(){try{const j=await api('/api/models');for(const id of ['models','base-model']){const select=$(id),previous=select.value;select.textContent='';j.models.forEach(m=>{const o=document.createElement('option');o.value=m.name;o.textContent=m.label;select.appendChild(o)});if(j.models.some(m=>m.name===previous))select.value=previous;else if(j.models.some(m=>m.name==='tinystories_33m'))select.value='tinystories_33m';else if(j.models.some(m=>m.name==='pythia_70m'))select.value='pythia_70m';else if(j.models.some(m=>m.name==='nanogpt_starter'))select.value='nanogpt_starter';if(!j.models.length){const o=document.createElement('option');o.textContent='No models found';select.appendChild(o)}}}catch(e){console.error(e)}}
function selectedDataFiles(){return [...document.querySelectorAll('#dataFiles input[type=checkbox]:checked')].map(x=>x.value)}
function updateDataCount(){$('dataCount').textContent=selectedDataFiles().length+' selected'}
async function loadDataFiles(){const box=$('dataFiles');try{const j=await api('/api/data-files');box.textContent='';j.files.forEach(f=>{const row=document.createElement('label');row.className='fileitem';const input=document.createElement('input');input.type='checkbox';input.value=f.path;input.checked=f.path==='training_corpus.txt';input.addEventListener('change',updateDataCount);const name=document.createElement('span');name.textContent=f.path;const meta=document.createElement('span');meta.className='filemeta';meta.textContent=f.chars.toLocaleString()+' chars';row.append(input,name,meta);box.appendChild(row)});if(!j.files.length)box.textContent='No .txt files found in Training_Data. Add UTF-8 text files there and reload.';updateDataCount()}catch(e){box.textContent='Could not load training files: '+e.message}}
$('selectAllData').onclick=()=>{document.querySelectorAll('#dataFiles input[type=checkbox]').forEach(x=>x.checked=true);updateDataCount()};$('clearData').onclick=()=>{document.querySelectorAll('#dataFiles input[type=checkbox]').forEach(x=>x.checked=false);updateDataCount()};
function renderChat(){const box=$('chatbox');box.textContent='';if(!chats.length){const b=document.createElement('div');b.className='bubble assistant';b.textContent='Try TinyStories for simple story continuation, or Pythia-70M for broader text completion. Neither is chat-tuned or fact-checked. Scratch models are learning demos.';box.appendChild(b);return}chats.forEach(m=>{const b=document.createElement('div');b.className='bubble '+(m.role==='user'?'user':'assistant');b.textContent=m.text;box.appendChild(b)});box.scrollTop=box.scrollHeight}
async function sendChat(){const input=$('chatPrompt'),message=input.value.trim();if(!message)return;const btn=$('send');chats.push({role:'user',text:message});input.value='';renderChat();btn.disabled=true;btn.textContent='Thinking…';try{const j=await api('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:$('models').value,messages:chats.slice(-10),max_new_tokens:+$('newtokens').value,temperature:+$('temperature').value})});chats.push({role:'assistant',text:j.text});renderChat()}catch(e){chats.push({role:'assistant',text:'Error: '+e.message});renderChat()}finally{btn.disabled=false;btn.textContent='Send';input.focus()}}
$('send').onclick=sendChat;$('chatPrompt').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendChat()}});$('clearChat').onclick=()=>{chats=[];renderChat()};
refresh();loadModels();loadDataFiles();estimate();setInterval(refresh,2000);
</script></body></html>'''


def safe_model_dir(name):
    name = re.sub(r"[^A-Za-z0-9_-]", "_", str(name or "model"))[:40].strip("_") or "model"
    return ROOT / "Trained_models" / name


def tail_log():
    if not log_path.exists():
        return ""
    with log_lock:
        return "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-250:])


@app.get("/")
def index():
    return render_template_string(PAGE)


@app.get("/api/status")
def status():
    global process
    try:
        import psutil
        cpu = round(psutil.cpu_percent(interval=0.1))
        ram = round(psutil.virtual_memory().percent)
    except Exception:
        cpu, ram = 0, 0
    try:
        import torch
        torch_version = torch.__version__
        cuda_available = torch.cuda.is_available()
        gpu = (torch.cuda.get_device_name(0) + " · " + f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB") if cuda_available else "None"
        device = "CUDA GPU: " + gpu if cuda_available else "CPU (CUDA GPU not detected by PyTorch)"
    except Exception as exc:
        torch_version, gpu, device = "not installed", "Unavailable", str(exc)
    with process_lock:
        running = process is not None and process.poll() is None
    py = f"Python {sys.version.split()[0]} · PyTorch {torch_version}"
    return jsonify(running=running, cpu=cpu, ram=ram, gpu=gpu, summary=py + "\n" + device,
                   details=f"Project folder: {ROOT}\nPython: {sys.version.split()[0]}\nPyTorch: {torch_version}\nCompute: {device}\nTraining data: Training_Data/training_corpus.txt\nOutput: Trained_models/", log=tail_log())


@app.get("/api/data-files")
def data_files():
    data_root = ROOT / "Training_Data"
    items = []
    for path in sorted(data_root.rglob("*.txt")):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
            relative = path.relative_to(data_root).as_posix()
            items.append({"path": relative, "chars": len(content), "bytes": path.stat().st_size})
        except (OSError, UnicodeDecodeError):
            continue
    # Put the combined ready-to-train corpus first; the UI selects it by default.
    items.sort(key=lambda item: (item["path"] != "training_corpus.txt", item["path"].lower()))
    return jsonify(files=items)


@app.post("/api/start")
def start_training():
    global process
    payload = request.get_json(force=True)
    try:
        mode = payload.get("mode", "scratch")
        if mode not in ("scratch", "finetune"):
            raise ValueError("Choose scratch training or fine-tuning.")
        size = payload.get("size", "2M")
        if size not in ("2M", "8M", "100M"):
            raise ValueError("Choose a supported model size.")
        steps = int(payload.get("steps", 500)); batch_size = int(payload.get("batch_size", 8))
        context = int(payload.get("context", 128)); lr = float(payload.get("learning_rate", 0.0003))
        if not 10 <= steps <= 1_000_000 or not 1 <= batch_size <= 256 or context not in (64, 128, 256, 512) or not 0 < lr <= .1:
            raise ValueError("Training settings are outside the allowed range.")
        selected = payload.get("data_files")
        if not selected:
            legacy = payload.get("data")
            selected = [legacy] if legacy else ["training_corpus.txt"]
        if not isinstance(selected, list) or not selected:
            raise ValueError("Select at least one training text file.")
        data_root = (ROOT / "Training_Data").resolve()
        data_paths = []
        for item in dict.fromkeys(str(item) for item in selected):
            rel = Path(item)
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError("Training files must be selected from Training_Data.")
            data_path = (data_root / rel).resolve()
            if data_root not in data_path.parents or not data_path.is_file() or data_path.suffix.lower() != ".txt":
                raise ValueError(f"Invalid training text file: {item}")
            data_paths.append(data_path)
        if not data_paths:
            raise ValueError("Select at least one training text file.")
        out = safe_model_dir(payload.get("name", "my_first_model"))
        if (out / "ckpt.pt").exists():
            raise ValueError("That output name already has a saved model. Pick a new name to avoid overwriting it.")
        cmd = []
        if mode == "scratch":
            cmd = [sys.executable, "-u", str(ROOT / "train.py"), "--data", *[str(path) for path in data_paths], "--output", str(out), "--mode", mode, "--size", size, "--steps", str(steps), "--batch-size", str(batch_size), "--context", str(context), "--learning-rate", str(lr)]
        else:
            base = safe_model_dir(payload.get("base_model", ""))
            base_info = {}
            info_file = base / "model-info.json"
            if info_file.is_file():
                try: base_info = json.loads(info_file.read_text(encoding="utf-8"))
                except Exception: pass
            if out == base:
                raise ValueError("Choose a new output name so the base model is preserved.")
            if base_info.get("kind") == "transformers_causal_lm" and (base / "config.json").is_file() and (base / "model.safetensors").is_file():
                cmd = [sys.executable, "-u", str(ROOT / "train_pretrained.py"), "--base-model", str(base), "--data", *[str(path) for path in data_paths], "--output", str(out), "--steps", str(steps), "--batch-size", str(batch_size), "--context", str(context), "--learning-rate", str(lr)]
            elif (base / "ckpt.pt").is_file():
                cmd = [sys.executable, "-u", str(ROOT / "train.py"), "--data", *[str(path) for path in data_paths], "--output", str(out), "--mode", mode, "--size", size, "--steps", str(steps), "--batch-size", str(batch_size), "--context", str(context), "--learning-rate", str(lr), "--base-model", str(base)]
            else:
                raise ValueError("Select a supported saved nanoGPT or Transformers model to fine-tune.")
        if out.exists() and any(out.iterdir()):
            raise ValueError("That output folder already contains files. Choose a new model name.")
        out.mkdir(parents=True, exist_ok=True)
        with process_lock:
            if process is not None and process.poll() is None:
                raise ValueError("A training run is already active.")
            with log_lock:
                log_path.write_text("Launching: " + " ".join(cmd) + "\n", encoding="utf-8")
            env = os.environ.copy(); env["PYTHONUNBUFFERED"] = "1"
            with open(log_path, "a", encoding="utf-8") as logfile:
                process = subprocess.Popen(cmd, cwd=ROOT, stdout=logfile, stderr=subprocess.STDOUT, env=env)
        return jsonify(ok=True)
    except Exception as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/stop")
def stop_training():
    global process
    with process_lock:
        if process is not None and process.poll() is None:
            process.terminate()
            return jsonify(ok=True)
    return jsonify(error="No training run is active."), 400


@app.get("/api/models")
def models():
    items = []
    folder = ROOT / "Trained_models"
    if not folder.is_dir():
        return jsonify(models=items)
    for p in sorted(folder.iterdir()):
        if not p.is_dir():
            continue
        info = {}
        info_path = p / "model-info.json"
        metadata_path = p / "metadata.json"
        for file in (info_path, metadata_path):
            if file.is_file():
                try: info = json.loads(file.read_text(encoding="utf-8")); break
                except Exception: pass
        if (p / "ckpt.pt").is_file():
            kind = "nanogpt_char"
        elif (p / "config.json").is_file() and (p / "model.safetensors").is_file():
            kind = info.get("kind", "transformers_causal_lm")
        else:
            continue
        label = info.get("name") or p.name
        params = info.get("parameters")
        if params: label += f" · {float(params)/1_000_000:.1f}M"
        items.append({"name": p.name, "kind": kind, "label": label})
    return jsonify(models=items)


def generate_transformer(folder, payload):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(folder), local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        str(folder), local_files_only=True, trust_remote_code=False, use_safetensors=True,
        torch_dtype=torch.float32,
    )
    messages = payload.get("messages") or []
    info = {}
    try:
        info = json.loads((folder / "model-info.json").read_text(encoding="utf-8"))
    except Exception:
        pass
    if info.get("source") == "roneneldan/TinyStories-33M" and messages:
        # This checkpoint is trained to continue stories, not role-labeled chats.
        prompt = next((str(item.get("text", ""))[:1200] for item in reversed(messages) if item.get("role") == "user"), "")
    elif messages:
        prompt = "\n".join(
            ("User: " if item.get("role") == "user" else "Assistant: ") + str(item.get("text", ""))[:1200]
            for item in messages[-10:]
        ) + "\nAssistant:"
    else:
        prompt = str(payload.get("prompt", ""))[:1200]
    if not prompt.strip():
        prompt = "Once upon a time"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device).eval()
    inputs = {key: value.to(device) for key, value in inputs.items()}
    input_length = inputs["input_ids"].shape[1]
    max_positions = int(getattr(model.config, "max_position_embeddings", 2048))
    count = max(1, min(1000, int(payload.get("max_new_tokens", 160)), max_positions - input_length))
    temperature = max(0.1, min(2.0, float(payload.get("temperature", 0.8))))
    with torch.inference_mode():
        output = model.generate(
            **inputs, max_new_tokens=count, do_sample=True, temperature=temperature,
            top_p=0.92, top_k=50, repetition_penalty=1.12,
            pad_token_id=tokenizer.eos_token_id,
        )
    answer = tokenizer.decode(output[0, input_length:], skip_special_tokens=True).strip()
    return answer or "(No text generated; try a different prompt.)"


@app.post("/api/generate")
def generate():
    try:
        import torch
        payload = request.get_json(force=True)
        folder = safe_model_dir(str(payload.get("model", "")))
        if (folder / "model.safetensors").is_file() and (folder / "config.json").is_file():
            return jsonify(text=generate_transformer(folder, payload))
        from nanoGPT.model import GPT, GPTConfig
        checkpoint_path = folder / "ckpt.pt"
        if not checkpoint_path.is_file():
            raise ValueError("Choose a completed local model checkpoint.")
        try:
            checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        except TypeError:
            checkpoint = torch.load(checkpoint_path, map_location="cpu")
        model_args = checkpoint["model_args"]
        model = GPT(GPTConfig(**model_args))
        state = checkpoint["model"]
        prefix = "_orig_mod."
        if any(key.startswith(prefix) for key in state):
            state = {key[len(prefix):] if key.startswith(prefix) else key: value for key, value in state.items()}
        model.load_state_dict(state)
        chars = checkpoint["chars"]
        to_id = {char: idx for idx, char in enumerate(chars)}
        messages = payload.get("messages") or []
        if messages:
            prompt = "\n".join(("User: " if item.get("role") == "user" else "Assistant: ") + str(item.get("text", ""))[:1200] for item in messages[-10:]) + "\nAssistant:"
        else:
            prompt = str(payload.get("prompt", ""))[:1200]
        fallback = to_id.get(" ", 0)
        tokens = torch.tensor([[to_id.get(char, fallback) for char in prompt]], dtype=torch.long)
        if tokens.shape[1] == 0:
            tokens = torch.zeros((1, 1), dtype=torch.long)
        count = max(1, min(1000, int(payload.get("max_new_tokens", 160))))
        temp = max(0.1, min(2.0, float(payload.get("temperature", 0.8))))
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device).eval()
        with torch.no_grad():
            result = model.generate(tokens.to(device), max_new_tokens=count, temperature=temp, top_k=40)
        answer = "".join(chars[int(idx)] for idx in result[0, tokens.shape[1]:].cpu().tolist()).strip()
        return jsonify(text=answer or "(No text generated; try a longer reply or a different prompt.)")
    except Exception as exc:
        return jsonify(error=str(exc)), 400


if __name__ == "__main__":
    # Default to loopback for local use. Preview environments can override the host explicitly.
    app.run(host=os.environ.get("LLM_STUDIO_HOST", "127.0.0.1"), port=7860, debug=False, threaded=True)
