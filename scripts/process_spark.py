import pandas as pd
import numpy as np
from pathlib import Path
import glob

DATA_DIR    = Path(__file__).parent.parent / 'data'
EXPORTS_DIR = Path(__file__).parent.parent / 'exports'
EXPORTS_DIR.mkdir(exist_ok=True)

def load_data():
    csv_files = list(DATA_DIR.glob('*.csv'))
    print(f"Found {len(csv_files)} CSV files")
    frames = []
    for f in csv_files:
        print(f"  Loading {f.name}...")
        df = pd.read_csv(f, low_memory=False)
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    print(f"Total rows loaded: {len(combined):,}")
    return combined

def clean_data(df):
    rename_map = {
        'starttime': 'started_at',
        'stoptime': 'ended_at',
        'start station id': 'start_station_id',
        'start station name': 'start_station_name',
        'start station latitude': 'start_lat',
        'start station longitude': 'start_lng',
        'end station id': 'end_station_id',
        'end station name': 'end_station_name',
        'end station latitude': 'end_lat',
        'end station longitude': 'end_lng',
        'usertype': 'member_casual',
        'tripduration': 'duration_seconds'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    df['started_at'] = pd.to_datetime(df['started_at'], errors='coerce')
    df['ended_at']   = pd.to_datetime(df['ended_at'],   errors='coerce')

    if 'duration_seconds' not in df.columns:
        df['duration_seconds'] = (df['ended_at'] - df['started_at']).dt.total_seconds()

    df['duration_minutes'] = df['duration_seconds'] / 60

    df['hour']        = df['started_at'].dt.hour
    df['day_of_week'] = df['started_at'].dt.dayofweek
    df['month']       = df['started_at'].dt.month
    df['date']        = df['started_at'].dt.date
    df['is_weekend']  = df['day_of_week'].isin([5, 6])

    df = df[(df['duration_minutes'] >= 1) & (df['duration_minutes'] <= 180)]
    df = df.dropna(subset=['started_at', 'ended_at'])

    print(f"Clean rows: {len(df):,}")
    return df

def run_aggregations(df):

    print("Running aggregation 1: hourly trip patterns...")
    hourly = (df.groupby(['hour', 'is_weekend'])
               .agg(trip_count=('duration_minutes', 'count'),
                    avg_duration=('duration_minutes', 'mean'))
               .reset_index())
    total = hourly['trip_count'].sum()
    hourly['pct_of_total'] = (hourly['trip_count'] / total * 100).round(2)
    hourly.to_csv(EXPORTS_DIR / 'hourly_patterns.csv', index=False)
    print("  Saved hourly_patterns.csv")

    print("Running aggregation 2: busiest start stations...")
    stations = (df.groupby(['start_station_name', 'start_station_id'])
                  .agg(lat=('start_lat', 'mean'),
                       lng=('start_lng', 'mean'),
                       departures=('duration_minutes', 'count'),
                       avg_trip_duration=('duration_minutes', 'mean'),
                       weekend_trips=('is_weekend', 'sum'))
                  .reset_index())
    stations['weekday_trips'] = stations['departures'] - stations['weekend_trips']
    stations = stations.sort_values('departures', ascending=False).head(100)
    stations.to_csv(EXPORTS_DIR / 'top_stations.csv', index=False)
    print("  Saved top_stations.csv")

    print("Running aggregation 3: monthly trends...")
    monthly = (df.groupby('month')
                 .agg(total_trips=('duration_minutes', 'count'),
                      avg_duration=('duration_minutes', 'mean'),
                      active_stations=('start_station_id', 'nunique'))
                 .reset_index())
    if 'member_casual' in df.columns:
        member = df[df['member_casual'] == 'member'].groupby('month').size().reset_index(name='member_trips')
        casual = df[df['member_casual'] == 'casual'].groupby('month').size().reset_index(name='casual_trips')
        monthly = monthly.merge(member, on='month', how='left')
        monthly = monthly.merge(casual, on='month', how='left')
    monthly.to_csv(EXPORTS_DIR / 'monthly_trends.csv', index=False)
    print("  Saved monthly_trends.csv")

    print("Running aggregation 4: trip duration distribution...")
    df['duration_bucket'] = (df['duration_minutes'] // 5 * 5).astype(int)
    duration_dist = (df[df['duration_minutes'] <= 60]
                     .groupby(['duration_bucket', 'member_casual'])
                     .size()
                     .reset_index(name='trip_count'))
    duration_dist.to_csv(EXPORTS_DIR / 'duration_distribution.csv', index=False)
    print("  Saved duration_distribution.csv")

    print("Running aggregation 5: top routes...")
    routes = (df.groupby(['start_station_name', 'end_station_name'])
                .agg(trip_count=('duration_minutes', 'count'),
                     avg_duration=('duration_minutes', 'mean'))
                .reset_index())
    routes = routes[routes['start_station_name'] != routes['end_station_name']]
    routes = routes.sort_values('trip_count', ascending=False).head(50)
    routes.to_csv(EXPORTS_DIR / 'top_routes.csv', index=False)
    print("  Saved top_routes.csv")

    print("All aggregations complete.")

if __name__ == '__main__':
    print("Loading data...")
    df = load_data()
    print("Cleaning data...")
    df = clean_data(df)
    run_aggregations(df)
    print("Done.")