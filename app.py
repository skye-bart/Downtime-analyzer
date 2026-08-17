from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os
import uuid

app = Flask(__name__)
app.secret_key = 'downtime-analyzer-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

UPLOAD_FOLDER = 'uploads'
CHART_FOLDER = 'static/charts'
ALLOWED_EXTENSIONS = {'csv'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHART_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_and_chart(csv_path, session_id):
    df = pd.read_csv(csv_path)

    # Validate required columns
    required = {'date', 'shift', 'area', 'equipment_tag', 'reason', 'duration_minutes'}
    missing = required - set(df.columns)
    if missing:
        return None, f"Missing columns: {', '.join(missing)}"

    # Clean data
    df['duration_minutes'] = pd.to_numeric(df['duration_minutes'], errors='coerce')
    df = df.dropna(subset=['duration_minutes'])
    df['duration_minutes'] = df['duration_minutes'].astype(int)

    if len(df) == 0:
        return None, "No valid data found in CSV."

    # Calculate metrics
    total_downtime = int(df['duration_minutes'].sum())
    total_events = len(df)
    avg_duration = round(df['duration_minutes'].mean(), 1)

    # Reason summary (Pareto)
    reason_summary = df.groupby('reason')['duration_minutes'].sum().sort_values(ascending=False).reset_index()
    reason_summary.columns = ['reason', 'total_minutes']
    reason_summary['cumulative_pct'] = reason_summary['total_minutes'].cumsum() / reason_summary['total_minutes'].sum() * 100

    # Shift summary
    shift_order = ['Day', 'Afternoon', 'Night']
    shift_summary = df.groupby('shift')['duration_minutes'].sum()
    shift_summary = shift_summary.reindex([s for s in shift_order if s in shift_summary.index])

    # Area summary
    area_summary = df.groupby('area')['duration_minutes'].sum().sort_values(ascending=True)

    # Equipment summary
    equip_summary = df.groupby('equipment_tag')['duration_minutes'].sum().sort_values(ascending=False).head(10)

    # Top insights
    top_3_reasons = reason_summary.head(3)
    top_3_time = int(top_3_reasons['total_minutes'].sum())
    top_3_pct = round(top_3_time / total_downtime * 100, 1)
    worst_area = area_summary.idxmax() if len(area_summary) > 0 else "N/A"
    worst_area_time = int(area_summary.max()) if len(area_summary) > 0 else 0
    worst_equip = equip_summary.index[0] if len(equip_summary) > 0 else "N/A"
    worst_equip_time = int(equip_summary.iloc[0]) if len(equip_summary) > 0 else 0

    # Generate charts
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.suptitle('Equipment Downtime Analysis Dashboard', fontsize=16, fontweight='bold', y=0.98)

    # Chart 1: Pareto
    ax1 = axes[0, 0]
    bars = ax1.bar(range(len(reason_summary)), reason_summary['total_minutes'], color='#2563eb', alpha=0.8)
    ax1.set_xticks(range(len(reason_summary)))
    ax1.set_xticklabels(reason_summary['reason'], rotation=45, ha='right', fontsize=8)
    ax1.set_ylabel('Total Downtime (minutes)', color='#2563eb')
    ax1.tick_params(axis='y', labelcolor='#2563eb')
    ax1_twin = ax1.twinx()
    ax1_twin.plot(range(len(reason_summary)), reason_summary['cumulative_pct'], color='#dc2626', marker='o', linewidth=2, markersize=4)
    ax1_twin.axhline(y=80, color='#dc2626', linestyle='--', alpha=0.5)
    ax1_twin.set_ylabel('Cumulative %', color='#dc2626')
    ax1_twin.tick_params(axis='y', labelcolor='#dc2626')
    ax1_twin.set_ylim(0, 105)
    ax1.set_title('Pareto Analysis: Downtime by Reason', fontweight='bold', pad=10)
    ax1.grid(axis='y', alpha=0.3)

    # Chart 2: By Shift
    ax2 = axes[0, 1]
    colors_shift = ['#16a34a', '#ca8a04', '#1e293b']
    bars2 = ax2.bar(shift_summary.index, shift_summary.values, color=colors_shift[:len(shift_summary)], alpha=0.85, edgecolor='white', linewidth=1.5)
    ax2.set_ylabel('Total Downtime (minutes)')
    ax2.set_title('Downtime by Shift', fontweight='bold', pad=10)
    ax2.grid(axis='y', alpha=0.3)
    for bar in bars2:
        height = bar.get_height()
        ax2.annotate(f'{int(height)} min', xy=(bar.get_x() + bar.get_width()/2, height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Chart 3: By Area
    ax3 = axes[1, 0]
    colors_area = plt.cm.RdYlBu_r(np.linspace(0.2, 0.8, len(area_summary)))
    bars3 = ax3.barh(area_summary.index, area_summary.values, color=colors_area, alpha=0.85, edgecolor='white', linewidth=1.5)
    ax3.set_xlabel('Total Downtime (minutes)')
    ax3.set_title('Downtime by Area/Zone', fontweight='bold', pad=10)
    ax3.grid(axis='x', alpha=0.3)
    for bar in bars3:
        width = bar.get_width()
        ax3.annotate(f'{int(width)}', xy=(width, bar.get_y() + bar.get_height()/2), xytext=(5, 0), textcoords="offset points", ha='left', va='center', fontsize=9, fontweight='bold')

    # Chart 4: Top Equipment
    ax4 = axes[1, 1]
    bars4 = ax4.bar(range(len(equip_summary)), equip_summary.values, color='#7c3aed', alpha=0.85, edgecolor='white', linewidth=1.5)
    ax4.set_xticks(range(len(equip_summary)))
    ax4.set_xticklabels(equip_summary.index, rotation=45, ha='right', fontsize=8)
    ax4.set_ylabel('Total Downtime (minutes)')
    ax4.set_title('Top 10 Equipment by Downtime', fontweight='bold', pad=10)
    ax4.grid(axis='y', alpha=0.3)
    for bar in bars4:
        height = bar.get_height()
        ax4.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width()/2, height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    chart_filename = f'dashboard_{session_id}.png'
    chart_path = os.path.join(CHART_FOLDER, chart_filename)
    plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    results = {
        'total_downtime': total_downtime,
        'total_events': total_events,
        'avg_duration': avg_duration,
        'top_3_reasons': top_3_reasons.to_dict('records'),
        'top_3_time': top_3_time,
        'top_3_pct': top_3_pct,
        'shift_summary': shift_summary.to_dict(),
        'worst_area': worst_area,
        'worst_area_time': worst_area_time,
        'worst_equip': worst_equip,
        'worst_equip_time': worst_equip_time,
        'chart_filename': chart_filename,
        'date_range': f"{df['date'].min()} to {df['date'].max()}"
    }

    return results, None

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        session_id = str(uuid.uuid4())[:8]
        filename = f"{session_id}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        results, error = analyze_and_chart(filepath, session_id)

        if error:
            flash(error, 'error')
            os.remove(filepath)
            return redirect(url_for('index'))

        return render_template('dashboard.html', results=results)
    else:
        flash('Please upload a CSV file.', 'error')
        return redirect(url_for('index'))

@app.route('/sample')
def download_sample():
    return send_from_directory('.', 'sample_downtime.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)
