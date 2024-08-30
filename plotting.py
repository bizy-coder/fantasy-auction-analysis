import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
from uuid import uuid4
from plotly.utils import PlotlyJSONEncoder
import json
from utils import get_starter_quality_threshold
from fasthtml.common import *

# Global variables
from config import POSITIONS, NUM_STARTERS, FLEX_POSITIONS


def to_json(fig):
    return json.dumps(fig, cls=PlotlyJSONEncoder)

def plotly2fasthtml(chart):
    chart_id = f'uniq-{uuid4()}'
    chart_json = to_json(chart)
    return Div(Script(f"""
        var plotly_data = {chart_json};
        Plotly.newPlot('{chart_id}', plotly_data.data, plotly_data.layout);
    """), id=chart_id)

def plot_regression_and_outliers(df, fit_type='polynomial', swap_axes=False, color_by='team', player_filter='all', points_type='absolute', combine_graphs=False):
    if combine_graphs:
        fig = go.Figure()
    else:
        fig = make_subplots(rows=2, cols=2, subplot_titles=POSITIONS)

    # Create color scales
    if color_by == 'team':
        color_scale = px.colors.qualitative.Plotly
        color_map = {team: color_scale[i % len(color_scale)] for i, team in enumerate(df['Team'].unique())}
    else:  # color_by == 'position'
        color_map = {pos: px.colors.qualitative.Plotly[i] for i, pos in enumerate(POSITIONS)}

    # For combined graphs, calculate the fit line for all data at once
    if combine_graphs:
        all_x = []
        all_y = []

    for i, pos in enumerate(POSITIONS, 1):
        pos_data = df[df['Position'] == pos]

        # Filter data based on player_filter
        if player_filter == 'starters':
            pos_data = pos_data[pos_data['Starter'] == 'Starter']
        elif player_filter == 'starter_quality':
            threshold = get_starter_quality_threshold(df, pos)
            pos_data = pos_data[pos_data['Projected_Points'] >= threshold]

        # Swap X and Y based on the swap_axes flag
        if swap_axes:
            x = pos_data['Projected_Points']
            y = pos_data['Price']
            x_label = 'Projected Points'
            y_label = 'Price'
        else:
            x = pos_data['Price']
            y = pos_data['Projected_Points']
            x_label = 'Price'
            y_label = 'Projected Points'

        if combine_graphs:
            all_x.extend(x)
            all_y.extend(y)

        # Plot scatter plot of data points
        row = (i - 1) // 2 + 1
        col = (i - 1) % 2 + 1

        if color_by == 'team':
            for team in pos_data['Team'].unique():
                team_data = pos_data[pos_data['Team'] == team]
                for category in ['Starter', 'Bench']:
                    category_data = team_data[team_data['Starter'] == category]
                    if not category_data.empty:
                        scatter = create_scatter(category_data, x_label, y_label, swap_axes, color_map[team], 
                                                 f"{team} ({category})", category == 'Starter', 
                                                 combine_graphs, team, i == 1 and category == 'Starter')
                        add_trace(fig, scatter, combine_graphs, row, col)
        else:  # color_by == 'position'
            for category in ['Starter', 'Bench']:
                category_data = pos_data[pos_data['Starter'] == category]
                if not category_data.empty:
                    scatter = create_scatter(category_data, x_label, y_label, swap_axes, color_map[pos], 
                                             f"{pos} ({category})", category == 'Starter', 
                                             combine_graphs, pos, True)
                    add_trace(fig, scatter, combine_graphs, row, col)

        if not combine_graphs:
            # Generate the fit line across the full range for individual graphs
            x_fit = np.linspace(x.min(), x.max(), 100)
            line = calculate_fit_line(x, y, x_fit, fit_type)

            # Plot the constrained fit line for individual graphs
            fit_line = go.Scatter(
                x=x_fit,
                y=line,
                mode='lines',
                name=f'Fit ({fit_type})',
                legendgroup='fit',
                showlegend=(i == 1),
                line=dict(color='black'),
                hoverinfo='text',
                hovertext=[f"{x_label}: {x:.2f}<br>{y_label}: {y:.2f}" for x, y in zip(x_fit, line)]
            )
            fig.add_trace(fit_line, row=row, col=col)

            fig.update_xaxes(title_text=x_label, row=row, col=col)
            fig.update_yaxes(title_text=y_label, row=row, col=col)

    if combine_graphs:
        # Calculate and plot a single fit line for combined graphs
        x_fit = np.linspace(min(all_x), max(all_x), 100)
        line = calculate_fit_line(all_x, all_y, x_fit, fit_type)

        fit_line = go.Scatter(
            x=x_fit,
            y=line,
            mode='lines',
            name=f'Fit ({fit_type})',
            line=dict(color='black'),
            hoverinfo='text',
            hovertext=[f"{x_label}: {x:.2f}<br>{y_label}: {y:.2f}" for x, y in zip(x_fit, line)]
        )
        fig.add_trace(fit_line)

    filter_text = "Starters Only" if player_filter == 'starters' else "Starter Quality" if player_filter == 'starter_quality' else "All Players"
    points_text = "Absolute Points" if points_type == 'absolute' else "Points Relative to Worst Starter" if points_type == 'relative_worst_starter' else "Points Relative to Theoretical Worst Starter"
    
    layout_update = dict(
        height=800 if not combine_graphs else 600, 
        width=1000, 
        title_text=f"Price vs {points_text} by {'Team' if color_by == 'team' else 'Position'} ({filter_text})",
        legend_title_text='Team' if color_by == 'team' else 'Position'
    )
    
    if combine_graphs:
        layout_update.update(
            xaxis_title=x_label,
            yaxis_title=y_label
        )
    
    fig.update_layout(**layout_update)
    
    return plotly2fasthtml(fig)

