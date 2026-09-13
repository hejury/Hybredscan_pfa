CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root {
  --bg:#FFFFFF; --surface:#F7F9FB; --line:#E3E8EF; --txt:#1A2332; --dim:#6B7A90;
  --vert:#00A88E; --vert2:#12C4A6; --rouge:#E5484D; --jaune:#E6A700;
}
.stApp { background:var(--bg); }
html, body, [class*="css"], .stMarkdown, p, span, div, label {
  font-family:'Inter',sans-serif !important; color:var(--txt);
}
.block-container { padding-top:2rem !important; max-width:1000px; }

/* ---- Sidebar Kaspersky ---- */
[data-testid="stSidebar"] { background:#FFFFFF; border-right:1px solid var(--line); min-width:290px !important; }
[data-testid="collapsedControl"] { display:block !important; }
[data-testid="stSidebar"] > div { padding-top:1.5rem; }
.kl { display:flex; align-items:center; gap:12px; padding:0 4px 20px 4px; }
.kl-hex { width:44px; height:44px; border-radius:12px;
  background:linear-gradient(135deg,var(--vert),var(--vert2));
  display:flex; align-items:center; justify-content:center;
  color:#fff; font-size:22px; flex-shrink:0; }
.kl-t { font-size:0.92rem; font-weight:700; color:var(--txt); line-height:1.2; }
.kl-s { font-size:0.68rem; color:var(--dim); margin-top:2px; }
.ki { padding:11px 14px; border-radius:10px; font-size:0.86rem; font-weight:500;
  color:var(--dim); margin-bottom:-42px; position:relative; z-index:1; transition:all 0.15s; }
.ki.actif { background:#E8F7F4; color:var(--vert); font-weight:700; }
.kf { font-size:0.66rem; color:var(--dim); padding:18px 4px 0 4px;
  border-top:1px solid var(--line); margin-top:14px; line-height:1.5; }
[data-testid="stSidebar"] .stButton > button {
  background:transparent !important; border:none !important; box-shadow:none !important;
  color:transparent !important; height:42px; padding:0 !important; position:relative; z-index:3; }
[data-testid="stSidebar"] .stButton > button:hover { background:rgba(0,168,142,0.05) !important; }

/* ---- Header ---- */
.hdr { border-left:none; padding:0 0 4px 0; margin-bottom:20px; }
.hdr h1 { font-size:2.2rem; font-weight:800; margin:0; color:var(--txt); letter-spacing:-0.5px; }
.hdr .sub { font-size:0.72rem; color:var(--dim); letter-spacing:1.5px;
  text-transform:uppercase; margin-top:4px; font-weight:600; }

/* ---- Verdict ---- */
.verdict { border-radius:14px; padding:24px 28px; margin:18px 0;
  border:1px solid var(--line); border-left:5px solid; background:var(--surface); }
.verdict .etat { font-size:2rem; font-weight:800; line-height:1; }
.verdict .via { font-size:0.66rem; letter-spacing:1.5px; text-transform:uppercase;
  color:var(--dim); margin-bottom:8px; font-weight:700; }
.verdict .msg { font-size:0.88rem; margin-top:12px; color:var(--dim); }
.v-mal { background:#FDECEC; border-color:var(--rouge) !important; }
.v-mal .etat { color:var(--rouge); }
.v-sain { background:#E8F7F4; border-color:var(--vert) !important; }
.v-sain .etat { color:var(--vert); }
.v-ind { background:#FEF7E6; border-color:var(--jaune) !important; }
.v-ind .etat { color:var(--jaune); }

/* ---- Jauge ---- */
.jauge-lbl { display:flex; justify-content:space-between; font-size:0.66rem;
  color:var(--dim); margin-bottom:6px; font-weight:600; }
.jauge { height:7px; background:var(--line); border-radius:99px; overflow:hidden; }
.jauge > div { height:100%; border-radius:99px;
  background:linear-gradient(90deg,var(--vert),var(--vert2)); }

/* ---- Cartes ---- */
.carte { background:#fff; border:1px solid var(--line); border-radius:14px;
  padding:16px 18px; transition:all 0.2s; }
.carte:hover { border-color:var(--vert); box-shadow:0 6px 18px rgba(0,168,142,0.08); }
.carte .k { font-size:0.6rem; letter-spacing:1.5px; text-transform:uppercase;
  color:var(--dim); margin-bottom:6px; font-weight:700; }
.carte .v { font-size:1.3rem; font-weight:800; }
.hash { background:var(--surface); border:1px solid var(--line); border-radius:10px;
  padding:11px 15px; font-size:0.72rem; color:var(--dim); word-break:break-all; }
.hash b { color:var(--vert); font-weight:700; }

/* ---- SHAP ---- */
.shap-ax { display:flex; justify-content:space-between; font-size:0.58rem;
  letter-spacing:1px; text-transform:uppercase; color:var(--dim);
  padding-bottom:10px; border-bottom:1px solid var(--line); margin-bottom:12px; font-weight:700; }
.shap-l { display:flex; align-items:center; height:28px; font-size:0.74rem; }
.shap-nom { width:30%; color:var(--dim); text-align:right; padding-right:12px; }
.shap-bar { width:52%; display:flex; align-items:center; position:relative; }
.shap-bar::before { content:''; position:absolute; left:50%; top:-3px; bottom:-3px;
  width:1px; background:var(--line); }
.shap-half { width:50%; display:flex; }
.shap-half.g { justify-content:flex-end; }
.shap-fill { height:10px; border-radius:99px; }
.shap-val { width:18%; text-align:right; font-size:0.72rem; color:var(--dim); font-weight:600; }

/* ---- Boutons principaux ---- */
.stButton > button { background:var(--vert); color:#fff; border:none; border-radius:10px;
  font-size:0.82rem; font-weight:700; padding:11px 30px; transition:all 0.2s; }
.stButton > button:hover { background:var(--vert2); color:#fff; transform:translateY(-1px);
  box-shadow:0 8px 20px rgba(0,168,142,0.25); }

/* ---- Uploader ---- */
[data-testid="stFileUploader"] section {
  background:var(--surface) !important; border:2px dashed var(--line) !important;
  border-radius:14px !important; }
[data-testid="stFileUploader"] section:hover { border-color:var(--vert) !important; }

[data-testid="stMetric"] { background:#fff; border:1px solid var(--line);
  border-radius:14px; padding:16px 18px; }
[data-testid="stMetricValue"] { color:var(--vert) !important; font-weight:800 !important; }
.streamlit-expanderHeader { background:var(--surface) !important;
  border:1px solid var(--line) !important; border-radius:10px !important; }
.stDataFrame { border:1px solid var(--line); border-radius:10px; overflow:hidden; }
hr { border-color:var(--line); }

/* Force sidebar visible */
[data-testid="stSidebar"] { min-width:280px !important; max-width:280px !important;
  transform:none !important; visibility:visible !important; }
[data-testid="stSidebarCollapsedControl"] { display:none !important; }
section[data-testid="stSidebar"][aria-expanded="false"] { margin-left:0 !important; }
/* sidebar_force */

/* Fix texte double : cacher le label HTML, styler le vrai bouton */
[data-testid="stSidebar"] .ki { display:none !important; }
[data-testid="stSidebar"] .stButton > button {
  background:transparent !important; border:none !important; box-shadow:none !important;
  color:var(--dim) !important; text-align:left !important; justify-content:flex-start !important;
  font-size:0.88rem !important; font-weight:500 !important; padding:11px 14px !important;
  height:auto !important; border-radius:10px !important; }
[data-testid="stSidebar"] .stButton > button:hover {
  background:#E8F7F4 !important; color:var(--vert) !important; transform:none !important; }
/* fix_double */

/* ---- Rangement final ---- */
/* Cacher texte double du file uploader */
[data-testid="stFileUploaderDropzoneInstructions"] span { display:none; }
[data-testid="stFileUploaderDropzoneInstructions"]::before {
  content:"Glissez un fichier ou cliquez"; font-size:0.82rem; color:var(--dim); }
[data-testid="stFileUploader"] button { background:var(--vert) !important;
  color:#fff !important; border-radius:8px !important; font-size:0.78rem !important; }

/* Sidebar : liens alignes a gauche, meilleur espacement */
[data-testid="stSidebar"] .stButton > button {
  text-align:left !important; padding-left:16px !important; }
[data-testid="stSidebar"] .stButton { margin-bottom:2px; }

/* Espacement general */
.block-container { padding-top:2.5rem !important; padding-left:3rem !important; }
[data-testid="stHorizontalBlock"] { gap:14px; }

/* Titre plus propre */
.hdr h1 { margin-bottom:2px !important; }
/* rangement_final */
footer, #MainMenu, header { visibility:hidden; }
</style>
"""
