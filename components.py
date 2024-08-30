from fasthtml.common import *
from utils import scrollable_table_style

# Global variables
from config import POSITIONS, NUM_STARTERS, FLEX_POSITIONS, PLAYERS, sorted_teams_and_players 


def SidebarItem(text, hx_get, hx_target, **kwargs):
	return Div(
		I(cls=f'bi bi-{text.lower().replace(" ", "-")}'),
		Span(text),
		hx_get=hx_get, hx_target=hx_target,
		data_bs_parent='#sidebar', role='button',
		cls='list-group-item border-end-0 d-inline-block text-truncate',
		**kwargs
	)

def Sidebar(sidebar_items, hx_get, hx_target):
	return Div(
		Div(*(SidebarItem(o, f"{hx_get}?menu={o}", hx_target) for o in sidebar_items),
			id='sidebar-nav',
			cls='list-group border-0 rounded-0 text-sm-start min-vh-100'
		),
		id='sidebar',
		cls='collapse collapse-horizontal show border-end'
	)

def draft_results_table():
	return Div(
		Table(
			Thead(
				Tr(Th("Player Name"), Th("Price"), Th("Drafted Team"))
			),
			Tbody(
				*[Tr(Td(name), Td(f"${data['price']}"), Td(data['fantasy_team']))
				  for name, data in PLAYERS.items() if 'price' in data and 'fantasy_team' in data]
			),
			cls="table table-striped"
		),
		cls="table-scrollable"
	)

def draft_results_content():
	return Div(
		scrollable_table_style(),
		H1("Draft Results: Insert Auction Draft Results"),
		P("Input the auction draft results in the format: player_name, price, drafted_team."),
		Form(
			Textarea(
				placeholder="Example:\nPlayer1, 50, TeamA\nPlayer2, 45, TeamB",
				rows="10",
				name="auction_input",
				style="padding-right: 15px; margin-right: -15px; border: 1px solid #dee2e6;"  # Ensures enough space for the border
			),
			Button("Submit", type="submit"),
			hx_post="/process_draft_results",
			hx_target="#draft-results-table",
			hx_swap="innerHTML"
		),
		Div(draft_results_table(), id="draft-results-table"),
		id="current-menu-content"
	)

def player_info_table():
	return Div(
		Table(
			Thead(
				Tr(Th("Player Name"), Th("Football Team"), Th("Position"), Th("Projected FPts"))
			),
			Tbody(
				*[Tr(Td(name), Td(data['football_team']), Td(data['position']), Td(f"{data['projected_fpts']:.2f}"))
				  for name, data in PLAYERS.items() if 'football_team' in data and 'position' in data and 'projected_fpts' in data]
			),
			cls="table table-striped"
		),
		cls="table-scrollable"
	)

def player_info_content():
	return Div(
		scrollable_table_style(),
		H1("Player Info: Insert Player Details"),
		P("Input the player details in the format: player_name, football_team, position, projected_fpts."),
		Form(
			Textarea(
				placeholder="Example:\nPlayer1, TeamA, QB, 300\nPlayer2, TeamB, RB, 250",
				rows="10",
				name="player_info_input",
				style="padding-right: 15px; margin-right: -15px; border: 1px solid #dee2e6;"  # Ensures enough space for the border
			),
			Button("Submit", type="submit"),
			hx_post="/process_player_info",
			hx_target="#player-info-table",
			hx_swap="innerHTML"
		),
		Div(player_info_table(), id="player-info-table"),
		id="current-menu-content"
	)


