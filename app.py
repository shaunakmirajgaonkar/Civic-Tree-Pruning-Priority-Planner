from pathlib import Path
import io
import math
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='Civic Tree-Pruning Priority Planner', page_icon='🌳', layout='wide', initial_sidebar_state='expanded')

ROOT = Path(__file__).parent
DATA = ROOT / 'data'
ASSETS = ROOT / 'assets'

REQUIRED = [
    'tree_id','tree_species','zone','street_name','latitude','longitude','tree_height_m',
    'branch_condition_score','power_line_distance_m','pedestrian_use_index','wind_risk_index',
    'inspection_condition_score','inspection_age_days','dead_branch_pct','canopy_density_pct',
    'last_pruned_days','crew_access_score','near_school_score','near_road_score','recent_incident_count',
    'work_order_status','last_inspection_date'
]

NUMERIC = [c for c in REQUIRED if c not in ['tree_id','tree_species','zone','street_name','work_order_status','last_inspection_date']]

@st.cache_data

def load_csv(source, fallback):
    if source is None:
        return pd.read_csv(fallback)
    try:
        return pd.read_csv(source)
    except Exception:
        return pd.read_csv(fallback)


def validate(df):
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return False, missing
    out = df.copy()
    for c in NUMERIC:
        out[c] = pd.to_numeric(out[c], errors='coerce').fillna(0)
    return True, out


def clamp(s):
    return pd.Series(s).clip(0, 100)


def score_trees(df):
    x = df.copy()
    # Higher score = stronger reason for additional pruning review.
    condition = 100 - clamp(x['branch_condition_score'])
    line = clamp(100 - x['power_line_distance_m'] * 10)
    pedestrian = clamp(x['pedestrian_use_index'])
    wind = clamp(x['wind_risk_index'])
    inspection = 100 - clamp(x['inspection_condition_score'])
    dead = clamp(x['dead_branch_pct'] * 2.0)
    overdue = clamp((x['last_pruned_days'] - 180) / 3.0)
    recency = clamp(x['inspection_age_days'] / 3.65)
    incidents = clamp(x['recent_incident_count'] * 20)
    road = clamp(x['near_road_score'])
    school = clamp(x['near_school_score'])
    x['priority_score'] = np.round(clamp(
        condition*0.20 + line*0.14 + pedestrian*0.12 + wind*0.13 + inspection*0.14 +
        dead*0.08 + overdue*0.06 + recency*0.04 + incidents*0.04 + road*0.025 + school*0.025
    ), 1)
    x['priority_class'] = pd.cut(x['priority_score'], [-1, 24.9, 49.9, 74.9, 101], labels=['Routine','Watch','High','Critical'])
    x['pruning_urgency_days'] = np.select(
        [x['priority_score']>=75, x['priority_score']>=50, x['priority_score']>=25], [7, 30, 90], default=180
    )
    x['power_line_risk'] = clamp(100 - x['power_line_distance_m']*10)
    x['pedestrian_exposure'] = pedestrian
    x['structural_risk'] = clamp(condition*0.65 + inspection*0.35)
    x['access_adjusted_priority'] = np.round(clamp(x['priority_score']*0.82 + (100-x['crew_access_score'])*0.18), 1)
    def drivers(r):
        vals = {
            'Branch condition': condition.loc[r.name], 'Power-line proximity': line.loc[r.name],
            'Pedestrian exposure': pedestrian.loc[r.name], 'Wind risk': wind.loc[r.name],
            'Inspection condition': inspection.loc[r.name], 'Dead branches': dead.loc[r.name]
        }
        return ', '.join([k for k,v in sorted(vals.items(), key=lambda z:z[1], reverse=True)[:3]])
    x['top_risk_drivers'] = x.apply(drivers, axis=1)
    return x


def metric_card(label, value, sub=''):
    st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)


def pct(v): return f'{float(v):.1f}%'

