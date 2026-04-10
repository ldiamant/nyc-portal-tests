#!/usr/bin/env python3
"""
Generate Social Vulnerability Index (SVI) analysis JSON for the IBX Impact Dashboard.
Uses CDC/ATSDR SVI 2022 data.
"""

import json
import gzip
import csv
import os
from datetime import datetime

def safe_float(v):
    """Convert to float, treating -999 and -666666666 as null."""
    try:
        val = float(v)
        return val if val != -999 and val != -666666666 else None
    except:
        return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')

    # Load IBX summary data
    with gzip.open(os.path.join(data_dir, 'tract_summary_data.json.gz'), 'rt') as f:
        summary = json.load(f)

    ibx_tracts = set(summary['by_origin'].keys())
    print(f"IBX-affected tracts: {len(ibx_tracts)}")

    # Load SVI data
    svi = {}
    with open(os.path.join(data_dir, 'census', 'NewYork.csv'), 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fips = row['FIPS']
            if fips in ibx_tracts:
                svi[fips] = row

    print(f"SVI records matching IBX tracts: {len(svi)}")

    # Load census for population
    census = {}
    with open(os.path.join(data_dir, 'census', 'NYC_Census.csv'), 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            census[row['GEOID']] = row

    # Build tract data with SVI
    tracts_with_svi = []
    for t in ibx_tracts:
        if t not in svi:
            continue
        rpl = safe_float(svi[t]['RPL_THEMES'])
        if rpl is None:
            continue

        pop = safe_float(census[t]['pop_total']) or 0
        time_change = summary['by_origin'][t]['avg_time_change_min']
        hours_saved = summary['by_origin'][t]['total_time_saved_hours']

        tracts_with_svi.append({
            'geoid': t,
            'svi': rpl,
            'svi_t1': safe_float(svi[t]['RPL_THEME1']),
            'svi_t2': safe_float(svi[t]['RPL_THEME2']),
            'svi_t3': safe_float(svi[t]['RPL_THEME3']),
            'svi_t4': safe_float(svi[t]['RPL_THEME4']),
            'pop': pop,
            'time_change': time_change,
            'hours_saved': hours_saved,
            'borough': census[t]['BOROUGH']
        })

    print(f"Tracts with valid SVI: {len(tracts_with_svi)}")

    # Calculate total population
    total_pop = sum(t['pop'] for t in tracts_with_svi)
    total_hours = sum(t['hours_saved'] for t in tracts_with_svi)

    # === BUILD ANALYSIS ===
    analysis = {
        'generated': datetime.now().isoformat(),
        'overview': {},
        'quartiles': [],
        'themes': [],
        'spotlight': {},
        'correlation': {}
    }

    # --- Overview ---
    analysis['overview'] = {
        'tracts_with_svi': len(tracts_with_svi),
        'total_population': round(total_pop),
        'total_hours_saved': round(total_hours),
    }

    # --- Quartile Analysis ---
    tracts_with_svi.sort(key=lambda x: x['svi'])
    n = len(tracts_with_svi)
    quartile_defs = [
        ('low', 'Low Vulnerability', 0, n//4),
        ('moderate', 'Moderate', n//4, n//2),
        ('high', 'High', n//2, 3*n//4),
        ('very_high', 'Very High', 3*n//4, n),
    ]

    for key, label, start, end in quartile_defs:
        group = tracts_with_svi[start:end]
        total_p = sum(t['pop'] for t in group)
        weighted_time = sum(t['time_change'] * t['pop'] for t in group)
        avg_time = weighted_time / total_p if total_p > 0 else 0
        total_h = sum(t['hours_saved'] for t in group)
        svi_min = group[0]['svi']
        svi_max = group[-1]['svi']

        analysis['quartiles'].append({
            'key': key,
            'label': label,
            'svi_min': round(svi_min, 2),
            'svi_max': round(svi_max, 2),
            'tract_count': len(group),
            'population': round(total_p),
            'pct_of_total': round((total_p / total_pop) * 100, 1),
            'avg_time_change': round(avg_time, 1),
            'total_hours_saved': round(total_h),
        })

    # --- Theme Analysis ---
    theme_defs = [
        ('socioeconomic', 'Socioeconomic Status', 'svi_t1',
         'Poverty, unemployment, housing cost burden, education, insurance'),
        ('household', 'Household Composition', 'svi_t2',
         'Elderly, children, disabled, single-parent households'),
        ('minority', 'Minority Status & Language', 'svi_t3',
         'Minority population, limited English proficiency'),
        ('housing', 'Housing & Transportation', 'svi_t4',
         'Multi-unit housing, crowding, no vehicle, group quarters'),
    ]

    for key, label, field, description in theme_defs:
        valid = [t for t in tracts_with_svi if t[field] is not None]
        high_vuln = [t for t in valid if t[field] >= 0.5]
        low_vuln = [t for t in valid if t[field] < 0.5]

        high_pop = sum(t['pop'] for t in high_vuln)
        high_time = sum(t['time_change'] * t['pop'] for t in high_vuln) / high_pop if high_pop > 0 else 0
        high_hours = sum(t['hours_saved'] for t in high_vuln)

        low_pop = sum(t['pop'] for t in low_vuln)
        low_time = sum(t['time_change'] * t['pop'] for t in low_vuln) / low_pop if low_pop > 0 else 0
        low_hours = sum(t['hours_saved'] for t in low_vuln)

        diff = high_time - low_time
        # Positive diff means high vulnerability benefits MORE (equitable)
        # Since time_change is negative, more negative = more benefit
        # So if high_time is more negative than low_time, diff is negative, meaning high vuln benefits more

        analysis['themes'].append({
            'key': key,
            'label': label,
            'description': description,
            'high_vulnerability': {
                'tract_count': len(high_vuln),
                'population': round(high_pop),
                'avg_time_change': round(high_time, 1),
                'total_hours_saved': round(high_hours),
            },
            'low_vulnerability': {
                'tract_count': len(low_vuln),
                'population': round(low_pop),
                'avg_time_change': round(low_time, 1),
                'total_hours_saved': round(low_hours),
            },
            'difference': round(diff, 1),
            'equitable': diff < 0,  # True if high vulnerability benefits more
        })

    # --- Correlation ---
    svi_scores = [t['svi'] for t in tracts_with_svi]
    time_changes = [t['time_change'] for t in tracts_with_svi]

    mean_svi = sum(svi_scores) / len(svi_scores)
    mean_time = sum(time_changes) / len(time_changes)

    numerator = sum((s - mean_svi) * (t - mean_time) for s, t in zip(svi_scores, time_changes))
    denom_svi = sum((s - mean_svi)**2 for s in svi_scores)**0.5
    denom_time = sum((t - mean_time)**2 for t in time_changes)**0.5
    correlation = numerator / (denom_svi * denom_time) if denom_svi * denom_time > 0 else 0

    analysis['correlation'] = {
        'value': round(correlation, 3),
        'interpretation': 'equitable' if correlation < 0 else 'inequitable',
        'description': 'More vulnerable areas see more time savings' if correlation < 0 else 'More vulnerable areas see less time savings'
    }

    # --- Scatter Plot Data ---
    # Sample tracts for scatter plot (every 3rd tract, sorted by SVI)
    sorted_tracts = sorted(tracts_with_svi, key=lambda x: x['svi'])
    scatter_points = []
    for i, t in enumerate(sorted_tracts):
        if i % 3 == 0:  # Sample every 3rd tract
            scatter_points.append({
                'svi': round(t['svi'], 3),
                'time': round(t['time_change'], 1),
                'pop': round(t['pop'] / 1000, 1)  # Population in thousands for sizing
            })

    analysis['scatter'] = {
        'points': scatter_points,
        'x_label': 'Social Vulnerability Index',
        'y_label': 'Time Savings (minutes)',
    }

    # --- Per-Tract SVI Lookup (for map coloring) ---
    analysis['tracts'] = {}
    for t in tracts_with_svi:
        analysis['tracts'][t['geoid']] = round(t['svi'], 3)

    # --- Equity Spotlight ---
    very_high = [t for t in tracts_with_svi if t['svi'] >= 0.75]
    very_high_big_benefit = [t for t in very_high if t['time_change'] <= -10]
    very_high_pop = sum(t['pop'] for t in very_high)
    very_high_big_pop = sum(t['pop'] for t in very_high_big_benefit)
    very_high_hours = sum(t['hours_saved'] for t in very_high)

    # Best and worst outcomes
    very_high_sorted = sorted(very_high, key=lambda x: x['time_change'])
    best_outcomes = []
    for t in very_high_sorted[:5]:
        best_outcomes.append({
            'geoid': t['geoid'],
            'svi': round(t['svi'], 2),
            'time_change': round(t['time_change'], 1),
            'population': round(t['pop']),
            'borough': t['borough']
        })

    smallest_gains = []
    for t in very_high_sorted[-5:]:
        smallest_gains.append({
            'geoid': t['geoid'],
            'svi': round(t['svi'], 2),
            'time_change': round(t['time_change'], 1),
            'population': round(t['pop']),
            'borough': t['borough']
        })

    analysis['spotlight'] = {
        'very_high_vulnerability': {
            'tract_count': len(very_high),
            'population': round(very_high_pop),
            'total_hours_saved': round(very_high_hours),
            'tracts_10plus_min': len(very_high_big_benefit),
            'tracts_10plus_pct': round(len(very_high_big_benefit) / len(very_high) * 100) if very_high else 0,
            'pop_10plus_min': round(very_high_big_pop),
            'pop_10plus_pct': round(very_high_big_pop / very_high_pop * 100) if very_high_pop > 0 else 0,
        },
        'best_outcomes': best_outcomes,
        'smallest_gains': smallest_gains,
    }

    # Write output
    output_path = os.path.join(data_dir, 'svi_analysis.json')
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"\nGenerated: {output_path}")
    print(f"Quartiles: {[q['label'] + ': ' + str(q['avg_time_change']) + ' min' for q in analysis['quartiles']]}")

if __name__ == '__main__':
    main()