def team_analysis_page():
	if not sorted_teams_and_players:
		return Div(
			H2("No team data available"),
			P("Please input draft results and player info first."),
			id="current-menu-content"
		)

	view_options = ['Separate', 'Combined', 'Position']
	position_options = ['TOTAL'] + POSITIONS
	type_options = ['Starters', 'Bench 1', 'Bench 2', 'Bench 3']

	def create_dropdown(name, options, default):
		return Select(
			*(Option(opt, value=opt, selected=(opt == default)) for opt in options),
			name=name,
			cls="form-select",
			hx_get="/update_team_analysis",
			hx_target="#team-analysis-content",
			hx_trigger="change",
			hx_include="[name='view'],[name='sort_position'],[name='sort_type']"
		)

	controls = Div(
		Div(
			Label("View:", fr="view-select"),
			create_dropdown("view", view_options, "Separate"),
			cls="col-md-3"
		),
		Div(
			Label("Position:", fr="sort-position-select"),
			create_dropdown("sort_position", position_options, "TOTAL"),
			cls="col-md-3"
		),
		Div(
			Label("Type:", fr="sort-type-select"),
			create_dropdown("sort_type", type_options, "Starters"),
			cls="col-md-3"
		),
		cls="row mb-3"
	)

	return Div(
		H2("Team Analysis"),
		controls,
		Div(id="team-analysis-content", hx_get="/update_team_analysis", hx_trigger="load", hx_include="[name='view'],[name='sort_position'],[name='sort_type']"),
		Script("""
			htmx.trigger('#team-analysis-content', 'load');
			document.body.addEventListener('htmx:afterSettle', function(evt) {
				tippy('[title]', {
					content: (reference) => reference.getAttribute('title'),
					allowHTML: true,
					delay: [0, 0],
					duration: [200, 100],
				});
			});
		"""),
		id="current-menu-content"
	)

