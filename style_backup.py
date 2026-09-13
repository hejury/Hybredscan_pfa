CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');
:root {
  --bg:#0B0E11; --surface:#141920; --line:#222B36; --txt:#E4E9EF; --dim:#7A8899;
  --vert:#00E676; --rouge:#FF3D3D; --jaune:#FFC400;
}
.stApp { background: var(--bg); }
html, body, [class*="css"], .stMarkdown, p, span, div, label {
  font-family:'JetBrains Mono',monospace !important; color:var(--txt);
}
.hdr { border-left:3px solid var(--vert); padding:4px 0 4px 16px; margin-bottom:4px; }
.hdr h1 { font-size:1.6rem; font-weight:700; margin:0; color:var(--txt); }
.hdr .sub { font-size:0.72rem; color:var(--dim); letter-spacing:1.5px; text-transform:uppercase; margin-top:3px; }
.verdict { border-radius:3px; padding:22px 26px; margin:18px 0; border-left:5px solid; }
.verdict .etat { font-size:2.1rem; font-weight:700; line-height:1; }
.verdict .via { font-size:0.68rem; letter-spacing:2px; text-transform:uppercase; color:var(--dim); margin-bottom:8px; }
.verdict .msg { font-size:0.85rem; margin-top:12px; opacity:0.85; }
.v-mal { background:rgba(255,61,61,0.07); border-color:var(--rouge); }
.v-mal .etat { color:var(--rouge); }
.v-sain { background:rgba(0,230,118,0.06); border-color:var(--vert); }
.v-sain .etat { color:var(--vert); }
.v-ind { background:rgba(255,196,0,0.06); border-color:var(--jaune); }
.v-ind .etat { color:var(--jaune); }
.jauge-lbl { display:flex; justify-content:space-between; font-size:0.65rem; color:var(--dim); letter-spacing:1px; margin-bottom:5px; }
.jauge { height:5px; background:var(--line); border-radius:3px; overflow:hidden; }
.jauge > div { height:100%; border-radius:3px; }
.carte { background:var(--surface); border:1px solid var(--line); border-radius:3px; padding:14px 16px; }
.carte .k { font-size:0.62rem; letter-spacing:1.5px; text-transform:uppercase; color:var(--dim); margin-bottom:5px; }
.carte .v { font-size:1.25rem; font-weight:500; }
.hash { background:var(--surface); border:1px solid var(--line); border-radius:3px; padding:9px 13px; font-size:0.72rem; color:var(--dim); word-break:break-all; }
.hash b { color:var(--vert); font-weight:500; }
.shap-ax { display:flex; justify-content:space-between; font-size:0.6rem; letter-spacing:1.5px; text-transform:uppercase; color:var(--dim); padding-bottom:8px; border-bottom:1px solid var(--line); margin-bottom:10px; }
.shap-l { display:flex; align-items:center; height:26px; font-size:0.72rem; }
.shap-nom { width:30%; color:var(--dim); text-align:right; padding-right:12px; }
.shap-bar { width:52%; display:flex; align-items:center; position:relative; }
.shap-bar::before { content:''; position:absolute; left:50%; top:-3px; bottom:-3px; width:1px; background:var(--line); }
.shap-half { width:50%; display:flex; }
.shap-half.g { justify-content:flex-end; }
.shap-fill { height:9px; border-radius:1px; }
.shap-val { width:18%; text-align:right; font-size:0.68rem; color:var(--dim); }
.stTabs [data-baseweb="tab-list"] { gap:2px; background:transparent; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { background:transparent; color:var(--dim); border-radius:0; font-size:0.72rem !important; letter-spacing:1.5px; text-transform:uppercase; padding:10px 20px; }
.stTabs [aria-selected="true"] { color:var(--vert) !important; border-bottom:2px solid var(--vert); }
.stButton > button { background:var(--vert); color:var(--bg); border:none; border-radius:2px; font-family:'JetBrains Mono',monospace !important; font-weight:700; font-size:0.72rem; letter-spacing:2px; text-transform:uppercase; padding:11px 30px; }
.stButton > button:hover { opacity:0.82; color:var(--bg); }
[data-testid="stFileUploader"] { background:var(--surface); border:1px dashed var(--line); border-radius:3px; }
[data-testid="stFileUploader"] section { background:transparent; }
.streamlit-expanderHeader { background:var(--surface) !important; border:1px solid var(--line) !important; font-size:0.72rem !important; color:var(--dim) !important; }
.stDataFrame { border:1px solid var(--line); }
hr { border-color:var(--line); }
footer, #MainMenu, header { visibility:hidden; }
.note { font-size:0.65rem; color:var(--dim); border-top:1px solid var(--line); padding-top:12px; margin-top:28px; }
</style>
"""
