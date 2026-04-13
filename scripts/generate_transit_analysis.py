#!/usr/bin/env python3
"""
Generate transit_analysis.json for the Transit Analysis Dashboard.
Processes route_summary.json.gz and ibx_stops.json.gz to create summary statistics.
"""

import json
import gzip
from datetime import datetime
from pathlib import Path

def main():
    data_dir = Path(__file__).parent.parent / 'data'

    # Load route summary
    with gzip.open(data_dir / 'route_summary.json.gz', 'rt') as f:
        route_data = json.load(f)

    # Load IBX stops (station ridership data)
    with gzip.open(data_dir / 'ibx_stops.json.gz', 'rt') as f:
        all_stops_data = json.load(f)

    # Load actual IBX stations from GeoJSON to get real station count
    with open(data_dir / 'IBX' / 'stations.geojson', 'r') as f:
        ibx_stations_geo = json.load(f)

    ibx_station_count = len(ibx_stations_geo['features'])  # 19 stations

    # Get IBX station names for filtering
    ibx_station_names = [
        f['properties'].get('name', f['properties'].get('Name', ''))
        for f in ibx_stations_geo['features']
    ]

    # Filter stops to IBX stations (exact match)
    stops_data = [s for s in all_stops_data if s['Stop'] in ibx_station_names]

    # Sort by ridership
    stops_data = sorted(stops_data, key=lambda x: x['Total Passengers'], reverse=True)

    routes = route_data['routes']

    # Separate IBX from other routes
    ibx_route = next((r for r in routes if r['route'] == 'IBX'), None)
    other_routes = [r for r in routes if r['route'] != 'IBX']

    # Categorize routes
    gaining_routes = [r for r in other_routes if isinstance(r['pct_change'], (int, float)) and r['pct_change'] > 0]
    losing_routes = [r for r in other_routes if isinstance(r['pct_change'], (int, float)) and r['pct_change'] < 0]

    # Sort by impact
    gaining_routes.sort(key=lambda x: x['passenger_change'], reverse=True)
    losing_routes.sort(key=lambda x: x['passenger_change'])

    # Calculate network totals
    total_gained = sum(r['passenger_change'] for r in gaining_routes)
    total_lost = sum(r['passenger_change'] for r in losing_routes)

    # Process stations - sort by total passengers
    stations = sorted(stops_data, key=lambda x: x['Total Passengers'], reverse=True)

    # Determine route types (simplified - based on route name patterns)
    def get_route_type(route_name):
        if route_name in ['1', '2', '3', '4', '5', '6', '7', 'A', 'C', 'E', 'B', 'D', 'F', 'M',
                          'G', 'J', 'Z', 'L', 'N', 'Q', 'R', 'W', 'S']:
            return 'subway'
        elif route_name.startswith('SIR') or route_name in ['LIRR', 'MNR']:
            return 'rail'
        else:
            return 'bus'

    # Categorize by route type
    subway_impact = {'gaining': 0, 'losing': 0, 'routes_gaining': 0, 'routes_losing': 0}
    bus_impact = {'gaining': 0, 'losing': 0, 'routes_gaining': 0, 'routes_losing': 0}

    for r in other_routes:
        if not isinstance(r['pct_change'], (int, float)):
            continue
        rtype = get_route_type(r['route'])
        change = r['passenger_change']
        if rtype == 'subway':
            if change > 0:
                subway_impact['gaining'] += change
                subway_impact['routes_gaining'] += 1
            else:
                subway_impact['losing'] += change
                subway_impact['routes_losing'] += 1
        else:  # bus
            if change > 0:
                bus_impact['gaining'] += change
                bus_impact['routes_gaining'] += 1
            else:
                bus_impact['losing'] += change
                bus_impact['routes_losing'] += 1

    # Build output
    analysis = {
        'generated': datetime.now().isoformat(),
        'ibx': {
            'projected_ridership': ibx_route['new_passengers'] if ibx_route else 0,
            'station_count': ibx_station_count,
            'total_boarding': sum(s['Boarding'] for s in stations),
            'total_alighting': sum(s['Alighting'] for s in stations),
            'total_transfers': sum(s['Transfers'] for s in stations),
        },
        'stations': {
            'top_10': [
                {
                    'name': s['Stop'],
                    'total': round(s['Total Passengers']),
                    'boarding': round(s['Boarding']),
                    'alighting': round(s['Alighting']),
                    'transfers': round(s['Transfers']),
                }
                for s in stations[:10]
            ],
            'all': [
                {
                    'name': s['Stop'],
                    'total': round(s['Total Passengers']),
                }
                for s in stations
            ]
        },
        'network_effects': {
            'routes_gaining': len(gaining_routes),
            'routes_losing': len(losing_routes),
            'total_passengers_gained': total_gained,
            'total_passengers_lost': abs(total_lost),
            'net_redistribution': total_gained + total_lost,
        },
        'top_gainers': [
            {
                'route': r['route'],
                'type': get_route_type(r['route']),
                'baseline': r['baseline_passengers'],
                'new': r['new_passengers'],
                'change': r['passenger_change'],
                'pct_change': round(r['pct_change'], 1) if isinstance(r['pct_change'], (int, float)) else r['pct_change'],
            }
            for r in gaining_routes[:8]
        ],
        'top_losers': [
            {
                'route': r['route'],
                'type': get_route_type(r['route']),
                'baseline': r['baseline_passengers'],
                'new': r['new_passengers'],
                'change': r['passenger_change'],
                'pct_change': round(r['pct_change'], 1) if isinstance(r['pct_change'], (int, float)) else r['pct_change'],
            }
            for r in losing_routes[:8]
        ],
        'by_type': {
            'subway': subway_impact,
            'bus': bus_impact,
        }
    }

    # Write output
    output_path = data_dir / 'transit_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"Generated {output_path}")
    print(f"  IBX ridership: {analysis['ibx']['projected_ridership']:,}")
    print(f"  Stations: {analysis['ibx']['station_count']}")
    print(f"  Routes gaining: {len(gaining_routes)}")
    print(f"  Routes losing: {len(losing_routes)}")

if __name__ == '__main__':
    main()
