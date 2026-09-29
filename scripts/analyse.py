import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import folium
from folium.plugins import HeatMap
from pathlib import Path

EXPORTS = Path(__file__).parent.parent / 'exports'
DOCS    = Path(__file__).parent.parent / 'docs'
DOCS.mkdir(exist_ok=True)

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 150
})

def chart_hourly_heatmap():
    df = pd.read_csv(EXPORTS / 'hourly_patterns.csv')
    pivot = df.pivot_table(
        index='is_weekend', columns='hour',
        values='trip_count', aggfunc='sum'
    )
    pivot.index = ['Weekday', 'Weekend']

    fig, ax = plt.subplots(figsize=(14, 3.5))
    sns.heatmap(pivot, cmap='Blues', annot=True, fmt='.0f',
                linewidths=0.5, ax=ax, cbar_kws={'label': 'Trips'})
    ax.set_title('Trip Volume by Hour — Weekday vs Weekend',
                 fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('')
    plt.tight_layout()
    plt.savefig(DOCS / 'hourly_heatmap.png', bbox_inches='tight')
    plt.close()
    print("Saved hourly_heatmap.png")

def chart_duration_distribution():
    df = pd.read_csv(EXPORTS / 'duration_distribution.csv')

    fig, ax = plt.subplots(figsize=(11, 5))
    for user_type, grp in df.groupby('member_casual'):
        ax.bar(grp['duration_bucket'], grp['trip_count'],
               alpha=0.7, label=user_type.capitalize(), width=4)

    ax.set_title('Trip Duration Distribution — Members vs Casual Riders',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Trip Duration (minutes)')
    ax.set_ylabel('Number of Trips')
    ax.legend()
    ax.xaxis.set_major_locator(plt.MultipleLocator(5))
    plt.tight_layout()
    plt.savefig(DOCS / 'duration_distribution.png', bbox_inches='tight')
    plt.close()
    print("Saved duration_distribution.png")

def chart_monthly_trend():
    df = pd.read_csv(EXPORTS / 'monthly_trends.csv')
    month_labels = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                    7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    df['month_name'] = df['month'].map(month_labels)

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(df['month_name'], df['total_trips'],
            color='#185FA5', alpha=0.8, label='Total trips')
    ax1.set_ylabel('Total Trips', color='#185FA5')
    ax1.set_title('Monthly Trip Volume and Average Duration',
                  fontsize=13, fontweight='bold')

    ax2 = ax1.twinx()
    ax2.plot(df['month_name'], df['avg_duration'],
             color='#E07B39', marker='o', linewidth=2,
             label='Avg duration (min)')
    ax2.set_ylabel('Avg Duration (min)', color='#E07B39')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    plt.tight_layout()
    plt.savefig(DOCS / 'monthly_trend.png', bbox_inches='tight')
    plt.close()
    print("Saved monthly_trend.png")

def make_station_map():
    df = pd.read_csv(EXPORTS / 'top_stations.csv')
    df = df.dropna(subset=['lat', 'lng'])
    df = df[(df['lat'] > 40) & (df['lat'] < 41)]

    norm = (df['departures'] - df['departures'].min()) / (
            df['departures'].max() - df['departures'].min())

    m = folium.Map(location=[40.7282, -73.9942], zoom_start=12,
                   tiles='CartoDB positron')

    for idx, row in df.iterrows():
        n = norm[idx]
        colour = plt.cm.RdYlBu_r(n)
        hex_colour = mcolors.to_hex(colour)
        radius = 5 + (n * 20)

        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=radius,
            color=hex_colour,
            fill=True,
            fill_color=hex_colour,
            fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>{row['start_station_name']}</b><br>"
                f"Departures: {int(row['departures']):,}<br>"
                f"Avg trip: {row['avg_trip_duration']:.1f} min",
                max_width=250
            )
        ).add_to(m)

    heat_data = [[row['lat'], row['lng'], row['departures']]
                 for _, row in df.iterrows()]
    HeatMap(heat_data, radius=20, blur=15).add_to(m)

    map_path = DOCS / 'station_map.html'
    m.save(str(map_path))
    print("Saved station_map.html")

if __name__ == '__main__':
    chart_hourly_heatmap()
    chart_duration_distribution()
    chart_monthly_trend()
    make_station_map()
    print("All charts and map generated.")