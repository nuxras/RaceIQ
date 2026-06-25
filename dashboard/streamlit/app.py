"""
RaceIQ — Formula 1 Strategy Intelligence Platform
Dashboard: Module 1 — Driver Performance Analytics
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import warnings
warnings.filterwarnings('ignore')

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RaceIQ — F1 Strategy Intelligence",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS — RaceIQ Dark Theme
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* Global */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #0F0F0F !important;
        color: #FFFFFF !important;
    }
    .stApp {
        background-color: #0F0F0F;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1A1A 0%, #0F0F0F 100%);
        border-right: 1px solid #2A2A2A;
    }
    [data-testid="stSidebar"] .css-1d391kg { padding: 1rem 0.5rem; }

    /* Header */
    .raceiq-header {
        background: linear-gradient(135deg, #1A1A1A 0%, #0D0D0D 100%);
        border-bottom: 2px solid #E8002D;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        border-radius: 0 0 12px 12px;
    }
    .raceiq-title {
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(90deg, #E8002D 0%, #FF4444 50%, #FFD700 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -1px;
        margin: 0;
    }
    .raceiq-subtitle {
        color: #888888;
        font-size: 0.9rem;
        font-weight: 400;
        margin-top: 4px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1A1A1A 0%, #222222 100%);
        border: 1px solid #2A2A2A;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s, border-color 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: #E8002D;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #E8002D, #FFD700);
    }
    .kpi-label {
        font-size: 0.75rem;
        color: #888888;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        color: #FFFFFF;
        margin: 0.3rem 0;
        line-height: 1;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #E8002D;
        font-weight: 500;
    }

    /* Section headers */
    .section-header {
        color: #FFFFFF;
        font-size: 1.1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        padding: 0.5rem 0;
        border-bottom: 1px solid #E8002D;
        margin-bottom: 1rem;
    }

    /* Divider */
    hr {
        border-color: #2A2A2A !important;
        margin: 1.5rem 0 !important;
    }

    /* Multiselect */
    .stMultiSelect > div { background-color: #1A1A1A !important; border-color: #3A3A3A !important; }

    /* Footer */
    .footer {
        text-align: center;
        color: #444;
        font-size: 0.75rem;
        padding: 2rem 0 1rem;
        border-top: 1px solid #1A1A1A;
        margin-top: 2rem;
    }
    .footer span { color: #E8002D; }

    /* Driver badge */
    .driver-badge {
        display: inline-block;
        background: #E8002D;
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# COLOR SCHEME
# ──────────────────────────────────────────────────────────────────────────────
C_DARK  = '#0F0F0F'
C_CARD  = '#1A1A1A'
C_RED   = '#E8002D'
C_WHITE = '#FFFFFF'
C_GOLD  = '#FFD700'
C_GREY  = '#3A3A3A'
C_LGREY = '#888888'

def style_fig(fig, height=450):
    fig.update_layout(
        paper_bgcolor=C_DARK,
        plot_bgcolor='#111111',
        font=dict(color=C_WHITE, family='Inter'),
        height=height,
        margin=dict(l=50, r=30, t=60, b=50),
        legend=dict(bgcolor=C_CARD, bordercolor=C_GREY, borderwidth=1,
                    font=dict(color=C_WHITE)),
        title_font=dict(color=C_WHITE, size=15, family='Inter'),
    )
    fig.update_xaxes(gridcolor='#1E1E1E', zeroline=False, linecolor=C_GREY)
    fig.update_yaxes(gridcolor='#1E1E1E', zeroline=False, linecolor=C_GREY)
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    # Find data directory
    current = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(current, '..', '..', 'data', 'raw'),
        os.path.join(current, '..', 'data', 'raw'),
        os.path.join(current, 'data', 'raw'),
    ]
    data_dir = None
    for c in candidates:
        if os.path.exists(c) and any(f.endswith('.csv') for f in os.listdir(c)):
            data_dir = os.path.normpath(c)
            break

    if data_dir is None:
        # Last resort: look from CWD
        for root, dirs, files in os.walk(os.getcwd()):
            if 'drivers.csv' in files:
                data_dir = root
                break

    if data_dir is None:
        st.error("Could not find data directory. Run from the RaceIQ project root.")
        st.stop()

    null_vals = ['\\N', 'NULL', '']

    drivers_df      = pd.read_csv(os.path.join(data_dir, 'drivers.csv'), na_values=null_vals)
    results_df      = pd.read_csv(os.path.join(data_dir, 'results.csv'), na_values=null_vals)
    races_df        = pd.read_csv(os.path.join(data_dir, 'races.csv'), na_values=null_vals)
    standings_df    = pd.read_csv(os.path.join(data_dir, 'driver_standings.csv'), na_values=null_vals)
    constructors_df = pd.read_csv(os.path.join(data_dir, 'constructors.csv'), na_values=null_vals)
    status_df       = pd.read_csv(os.path.join(data_dir, 'status.csv'), na_values=null_vals)

    # Filter to 2014-2025
    races_filtered = races_df[races_df['year'].between(2014, 2025)].copy()

    master = (
        results_df
        .merge(races_filtered[['raceId', 'year', 'round', 'name', 'circuitId', 'date']],
               on='raceId', how='inner')
        .merge(drivers_df[['driverId', 'driverRef', 'code', 'forename', 'surname', 'nationality']],
               on='driverId', how='left')
        .merge(constructors_df[['constructorId', 'name']].rename(columns={'name': 'constructor_name'}),
               on='constructorId', how='left')
        .merge(status_df[['statusId', 'status']], on='statusId', how='left')
    )

    master['driver_name'] = master['forename'] + ' ' + master['surname']
    master['positionOrder'] = pd.to_numeric(master['positionOrder'], errors='coerce')
    master['grid']          = pd.to_numeric(master['grid'], errors='coerce')
    master['points']        = pd.to_numeric(master['points'], errors='coerce').fillna(0)
    master['laps']          = pd.to_numeric(master['laps'], errors='coerce')
    master['date']          = pd.to_datetime(master['date'], errors='coerce')

    laps_pat = master['status'].str.contains('[+][0-9]+ Lap', na=False, regex=True)
    master['is_win']    = (master['positionOrder'] == 1).astype(int)
    master['is_podium'] = (master['positionOrder'] <= 3).astype(int)
    master['is_dnf']    = (~(master['status'] == 'Finished') & ~laps_pat).astype(int)
    master['pos_improvement'] = master['grid'] - master['positionOrder']

    return master, races_filtered

@st.cache_data(show_spinner=False)
def build_driver_stats(master):
    stats = master.groupby(['driverId', 'driver_name', 'nationality']).agg(
        total_races    = ('raceId', 'count'),
        total_wins     = ('is_win', 'sum'),
        total_podiums  = ('is_podium', 'sum'),
        total_dnf      = ('is_dnf', 'sum'),
        total_points   = ('points', 'sum'),
        avg_grid       = ('grid', 'mean'),
        avg_finish     = ('positionOrder', 'mean'),
        avg_improvement= ('pos_improvement', 'mean'),
        seasons_active = ('year', 'nunique'),
        constructors   = ('constructor_name', lambda x: ', '.join(x.dropna().unique()[:3])),
    ).reset_index()

    stats = stats[stats['total_races'] >= 5].copy()
    stats['win_rate']       = stats['total_wins']    / stats['total_races']
    stats['podium_rate']    = stats['total_podiums'] / stats['total_races']
    stats['dnf_rate']       = stats['total_dnf']     / stats['total_races']
    stats['points_per_race']= stats['total_points']  / stats['total_races']
    return stats

# ──────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────────────────────
with st.spinner("Loading RaceIQ data..."):
    master, races_filtered = load_data()
    driver_stats = build_driver_stats(master)

# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="raceiq-header">
    <p class="raceiq-title">🏎️ RaceIQ</p>
    <p class="raceiq-subtitle">Formula 1 Strategy Intelligence Platform — Module 1: Driver Analytics</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛️ Filters")
    st.markdown("---")

    all_seasons = sorted(master['year'].unique())
    sel_seasons = st.multiselect(
        "📅 Season", all_seasons, default=all_seasons,
        help="Select one or more seasons to analyze"
    )
    if not sel_seasons:
        sel_seasons = all_seasons

    all_drivers = sorted(master['driver_name'].dropna().unique())
    sel_drivers = st.multiselect(
        "👤 Driver (optional)", all_drivers,
        help="Leave empty to show all drivers"
    )

    all_constructors = sorted(master['constructor_name'].dropna().unique())
    sel_constructors = st.multiselect(
        "🏗️ Constructor (optional)", all_constructors,
        help="Leave empty to show all constructors"
    )

    st.markdown("---")
    st.markdown("### 📊 Dataset Info")
    st.markdown(f"**Seasons:** 2014–2025")
    st.markdown(f"**Races:** {master['raceId'].nunique():,}")
    st.markdown(f"**Drivers:** {master['driverId'].nunique()}")
    st.markdown(f"**Source:** Ergast F1 API")

# Apply filters
filtered = master[master['year'].isin(sel_seasons)].copy()
if sel_drivers:
    filtered = filtered[filtered['driver_name'].isin(sel_drivers)]
if sel_constructors:
    filtered = filtered[filtered['constructor_name'].isin(sel_constructors)]

f_stats = build_driver_stats(filtered)
f_stats_min = f_stats[f_stats['total_races'] >= max(1, int(len(sel_seasons) * 2))]

# ──────────────────────────────────────────────────────────────────────────────
# ROW 1 — KPI Cards
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">Key Performance Indicators</p>', unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_races = filtered['raceId'].nunique()
total_drivers = filtered['driverId'].nunique()
top10_stats = f_stats.nlargest(10, 'total_points')
avg_win_rate = top10_stats['win_rate'].mean() * 100 if len(top10_stats) > 0 else 0
dominant = f_stats.nlargest(1, 'total_points')
dominant_name = dominant['driver_name'].values[0] if len(dominant) > 0 else 'N/A'
dominant_pts  = dominant['total_points'].values[0] if len(dominant) > 0 else 0

with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Total Races Analyzed</p>
        <p class="kpi-value">{total_races:,}</p>
        <p class="kpi-sub">Seasons: {', '.join(str(s) for s in sorted(sel_seasons)[:3])}{'...' if len(sel_seasons)>3 else ''}</p>
    </div>""", unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Unique Drivers</p>
        <p class="kpi-value">{total_drivers}</p>
        <p class="kpi-sub">Active in selected period</p>
    </div>""", unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Avg Win Rate (Top 10)</p>
        <p class="kpi-value">{avg_win_rate:.1f}%</p>
        <p class="kpi-sub">Among top 10 drivers by points</p>
    </div>""", unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Most Dominant Driver</p>
        <p class="kpi-value" style="font-size:1.2rem; padding-top: 0.4rem;">{dominant_name}</p>
        <p class="kpi-sub">{dominant_pts:,.0f} pts total</p>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# ROW 2 — Main Charts
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">Driver Performance Overview</p>', unsafe_allow_html=True)
col_l, col_r = st.columns([1.2, 1])

