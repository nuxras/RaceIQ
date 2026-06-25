"""
RaceIQ — PNG Export Script
Generates 5 high-quality (1920x900) visualization PNGs for the README.
"""
import sys
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Resolve paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'images')
os.makedirs(ASSETS_DIR, exist_ok=True)

# Color scheme
C_DARK  = '#0F0F0F'
C_CARD  = '#1A1A1A'
C_RED   = '#E8002D'
C_WHITE = '#FFFFFF'
C_GOLD  = '#FFD700'
C_GREY  = '#3A3A3A'
C_LGREY = '#888888'

def style_fig(fig, height=900, width=1920):
    fig.update_layout(
        paper_bgcolor=C_DARK,
        plot_bgcolor='#111111',
        font=dict(color=C_WHITE, family='Arial', size=14),
        height=height, width=width,
        margin=dict(l=80, r=60, t=90, b=80),
        legend=dict(bgcolor=C_CARD, bordercolor=C_GREY, borderwidth=1,
                    font=dict(color=C_WHITE, size=12)),
        title_font=dict(color=C_WHITE, size=22, family='Arial Black'),
    )
    fig.update_xaxes(gridcolor='#1E1E1E', zeroline=False, linecolor=C_GREY, tickfont=dict(size=12))
    fig.update_yaxes(gridcolor='#1E1E1E', zeroline=False, linecolor=C_GREY, tickfont=dict(size=12))
    return fig

# ── Load Data ─────────────────────────────────────────────────────────────────
print("[1/6] Loading data...")
null_vals = ['\\N', 'NULL', '']
drivers_df      = pd.read_csv(os.path.join(DATA_DIR, 'drivers.csv'), na_values=null_vals)
results_df      = pd.read_csv(os.path.join(DATA_DIR, 'results.csv'), na_values=null_vals)
races_df        = pd.read_csv(os.path.join(DATA_DIR, 'races.csv'), na_values=null_vals)
constructors_df = pd.read_csv(os.path.join(DATA_DIR, 'constructors.csv'), na_values=null_vals)
standings_df    = pd.read_csv(os.path.join(DATA_DIR, 'driver_standings.csv'), na_values=null_vals)
status_df       = pd.read_csv(os.path.join(DATA_DIR, 'status.csv'), na_values=null_vals)

races_filtered = races_df[races_df['year'].between(2014, 2025)].copy()

master = (
    results_df
    .merge(races_filtered[['raceId', 'year', 'round', 'name', 'circuitId', 'date']], on='raceId', how='inner')
    .merge(drivers_df[['driverId', 'driverRef', 'code', 'forename', 'surname', 'nationality']], on='driverId', how='left')
    .merge(constructors_df[['constructorId', 'name']].rename(columns={'name': 'constructor_name'}), on='constructorId', how='left')
    .merge(status_df[['statusId', 'status']], on='statusId', how='left')
)

master['driver_name'] = master['forename'] + ' ' + master['surname']
master['positionOrder'] = pd.to_numeric(master['positionOrder'], errors='coerce')
master['grid']          = pd.to_numeric(master['grid'], errors='coerce')
master['points']        = pd.to_numeric(master['points'], errors='coerce').fillna(0)

laps_pat = master['status'].str.contains('[+][0-9]+ Lap', na=False, regex=True)
master['is_win']    = (master['positionOrder'] == 1).astype(int)
master['is_podium'] = (master['positionOrder'] <= 3).astype(int)
master['is_dnf']    = (~(master['status'] == 'Finished') & ~laps_pat).astype(int)
master['pos_improvement'] = master['grid'] - master['positionOrder']

driver_stats = master.groupby(['driverId', 'driver_name', 'nationality']).agg(
    total_races    = ('raceId', 'count'),
    total_wins     = ('is_win', 'sum'),
    total_podiums  = ('is_podium', 'sum'),
    total_dnf      = ('is_dnf', 'sum'),
    total_points   = ('points', 'sum'),
    avg_finish     = ('positionOrder', 'mean'),
    avg_improvement= ('pos_improvement', 'mean'),
).reset_index()
driver_stats = driver_stats[driver_stats['total_races'] >= 15].copy()
driver_stats['win_rate']        = driver_stats['total_wins']    / driver_stats['total_races']
driver_stats['podium_rate']     = driver_stats['total_podiums'] / driver_stats['total_races']
driver_stats['dnf_rate']        = driver_stats['total_dnf']     / driver_stats['total_races']
driver_stats['points_per_race'] = driver_stats['total_points']  / driver_stats['total_races']

print(f"   Loaded {len(master):,} race results, {len(driver_stats)} qualified drivers")

# ── PNG 1: Total Points ───────────────────────────────────────────────────────
print("[2/6] Generating driver_01_total_points.png...")
top15 = driver_stats.nlargest(15, 'total_points').sort_values('total_points')
colors1 = [C_GOLD if i == len(top15)-1 else C_RED for i in range(len(top15))]

