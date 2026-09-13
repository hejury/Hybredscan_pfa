"""style"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
  --bg:#0A0E1A; --bg2:#0F1524; --surface:#141B2D; --surface2:#1A2338;
  --line:#232D45; --line2:#2E3B57;
  --txt:#E8EDF7; --dim:#8494B4; --dim2:#5A6B8C;
  --cyan:#00D9FF; --cyan2:#00A8E0; --bleu:#2E7DFF;
  --vert:#00E5A0; --rouge:#FF4D6D; --jaune:#FFB020;
  --glow:rgba(0,217,255,0.15);
}

.stApp { background:var(--bg);
  background-image:radial-gradient(circle at 15% 0%, rgba(46,125,255,0.08) 0%, transparent 40%),
                   radial-gradient(circle at 85% 100%, rgba(0,217,255,0.06) 0%, transparent 40%); }
html, body, [class*="css"], .stMarkdown, p, span, div, label {
  font-family:'Inter',sans-serif !important; color:var(--txt); }
.block-container { padding-top:2.5rem !important; padding-left:3rem !important; max-width:1050px; }

[data-testid="stSidebar"] { background:var(--bg2);
  border-right:1px solid var(--line); min-width:280px !important; max-width:280px !important;
  transform:none !important; visibility:visible !important; }
[data-testid="stSidebarCollapsedControl"] { display:none !important; }
section[data-testid="stSidebar"][aria-expanded="false"] { margin-left:0 !important; }
[data-testid="stSidebar"] > div { padding-top:1.5rem; }

.kl { display:flex; align-items:center; gap:12px; padding:0 8px 22px 8px;
  border-bottom:1px solid var(--line); margin-bottom:14px; }
.kl-hex { width:46px; height:46px; border-radius:13px;
  background:linear-gradient(135deg,var(--cyan),var(--bleu));
  display:flex; align-items:center; justify-content:center;
  color:#04101F; font-size:22px; font-weight:900; flex-shrink:0;
  box-shadow:0 0 20px var(--glow); }
.kl-t { font-size:0.94rem; font-weight:800; color:var(--txt); line-height:1.2; }
.kl-s { font-size:0.66rem; color:var(--dim2); margin-top:3px; letter-spacing:0.3px; }

.kl-lbl { font-size:0.6rem; letter-spacing:1.6px; text-transform:uppercase;
  color:var(--dim2); padding:4px 10px 8px; font-weight:700; }

.kf { font-size:0.64rem; color:var(--dim2); padding:18px 4px 0 4px;
  border-top:1px solid var(--line); margin-top:16px; line-height:1.5; }

[data-testid="stSidebar"] .stButton > button {
  background:transparent !important; border:none !important; box-shadow:none !important;
  color:var(--dim) !important; text-align:left !important; justify-content:flex-start !important;
  font-size:0.88rem !important; font-weight:500 !important; padding:11px 16px !important;
  height:auto !important; border-radius:10px !important; width:100% !important;
  transition:background 0.15s, color 0.15s !important; }
[data-testid="stSidebar"] .stButton > button:hover {
  background:var(--surface2) !important; color:var(--cyan) !important; transform:none !important;
  box-shadow:none !important; }
[data-testid="stSidebar"] .stButton > button:focus {
  background:var(--surface2) !important; color:var(--cyan) !important; box-shadow:none !important; }
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background:linear-gradient(135deg,rgba(0,217,255,0.12),rgba(46,125,255,0.08)) !important;
  color:var(--cyan) !important; font-weight:700 !important;
  box-shadow:inset 3px 0 0 var(--cyan) !important; }
[data-testid="stSidebar"] .stButton { margin-bottom:3px; }

.hdr { border-left:none; padding:0 0 6px 0; margin-bottom:24px; }
.hdr h1 { font-size:2.3rem; font-weight:900; margin:0 0 2px 0 !important; color:var(--txt);
  letter-spacing:-0.8px;
  background:linear-gradient(135deg,var(--txt) 40%,var(--cyan));
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.hdr .sub { font-size:0.72rem; color:var(--dim); letter-spacing:1.5px;
  text-transform:uppercase; margin-top:10px; font-weight:600; }

.verdict { border-radius:16px; padding:26px 30px; margin:18px 0;
  border:1px solid var(--line); border-left:5px solid;
  background:var(--surface); position:relative; overflow:hidden; }
.verdict::after { content:''; position:absolute; top:0; right:0; width:180px; height:100%;
  background:radial-gradient(circle at right, var(--glow), transparent 70%); opacity:0.5; }
.verdict .etat { font-size:2.1rem; font-weight:900; line-height:1; }
.verdict .via { font-size:0.66rem; letter-spacing:1.5px; text-transform:uppercase;
  color:var(--dim); margin-bottom:8px; font-weight:700; }
.verdict .msg { font-size:0.9rem; margin-top:12px; color:var(--dim); }
.v-mal { border-color:var(--rouge) !important; }
.v-mal .etat { color:var(--rouge); }
.v-sain { border-color:var(--vert) !important; }
.v-sain .etat { color:var(--vert); }
.v-ind { border-color:var(--jaune) !important; }
.v-ind .etat { color:var(--jaune); }

.jauge-lbl { display:flex; justify-content:space-between; font-size:0.66rem;
  color:var(--dim); margin-bottom:6px; font-weight:600; }
.jauge { height:8px; background:var(--line); border-radius:99px; overflow:hidden; }
.jauge > div { height:100%; border-radius:99px;
  background:linear-gradient(90deg,var(--cyan),var(--bleu));
  box-shadow:0 0 10px var(--glow); }

.carte { background:var(--surface); border:1px solid var(--line); border-radius:16px;
  padding:18px 20px; transition:all 0.2s; }
.carte:hover { border-color:var(--cyan); box-shadow:0 6px 24px rgba(0,217,255,0.1); }
.carte .k { font-size:0.6rem; letter-spacing:1.5px; text-transform:uppercase;
  color:var(--dim2); margin-bottom:8px; font-weight:700; }
.carte .v { font-size:1.35rem; font-weight:800; }
.hash { background:var(--surface); border:1px solid var(--line); border-radius:12px;
  padding:12px 16px; font-size:0.72rem; color:var(--dim); word-break:break-all;
  font-family:'Courier New',monospace; }
.hash b { color:var(--cyan); font-weight:700; font-family:'Inter'; }

.safenote { display:flex; align-items:center; gap:10px; margin:16px 0 8px;
  font-size:0.8rem; color:var(--dim);
  background:rgba(0,229,160,0.06); border:1px solid rgba(0,229,160,0.16);
  border-radius:12px; padding:12px 16px; }
.safenote .dot { color:var(--vert); font-size:0.7rem; }

.shap-ax { display:flex; justify-content:space-between; font-size:0.58rem;
  letter-spacing:1px; text-transform:uppercase; color:var(--dim2);
  padding-bottom:10px; border-bottom:1px solid var(--line); margin-bottom:12px; font-weight:700; }
.shap-l { display:flex; align-items:center; height:28px; font-size:0.74rem; }
.shap-nom { width:30%; color:var(--dim); text-align:right; padding-right:12px; }
.shap-bar { width:52%; display:flex; align-items:center; position:relative; }
.shap-bar::before { content:''; position:absolute; left:50%; top:-3px; bottom:-3px;
  width:1px; background:var(--line2); }
.shap-half { width:50%; display:flex; }
.shap-half.g { justify-content:flex-end; }
.shap-fill { height:10px; border-radius:99px; }
.shap-val { width:18%; text-align:right; font-size:0.72rem; color:var(--dim); font-weight:600; }

.stButton > button { background:linear-gradient(135deg,var(--cyan),var(--bleu));
  color:#04101F; border:none; border-radius:11px; font-size:0.82rem; font-weight:800;
  padding:11px 32px; transition:all 0.2s; box-shadow:0 0 0 rgba(0,217,255,0); }
.stButton > button:hover { transform:translateY(-2px);
  box-shadow:0 8px 24px rgba(0,217,255,0.35); color:#04101F; }

[data-testid="stFileUploader"] { max-width:520px; margin:10px auto 0 auto; display:flex !important; flex-direction:column !important; align-items:center !important; }
[data-testid="stFileUploader"] svg { display:none !important; }
[data-testid="stFileUploader"] section { align-items:center !important; text-align:center !important;
  background:transparent !important; border:none !important;
  padding:16px 0 !important; display:flex !important; flex-direction:column !important;
  align-items:center !important; justify-content:center !important; gap:26px !important; }
[data-testid="stFileUploaderDropzoneInstructions"] { display:none !important; }
[data-testid="stFileUploader"] section::before {
  content:'' !important; display:block !important; width:100px !important; height:116px !important;
  background-repeat:no-repeat !important; background-position:center !important;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 116' fill='none'><path d='M20 6 h44 l18 18 v86 h-62 z' stroke='%23FFFFFF' stroke-width='3'/><path d='M64 6 v18 h18' stroke='%23FFFFFF' stroke-width='3'/><line x1='8' y1='44' x2='92' y2='44' stroke='%232E7DFF' stroke-width='6'/><g stroke='%23FFFFFF' stroke-width='2.4' fill='none' stroke-linecap='round'><path d='M50 58 c-11 0 -20 9 -20 20 v8'/><path d='M50 58 c11 0 20 9 20 20 v4'/><path d='M50 66 c-7 0 -12 5 -12 12 v10'/><path d='M50 66 c7 0 12 5 12 12 v6 c0 3 0 6 -1 9'/><path d='M50 74 c-4 0 -6 3 -6 8 v10'/><path d='M50 74 c4 0 6 3 6 8 v8'/><path d='M50 82 v14'/></g></svg>") !important; }









[data-testid="stExpander"] summary,
[data-testid="stExpander"] details summary {
  display:flex !important; align-items:center !important;
  white-space:nowrap !important; overflow:hidden !important;
  letter-spacing:normal !important; }
[data-testid="stExpander"] summary > *,
[data-testid="stExpander"] summary p {
  position:static !important; float:none !important;
  transform:none !important; margin:0 !important;
  font-family:'Courier New',monospace !important; font-size:0.8rem !important;
  color:#E8EDF7 !important; }

[data-testid="stExpander"] summary svg,
[data-testid="stExpander"] summary [data-testid="stIconMaterial"],
[data-testid="stExpander"] summary .material-icons,
[data-testid="stExpander"] summary span[class*="icon"],
[data-testid="stExpander"] summary i {
  display:none !important; }
[data-testid="stExpander"] summary {
  display:flex !important; align-items:center !important; gap:8px !important; }
[data-testid="stExpander"] summary p {
  font-family:'Courier New',monospace !important; font-size:0.8rem !important;
  color:#E8EDF7 !important; white-space:nowrap !important;
  overflow:hidden !important; text-overflow:ellipsis !important; }

[data-testid="stExpander"] summary::-webkit-details-marker { display:none !important; }
[data-testid="stExpander"] summary { list-style:none !important; }
span[data-testid="stIconMaterial"],
[class*="material-symbols"],
[class*="material-icons"] { font-size:0 !important; width:0 !important; overflow:hidden !important; }
[data-testid="stExpander"] details > summary > span:first-child { font-size:0 !important; }

[data-testid="stFileUploader"] section {
  align-items:center !important; text-align:center !important; }



























[data-testid="stFileUploader"] section { display:flex !important; flex-direction:column !important; align-items:center !important; }
[data-testid="stFileUploader"] section > button {
  all:unset !important; box-sizing:border-box !important; cursor:pointer !important;
  display:flex !important; align-items:center !important; justify-content:center !important;
  width:auto !important; margin:0 auto !important; padding:12px 40px !important;
  border:1px solid #6B7BA5 !important; border-radius:8px !important;
  color:#B8C4E0 !important; font-size:1rem !important; font-weight:500 !important;
  font-family:'Inter',sans-serif !important; text-align:center !important; }
[data-testid="stFileUploader"] section > button:hover {
  border-color:#00D9FF !important; color:#00D9FF !important; }
[data-testid="stFileUploader"] section > button > * {
  all:unset !important; font:inherit !important; color:inherit !important; }

[data-testid="stFileUploaderDropzone"] > button,
[data-testid="stFileUploader"] section > button {
  display:flex !important; align-items:center !important; justify-content:center !important;
  text-indent:0 !important; }
[data-testid="stFileUploader"] section > button::first-letter { margin:0 !important; }
[data-testid="stBaseButton-secondary"] {
  display:flex !important; align-items:center !important; justify-content:center !important; }
[data-testid="stBaseButton-secondary"] > * { margin:0 auto !important; }
</style>
"""
