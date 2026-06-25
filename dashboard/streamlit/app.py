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
# CUSTOM CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; background-color: #0F0F0F !important; color: #FFFFFF !important; }
    .stApp { background-color: #0F0F0F; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1A1A1A 0%, #0F0F0F 100%); border-right: 1px solid #2A2A2A; }
    .raceiq-header { background: linear-gradient(135deg, #1A1A1A 0%, #0D0D0D 100%); border-bottom: 2px solid #E8002D; padding: 1.5rem 2rem; margin-bottom: 1.5rem; border-radius: 0 0 12px 12px; }
    .raceiq-title { font-size: 2.2rem; font-weight: 900; background: linear-gradient(90deg, #E8002D 0%, #FF4444 50%, #FFD700 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
    .raceiq-subtitle { color: #888888; font-size: 0.9rem; font-weight: 400; margin-top: 4px; letter-spacing: 2px; text-transform: uppercase; }
    .kpi-card { background: linear-gradient(135deg, #1A1A1A 0%, #222222 100%); border: 1px solid #2A2A2A; border-radius: 12px; padding: 1.2rem 1.5rem; text-align: center; position: relative; transition: transform 0.2s; }
    .kpi-card:hover { transform: translateY(-2px); border-color: #E8002D; }
    .kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #E8002D, #FFD700); }
    .kpi-label { font-size: 0.75rem; color: #888888; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; }
    .kpi-value { font-size: 2rem; font-weight: 800; color: #FFFFFF; margin: 0.3rem 0; line-height: 1; }
    .kpi-sub { font-size: 0.8rem; color: #E8002D; font-weight: 500; }
    .section-header { color: #FFFFFF; font-size: 1.1rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; padding: 0.5rem 0; border-bottom: 1px solid #E8002D; margin-bottom: 1rem; }
    hr { border-color: #2A2A2A !important; margin: 1.5rem 0 !important; }
    .stMultiSelect > div { background-color: #1A1A1A !important; border-color: #3A3A3A !important; }
</style>
""", unsafe_allow_html=True)

C_DARK, C_CARD, C_RED, C_WHITE, C_GOLD, C_GREY, C_LGREY = '#0F0F0F', '#1A1A1A', '#E8002D', '#FFFFFF', '#FFD700', '#3A3A3A', '#888888'
TEAM_COLORS = {'Mercedes': '#00D2BE', 'Red Bull': '#0600EF', 'Ferrari': '#DC0000', 'McLaren': '#FF8700', 'Aston Martin': '#006F62', 'Williams': '#005AFF', 'Alpine F1 Team': '#0090FF'}

def style_fig(fig, height=450):
    fig.update_layout(paper_bgcolor=C_DARK, plot_bgcolor='#111111', font=dict(color=C_WHITE, family='Inter'), height=height, margin=dict(l=50, r=30, t=60, b=50), legend=dict(bgcolor=C_CARD, bordercolor=C_GREY, borderwidth=1, font=dict(color=C_WHITE)), title_font=dict(color=C_WHITE, size=15))
    fig.update_xaxes(gridcolor='#1E1E1E', zeroline=False, linecolor=C_GREY)
    fig.update_yaxes(gridcolor='#1E1E1E', zeroline=False, linecolor=C_GREY)
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    current = os.path.dirname(os.path.abspath(__file__))
    candidates = [os.path.join(current, '..', '..', 'data', 'raw'), os.path.join(current, '..', 'data', 'raw'), os.path.join(current, 'data', 'raw')]
    data_dir = next((os.path.normpath(c) for c in candidates if os.path.exists(c) and any(f.endswith('.csv') for f in os.listdir(c))), None)
    if not data_dir: st.error("Data directory not found."); st.stop()
    null_vals = ['\\N', 'NULL', '']
    drivers_df = pd.read_csv(os.path.join(data_dir, 'drivers.csv'), na_values=null_vals)
    results_df = pd.read_csv(os.path.join(data_dir, 'results.csv'), na_values=null_vals)
    races_df = pd.read_csv(os.path.join(data_dir, 'races.csv'), na_values=null_vals)
    constructors_df = pd.read_csv(os.path.join(data_dir, 'constructors.csv'), na_values=null_vals)
    status_df = pd.read_csv(os.path.join(data_dir, 'status.csv'), na_values=null_vals)
    pit_stops_df = pd.read_csv(os.path.join(data_dir, 'pit_stops.csv'), na_values=null_vals)

    races_filtered = races_df[races_df['year'].between(2014, 2025)].copy()
    master = results_df.merge(races_filtered[['raceId', 'year', 'round', 'name', 'circuitId']], on='raceId', how='inner') \
                       .merge(drivers_df[['driverId', 'forename', 'surname', 'nationality']], on='driverId', how='left') \
                       .merge(constructors_df[['constructorId', 'name']].rename(columns={'name': 'constructor_name'}), on='constructorId', how='left') \
                       .merge(status_df[['statusId', 'status']], on='statusId', how='left')

    master['driver_name'] = master['forename'] + ' ' + master['surname']
    master['positionOrder'] = pd.to_numeric(master['positionOrder'], errors='coerce')
    master['grid'] = pd.to_numeric(master['grid'], errors='coerce')
    master['points'] = pd.to_numeric(master['points'], errors='coerce').fillna(0)
    laps_pat = master['status'].str.contains('[+][0-9]+ Lap', na=False, regex=True)
    master['is_win'] = (master['positionOrder'] == 1).astype(int)
    master['is_podium'] = (master['positionOrder'] <= 3).astype(int)
    master['is_dnf'] = (~(master['status'] == 'Finished') & ~laps_pat).astype(int)
    master['pos_improvement'] = master['grid'] - master['positionOrder']

    return master, pit_stops_df

with st.spinner("Loading RaceIQ data..."):
    master, pit_stops_df = load_data()

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧭 Navigation")
    page = st.radio("Select Module:", ["🏎️ Driver Analytics", "🏗️ Constructor Analytics"])
    st.markdown("---")
    st.markdown("## 🎛️ Filters")
    all_seasons = sorted(master['year'].unique())
    sel_seasons = st.multiselect("📅 Season", all_seasons, default=all_seasons) or all_seasons
    all_drivers = sorted(master['driver_name'].dropna().unique())
    sel_drivers = st.multiselect("👤 Driver (optional)", all_drivers)
    all_constructors = sorted(master['constructor_name'].dropna().unique())
    sel_constructors = st.multiselect("🏗️ Constructor (optional)", all_constructors)

# Global filter
filtered = master[master['year'].isin(sel_seasons)].copy()
if sel_drivers: filtered = filtered[filtered['driver_name'].isin(sel_drivers)]
if sel_constructors: filtered = filtered[filtered['constructor_name'].isin(sel_constructors)]

# ──────────────────────────────────────────────────────────────────────────────
# DRIVER ANALYTICS (Module 1)
# ──────────────────────────────────────────────────────────────────────────────
if page == "🏎️ Driver Analytics":
    st.markdown('<div class="raceiq-header"><p class="raceiq-title">🏎️ RaceIQ</p><p class="raceiq-subtitle">Module 1: Driver Analytics</p></div>', unsafe_allow_html=True)
    
    # Process stats
    d_stats = filtered.groupby('driver_name').agg(
        total_races=('raceId', 'count'), total_wins=('is_win', 'sum'), total_podiums=('is_podium', 'sum'),
        total_dnf=('is_dnf', 'sum'), total_points=('points', 'sum'), avg_finish=('positionOrder', 'mean')
    ).reset_index()
    d_stats = d_stats[d_stats['total_races'] >= max(1, int(len(sel_seasons)))]
    d_stats['win_rate'] = d_stats['total_wins'] / d_stats['total_races']
    d_stats['podium_rate'] = d_stats['total_podiums'] / d_stats['total_races']
    d_stats['dnf_rate'] = d_stats['total_dnf'] / d_stats['total_races']

    # KPIs
    st.markdown('<p class="section-header">Key Performance Indicators</p>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    top10_pts = d_stats.nlargest(10, 'total_points')
    with k1: st.markdown(f'<div class="kpi-card"><p class="kpi-label">Races Analyzed</p><p class="kpi-value">{filtered["raceId"].nunique()}</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="kpi-card"><p class="kpi-label">Unique Drivers</p><p class="kpi-value">{filtered["driverId"].nunique()}</p></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="kpi-card"><p class="kpi-label">Avg Win Rate (Top 10)</p><p class="kpi-value">{top10_pts["win_rate"].mean()*100:.1f}%</p></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="kpi-card"><p class="kpi-label">Most Dominant</p><p class="kpi-value" style="font-size:1.2rem;">{top10_pts["driver_name"].iloc[0] if len(top10_pts) else "N/A"}</p><p class="kpi-sub">{top10_pts["total_points"].iloc[0] if len(top10_pts) else 0:,.0f} pts</p></div>', unsafe_allow_html=True)

    # Charts
    c1, c2 = st.columns([1.2, 1])
    with c1:
        top15 = d_stats.nlargest(15, 'total_points').sort_values('total_points')
        fig = go.Figure(go.Bar(x=top15['total_points'], y=top15['driver_name'], orientation='h', marker=dict(color=[C_GOLD if i == len(top15)-1 else C_RED for i in range(len(top15))])))
        st.plotly_chart(style_fig(fig.update_layout(title='🏆 Top 15 Drivers — Total Points')), use_container_width=True)
    with c2:
        highlight = ['Max Verstappen', 'Lewis Hamilton', 'Sebastian Vettel', 'Charles Leclerc']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=d_stats['win_rate']*100, y=d_stats['podium_rate']*100, mode='markers', marker=dict(color=C_GOLD), text=d_stats['driver_name']))
        st.plotly_chart(style_fig(fig.update_layout(title='🎯 Consistency Map (Win vs Podium)')), use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# CONSTRUCTOR ANALYTICS (Module 2)
# ──────────────────────────────────────────────────────────────────────────────
elif page == "🏗️ Constructor Analytics":
    st.markdown('<div class="raceiq-header"><p class="raceiq-title">🏎️ RaceIQ</p><p class="raceiq-subtitle">Module 2: Constructor & Team Analytics</p></div>', unsafe_allow_html=True)

    # Process Stats
    cr = filtered.groupby(['constructorId', 'constructor_name', 'raceId', 'year']).agg(
        points=('points', 'sum'), best_pos=('positionOrder', 'min'), entries=('driverId', 'count'), dnfs=('is_dnf', 'sum')
    ).reset_index()
    cr['is_win'] = (cr['best_pos'] == 1).astype(int)
    cr['is_podium'] = (cr['best_pos'] <= 3).astype(int)

    season_stats = cr.groupby(['constructor_name', 'year']).agg(races=('raceId', 'count'), wins=('is_win', 'sum'), points=('points', 'sum')).reset_index()
    c_stats = cr.groupby('constructor_name').agg(
        races=('raceId', 'count'), wins=('is_win', 'sum'), podiums=('is_podium', 'sum'),
        points=('points', 'sum'), entries=('entries', 'sum'), dnfs=('dnfs', 'sum'), avg_finish=('best_pos', 'mean')
    ).reset_index()
    c_stats = c_stats[c_stats['races'] >= max(1, len(sel_seasons))]
    c_stats['win_rate'] = c_stats['wins'] / c_stats['races']
    c_stats['dnf_rate'] = c_stats['dnfs'] / c_stats['entries']
    c_stats['reliability'] = 1 - c_stats['dnf_rate']
    c_stats['pts_per_race'] = c_stats['points'] / c_stats['races']

    # Pit stops
    pit_master = pit_stops_df.merge(master[['raceId', 'driverId', 'constructor_name', 'year']], on=['raceId', 'driverId'], how='inner')
    pit_master['milliseconds'] = pd.to_numeric(pit_master['milliseconds'], errors='coerce')
    pit_filtered = pit_master[(pit_master['milliseconds'] < 40000) & (pit_master['year'].isin(sel_seasons))]
    pit_stats = pit_filtered.groupby('constructor_name')['milliseconds'].mean().reset_index()
    c_stats = c_stats.merge(pit_stats, on='constructor_name', how='left')

    # KPIs
    st.markdown('<p class="section-header">Key Performance Indicators</p>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    top_c = c_stats.nlargest(1, 'points')
    rel_c = c_stats[c_stats['races']>=10].nlargest(1, 'reliability')
    pit_c = c_stats.dropna(subset=['milliseconds']).nsmallest(1, 'milliseconds')
    
    with k1: st.markdown(f'<div class="kpi-card"><p class="kpi-label">Total Constructors</p><p class="kpi-value">{len(c_stats)}</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="kpi-card"><p class="kpi-label">Most Dominant</p><p class="kpi-value" style="font-size:1.2rem;">{top_c["constructor_name"].iloc[0] if len(top_c) else "-"}</p><p class="kpi-sub">{top_c["points"].iloc[0] if len(top_c) else 0:,.0f} pts</p></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="kpi-card"><p class="kpi-label">Best Reliability</p><p class="kpi-value" style="font-size:1.2rem;">{rel_c["constructor_name"].iloc[0] if len(rel_c) else "-"}</p><p class="kpi-sub">{rel_c["reliability"].iloc[0]*100 if len(rel_c) else 0:.1f}% Finish</p></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="kpi-card"><p class="kpi-label">Fastest Pit Crew</p><p class="kpi-value" style="font-size:1.2rem;">{pit_c["constructor_name"].iloc[0] if len(pit_c) else "-"}</p><p class="kpi-sub">{pit_c["milliseconds"].iloc[0]/1000 if len(pit_c) else 0:.2f}s Avg</p></div>', unsafe_allow_html=True)

    # Row 2: Main Charts
    st.markdown('<p class="section-header">Championship Performance</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        top10 = c_stats.nlargest(10, 'points').sort_values('points')
        fig = go.Figure(go.Bar(x=top10['points'], y=top10['constructor_name'], orientation='h', marker=dict(color=[C_GOLD if i == len(top10)-1 else C_RED for i in range(len(top10))])))
        st.plotly_chart(style_fig(fig.update_layout(title='🏆 Total Points')), use_container_width=True)
    with c2:
        top_w = c_stats.nlargest(8, 'wins')
        fig = go.Figure(go.Bar(x=top_w['constructor_name'], y=top_w['wins'], marker=dict(color=C_RED)))
        st.plotly_chart(style_fig(fig.update_layout(title='🥇 Race Wins')), use_container_width=True)

    # Row 3: Progression
    st.markdown('<p class="section-header">Season Progression</p>', unsafe_allow_html=True)
    c3, c4 = st.columns([1.5, 1])
    with c3:
        top6 = c_stats.nlargest(6, 'points')['constructor_name'].tolist()
        fig = go.Figure()
        for t in top6:
            df_t = season_stats[season_stats['constructor_name'] == t].sort_values('year')
            fig.add_trace(go.Scatter(x=df_t['year'], y=df_t['points'], mode='lines+markers', name=t, line=dict(color=TEAM_COLORS.get(t, C_WHITE))))
        st.plotly_chart(style_fig(fig.update_layout(title='📈 Points Progression (Top 6)', xaxis=dict(dtick=1))), use_container_width=True)
    with c4:
        heat = season_stats.pivot(index='constructor_name', columns='year', values='points').fillna(0)
        heat = heat.loc[[t for t in top6 if t in heat.index][::-1]]
        fig = go.Figure(go.Heatmap(z=heat.values, x=heat.columns, y=heat.index, colorscale='Reds'))
        st.plotly_chart(style_fig(fig.update_layout(title='🔥 Points Heatmap')), use_container_width=True)

    # Row 4: Pit Stops & Reliability
    st.markdown('<p class="section-header">Pit Stop Efficiency & Reliability</p>', unsafe_allow_html=True)
    c5, c6 = st.columns(2)
    with c5:
        pit_t = pit_filtered.groupby(['year', 'constructor_name'])['milliseconds'].mean().reset_index()
        top5_pit = c_stats.dropna(subset=['milliseconds']).nsmallest(5, 'milliseconds')['constructor_name'].tolist()
        fig = go.Figure()
        for t in top5_pit:
            df_t = pit_t[pit_t['constructor_name'] == t].sort_values('year')
            fig.add_trace(go.Scatter(x=df_t['year'], y=df_t['milliseconds']/1000, mode='lines+markers', name=t, line=dict(color=TEAM_COLORS.get(t, C_WHITE))))
        st.plotly_chart(style_fig(fig.update_layout(title='📉 Pit Stop Duration Trend (Seconds)', xaxis=dict(dtick=1))), use_container_width=True)
    with c6:
        fig = go.Figure(go.Scatter(x=c_stats['win_rate']*100, y=c_stats['reliability']*100, mode='markers+text',
                                   marker=dict(size=c_stats['races']/5, color=C_GOLD, line=dict(color=C_WHITE, width=1)),
                                   text=c_stats['constructor_name'], textposition='top center'))
        st.plotly_chart(style_fig(fig.update_layout(title='🎯 Win Rate vs Reliability', xaxis_title='Win Rate (%)', yaxis_title='Reliability (%)')), use_container_width=True)

    # Row 5 & 6: Momentum & H2H
    st.markdown('<p class="section-header">Momentum & Head-to-Head</p>', unsafe_allow_html=True)
    c7, c8 = st.columns([1, 1.2])
    with c7:
        mom_df = season_stats[season_stats['year'].isin(sorted(sel_seasons)[-3:])]
        mom_piv = mom_df.pivot(index='constructor_name', columns='year', values='points').fillna(0)
        cols = mom_piv.columns
        if len(cols) >= 2:
            mom_piv['growth'] = ((mom_piv[cols[-1]] - mom_piv[cols[-2]]) / mom_piv[cols[-2]].replace(0, np.nan)) * 100
            g_df = mom_piv.dropna().sort_values('growth')
            g_df = g_df[g_df['growth'].between(-100, 500)].tail(8)
            fig = go.Figure(go.Bar(x=g_df['growth'], y=g_df.index, orientation='h', marker=dict(color=[C_GOLD if v>0 else C_RED for v in g_df['growth']])))
            st.plotly_chart(style_fig(fig.update_layout(title='📊 YoY Points Growth (%)')), use_container_width=True)
        else:
            st.info("Select at least 2 seasons for YoY growth.")
    with c8:
        t_list = c_stats['constructor_name'].tolist()
        t1 = st.selectbox("Team 1", t_list, index=t_list.index('Mercedes') if 'Mercedes' in t_list else 0)
        t2 = st.selectbox("Team 2", t_list, index=t_list.index('Red Bull') if 'Red Bull' in t_list else min(1, len(t_list)-1))
        def get_h2h(t):
            r = c_stats[c_stats['constructor_name']==t]
            if r.empty: return [0]*5
            r = r.iloc[0]
            return [r['win_rate']*100, r['podium_rate']*100, r['reliability']*100, max(0, 100-(r['milliseconds']/100)) if pd.notnull(r['milliseconds']) else 0, r['pts_per_race']]
        cats = ['Win %', 'Podium %', 'Reliability', 'Pit Efficiency', 'Pts/Race']
        fig = go.Figure()
        for v, n, c in [(get_h2h(t1), t1, '#00D2BE'), (get_h2h(t2), t2, '#0600EF')]:
            fig.add_trace(go.Scatterpolar(r=v+[v[0]], theta=cats+[cats[0]], name=n, fill='toself', line=dict(color=c, width=2), fillcolor=f'rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.15)'))
        st.plotly_chart(style_fig(fig.update_layout(polar=dict(bgcolor='#111111', radialaxis=dict(visible=True, range=[0, 100])), title=f'⚔️ {t1} vs {t2}')), use_container_width=True)
