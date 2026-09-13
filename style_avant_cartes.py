CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
:root {
  --bg:#070B14; --surface:#0F1623; --surface2:#141C2B; --line:#1E2A3D;
  --txt:#EAF0F7; --dim:#7C8BA1; --teal:#3DD9C4; --teal2:#5EEAD4;
  --vert:#3DD9C4; --rouge:#FF4D6A; --jaune:#FFC24B;
}
.stApp { background:
  radial-gradient(1200px 600px at 80% -10%, rgba(61,217,196,0.08), transparent 60%),
  radial-gradient(900px 500px at -10% 20%, rgba(94,234,212,0.05), transparent 55%),
  var(--bg);
}
html, body, [class*="css"], .stMarkdown, p, span, div, label {
  font-family:'Inter',sans-serif !important; color:var(--txt);
}
.block-container { padding-top:2.5rem !important; max-width:1100px; }

/* ---- Header ---- */
.hdr { display:flex; align-items:center; gap:16px; margin-bottom:6px; }
.hdr .logo {
  width:52px; height:52px; border-radius:14px; flex-shrink:0;
  background:linear-gradient(135deg,#3DD9C4,#5EEAD4);
  display:flex; align-items:center; justify-content:center;
  font-size:26px; box-shadow:0 8px 24px rgba(61,217,196,0.35);
}
.hdr h1 {
  font-size:2.3rem; font-weight:900; margin:0; letter-spacing:-1px; line-height:1.1;
  background:linear-gradient(90deg,#EAF0F7 20%,#3DD9C4);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.hdr .sub {
  font-size:0.72rem; color:var(--dim); letter-spacing:2px;
  text-transform:uppercase; margin-top:6px; font-weight:600;
}

/* ---- Verdict ---- */
.verdict {
  border-radius:18px; padding:26px 30px; margin:22px 0;
  border:1px solid var(--line); position:relative; overflow:hidden;
  background:linear-gradient(180deg,var(--surface2),var(--surface));
  box-shadow:0 20px 50px rgba(0,0,0,0.4);
}
.verdict::before {
  content:''; position:absolute; left:0; top:0; bottom:0; width:5px;
}
.verdict .etat { font-size:2.3rem; font-weight:900; line-height:1; letter-spacing:-0.5px; }
.verdict .via {
  font-size:0.65rem; letter-spacing:2.5px; text-transform:uppercase;
  color:var(--dim); margin-bottom:10px; font-weight:700;
}
.verdict .msg { font-size:0.9rem; margin-top:14px; color:var(--dim); line-height:1.5; }
.v-mal { background:linear-gradient(180deg,rgba(255,77,106,0.10),var(--surface)); }
.v-mal::before { background:var(--rouge); }
.v-mal .etat { color:var(--rouge); }
.v-sain::before { background:var(--teal); }
.v-sain .etat { color:var(--teal); }
.v-ind::before { background:var(--jaune); }
.v-ind .etat { color:var(--jaune); }

/* ---- Jauge ---- */
.jauge-lbl { display:flex; justify-content:space-between; font-size:0.68rem;
  color:var(--dim); letter-spacing:0.5px; margin-bottom:7px; font-weight:600; }
.jauge { height:7px; background:var(--line); border-radius:99px; overflow:hidden; }
.jauge > div { height:100%; border-radius:99px;
  background:linear-gradient(90deg,var(--teal),var(--teal2)); }

/* ---- Cartes ---- */
.grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:16px 0; }
.carte {
  background:linear-gradient(180deg,var(--surface2),var(--surface));
  border:1px solid var(--line); border-radius:16px; padding:18px 20px;
  transition:all 0.2s ease;
}
.carte:hover { border-color:var(--teal); transform:translateY(-2px);
  box-shadow:0 12px 30px rgba(61,217,196,0.12); }
.carte .k { font-size:0.6rem; letter-spacing:2px; text-transform:uppercase;
  color:var(--dim); margin-bottom:8px; font-weight:700; }
.carte .v { font-size:1.35rem; font-weight:800; }
.hash { background:var(--surface); border:1px solid var(--line);
  border-radius:12px; padding:12px 16px; font-size:0.72rem;
  color:var(--dim); word-break:break-all; font-family:'Inter',monospace; }
.hash b { color:var(--teal); font-weight:700; }

/* ---- SHAP ---- */
.shap-ax { display:flex; justify-content:space-between; font-size:0.58rem;
  letter-spacing:1.5px; text-transform:uppercase; color:var(--dim);
  padding-bottom:10px; border-bottom:1px solid var(--line); margin-bottom:12px; font-weight:700; }
.shap-l { display:flex; align-items:center; height:30px; font-size:0.75rem; }
.shap-nom { width:30%; color:var(--dim); text-align:right; padding-right:14px; font-weight:500; }
.shap-bar { width:52%; display:flex; align-items:center; position:relative; }
.shap-bar::before { content:''; position:absolute; left:50%; top:-3px; bottom:-3px;
  width:1px; background:var(--line); }
.shap-half { width:50%; display:flex; }
.shap-half.g { justify-content:flex-end; }
.shap-fill { height:11px; border-radius:99px; }
.shap-val { width:18%; text-align:right; font-size:0.72rem; color:var(--dim); font-weight:600; }

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] { gap:6px; background:transparent;
  border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { background:transparent; color:var(--dim);
  border-radius:10px 10px 0 0; font-size:0.82rem !important; letter-spacing:0.3px;
  font-weight:600; padding:12px 20px; transition:all 0.15s; }
.stTabs [data-baseweb="tab"]:hover { color:var(--txt); background:rgba(61,217,196,0.05); }
.stTabs [aria-selected="true"] { color:var(--teal) !important;
  border-bottom:2px solid var(--teal); font-weight:700; }

/* ---- Boutons ---- */
.stButton > button {
  background:linear-gradient(135deg,var(--teal),var(--teal2)); color:#04141A;
  border:none; border-radius:12px; font-size:0.82rem; letter-spacing:0.5px;
  text-transform:uppercase; padding:12px 34px; font-weight:800;
  box-shadow:0 8px 20px rgba(61,217,196,0.3); transition:all 0.2s;
}
.stButton > button:hover { transform:translateY(-2px);
  box-shadow:0 12px 28px rgba(61,217,196,0.45); color:#04141A; }

/* ---- Uploader ---- */
[data-testid="stFileUploader"] { background:transparent; }
[data-testid="stFileUploader"] section {
  background:linear-gradient(180deg,var(--surface2),var(--surface)) !important;
  border:1.5px dashed var(--line) !important; border-radius:16px !important;
  transition:all 0.2s; }
[data-testid="stFileUploader"] section:hover { border-color:var(--teal) !important; }

/* ---- Métriques ---- */
[data-testid="stMetric"] {
  background:linear-gradient(180deg,var(--surface2),var(--surface));
  border:1px solid var(--line); border-radius:16px; padding:16px 20px; }
[data-testid="stMetricValue"] { color:var(--teal) !important; font-weight:800 !important; }

.streamlit-expanderHeader { background:var(--surface) !important;
  border:1px solid var(--line) !important; border-radius:12px !important;
  font-size:0.75rem !important; color:var(--dim) !important; }
.stDataFrame { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
hr { border-color:var(--line); }
footer, #MainMenu, header { visibility:hidden; }
</style>
"""