fig1 = go.Figure(go.Bar(
    x=top15['total_points'], y=top15['driver_name'],
    orientation='h',
    marker=dict(color=colors1, line=dict(color='#000', width=0.5)),
    text=top15['total_points'].apply(lambda x: f'{x:,.0f} pts'),
    textposition='outside', textfont=dict(color=C_WHITE, size=13),
))
fig1.update_layout(
    title='🏆 RaceIQ — Total Championship Points (2014–2025)',
    xaxis_title='Total Points', yaxis_title='',
    annotations=[dict(
        text='Source: Ergast F1 API | RaceIQ Analytics Platform',
        xref='paper', yref='paper', x=1, y=-0.06,
        showarrow=False, font=dict(color=C_LGREY, size=11), xanchor='right'
    )]
)
fig1 = style_fig(fig1, 820, 1920)
fig1.write_image(os.path.join(ASSETS_DIR, 'driver_01_total_points.png'), scale=1)
print("   Saved driver_01_total_points.png")

# ── PNG 2: Consistency Scatter ────────────────────────────────────────────────
print("[3/6] Generating driver_02_consistency_scatter.png...")
plot_data = driver_stats[driver_stats['total_races'] >= 30].copy()
highlight = ['Max Verstappen', 'Lewis Hamilton', 'Sebastian Vettel',
             'Charles Leclerc', 'Fernando Alonso', 'Lando Norris', 'Valtteri Bottas']
cmap = {
    'Max Verstappen':  C_GOLD,
    'Lewis Hamilton':  '#00A0DE',
    'Sebastian Vettel':C_RED,
    'Charles Leclerc': '#FF6666',
    'Fernando Alonso': '#0066FF',
    'Lando Norris':    '#FF8000',
    'Valtteri Bottas': '#5FC8FF',
}

fig2 = go.Figure()
others = plot_data[~plot_data['driver_name'].isin(highlight)]
fig2.add_trace(go.Scatter(
    x=others['win_rate']*100, y=others['podium_rate']*100,
    mode='markers', marker=dict(size=9, color=C_LGREY, opacity=0.4),
    hovertemplate='<b>%{customdata}</b><br>Win: %{x:.1f}%<br>Podium: %{y:.1f}%<extra></extra>',
    customdata=others['driver_name'], name='Other Drivers'
))
for d in highlight:
    row = plot_data[plot_data['driver_name'] == d]
    if row.empty: continue
    row = row.iloc[0]
    fig2.add_trace(go.Scatter(
        x=[row['win_rate']*100], y=[row['podium_rate']*100],
        mode='markers+text',
        marker=dict(size=max(12, min(28, row['total_races']/7)),
                    color=cmap.get(d, C_WHITE), line=dict(color=C_WHITE, width=2)),
        text=[d.split()[-1]], textposition='top center',
        textfont=dict(color=C_WHITE, size=12, family='Arial Black'),
        name=d, showlegend=True
    ))
fig2.add_annotation(text='Elite Zone', x=38, y=78, showarrow=False,
                    font=dict(color=C_GOLD, size=14, family='Arial Black'), opacity=0.8)
fig2.update_layout(
    title='🎯 RaceIQ — Driver Consistency Map: Win Rate vs Podium Rate (2014–2025)',
    xaxis_title='Win Rate (%)', yaxis_title='Podium Rate (%)',
    legend=dict(orientation='v', x=0.01, y=0.99)
)
fig2 = style_fig(fig2, 900, 1920)
fig2.write_image(os.path.join(ASSETS_DIR, 'driver_02_consistency_scatter.png'), scale=1)
print("   Saved driver_02_consistency_scatter.png")

# ── PNG 3: Points Progression ─────────────────────────────────────────────────
print("[4/6] Generating driver_03_points_progression.png...")
top5_names = driver_stats.nlargest(5, 'total_points')['driver_name'].tolist()
season_pts = master[master['driver_name'].isin(top5_names)].groupby(
    ['driver_name', 'year'])['points'].sum().reset_index()

palette5 = [C_GOLD, '#00A0DE', C_RED, '#5FCFFF', '#FF8000']
fig3 = go.Figure()
for i, d in enumerate(top5_names):
    df_d = season_pts[season_pts['driver_name'] == d].sort_values('year')
    if df_d.empty: continue
    fig3.add_trace(go.Scatter(
        x=df_d['year'], y=df_d['points'],
        mode='lines+markers', name=d,
        line=dict(color=palette5[i], width=3),
        marker=dict(size=10, color=palette5[i], line=dict(color=C_WHITE, width=1.5)),
    ))
fig3.update_layout(
    title='📈 RaceIQ — Season Points Progression: Top 5 Drivers (2014–2025)',
    xaxis_title='Season', yaxis_title='Season Points',
    xaxis=dict(dtick=1, tickangle=-45),
    legend=dict(orientation='h', y=1.08, x=0.5, xanchor='center', font=dict(size=13))
)
fig3 = style_fig(fig3, 820, 1920)
fig3.write_image(os.path.join(ASSETS_DIR, 'driver_03_points_progression.png'), scale=1)
print("   Saved driver_03_points_progression.png")