with col_l:
    top15 = f_stats.nlargest(15, 'total_points').sort_values('total_points')
    colors = [C_GOLD if i == len(top15)-1 else C_RED for i in range(len(top15))]
    fig_pts = go.Figure(go.Bar(
        x=top15['total_points'], y=top15['driver_name'],
        orientation='h',
        marker=dict(color=colors),
        text=top15['total_points'].apply(lambda x: f'{x:,.0f}'),
        textposition='outside', textfont=dict(color=C_WHITE, size=10),
    ))
    fig_pts.update_layout(title='🏆 Top 15 Drivers — Total Points')
    fig_pts = style_fig(fig_pts, 460)
    st.plotly_chart(fig_pts, use_container_width=True)

with col_r:
    plot_data = f_stats[f_stats['total_races'] >= max(5, int(len(sel_seasons) * 2))].copy()
    highlight_d = ['Max Verstappen', 'Lewis Hamilton', 'Sebastian Vettel',
                   'Charles Leclerc', 'Fernando Alonso', 'Lando Norris']
    color_map = {
        'Max Verstappen':  C_GOLD,
        'Lewis Hamilton':  '#00A0DE',
        'Sebastian Vettel':C_RED,
        'Charles Leclerc': '#FF6666',
        'Fernando Alonso': '#0066FF',
        'Lando Norris':    '#FF8000',
    }

    fig_scatter = go.Figure()
    # Background dots
    others = plot_data[~plot_data['driver_name'].isin(highlight_d)]
    fig_scatter.add_trace(go.Scatter(
        x=others['win_rate']*100, y=others['podium_rate']*100,
        mode='markers',
        marker=dict(size=7, color=C_LGREY, opacity=0.4),
        hovertemplate='<b>%{customdata}</b><br>Win: %{x:.1f}%<br>Podium: %{y:.1f}%<extra></extra>',
        customdata=others['driver_name'], name='Other'
    ))
    # Highlighted
    for d in highlight_d:
        row = plot_data[plot_data['driver_name'] == d]
        if row.empty:
            continue
        row = row.iloc[0]
        fig_scatter.add_trace(go.Scatter(
            x=[row['win_rate']*100], y=[row['podium_rate']*100],
            mode='markers+text',
            marker=dict(size=max(10, min(22, row['total_races']/8)),
                        color=color_map.get(d, C_WHITE),
                        line=dict(color=C_WHITE, width=1.5)),
            text=[d.split()[-1]], textposition='top center',
            textfont=dict(color=C_WHITE, size=9),
            name=d,
            hovertemplate=f'<b>{d}</b><br>Win: {row["win_rate"]:.1%}<br>Podium: {row["podium_rate"]:.1%}<br>Races: {row["total_races"]}<extra></extra>',
        ))

    fig_scatter.update_layout(
        title='🎯 Consistency Map — Win Rate vs Podium Rate',
        xaxis_title='Win Rate (%)', yaxis_title='Podium Rate (%)',
        showlegend=False,
    )
    fig_scatter = style_fig(fig_scatter, 460)
    st.plotly_chart(fig_scatter, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# ROW 3 — Deep Dive
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">Season-Level Deep Dive</p>', unsafe_allow_html=True)
col3a, col3b = st.columns([1.5, 1])

with col3a:
    top5_names = f_stats.nlargest(5, 'total_points')['driver_name'].tolist()
    season_pts = filtered[filtered['driver_name'].isin(top5_names)].groupby(
        ['driver_name', 'year'])['points'].sum().reset_index()

    palette5 = [C_GOLD, '#00A0DE', C_RED, '#5FCFFF', '#FF8000']
    fig_prog = go.Figure()
    for i, d in enumerate(top5_names):
        df_d = season_pts[season_pts['driver_name'] == d].sort_values('year')
        if df_d.empty:
            continue
        fig_prog.add_trace(go.Scatter(
            x=df_d['year'], y=df_d['points'],
            mode='lines+markers', name=d,
            line=dict(color=palette5[i % 5], width=2.5),
            marker=dict(size=8, color=palette5[i % 5]),
        ))
    fig_prog.update_layout(
        title='📈 Season Points Progression — Top 5 Drivers',
        xaxis_title='Season', yaxis_title='Total Points',
        xaxis=dict(dtick=1, tickangle=-45),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    fig_prog = style_fig(fig_prog, 420)
    st.plotly_chart(fig_prog, use_container_width=True)

with col3b:
    st.markdown("#### ⚔️ Head-to-Head Comparison")
    h2h_drivers = sorted(f_stats[f_stats['total_races'] >= 5]['driver_name'].tolist())
    default_idx1 = h2h_drivers.index('Max Verstappen') if 'Max Verstappen' in h2h_drivers else 0
    default_idx2 = h2h_drivers.index('Lewis Hamilton') if 'Lewis Hamilton' in h2h_drivers else 1

    d1 = st.selectbox("Driver 1", h2h_drivers, index=default_idx1, key='d1')
    d2 = st.selectbox("Driver 2", h2h_drivers, index=default_idx2, key='d2')

    def get_radar_vals(dname):
        row = f_stats[f_stats['driver_name'] == dname]
        if row.empty:
            return None
        row = row.iloc[0]
        return [
            round(row['win_rate'] * 100, 1),
            round(row['podium_rate'] * 100, 1),
            round(min(row['points_per_race'], 25), 1),
            round((1 - row['dnf_rate']) * 100, 1),
            round(max(0, 100 - row['avg_finish'] * 5), 1),
        ]

    cats = ['Win %', 'Podium %', 'Pts/Race', 'Reliability', 'Consistency']
    v1 = get_radar_vals(d1)
    v2 = get_radar_vals(d2)

    if v1 and v2:
        fig_radar = go.Figure()
        for vals, name, color in [(v1, d1, C_GOLD), (v2, d2, '#00A0DE')]:
            fig_radar.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=cats + [cats[0]],
                name=name, fill='toself',
                line=dict(color=color, width=2),
                fillcolor=f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.15)',
            ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor='#111111',
                radialaxis=dict(visible=True, range=[0, 105], color=C_LGREY, gridcolor=C_GREY),
                angularaxis=dict(color=C_WHITE, gridcolor=C_GREY)
            ),
            paper_bgcolor=C_DARK,
            font=dict(color=C_WHITE, family='Inter'),
            height=350,
            margin=dict(l=30, r=30, t=40, b=30),
            legend=dict(bgcolor=C_CARD, font=dict(size=10)),
            title=dict(text=f'⚔️ {d1.split()[-1]} vs {d2.split()[-1]}',
                       font=dict(color=C_WHITE, size=13))
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# ROW 4 — Reliability & Overperformers
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">Reliability & Overperformance Analysis</p>', unsafe_allow_html=True)
col4a, col4b = st.columns(2)