# CSS: bright, readable, intentionally different from a generic dark analytics dashboard.
st.markdown('''
<style>
:root { color-scheme: light; }
.stApp { background: #f6f8fb; color: #172033; }
.block-container { padding-top: 1.4rem; max-width: 1500px; }
section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e7eaf0; }
section[data-testid="stSidebar"] * { color: #172033 !important; }
h1,h2,h3,h4,p,li,label,.stMarkdown { color: #172033 !important; }
.hero { background: linear-gradient(115deg,#ffffff 0%,#eef7ff 52%,#effcf4 100%); border: 1px solid #dfe8f2; border-radius: 26px; padding: 28px 30px; margin-bottom: 18px; box-shadow: 0 10px 28px rgba(40,65,95,.07); }
.hero-kicker { color:#1677b8 !important; font-size:12px; font-weight:800; letter-spacing:1.5px; text-transform:uppercase; }
.hero-title { font-size:38px; font-weight:900; line-height:1.05; margin:5px 0 8px; }
.hero-copy { font-size:15px; color:#536174 !important; max-width:900px; }
.metric-card { background:#fff; border:1px solid #e2e8f0; border-radius:18px; padding:18px; min-height:125px; box-shadow:0 6px 20px rgba(34,48,70,.05); }
.metric-label { font-size:12px; font-weight:800; color:#697689 !important; text-transform:uppercase; letter-spacing:.7px; }
.metric-value { font-size:31px; font-weight:900; color:#142033 !important; margin-top:6px; }
.metric-sub { font-size:12px; color:#718096 !important; margin-top:4px; }
.panel { background:#fff; border:1px solid #e2e8f0; border-radius:20px; padding:20px; box-shadow:0 6px 20px rgba(34,48,70,.045); margin:10px 0; }
.section-title { font-size:20px; font-weight:850; margin-bottom:2px; }
.section-sub { color:#6a7788 !important; font-size:13px; margin-bottom:14px; }
.badge { display:inline-block; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:800; margin-right:6px; }
.badge-green { background:#e8f7ed; color:#197344 !important; }
.badge-blue { background:#e8f2ff; color:#1766a7 !important; }
.badge-orange { background:#fff1df; color:#a65a00 !important; }
.badge-red { background:#ffe8e8; color:#b42318 !important; }
.queue-row { background:#fff; border:1px solid #e4e9ef; border-radius:14px; padding:13px 15px; margin:7px 0; }
.small-muted { color:#6d7988 !important; font-size:12px; }
.stButton>button { border-radius:12px; font-weight:750; }
[data-testid="stDataFrame"] { border-radius:14px; overflow:hidden; }
</style>
''', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('## 🌳 CanopyOps')
    st.caption('Local-first civic tree-pruning intelligence')
    st.divider()
    st.markdown('### 📥 Local data center')
    up = st.file_uploader('Upload tree inspection CSV', type=['csv'], help='CSV only; processing stays in this app session.')
    if up is not None:
        try:
            raw = pd.read_csv(up)
            ok, missing = validate(raw)
            if ok:
                df = raw.copy()
                st.success('Tree CSV accepted')
            else:
                st.error('Missing required columns')
                st.caption(', '.join(missing))
                df = pd.read_csv(DATA/'sample_tree_records.csv')
        except Exception as e:
            st.error('Could not read CSV; using sample data.')
            df = pd.read_csv(DATA/'sample_tree_records.csv')
    else:
        df = pd.read_csv(DATA/'sample_tree_records.csv')
    st.markdown('### 🎛️ Command filters')
    zones = sorted(df['zone'].dropna().unique().tolist())
    zone_sel = st.multiselect('Zones', zones, default=zones)
    classes = ['Routine','Watch','High','Critical']
    class_sel = st.multiselect('Priority class', classes, default=classes)
    min_score = st.slider('Minimum priority score', 0, 100, 0)
    status_sel = st.multiselect('Work-order status', sorted(df['work_order_status'].dropna().unique()), default=sorted(df['work_order_status'].dropna().unique()))
    st.divider()
    st.caption('LOCAL PROCESSING')
    st.caption('Pandas · NumPy · Plotly · Streamlit')
    st.caption('No external APIs required.')

valid, missing = validate(df)
if not valid:
    st.error('The dataset is missing required columns: ' + ', '.join(missing))
    st.stop()
df = score_trees(df)
view = df[df['zone'].isin(zone_sel) & df['priority_class'].astype(str).isin(class_sel) & (df['priority_score']>=min_score) & df['work_order_status'].isin(status_sel)].copy()

st.markdown('''<div class="hero"><div class="hero-kicker">CIVIC TREE-PRUNING PRIORITY PLANNER</div><div class="hero-title">🌳 Canopy Command Deck</div><div class="hero-copy">A local-first operational cockpit for screening trees that may need pruning review using branch condition, utility proximity, pedestrian exposure, wind risk, inspection signals, and maintenance history.</div><div style="margin-top:14px"><span class="badge badge-blue">LOCAL-FIRST</span><span class="badge badge-green">EXPLAINABLE SCORING</span><span class="badge badge-orange">WORK QUEUE READY</span></div></div>''', unsafe_allow_html=True)

# KPI ribbon
critical = int((view['priority_class'].astype(str)=='Critical').sum())
high = int((view['priority_class'].astype(str)=='High').sum())
avg = view['priority_score'].mean() if len(view) else 0
power = (view['power_line_distance_m'] <= 3).sum() if len(view) else 0
cols = st.columns(5)
for col, args in zip(cols, [
    ('Trees in view', f'{len(view):,}', f'{len(df):,} total records'),
    ('Critical queue', f'{critical}', 'priority ≥ 75'),
    ('High queue', f'{high}', 'priority 50–74.9'),
    ('Average priority', f'{avg:.1f}', '0–100 screening score'),
    ('Utility proximity', f'{power}', '≤ 3 m from power line')]):
    with col: metric_card(*args)

st.markdown('<div class="panel"><div class="section-title">Priority Landscape</div><div class="section-sub">Use the matrix to spot combinations of structural condition and exposure. Bubble size represents tree height.</div></div>', unsafe_allow_html=True)
left, right = st.columns([1.55,1])
with left:
    if len(view):
        fig = px.scatter(view, x='branch_condition_score', y='pedestrian_use_index', size='tree_height_m', color='priority_score', hover_name='tree_id', hover_data=['tree_species','zone','street_name','power_line_distance_m','wind_risk_index','priority_class'], labels={'branch_condition_score':'Branch condition score (higher = better)','pedestrian_use_index':'Pedestrian exposure index','priority_score':'Priority'})
        fig.update_layout(height=430, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fbfcfe', legend_title_text='')
        fig.add_hline(y=70, line_dash='dot', annotation_text='High pedestrian exposure')
        st.plotly_chart(fig, use_container_width=True)
    else: st.info('No trees match the current filters.')
with right:
    if len(view):
        zone = view.groupby('zone', as_index=False).agg(trees=('tree_id','count'), avg_priority=('priority_score','mean'), critical=('priority_class',lambda s:(s.astype(str)=='Critical').sum())).sort_values('avg_priority',ascending=False)
        fig2 = px.bar(zone, x='zone', y='avg_priority', color='critical', text='avg_priority', labels={'avg_priority':'Average priority','critical':'Critical trees'})
        fig2.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig2.update_layout(height=430, margin=dict(l=10,r=10,t=10,b=10), yaxis_range=[0,100], paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fbfcfe')
        st.plotly_chart(fig2, use_container_width=True)

st.markdown('<div class="panel"><div class="section-title">🧭 Pruning Work Queue</div><div class="section-sub">Prioritized records with the strongest review signals and suggested operational windows.</div></div>', unsafe_allow_html=True)
queue_cols = ['tree_id','tree_species','zone','street_name','priority_score','priority_class','pruning_urgency_days','top_risk_drivers','work_order_status']
queue = view.sort_values(['priority_score','recent_incident_count'], ascending=False)[queue_cols].head(20)
st.dataframe(queue, use_container_width=True, hide_index=True, column_config={
    'priority_score': st.column_config.ProgressColumn('Priority', min_value=0, max_value=100, format='%.1f'),
    'priority_class': st.column_config.TextColumn('Class'),
    'pruning_urgency_days': st.column_config.NumberColumn('Review within (days)')
})

st.markdown('<div class="panel"><div class="section-title">🔎 Tree Risk Anatomy</div><div class="section-sub">Select one record for an explainable driver profile and field-review context.</div></div>', unsafe_allow_html=True)
if len(view):
    selected = st.selectbox('Select tree', view['tree_id'].astype(str).tolist())
    r = view[view['tree_id'].astype(str)==selected].iloc[0]
    a,b,c,d = st.columns(4)
    with a: metric_card('Priority', f"{r.priority_score:.1f}", str(r.priority_class))
    with b: metric_card('Power-line distance', f"{r.power_line_distance_m:.1f} m", 'proximity signal')
    with c: metric_card('Wind risk', f"{r.wind_risk_index:.0f}/100", 'higher = greater risk')
    with d: metric_card('Inspection age', f"{r.inspection_age_days:.0f} days", 'since inspection')
    radar = pd.DataFrame({'Signal':['Branch condition','Power-line proximity','Pedestrian exposure','Wind risk','Inspection concern','Dead branches'], 'Score':[100-r.branch_condition_score,r.power_line_risk,r.pedestrian_exposure,r.wind_risk_index,100-r.inspection_condition_score,min(100,r.dead_branch_pct*2)]})
    fig3 = px.bar(radar, x='Score', y='Signal', orientation='h', range_x=[0,100], text='Score')
    fig3.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig3.update_layout(height=310, margin=dict(l=10,r=50,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fbfcfe')
    st.plotly_chart(fig3, use_container_width=True)
    st.info(f"Top review drivers: {r.top_risk_drivers}. Suggested review window: {int(r.pruning_urgency_days)} days. Crew access score: {r.crew_access_score:.0f}/100.")

# Scenario lab
st.markdown('<div class="panel"><div class="section-title">🧪 Scenario Lab</div><div class="section-sub">Test how changing operational assumptions could alter the size of the pruning review queue. This is a planning scenario, not a prediction of actual field conditions.</div></div>', unsafe_allow_html=True)
s1,s2,s3,s4 = st.columns(4)
with s1: branch_delta = st.slider('Branch-condition change', -30, 30, 0, step=5, help='Negative values mean worse condition scores.')
with s2: line_delta = st.slider('Utility proximity shift (m)', -2.0, 2.0, 0.0, step=0.5)
with s3: wind_delta = st.slider('Wind-risk change', -30, 30, 0, step=5)
with s4: pedestrian_delta = st.slider('Pedestrian exposure change', -30, 30, 0, step=5)
sc = view.copy()
if len(sc):
    sc['branch_condition_score'] = clamp(sc['branch_condition_score'] + branch_delta)
    sc['power_line_distance_m'] = clamp(sc['power_line_distance_m'] + line_delta*1.0)
    sc['wind_risk_index'] = clamp(sc['wind_risk_index'] + wind_delta)
    sc['pedestrian_use_index'] = clamp(sc['pedestrian_use_index'] + pedestrian_delta)
    sc = score_trees(sc)
    scc1,scc2,scc3 = st.columns(3)
    with scc1: metric_card('Current critical', str(critical), 'filtered view')
    with scc2: metric_card('Scenario critical', str(int((sc.priority_class.astype(str)=='Critical').sum())), 'after adjustments')
    with scc3: metric_card('Average shift', f"{sc.priority_score.mean()-avg:+.1f}", 'priority points')

# Local visual asset strip
st.markdown('<div class="panel"><div class="section-title">🌿 Canopy Field View</div><div class="section-sub">Local visual reference used by the dashboard; no external image service or map API is required.</div></div>', unsafe_allow_html=True)
img = ASSETS/'canopy_field_visual.svg'
if img.exists():
    st.markdown(img.read_text(encoding='utf-8'), unsafe_allow_html=True)

# Data explorer + export
st.markdown('<div class="panel"><div class="section-title">📊 Data Explorer & Export</div><div class="section-sub">Inspect the locally processed dataset and export the filtered review queue.</div></div>', unsafe_allow_html=True)
st.dataframe(view, use_container_width=True, hide_index=True)
export = view.to_csv(index=False).encode('utf-8')
st.download_button('⬇️ Download filtered tree-pruning queue CSV', export, file_name='tree_pruning_priority_queue.csv', mime='text/csv')

st.markdown('<div class="panel"><div class="small-muted"><b>Decision-support notice:</b> Screening scores surface combinations of local signals that may warrant additional arborist, utility, traffic, or municipal review. They do not certify tree safety, prescribe pruning work, or replace professional inspection and local policy.</div></div>', unsafe_allow_html=True)