# ── PNG 4: Head-to-Head Radar ─────────────────────────────────────────────────
print("[5/6] Generating driver_04_head_to_head.png...")

def get_radar_for_export(name):
    r = driver_stats[driver_stats['driver_name'] == name]
    if r.empty: return None
    r = r.iloc[0]
    try:
        qual_df = pd.read_csv(os.path.join(DATA_DIR, 'qualifying.csv'), na_values=null_vals)
        qual_m = qual_df.merge(races_filtered[['raceId']], on='raceId')
        qual_m = qual_m.merge(drivers_df[['driverId', 'forename', 'surname']], on='driverId')
        qual_m['driver_name'] = qual_m['forename'] + ' ' + qual_m['surname']
        poles = int(len(qual_m[(qual_m['driver_name'] == name) & (qual_m['position'] == 1)]))
    except:
        poles = 0
    return {
        'Wins %':      round(r['win_rate'] * 100, 1),
        'Podiums %':   round(r['podium_rate'] * 100, 1),
        'Pts/Race':    round(min(r['points_per_race'], 25), 1),
        'DNF Risk':    round((1 - r['dnf_rate']) * 100, 1),
        'Poles':       poles,
        'Consistency': round(max(0, 100 - r['avg_finish'] * 5), 1),
    }

ver_data = get_radar_for_export('Max Verstappen')
ham_data = get_radar_for_export('Lewis Hamilton')
cats = list(ver_data.keys())

def hex_to_rgba(hex_color, alpha=0.15):
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'

fig4 = go.Figure()
for data, name, color in [(ver_data, 'Max Verstappen', C_GOLD), (ham_data, 'Lewis Hamilton', '#00A0DE')]:
    vals = list(data.values())
    fig4.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=cats + [cats[0]],
        name=name, fill='toself',
        fillcolor=hex_to_rgba(color, 0.18),
        line=dict(color=color, width=3),
        marker=dict(size=8, color=color)
    ))

fig4.update_layout(
    title='⚔️ RaceIQ — Head-to-Head: Verstappen vs Hamilton (2014–2025)',
    polar=dict(
        bgcolor='#111111',
        radialaxis=dict(visible=True, range=[0, 115], color=C_LGREY, gridcolor=C_GREY,
                        tickfont=dict(size=11)),
        angularaxis=dict(color=C_WHITE, gridcolor=C_GREY, tickfont=dict(size=13))
    ),
    paper_bgcolor=C_DARK,
    font=dict(color=C_WHITE, family='Arial', size=13),
    height=900, width=1200,
    margin=dict(l=80, r=80, t=100, b=80),
    legend=dict(bgcolor=C_CARD, font=dict(size=14)),
    title_font=dict(color=C_WHITE, size=20, family='Arial Black'),
)
fig4.write_image(os.path.join(ASSETS_DIR, 'driver_04_head_to_head.png'), scale=1.6)
print("   Saved driver_04_head_to_head.png")

# ── PNG 5: DNF Reliability ────────────────────────────────────────────────────
print("[6/6] Generating driver_05_dnf_reliability.png...")
top10_dnf = driver_stats[driver_stats['total_races'] >= 30].nlargest(10, 'dnf_rate').sort_values('dnf_rate', ascending=False)

fig5 = go.Figure(go.Bar(
    x=top10_dnf['driver_name'],
    y=top10_dnf['dnf_rate'] * 100,
    marker=dict(
        color=top10_dnf['dnf_rate'],
        colorscale=[[0, C_GREY], [0.5, '#FF6B35'], [1, C_RED]],
        line=dict(color='#000', width=0.5)
    ),
    text=top10_dnf['dnf_rate'].apply(lambda x: f'{x:.1%}'),
    textposition='outside', textfont=dict(color=C_WHITE, size=14),
))
fig5.add_hline(y=20, line_dash='dash', line_color=C_GOLD, opacity=0.7,
               annotation_text='20% risk threshold', annotation_font_color=C_GOLD,
               annotation_font_size=13)
fig5.update_layout(
    title='⚠️ RaceIQ — DNF Rate Reliability Analysis: Top 10 (2014–2025)',
    xaxis_title='Driver', yaxis_title='DNF Rate (%)',
    xaxis=dict(tickangle=-30)
)
fig5 = style_fig(fig5, 820, 1920)
fig5.write_image(os.path.join(ASSETS_DIR, 'driver_05_dnf_reliability.png'), scale=1)
print("   Saved driver_05_dnf_reliability.png")

print(f"\n[DONE] All 5 PNG exports saved to: {ASSETS_DIR}")
for f in os.listdir(ASSETS_DIR):
    path = os.path.join(ASSETS_DIR, f)
    size_kb = os.path.getsize(path) / 1024
    print(f"   {f} ({size_kb:.0f} KB)")
