from fasthtml.common import *
from app import app
from config import *
from components import Sidebar, draft_results_table, player_info_table, team_analysis_page, auction_analysis_page, draft_results_content, player_info_content, trade_recommendations_page, create_trade_card, league_info_page
from models import get_sorted_teams_and_players, prepare_data, load_default_data, calculate_outliers, recommend_trades
from utils import get_starter_quality_threshold, scrollable_table_style
from plotting import plot_regression_and_outliers
import pandas as pd

# Define sidebar_items at the module level
sidebar_items = ('League Info', 'Draft Results', 'Player Info', 'Team Analysis', 'Auction Analysis', 'Trade Recommendations')

@app.get('/')
def home():
	# auction_input, player_info_input = load_default_data()
	
	# process_draft_results(auction_input)
	# process_player_info(player_info_input)
	# print(sorted_teams_and_players)
	return Div(
		Div(
			Sidebar(sidebar_items, hx_get='/menucontent', hx_target='#current-menu-content'),
			cls='col-auto px-0'
		),
		Main(
			Div(
				league_info_page(),
				# Div(
				# 	H1("Click a sidebar menu item"),
				# 	P("Each item has its own content."),
				# 	id="current-menu-content"
				# ),
				cls='col-12'
			),
			cls='row flex-grow-1',
			style="margin-left:20px; margin-right:20px"
		),
		cls='container-fluid d-flex flex-nowrap px-0',
		style="max-width: 100vw; margin: 0;"
	)

@app.get('/menucontent')
def menucontent(menu: str):
	if menu == 'League Info':
		return league_info_page()
	elif menu == 'Draft Results':
		return draft_results_content()
	elif menu == 'Player Info':
		return player_info_content()
	elif menu == 'Team Analysis':
		return team_analysis_page()
	elif menu == 'Auction Analysis':
		return auction_analysis_page()
	elif menu == 'Trade Recommendations':
		return trade_recommendations_page()
	else:
		return "Invalid menu item"

@app.post('/process_draft_results')
def process_draft_results(auction_input: str):
	global PLAYERS, sorted_teams_and_players
	if auction_input:
		for line in auction_input.splitlines():
			if line.strip():
				name, price, fantasy_team = map(str.strip, line.split(","))
				if name in PLAYERS:
					PLAYERS[name].update({"price": float(price), "fantasy_team": fantasy_team})
				else:
					PLAYERS[name] = {"price": float(price), "fantasy_team": fantasy_team}
	sorted_teams_and_players.clear()
	update_sorted_teams_and_players(get_sorted_teams_and_players(PLAYERS))
	
	return draft_results_table()

@app.post('/process_player_info')
def process_player_info(player_info_input: str):
	global PLAYERS, sorted_teams_and_players
	if player_info_input:
		for line in player_info_input.splitlines():
			if line.strip():
				name, football_team, position, projected_fpts = map(str.strip, line.split(","))
				if name in PLAYERS:
					PLAYERS[name].update({"football_team": football_team, "position": position, "projected_fpts": float(projected_fpts)})
				else:
					PLAYERS[name] = {"football_team": football_team, "position": position, "projected_fpts": float(projected_fpts)}
	
	sorted_teams_and_players.clear()
	update_sorted_teams_and_players(get_sorted_teams_and_players(PLAYERS))
	# print(sorted_teams_and_players,"\n"*10)
	return player_info_table()


def get_team_points(team, printing=False):
	positions = sorted_teams_and_players[team]
	starters = {}
	bench1 = {}
	bench2 = {}
	bench3 = {}
	for pos in POSITIONS:
		player_list = positions[pos]
		num_starters = NUM_STARTERS[pos]
		starters[pos] = sum(x[1] for x in player_list[:num_starters])
		bench1[pos] = sum([x[1] for x in player_list[num_starters:num_starters+1]] + [0])
		bench2[pos] = sum([x[1] for x in player_list[num_starters+1:num_starters+2]] + [0])
		bench3[pos] = sum([x[1] for x in player_list[num_starters+2:num_starters+3]] + [0])
	return starters, bench1, bench2, bench3



@app.get('/update_team_analysis')
def update_team_analysis(view: str = "Separate", sort_position: str = "TOTAL", sort_type: str = "Starters"):
	if view == 'Separate':
		return separate_view(sort_position, sort_type)
	elif view == 'Combined':
		return combined_view(sort_position, sort_type)
	else:  # Position view
		return position_view(sort_position, sort_type)