with col4a:
    min_r = max(5, int(len(sel_seasons) * 2))
    dnf_data = f_stats[f_stats['total_races'] >= min_r].nlargest(12, 'dnf_rate')
    dnf_sorted = dnf_data.sort_values('dnf_rate', ascending=False)

    fig_dnf = go.Figure(go.Bar(
        x=dnf_sorted['driver_name'],
        y=dnf_sorted['dnf_rate'] * 100,
        marker=dict(
            color=dnf_sorted['dnf_rate'],
            colorscale=[[0, C_GREY], [0.5, '#FF6B35'], [1, C_RED]],
        ),
        text=dnf_sorted['dnf_rate'].apply(lambda x: f'{x:.1%}'),
        textposition='outside', textfont=dict(color=C_WHITE, size=10),
    ))
    fig_dnf.update_layout(
        title='⚠️ DNF Rate — Reliability Risk (top 12)',
        xaxis_title='', yaxis_title='DNF Rate (%)',
        xaxis=dict(tickangle=-35),
    )
    fig_dnf.add_hline(y=15, line_dash='dash', line_color=C_GOLD, opacity=0.6,
                      annotation_text='15% risk line')
    fig_dnf = style_fig(fig_dnf, 420)
    st.plotly_chart(fig_dnf, use_container_width=True)