def create_scatter(data, x_label, y_label, swap_axes, color, name, is_starter, combine_graphs, group, show_legend):
    return go.Scatter(
        x=data['Projected_Points'] if swap_axes else data['Price'],
        y=data['Price'] if swap_axes else data['Projected_Points'],
        mode='markers',
        name=name,
        legendgroup=group,
        showlegend=show_legend,
        text=[f"Name: {name}<br>Team: {team}<br>{x_label}: {x_val:.2f}<br>{y_label}: {y_val:.2f}<br>Status: {status}" 
              for name, team, x_val, y_val, status in zip(
                  data['Name'], 
                  data['Team'], 
                  data['Projected_Points'] if swap_axes else data['Price'],
                  data['Price'] if swap_axes else data['Projected_Points'],
                  data['Starter'])],
        hoverinfo='text',
        marker=dict(
            color=color,
            size=8,
            symbol='circle' if is_starter else 'circle-open',
            line=dict(width=1, color='DarkSlateGrey')
        )
    )

def add_trace(fig, scatter, combine_graphs, row, col):
    if combine_graphs:
        fig.add_trace(scatter)
    else:
        fig.add_trace(scatter, row=row, col=col)

# Helper function to calculate fit line
def calculate_fit_line(x, y, x_fit, fit_type):
    if fit_type == 'linear':
        coefs = np.polyfit(x, y, 1)
        line = np.polyval(coefs, x_fit)
    elif fit_type == 'polynomial':
        coefs = np.polyfit(x, y, 2)
        line = np.polyval(coefs, x_fit)
    elif fit_type == 'logarithmic':
        log_x = np.log(x)
        coefs = np.polyfit(log_x, y, 1)
        line = np.polyval(coefs, np.log(x_fit))
    elif fit_type == 'exponential':
        log_y = np.log(y)
        coefs = np.polyfit(x, log_y, 1)
        line = np.exp(np.polyval(coefs, x_fit))
    else:
        raise ValueError("Invalid fit_type. Choose from 'linear', 'polynomial', 'logarithmic', or 'exponential'.")
    
    # Constrain the line to the data range
    line = np.clip(line, a_min=0, a_max=None)  # Ensure no value below 0
    line = np.clip(line, a_min=min(y), a_max=None)  # Ensure no value below the minimum represented value
    
    return line