def separate_view(sort_position, sort_type):
	content = []
	teams_data = []

	for team in sorted_teams_and_players:
		starters, bench1, bench2, bench3 = get_team_points(team)
		total_starters = sum(starters.values())
		total_bench1 = sum(bench1.values())
		total_bench2 = sum(bench2.values())
		total_bench3 = sum(bench3.values())
		
		teams_data.append((team, starters, bench1, bench2, bench3, total_starters, total_bench1, total_bench2, total_bench3))

	# Sort teams based on the selected criteria
	sort_index = ['Starters', 'Bench 1', 'Bench 2', 'Bench 3'].index(sort_type)
	if sort_position == 'TOTAL':
		teams_data.sort(key=lambda x: x[5 + sort_index], reverse=True)
	else:
		teams_data.sort(key=lambda x: x[1 + sort_index][sort_position], reverse=True)

	for team_data in teams_data:
		team, starters, bench1, bench2, bench3, total_starters, total_bench1, total_bench2, total_bench3 = team_data
		
		content.append(Div(
			H3(f"Team: {team}"),
			Table(
				Thead(
					Tr(
						Th("Position"),
						Th("Starters"),
						Th("Bench 1"),
						Th("Bench 2"),
						Th("Bench 3"),
					)
				),
				Tbody(
					*[
						Tr(
							Td(pos),
							*[Td(f"{data[pos]:.2f}", 
								 title=get_player_tooltip(team, pos, idx))
							  for idx, data in enumerate([starters, bench1, bench2, bench3])]
						) for pos in POSITIONS
					],
					Tr(
						Td("Total"),
						Td(f"{total_starters:.2f}"),
						Td(f"{total_bench1:.2f}"),
						Td(f"{total_bench2:.2f}"),
						Td(f"{total_bench3:.2f}")
					)
				),
				cls="table table-striped"
			),
			cls="mb-4"
		))
	
	return Div(*content)

def combined_view(sort_position, sort_type):
	teams = list(sorted_teams_and_players.keys())

	# Sort teams based on the selected position and type
	sort_index = ['Starters', 'Bench 1', 'Bench 2', 'Bench 3'].index(sort_type)
	if sort_position == 'TOTAL':
		teams.sort(key=lambda team: sum(get_team_points(team)[sort_index].values()), reverse=True)
	else:
		teams.sort(key=lambda team: get_team_points(team)[sort_index][sort_position], reverse=True)

	return Table(
		Thead(
			Tr(
				Th("Team"),
				*[Th(pos) for pos in POSITIONS],
				Th("Total")
			)
		),
		Tbody(
			*[
				Tr(
					Td(team),
					*[Td(f"{get_team_points(team)[sort_index][pos]:.2f}", 
						 title=get_player_tooltip(team, pos, sort_index))
					  for pos in POSITIONS],
					Td(f"{sum(get_team_points(team)[sort_index].values()):.2f}")
				) for team in teams
			]
		),
		cls="table table-striped"
	)

def position_view(sort_position, sort_type):
	teams = list(sorted_teams_and_players.keys())
	type_options = ['Starters', 'Bench 1', 'Bench 2', 'Bench 3', 'Total']

	# Sort teams based on the selected position and type
	sort_index = ['Starters', 'Bench 1', 'Bench 2', 'Bench 3'].index(sort_type)
	if sort_position == 'TOTAL':
		teams.sort(key=lambda team: sum(get_team_points(team)[sort_index].values()), reverse=True)
	else:
		teams.sort(key=lambda team: get_team_points(team)[sort_index][sort_position], reverse=True)

	return Table(
		Thead(
			Tr(
				Th("Team"),
				*[Th(type_opt) for type_opt in type_options]
			)
		),
		Tbody(
			*[
				Tr(
					Td(team),
					*[Td(get_cell_value(team, sort_position, idx), 
						 title=get_player_tooltip(team, sort_position, idx))
					  for idx, _ in enumerate(type_options[:-1])],
					Td(get_total_value(team, sort_position))
				) for team in teams
			]
		),
		cls="table table-striped"
	)

def get_cell_value(team, position, index):
	if position == 'TOTAL':
		return f"{sum(get_team_points(team)[index].values()):.2f}"
	else:
		return f"{get_team_points(team)[index][position]:.2f}"

def get_total_value(team, position):
	if position == 'TOTAL':
		return f"{sum(sum(type_data.values()) for type_data in get_team_points(team)):.2f}"
	else:
		return f"{sum(type_data[position] for type_data in get_team_points(team)):.2f}"

def get_player_tooltip(team, position, bench_index):
	if position == 'TOTAL':
		return "Total across all positions"
	players_lst = sorted_teams_and_players[team][position]
	num_starters = NUM_STARTERS[position]
	start = 0 if bench_index == 0 else num_starters + (bench_index - 1)
	end = start + 1 if bench_index > 0 else num_starters
	
	tooltip_players = players_lst[start:end]
	
	tooltip_content = "\n".join([
		f"{player}: {PLAYERS[player]['football_team']}, {PLAYERS[player]['projected_fpts']:.2f} pts"
		for player, data in tooltip_players
	])
	
	return tooltip_content if tooltip_content else "No player data"


@app.get('/update_plot')
def update_plot(
	fit_type: str = "polynomial",
	color_by: str = "team",
	player_filter: str = "all",
	swap_axes: str = "false",
	points_type: str = "absolute",
	combine_graphs: str = "false"
):
	global PLAYERS, sorted_teams_and_players
	
	df = prepare_data(PLAYERS, sorted_teams_and_players, points_type)
	
	plot_fig = plot_regression_and_outliers(
		df,
		fit_type=fit_type,
		swap_axes=(swap_axes == "true"),
		color_by=color_by,
		player_filter=player_filter,
		points_type=points_type,
		combine_graphs=(combine_graphs == "true")
	)
	
	return plot_fig

