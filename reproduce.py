#!/usr/bin/env python3
"""Reconstruct the five-scheduler comparison in Lu and Butler, Table 2.

SPDX-License-Identifier: MIT
Inputs are the published, rounded values, not simulated or measured anew.
Run: python3 reproduce.py [--output result.svg]
"""
import argparse
from pathlib import Path
from statistics import mean
from fractions import Fraction

# Scheduler, mean energy SD (static, adaptive) in J, mean efficiency
# (static, adaptive) in percent. Table 2, doi:10.1016/j.adhoc.2026.104346.
RESULTS = [
    ("Average",       5163.0, 1658.6, 57.8, 57.0),
    ("Baseline",      4285.1, 1586.7, 50.0, 50.3),
    ("Lyapunov",      2316.4, 1243.5, 59.4, 58.2),
    ("Prediction",    4285.1, 1594.5, 50.0, 49.7),
    ("Power control", 5046.8, 1434.8, 47.4, 47.3),
]


def worked_transfer(limit):
    """One illustrative allocation, given K. This does not choose or learn K."""
    demand, efficiency = Fraction(8), Fraction(4, 5)
    reserve = Fraction(2)
    balances = [Fraction(8), Fraction(6)]   # A is considered before B in this example.
    delivered, active = Fraction(0), 0
    for i, stored in enumerate(balances):
        if active == limit or delivered == demand:
            break
        debit = min(max(Fraction(0), stored - reserve), (demand - delivered)/efficiency)
        if debit:
            active += 1
            balances[i] -= debit
            delivered += debit * efficiency
    return active, delivered, demand - delivered


def comparison():
    _, fixed, adaptive, eff_fixed, eff_adaptive = zip(*RESULTS)
    return mean(fixed), mean(adaptive), mean(eff_fixed), mean(eff_adaptive)


def chart():
    """Draw the two measured quantities on separate, zero-based axes."""
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="920" height="440" viewBox="0 0 920 440" role="img" aria-labelledby="title detail">',
           '<title id="title">Dynamic-K: nominal simulation results</title>',
           '<desc id="detail">Five schedulers. Energy dispersion is lower under adaptive concurrency for all five. Mean transfer efficiency stays within 1.2 percentage points of the single-donor case in every row.</desc>',
           '<rect width="920" height="440" rx="18" fill="#fcfaf2"/>',
           '<g font-family="Arial,Helvetica,sans-serif" fill="#183f44">']
    def label(x, y, value, size, bold=False, color="#183f44"):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}">{value}</text>')
    def marker(x, y, adaptive):
        if adaptive:
            svg.append(f'<circle cx="{x:.2f}" cy="{y}" r="5.5" fill="#007b6b"/>')
        else:
            svg.append(f'<rect x="{x-5:.2f}" y="{y-5}" width="10" height="10" rx="1" fill="#a55717"/>')
    label(29, 40, 'Does adaptive donor concurrency improve energy balance?', 26, True)
    marker(35, 70, False); label(48, 76, 'Static K = 1', 17)
    marker(177, 70, True); label(190, 76, 'Dynamic-K', 17)
    label(29, 119, 'Scheduler', 18, True)
    label(176, 119, 'Energy dispersion (J)', 18, True)
    label(576, 119, 'Transfer efficiency (%)', 18, True)
    panels = [(180, 325, 6000, (0, 2000, 4000, 6000)), (578, 278, 60, (0, 20, 40, 60))]
    for left, width, limit, ticks in panels:
        for tick in ticks:
            x = left + tick * width / limit
            svg.append(f'<path d="M{x:.2f} 137V337" stroke="#dae3d7"/>')
            svg.append(f'<text x="{x:.2f}" y="363" text-anchor="middle" font-size="14">{tick:,}</text>')
    for index, (name, fixed, adaptive, eff0, eff1) in enumerate(RESULTS):
        y = 153 + index * 43
        label(29, y+6, name, 16)
        for (left, width, limit, _), (a, b) in zip(panels, ((fixed, adaptive), (eff0, eff1))):
            x0, x1 = left + a*width/limit, left + b*width/limit
            svg.append(f'<line x1="{x0:.2f}" x2="{x1:.2f}" y1="{y-4}" y2="{y+4}" stroke="#62797b" stroke-width="2"/>')
            marker(x0, y-4, False); marker(x1, y+4, True)
    sd0, sd1, ef0, ef1 = comparison()
    label(29, 397, f'Five-scheduler means: {sd0:,.1f} to {sd1:,.1f} J; efficiency {ef0:.1f}% to {ef1:.1f}%.', 17, True)
    label(29, 422, '25-node simulation · Table 2 · Lu and Butler, Ad Hoc Networks (2026)', 14)
    return '\n'.join(svg + ['</g></svg>', ''])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output', type=Path, default=Path('result.svg'))
    destination = parser.parse_args().output
    fixed, adaptive, eff0, eff1 = comparison()
    print('Illustrative single transfer (8 J requested):')
    for limit in (1, 2):
        n, received, unmet = worked_transfer(limit)
        print(f'  K={limit}: {n} active donor(s), {float(received):.1f} J received, {float(unmet):.1f} J unmet')
    print('Published five-scheduler comparison:')
    print(f'Mean energy dispersion: {fixed:,.1f} -> {adaptive:,.1f} J')
    print(f'Reduction in mean dispersion: {100*(1-adaptive/fixed):.1f}%')
    print(f'Mean transfer efficiency: {eff0:.1f}% -> {eff1:.1f}% ({eff1-eff0:+.1f} percentage points)')
    destination.write_text(chart(), encoding='utf-8')
    print(f'Figure: {destination}')


if __name__ == '__main__':
    main()