with col4b:
    ovp_data = filtered[
        (filtered['grid'].between(1, 20)) &
        (filtered['positionOrder'].between(1, 20))
    ].groupby(['driverId', 'driver_name'])['pos_improvement'].agg(['mean', 'count']).reset_index()
    ovp_data.columns = ['driverId', 'driver_name', 'avg_improvement', 'count']
    ovp_data = ovp_data[ovp_data['count'] >= max(5, int(len(sel_seasons) * 2))]
    ovp_top = ovp_data.nlargest(12, 'avg_improvement').sort_values('avg_improvement')

    colors_ov = [C_GOLD if v > 0 else '#444' for v in ovp_top['avg_improvement']]
    fig_ovp = go.Figure(go.Bar(
        x=ovp_top['avg_improvement'],
        y=ovp_top['driver_name'],
        orientation='h',
        marker=dict(color=colors_ov),
        text=ovp_top['avg_improvement'].apply(lambda x: f'+{x:.2f}' if x >= 0 else f'{x:.2f}'),
        textposition='outside', textfont=dict(color=C_WHITE, size=10),
    ))
    fig_ovp.update_layout(
        title='⚡ Overperformers — Avg Grid-to-Finish Improvement',
        xaxis_title='Avg Positions Gained',
    )
    fig_ovp.add_vline(x=0, line_dash='dash', line_color=C_WHITE, opacity=0.4)
    fig_ovp = style_fig(fig_ovp, 420)
    st.plotly_chart(fig_ovp, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# BONUS: Data Table
# ──────────────────────────────────────────────────────────────────────────────
with st.expander("📊 Full Driver Statistics Table"):
    table_cols = ['driver_name', 'nationality', 'total_races', 'total_wins',
                  'total_podiums', 'total_dnf', 'total_points',
                  'win_rate', 'podium_rate', 'dnf_rate', 'points_per_race']
    display_df = f_stats[table_cols].copy()
    display_df['win_rate']       = display_df['win_rate'].apply(lambda x: f'{x:.1%}')
    display_df['podium_rate']    = display_df['podium_rate'].apply(lambda x: f'{x:.1%}')
    display_df['dnf_rate']       = display_df['dnf_rate'].apply(lambda x: f'{x:.1%}')
    display_df['points_per_race']= display_df['points_per_race'].apply(lambda x: f'{x:.1f}')
    display_df = display_df.sort_values('total_points', ascending=False).reset_index(drop=True)
    display_df.columns = ['Driver', 'Nationality', 'Races', 'Wins', 'Podiums', 'DNFs',
                          'Points', 'Win Rate', 'Podium Rate', 'DNF Rate', 'Pts/Race']
    st.dataframe(display_df, use_container_width=True, height=350)

# ──────────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    RaceIQ © 2025 | Data: Ergast F1 API | Built with Python & Streamlit<br>
    Module 1: Driver Performance Analytics | 
    <span>Next: Module 2 — Constructor Analytics 🔄</span>
</div>
""", unsafe_allow_html=True)