@app.get('/update_outliers')
def update_outliers(
	fit_type: str = "polynomial",
	color_by: str = "team",
	player_filter: str = "all",
	swap_axes: str = "false",
	points_type: str = "absolute",
	combine_graphs: str = "false",
	include_positive: Optional[str] = None,
	include_negative: Optional[str] = None,
	include_QB: Optional[str] = None,
	include_RB: Optional[str] = None,
	include_WR: Optional[str] = None,
	include_TE: Optional[str] = None,
	include_FLEX: Optional[str] = None,
	num_rows: int = 10
):
	global PLAYERS, sorted_teams_and_players
		
	df = prepare_data(PLAYERS, sorted_teams_and_players, points_type)
	
	# Apply the same filters as in plot_regression_and_outliers
	if player_filter == 'starters':
		df = df[df['Starter'] == 'Starter']
	elif player_filter == 'starter_quality':
		for pos in POSITIONS:
			threshold = get_starter_quality_threshold(df, pos)
			df = df[(df['Position'] != pos) | (df['Projected_Points'] >= threshold)]
	
	# Calculate outliers
	outliers = calculate_outliers(df, fit_type)
	
	# Filter outliers based on user selection
	mask = pd.Series(True, index=outliers.index)
	if include_positive is None:
		mask &= outliers['Price_Difference'] <= 0
	if include_negative is None:
		mask &= outliers['Price_Difference'] >= 0
	
	positions_to_include = [pos for pos, include in 
							zip(POSITIONS, 
								[include_QB, include_RB, include_WR, include_TE, include_FLEX]) 
							if include is not None]
	mask &= outliers['Position'].isin(positions_to_include)
	
	outliers = outliers[mask]
	
	# Sort outliers
	outliers = outliers.reindex(outliers['Price_Difference'].abs().sort_values(ascending=False).index)
	
	# Select top num_rows
	outliers = outliers.head(num_rows)
	
	# Create a table for outliers
	outliers_table = Table(
		Thead(
			Tr(
				*(Th(col) for col in ['Name', 'Team', 'Position', f"Projected {'Relative '*(points_type!='absolute')}FPTS", 'Price', 'Predicted Price', 'Price Difference'])
			)
		),
		Tbody(
			*(Tr(
				Td(row['Name']),
				Td(row['Team']),
				Td(row['Position']),
				Td(f"{row['Projected_Points']:.2f}"),
				Td(f"${row['Price']:.2f}"),
				Td(f"${row['Predicted_Price']:.2f}"),
				Td(f"${row['Price_Difference']:.2f}"),
			) for _, row in outliers.iterrows())
		),
		cls="table table-striped table-hover"
	)
	
	return Div(
		P(f"Showing {len(outliers)} players sorted by absolute Price Difference."),
		outliers_table
	)


@app.get('/update_recommendations')
def update_recommendations(
	include_player: str = "",
	include_team_1: str = "",
	include_team_2: str = "",
	num_display: int = 10,
	num_players: int = 1
):
	included_teams = [team for team in [include_team_1, include_team_2] if team]
	recommendations = recommend_trades(
		sorted_teams_and_players,
		PLAYERS, 
		included_player=include_player if include_player else None, 
		included_teams=included_teams if included_teams else None, 
		num_recommendations=num_display,
		num_players=num_players
	)
	return Div(*[create_trade_card(rec, i) for i, rec in enumerate(recommendations)])

@app.get('/update_league_info')
def update_league_info(
	QB_count: int = 0, RB_count: int = 0, WR_count: int = 0, TE_count: int = 0, FLEX_count: int = 0,
	flex_QB: Optional[str] = None, flex_RB: Optional[str] = None, 
	flex_WR: Optional[str] = None, flex_TE: Optional[str] = None
):
	new_positions = []
	new_num_starters = {}
	new_flex_positions = []

	for pos in ['QB', 'RB', 'WR', 'TE', 'FLEX']:
		count = locals()[f"{pos}_count"]
		if count > 0:
			new_positions.append(pos)
			new_num_starters[pos] = count

	# print(f"{locals()=}")
	for pos in ['QB', 'RB', 'WR', 'TE']:
		if locals()[f"flex_{pos}"] is not None:
			new_flex_positions.append(pos)
	# print(f"{new_flex_positions}")
	# print(new_positions, new_num_starters, new_flex_positions)
	if "FLEX" in new_positions:
		if not new_flex_positions: new_flex_positions = ["RB", "WR"]
	update_league_settings(new_positions, new_num_starters, new_flex_positions)
	update_sorted_teams_and_players(get_sorted_teams_and_players(PLAYERS))
	return ""  # Return an empty string to avoid updating the page content

@app.post('/load_example_auction')
def load_example_auction():    
	auction_input, player_info_input = load_default_data()
	update_league_settings(['QB', 'RB', 'WR', 'TE'], {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1}, [])

	process_draft_results(auction_input)
	process_player_info(player_info_input)
	return league_info_page()
