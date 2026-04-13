#!/usr/bin/env python3
"""
Generate demographic analysis JSON for the IBX Impact Dashboard.
Run this script whenever census or summary data changes.
"""

import json
import gzip
import csv
import os

def safe_float(v):
    """Convert to float, treating -666666666 as null."""
    try:
        val = float(v)
        return val if val != -666666666 else None
    except:
        return None

def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')

    # Load IBX summary data
    with gzip.open(os.path.join(data_dir, 'tract_summary_data.json.gz'), 'rt') as f:
        summary = json.load(f)

    # Load census data
    census = {}
    with open(os.path.join(data_dir, 'census', 'NYC_Census.csv'), 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            census[row['GEOID']] = row

    # Get IBX-affected tracts that match census data
    ibx_tracts = set(summary['by_origin'].keys()) & set(census.keys())
    all_tracts = set(census.keys())

    print(f"IBX-affected tracts: {len(ibx_tracts)}")
    print(f"Total census tracts: {len(all_tracts)}")

    # === COMPUTE ANALYSIS ===

    analysis = {
        'generated': None,  # Will be set at end
        'overview': {},
        'income': {},
        'commute': {},
        'race_ethnicity': {},
        'transit_dependence': {},
        'borough': {},
        'age': {},
    }

    # --- Overview Stats ---
    total_pop = sum(safe_float(census[t]['pop_total']) or 0 for t in ibx_tracts)
    total_trips = sum(summary['by_origin'][t]['total_trips'] for t in ibx_tracts)
    total_hours_saved = sum(summary['by_origin'][t]['total_time_saved_hours'] for t in ibx_tracts)

    # Population-weighted average time change
    weighted_time = 0
    weight_sum = 0
    for t in ibx_tracts:
        pop = safe_float(census[t]['pop_total']) or 0
        if pop > 0:
            weighted_time += pop * summary['by_origin'][t]['avg_time_change_min']
            weight_sum += pop
    avg_time_change = weighted_time / weight_sum if weight_sum > 0 else 0

    analysis['overview'] = {
        'affected_tracts': len(ibx_tracts),
        'total_tracts': len(all_tracts),
        'population': round(total_pop),
        'total_trips': round(total_trips),
        'total_hours_saved': round(total_hours_saved),
        'avg_time_change_min': round(avg_time_change, 1),
    }

    # --- Income Quartiles ---
    incomes = [(t, safe_float(census[t]['med_hhinc'])) for t in ibx_tracts]
    incomes = [(t, i) for t, i in incomes if i is not None and i > 0]
    incomes.sort(key=lambda x: x[1])

    n = len(incomes)
    quartiles = [
        ('q1', 'Lowest Income', incomes[:n//4]),
        ('q2', 'Lower-Middle', incomes[n//4:n//2]),
        ('q3', 'Upper-Middle', incomes[n//2:3*n//4]),
        ('q4', 'Highest Income', incomes[3*n//4:]),
    ]

    analysis['income']['quartiles'] = []
    for key, label, quartile in quartiles:
        if not quartile:
            continue
        tract_ids = [t for t, _ in quartile]
        time_changes = [summary['by_origin'][t]['avg_time_change_min'] for t in tract_ids]
        hours_saved = [summary['by_origin'][t]['total_time_saved_hours'] for t in tract_ids]
        populations = [safe_float(census[t]['pop_total']) or 0 for t in tract_ids]

        # Population-weighted average
        weighted = sum(tc * p for tc, p in zip(time_changes, populations))
        total_p = sum(populations)
        avg_tc = weighted / total_p if total_p > 0 else sum(time_changes) / len(time_changes)
        total_hours = sum(hours_saved)

        analysis['income']['quartiles'].append({
            'key': key,
            'label': label,
            'income_min': round(quartile[0][1]),
            'income_max': round(quartile[-1][1]),
            'tract_count': len(quartile),
            'population': round(total_p),
            'avg_time_change': round(avg_tc, 1),
            'total_hours_saved': round(total_hours),
        })

    # --- Commute Length ---
    commute_data = [(t, safe_float(census[t]['mean_trvtm']), summary['by_origin'][t]['avg_time_change_min'])
                    for t in ibx_tracts if safe_float(census[t]['mean_trvtm'])]
    commute_data = [(t, c, tc) for t, c, tc in commute_data if c is not None and c > 0]

    commute_groups = [
        ('short', 'Short (<30 min)', [x for x in commute_data if x[1] < 30]),
        ('medium', 'Medium (30-45 min)', [x for x in commute_data if 30 <= x[1] < 45]),
        ('long', 'Long (45-60 min)', [x for x in commute_data if 45 <= x[1] < 60]),
        ('very_long', 'Very Long (60+ min)', [x for x in commute_data if x[1] >= 60]),
    ]

    analysis['commute']['groups'] = []
    for key, label, group in commute_groups:
        if not group:
            continue
        tract_ids = [t for t, _, _ in group]
        populations = [safe_float(census[t]['pop_total']) or 0 for t in tract_ids]
        hours_saved = [summary['by_origin'][t]['total_time_saved_hours'] for t in tract_ids]
        time_changes = [tc for _, _, tc in group]
        avg_commute = sum(c for _, c, _ in group) / len(group)

        # Population-weighted
        weighted = sum(tc * p for tc, p in zip(time_changes, populations))
        total_p = sum(populations)
        avg_tc = weighted / total_p if total_p > 0 else sum(time_changes) / len(time_changes)
        total_hours = sum(hours_saved)

        analysis['commute']['groups'].append({
            'key': key,
            'label': label,
            'avg_current_commute': round(avg_commute, 1),
            'tract_count': len(group),
            'population': round(total_p),
            'avg_time_change': round(avg_tc, 1),
            'total_hours_saved': round(total_hours),
        })

    # --- Race/Ethnicity ---
    race_fields = [
        ('hispanic', 'Hispanic/Latino', 'pct_hisp'),
        ('black', 'Black', 'pct_black'),
        ('asian', 'Asian', 'pct_asian'),
        ('white', 'White', 'pct_white'),
    ]

    analysis['race_ethnicity']['groups'] = []
    for key, label, field in race_fields:
        total_pop_group = 0
        weighted_time = 0
        weighted_hours = 0
        for t in ibx_tracts:
            pop = safe_float(census[t]['pop_total']) or 0
            pct = safe_float(census[t][field]) or 0
            group_pop = pop * (pct / 100)
            time_change = summary['by_origin'][t]['avg_time_change_min']
            hours_saved = summary['by_origin'][t]['total_time_saved_hours']
            weighted_time += group_pop * time_change
            # Attribute hours saved proportionally to demographic share
            weighted_hours += hours_saved * (pct / 100)
            total_pop_group += group_pop

        if total_pop_group > 0:
            avg_time = weighted_time / total_pop_group
            analysis['race_ethnicity']['groups'].append({
                'key': key,
                'label': label,
                'population': round(total_pop_group),
                'pct_of_total': round((total_pop_group / total_pop) * 100, 1),
                'avg_time_change': round(avg_time, 1),
                'total_hours_saved': round(weighted_hours),
            })

    # --- Transit Dependence (No Vehicle %) ---
    noveh = [(t, safe_float(census[t]['pct_noveh'])) for t in ibx_tracts]
    noveh = [(t, v) for t, v in noveh if v is not None]
    noveh.sort(key=lambda x: x[1])

    n = len(noveh)
    transit_groups = [
        ('low', 'Car-Owning', noveh[:n//3]),
        ('medium', 'Mixed', noveh[n//3:2*n//3]),
        ('high', 'Transit-Dependent', noveh[2*n//3:]),
    ]

    analysis['transit_dependence']['groups'] = []
    for key, label, group in transit_groups:
        if not group:
            continue
        tract_ids = [t for t, _ in group]
        populations = [safe_float(census[t]['pop_total']) or 0 for t in tract_ids]
        hours_saved = [summary['by_origin'][t]['total_time_saved_hours'] for t in tract_ids]
        time_changes = [summary['by_origin'][t]['avg_time_change_min'] for t in tract_ids]

        weighted = sum(tc * p for tc, p in zip(time_changes, populations))
        total_p = sum(populations)
        avg_tc = weighted / total_p if total_p > 0 else sum(time_changes) / len(time_changes)
        total_hours = sum(hours_saved)

        analysis['transit_dependence']['groups'].append({
            'key': key,
            'label': label,
            'pct_noveh_min': round(group[0][1], 1),
            'pct_noveh_max': round(group[-1][1], 1),
            'tract_count': len(group),
            'population': round(total_p),
            'avg_time_change': round(avg_tc, 1),
            'total_hours_saved': round(total_hours),
        })

    # --- Borough ---
    boroughs_data = {}
    for t in ibx_tracts:
        b = census[t]['BOROUGH']
        if b not in boroughs_data:
            boroughs_data[b] = {'tracts': [], 'time_changes': [], 'populations': [], 'incomes': [], 'hours_saved': []}
        boroughs_data[b]['tracts'].append(t)
        boroughs_data[b]['time_changes'].append(summary['by_origin'][t]['avg_time_change_min'])
        boroughs_data[b]['populations'].append(safe_float(census[t]['pop_total']) or 0)
        boroughs_data[b]['hours_saved'].append(summary['by_origin'][t]['total_time_saved_hours'])
        inc = safe_float(census[t]['med_hhinc'])
        if inc and inc > 0:
            boroughs_data[b]['incomes'].append(inc)

    analysis['borough']['groups'] = []
    for b in ['Queens', 'Brooklyn', 'Manhattan', 'Bronx', 'Staten Island']:
        if b not in boroughs_data:
            continue
        data = boroughs_data[b]
        total_p = sum(data['populations'])
        weighted = sum(tc * p for tc, p in zip(data['time_changes'], data['populations']))
        avg_tc = weighted / total_p if total_p > 0 else sum(data['time_changes']) / len(data['time_changes'])
        avg_inc = sum(data['incomes']) / len(data['incomes']) if data['incomes'] else 0
        total_hours = sum(data['hours_saved'])

        analysis['borough']['groups'].append({
            'key': b.lower().replace(' ', '_'),
            'label': b,
            'tract_count': len(data['tracts']),
            'population': round(total_p),
            'avg_time_change': round(avg_tc, 1),
            'median_income': round(avg_inc),
            'total_hours_saved': round(total_hours),
        })

    # --- Age Groups ---
    age_fields = [
        ('under_18', 'Under 18', 'pct_und18'),
        ('working_age', 'Working Age (18-64)', 'pct_18t64'),
        ('seniors', 'Seniors (65+)', 'pct_65plus'),
    ]

    analysis['age']['groups'] = []
    for key, label, field in age_fields:
        total_pop_group = 0
        weighted_time = 0
        weighted_hours = 0
        for t in ibx_tracts:
            pop = safe_float(census[t]['pop_total']) or 0
            pct = safe_float(census[t][field]) or 0
            group_pop = pop * (pct / 100)
            time_change = summary['by_origin'][t]['avg_time_change_min']
            hours_saved = summary['by_origin'][t]['total_time_saved_hours']
            weighted_time += group_pop * time_change
            weighted_hours += hours_saved * (pct / 100)
            total_pop_group += group_pop

        if total_pop_group > 0:
            avg_time = weighted_time / total_pop_group
            analysis['age']['groups'].append({
                'key': key,
                'label': label,
                'population': round(total_pop_group),
                'pct_of_total': round((total_pop_group / total_pop) * 100, 1),
                'avg_time_change': round(avg_time, 1),
                'total_hours_saved': round(weighted_hours),
            })

    # --- Time Savings Distribution ---
    # Create histogram buckets of time savings
    buckets = [
        ('0-5', '0-5 min', 0, 5),
        ('5-10', '5-10 min', 5, 10),
        ('10-15', '10-15 min', 10, 15),
        ('15-20', '15-20 min', 15, 20),
        ('20-25', '20-25 min', 20, 25),
        ('25+', '25+ min', 25, float('inf')),
    ]

    analysis['distribution'] = {'buckets': []}
    for key, label, min_val, max_val in buckets:
        bucket_pop = 0
        bucket_hours = 0
        bucket_tracts = 0
        for t in ibx_tracts:
            tc = abs(summary['by_origin'][t]['avg_time_change_min'])  # Use absolute value
            if min_val <= tc < max_val:
                pop = safe_float(census[t]['pop_total']) or 0
                hours = summary['by_origin'][t]['total_time_saved_hours']
                bucket_pop += pop
                bucket_hours += hours
                bucket_tracts += 1

        analysis['distribution']['buckets'].append({
            'key': key,
            'label': label,
            'min': min_val,
            'max': max_val if max_val != float('inf') else None,
            'population': round(bucket_pop),
            'pct_of_total': round((bucket_pop / total_pop) * 100, 1) if total_pop > 0 else 0,
            'tract_count': bucket_tracts,
            'total_hours_saved': round(bucket_hours),
        })

    # --- Comparison with NYC overall ---
    def nyc_weighted_avg(field, weight_field='pop_total'):
        total_weight = 0
        weighted_sum = 0
        for t in all_tracts:
            val = safe_float(census[t][field])
            weight = safe_float(census[t][weight_field])
            if val is not None and weight is not None and weight > 0:
                weighted_sum += val * weight
                total_weight += weight
        return weighted_sum / total_weight if total_weight > 0 else None

    def ibx_weighted_avg(field, weight_field='pop_total'):
        total_weight = 0
        weighted_sum = 0
        for t in ibx_tracts:
            val = safe_float(census[t][field])
            weight = safe_float(census[t][weight_field])
            if val is not None and weight is not None and weight > 0:
                weighted_sum += val * weight
                total_weight += weight
        return weighted_sum / total_weight if total_weight > 0 else None

    # Calculate % of workers using transit
    def calc_transit_pct(tracts):
        total_transit = 0
        total_workers = 0
        for t in tracts:
            transit = safe_float(census[t].get('cmut_trans', 0)) or 0
            car = safe_float(census[t].get('cmut_car', 0)) or 0
            bike = safe_float(census[t].get('cmut_bike', 0)) or 0
            walk = safe_float(census[t].get('cmut_walk', 0)) or 0
            workers = transit + car + bike + walk
            total_transit += transit
            total_workers += workers
        return (total_transit / total_workers * 100) if total_workers > 0 else 0

    analysis['comparison'] = {
        'ibx_vs_nyc': [
            {'label': 'Median HH Income', 'ibx': round(ibx_weighted_avg('med_hhinc') or 0), 'nyc': round(nyc_weighted_avg('med_hhinc') or 0), 'unit': '$'},
            {'label': 'Poverty Rate', 'ibx': round(ibx_weighted_avg('pct_povty') or 0, 1), 'nyc': round(nyc_weighted_avg('pct_povty') or 0, 1), 'unit': '%'},
            {'label': 'No Vehicle HH', 'ibx': round(ibx_weighted_avg('pct_noveh', 'hh_total') or 0, 1), 'nyc': round(nyc_weighted_avg('pct_noveh', 'hh_total') or 0, 1), 'unit': '%'},
            {'label': 'Transit Commute', 'ibx': round(calc_transit_pct(ibx_tracts), 1), 'nyc': round(calc_transit_pct(all_tracts), 1), 'unit': '%'},
        ]
    }

    # Add timestamp
    from datetime import datetime
    analysis['generated'] = datetime.now().isoformat()

    # Write output
    output_path = os.path.join(data_dir, 'demographic_analysis.json')
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"\nGenerated: {output_path}")
    print(f"Overview: {analysis['overview']}")

if __name__ == '__main__':
    main()