def auction_analysis_page():
	fit_options = ['linear', 'polynomial', 'logarithmic', 'exponential']
	color_options = ['team', 'position']
	filter_options = ['all', 'starters', 'starter_quality']
	points_options = ['absolute', 'relative_worst_starter', 'relative_theoretical_worst_starter']

	# Define default values
	defaults = {
		'fit_type': 'linear',
		'color_by': 'position',
		'player_filter': 'starter_quality',
		'points_type': 'relative_theoretical_worst_starter',
		'swap_axes': 'true',
		'combine_graphs': 'true',
		'num_rows': '10',
		'include_positive': 'on',
		'include_negative': 'on',
	}
	
	# Add default values for all positions
	for pos in POSITIONS:
		defaults[f'include_{pos}'] = 'on'

	def create_dropdown(name, options, default):
		return Select(
			*(Option(opt, value=opt, selected=(opt == default)) for opt in options),
			name=name,
			cls="form-select",
			hx_get="/update_plot",
			hx_target="#plot-container",
			hx_trigger="change",
			hx_include="[name]",
			**{"hx-on::after-request": "updateOutliers()"}
		)

	def create_checkbox(name, label, checked):
		return Div(
			Input(type="checkbox", name=name, id=name, checked=checked,
				  hx_get="/update_outliers", hx_target="#outliers-container", hx_trigger="change", hx_include="[name]"),
			Label(label, fr=name),
			cls="form-check"
		)

	plot_controls = Div(
		Div(
			Label("Fit Type:", fr="fit-type-select"),
			create_dropdown("fit_type", fit_options, defaults['fit_type']),
			cls="col-md-2"
		),
		Div(
			Label("Color By:", fr="color-by-select"),
			create_dropdown("color_by", color_options, defaults['color_by']),
			cls="col-md-2"
		),
		Div(
			Label("Player Filter:", fr="player-filter-select"),
			create_dropdown("player_filter", filter_options, defaults['player_filter']),
			cls="col-md-2"
		),
		Div(
			Label("Points Type:", fr="points-type-select"),
			create_dropdown("points_type", points_options, defaults['points_type']),
			cls="col-md-2"
		),
		Div(
			Label("Swap Axes:", fr="swap-axes-select"),
			create_dropdown("swap_axes", ["false", "true"], defaults['swap_axes']),
			cls="col-md-2"
		),
		Div(
			Label("Combine Graphs:", fr="combine-graphs-select"),
			create_dropdown("combine_graphs", ["false", "true"], defaults['combine_graphs']),
			cls="col-md-2"
		),
		cls="row mb-3"
	)

	outlier_controls = Div(
		Div(
			create_checkbox("include_positive", "Include Overpriced", defaults['include_positive'] == 'on'),
			create_checkbox("include_negative", "Include Underpriced", defaults['include_negative'] == 'on'),
			cls="col-md-3"
		),
		Div(
			*(create_checkbox(f"include_{pos}", f"Include {pos}", defaults[f'include_{pos}'] == 'on')
			  for pos in POSITIONS),
			cls="col-md-3"
		),
		Div(
			Label("Number of Rows:", fr="num-rows-input"),
			Input(type="number", name="num_rows", value=defaults['num_rows'], min="1", max="100",
				  hx_get="/update_outliers", hx_target="#outliers-container", hx_trigger="change", hx_include="[name]"),
			cls="col-md-3"
		),
		cls="row mb-3"
	)

	# Convert defaults to a JSON string for hx-vals
	import json
	default_vals = json.dumps(defaults)

	return Div(
		H2("Auction Analysis"),
		plot_controls,
		Div(
			id="plot-container",
			hx_get="/update_plot",
			hx_trigger="load",
			hx_vals=default_vals
		),
		H3("Top Value Discrepancies"),
		outlier_controls,
		Div(
			id="outliers-container",
			hx_get="/update_outliers",
			hx_trigger="load",
			hx_vals=default_vals
		),
		Script("""
		function updateOutliers() {
			var plotParams = ['fit_type', 'color_by', 'player_filter', 'points_type', 'swap_axes', 'combine_graphs'];
			var outlierParams = ['include_positive', 'include_negative', 'num_rows'];
			var positionParams = """ + json.dumps([f'include_{pos}' for pos in POSITIONS]) + """;
			var allParams = plotParams.concat(outlierParams, positionParams);
			var queryString = allParams.map(param => {
				var el = document.getElementsByName(param)[0];
				if (el) {
					if (el.type === 'checkbox') {
						return el.checked ? param + '=on' : '';
					}
					return param + '=' + el.value;
				}
				return '';
			}).filter(Boolean).join('&');
			htmx.ajax('GET', '/update_outliers?' + queryString, '#outliers-container');
		}
		"""),
		id="current-menu-content"
	)


def create_player_card(player):
	return Div(
		scrollable_table_style(),
		Div(player[0], cls="player-name"),
		Div(f"Team: {PLAYERS[player[0]]['football_team'] if player[0] != 'waiver' else "WAIVER"}", cls="player-team"),
		Div(f"Proj: {player[1]:.2f}", cls="player-proj"),
		Div(f"Price: ${PLAYERS[player[0]]['price']:.2f}", cls="player-price")  if player[0] != 'waiver' else Div("Price: WAIVER", cls="player-price"),
		cls="player-card"
	)

