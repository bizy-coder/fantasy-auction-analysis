POSITIONS = ['QB', 'RB', 'WR', 'TE', 'FLEX']
NUM_STARTERS = {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1}
FLEX_POSITIONS = ['RB', 'WR']
PLAYERS = {}
sorted_teams_and_players = {}

def update_league_settings(new_positions, new_num_starters, new_flex_positions):
	global POSITIONS, NUM_STARTERS, FLEX_POSITIONS
	POSITIONS.clear()
	POSITIONS.extend(new_positions)
	NUM_STARTERS.clear()
	NUM_STARTERS.update(new_num_starters)
	FLEX_POSITIONS.clear()
	FLEX_POSITIONS.extend(new_flex_positions)
	# print("UPDATED INFO ########\n",POSITIONS, NUM_STARTERS, FLEX_POSITIONS)
	# print(FLEX_POSITIONS)

def update_sorted_teams_and_players(new_sorted_teams_and_players):
    sorted_teams_and_players.clear()
    sorted_teams_and_players.update(new_sorted_teams_and_players)