def create_trade_card(rec, index):
	team1, team2, players1, players2, trade_result = rec
	
	trade_details = Div(
		scrollable_table_style(),

		Div(
			Div(f"{team1} gives:", cls="col-6 fw-bold"),
			Div(f"{team2} gives:", cls="col-6 fw-bold"),
			cls="row mb-2"
		),
		Div(
			Div(*(create_player_card(player) for player in players1), cls="col-6"),
			Div(*(create_player_card(player) for player in players2), cls="col-6"),
			cls="row"
		),
		cls="trade-details mb-3"
	)

	def create_changes_table(team1_data, team2_data):
		def create_team_column(team, data):
			rows = []
			for pos in POSITIONS:
				change = data['score_changes'].get(pos, {})
				if any(change.values()):
					rows.append(Tr(
						Td(pos, cls="fw-bold"),
						Td(f"{change.get('starter_change', 0):.2f}", cls="text-end"),
						Td(f"{change.get('bench1_change', 0):.2f}", cls="text-end"),
						Td(f"{change.get('bench2_change', 0):.2f}", cls="text-end"),
						Td(f"{change.get('bench3_change', 0):.2f}", cls="text-end"),
					))
			
			net_changes = {k: sum(change.get(k, 0) for change in data['score_changes'].values()) 
						   for k in ['starter_change', 'bench1_change', 'bench2_change', 'bench3_change']}
			rows.append(Tr(
				Td("Net", cls="fw-bold"),
				Td(f"{net_changes['starter_change']:.2f}", cls="text-end fw-bold"),
				Td(f"{net_changes['bench1_change']:.2f}", cls="text-end fw-bold"),
				Td(f"{net_changes['bench2_change']:.2f}", cls="text-end fw-bold"),
				Td(f"{net_changes['bench3_change']:.2f}", cls="text-end fw-bold"),
			))
			
			return Div(
				H6(team, cls="text-center mb-2"),
				Table(
					Thead(
						Tr(
							Th("Pos"),
							Th("Starter", cls="text-end"),
							Th("Bench1", cls="text-end"),
							Th("Bench2", cls="text-end"),
							Th("Bench3", cls="text-end"),
						)
					),
					Tbody(*rows),
					cls="table table-sm table-hover"
				),
				cls="col-md-6"
			)
		
		return Div(
			create_team_column(team1, team1_data),
			create_team_column(team2, team2_data),
			cls="row gx-4"
		)

	return Div(
		Div(
			Div(
				scrollable_table_style(),

				H5(f"Trade Recommendation {index + 1}", cls="card-title mb-3"),
				trade_details,
				create_changes_table(trade_result['team1'], trade_result['team2']),
				cls="card-body"
			),
			cls="card mb-4"
		)
	)

def trade_recommendations_page():
	if not sorted_teams_and_players:
		return Div(
			H2("No team data available"),
			P("Please input draft results and player info first."),
			id="current-menu-content"
		)

	all_players = [player for team in sorted_teams_and_players.values() for pos in team.values() for player in pos]
	all_players.sort(key=lambda x: x[0].split()[-1])  # Sort by last name

	all_teams = sorted(sorted_teams_and_players.keys())

	def create_filter_controls():
		return Div(
			Div(
				Label("Included Players:", fr="include-player"),
				Select(
					Option("None", value=""),
					*[Option(f"{player[0]} ({PLAYERS[player[0]]['football_team']})", value=player[0]) for player in all_players],
					name="include_player",
					id="include-player",
					cls="form-select",
					hx_get="/update_recommendations",
					hx_target="#recommendations-content",
					hx_trigger="change",
					hx_include="[name='include_player'],[name='include_team_1'],[name='include_team_2'],[name='num_display'],[name='num_players']",
					hx_indicator="#loading-indicator"
				),
				cls="col-md-2"
			),
			Div(
				Label("Included Teams:", fr="include-team-1"),
				Select(
					Option("None", value=""),
					*[Option(team, value=team) for team in all_teams],
					name="include_team_1",
					id="include-team-1",
					cls="form-select",
					hx_get="/update_recommendations",
					hx_target="#recommendations-content",
					hx_trigger="change",
					hx_include="[name='include_player'],[name='include_team_1'],[name='include_team_2'],[name='num_display'],[name='num_players']",
					hx_indicator="#loading-indicator"
				),
				Select(
					Option("None", value=""),
					*[Option(team, value=team) for team in all_teams],
					name="include_team_2",
					id="include-team-2",
					cls="form-select",
					hx_get="/update_recommendations",
					hx_target="#recommendations-content",
					hx_trigger="change",
					hx_include="[name='include_player'],[name='include_team_1'],[name='include_team_2'],[name='num_display'],[name='num_players']",
					hx_indicator="#loading-indicator"
				),
				cls="col-md-2"
			),
			Div(
				Label("Number to Display:", fr="num-display"),
				Input(
					type="number",
					name="num_display",
					id="num-display",
					value="10",
					min="1",
					max="50",
					cls="form-control",
					hx_get="/update_recommendations",
					hx_target="#recommendations-content",
					hx_trigger="change",
					hx_include="[name='include_player'],[name='include_team_1'],[name='include_team_2'],[name='num_display'],[name='num_players']",
					hx_indicator="#loading-indicator"
				),
				cls="col-md-2"
			),
			Div(
				Label("Number of Players:", fr="num-players"),
				Select(
					Option("1", value="1"),
					Option("2", value="2"),
					name="num_players",
					id="num-players",
					cls="form-select",
					hx_get="/update_recommendations",
					hx_target="#recommendations-content",
					hx_trigger="change",
					hx_include="[name='include_player'],[name='include_team_1'],[name='include_team_2'],[name='num_display'],[name='num_players']",
					hx_indicator="#loading-indicator"
				),
				cls="col-md-2"
			),
			cls="row mb-4"
		)


	loading_indicator = Div(
		Div(cls="spinner-border", role="status"),
		Span("Loading...", cls="sr-only"),
		id="loading-indicator",
		cls="text-center",
		style="display: none;"
	)

	recommendations_content = Div(
		id="recommendations-content",
		hx_get="/update_recommendations",
		hx_trigger="load",
		hx_include="[name='include_player'],[name='include_team_1'],[name='include_team_2'],[name='num_display'],[name='num_players']",
		hx_indicator="#loading-indicator"
	)

	return Div(
		H2("Trade Recommendations"),
		P("Note: For all trade evaluations we consider the benches to be stocked with players equivalent to 20 pts worse than the best available player at that position."),
		create_filter_controls(),
		loading_indicator,
		recommendations_content,
		Script("""
			htmx.on('htmx:beforeRequest', function(event) {
				document.getElementById('loading-indicator').style.display = 'block';
			});
			htmx.on('htmx:afterRequest', function(event) {
				document.getElementById('loading-indicator').style.display = 'none';
			});
		"""),
		id="current-menu-content"
	)

def league_info_page():
    def create_position_inputs():
        return Div(
            *(Div(
                Label(f"{pos}:", fr=f"{pos}-count"),
                Input(
                    type="number",
                    name=f"{pos}_count",
                    id=f"{pos}-count",
                    value=str(NUM_STARTERS.get(pos, 0)),
                    min="0",
                    cls="form-control",
                    hx_get="/update_league_info",
                    hx_trigger="change",
                    hx_include="[name$='_count'],[name^='flex_']"
                ),
                cls="col-md-2 mb-3"
            ) for pos in ['QB', 'RB', 'WR', 'TE', 'FLEX']),
            cls="row"
        )

    def create_flex_options():
        return Div(
            Label("FLEX Positions:", fr="flex-positions"),
            *(Div(
                Input(
                    type="checkbox",
                    name=f"flex_{pos}",
                    id=f"flex-{pos}",
                    value=pos,
                    checked=(pos in FLEX_POSITIONS),
                    hx_get="/update_league_info",
                    hx_trigger="change",
                    hx_include="[name$='_count'],[name^='flex_']"
                ),
                Label(pos, fr=f"flex-{pos}"),
                cls="form-check"
            ) for pos in ['QB', 'RB', 'WR', 'TE']),
            cls="mb-3"
        )

    return Div(
        H2("League Info"),
        H4("Starting Lineup Positions"),
        create_position_inputs(),
        H4("FLEX Options"),
        create_flex_options(),
        Button("Load Example Auction Info", type="button", cls="btn btn-secondary mb-3",
               hx_post="/load_example_auction", hx_target="#current-menu-content"),
        P("After setting these options, navigate to other pages using the sidebar."),
        id="current-menu-content"
    )