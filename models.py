from collections import defaultdict
import pandas as pd
import numpy as np

# Updated global variables
from config import POSITIONS, NUM_STARTERS, FLEX_POSITIONS, PLAYERS, sorted_teams_and_players

def load_default_data():
    with open('default_draft_results.txt', 'r') as f:
        auction_input = f.read()
    with open('default_player_info.txt', 'r') as f:
        player_info_input = f.read()
    return auction_input, player_info_input

def player_search(player):
    return PLAYERS.get(player, {}).get('projected_fpts', 0)

def get_sorted_teams_and_players(players):
    teams = defaultdict(lambda: defaultdict(list))
    failed = []
    succeeded = []
    for player, data in players.items():
        try:
            if 'fantasy_team' not in data:
                continue
            team = data['fantasy_team']
            position = data['position']
            if position in POSITIONS:
                projected_points = player_search(player)
                teams[team][position].append((player, projected_points))
            succeeded.append(player)
        except:
            failed.append(player)
    
    if succeeded:
        print(*failed,sep="\n")
    else:
        return teams
    
    # Sort each position list by projected points (descending order)
    for team in teams:
        for position in POSITIONS:
            teams[team][position].sort(key=lambda x: x[1], reverse=True)

    # Assign FLEX players if FLEX is in POSITIONS
    if 'FLEX' in POSITIONS:
        for team in teams:
            flex_candidates = []
            for pos in FLEX_POSITIONS:
                flex_candidates.extend(teams[team][pos][NUM_STARTERS[pos]:])
            flex_candidates.sort(key=lambda x: x[1], reverse=True)
            teams[team]['FLEX'] = flex_candidates
    
    return teams

def get_team_points(team, printing=False):
    positions = sorted_teams_and_players[team]
    starters = {}
    bench = {}
    for pos in POSITIONS:
        player_list = positions[pos]
        num_starters = NUM_STARTERS[pos]
        starters[pos] = sum(x[1] for x in player_list[:num_starters])
        bench[pos] = [x[1] for x in player_list[num_starters:]]
    
    # Add non-starting to FLEX bench if FLEX is in POSITIONS
    if 'FLEX' in POSITIONS:
        bench['FLEX'] = []
        for pos in FLEX_POSITIONS:
            bench['FLEX'].extend(bench[pos])
        bench['FLEX'].sort(reverse=True)
    
    return starters, bench

def prepare_data(players, sorted_teams_and_players, points_type='absolute'):
    df = []
    for team, team_data in sorted_teams_and_players.items():
        for position in POSITIONS:
            players_list = team_data.get(position, [])
            for i, (player, player_data) in enumerate(players_list):
                is_starter = i < NUM_STARTERS[position]
                df.append({
                    'Name': player,
                    'Price': players[player]['price'],
                    'Team': team,
                    'Position': position,
                    'Projected_Points': player_data,
                    'Starter': 'Starter' if is_starter else 'Bench'
                })
    
    df = pd.DataFrame(df)
    
    if points_type != 'absolute':
        for position in POSITIONS:
            if points_type == 'relative_worst_starter':
                baseline = df[(df['Position'] == position) & (df['Starter'] == 'Starter')]['Projected_Points'].min()
            elif points_type == 'relative_theoretical_worst_starter':
                num_starters = len(df['Team'].unique()) * NUM_STARTERS[position]
                baseline = df[df['Position'] == position]['Projected_Points'].nlargest(num_starters).min()
            
            df.loc[df['Position'] == position, 'Projected_Points'] -= baseline
    
    return df

def calculate_relative_points(df, relative_to):
    for position in POSITIONS:
        pos_data = df[df['Position'] == position]
        if relative_to == 'worst_starter':
            baseline = pos_data[pos_data['Starter'] == 'Starter']['Projected_Points'].min()
        elif relative_to == 'theoretical_worst_starter':
            num_starters = len(df['Team'].unique()) * NUM_STARTERS[position]
            baseline = pos_data['Projected_Points'].nlargest(num_starters).min()
        else:
            baseline = 0
        df.loc[df['Position'] == position, 'Relative_Points'] = df.loc[df['Position'] == position, 'Projected_Points'] - baseline
    return df

def calculate_outliers(df, fit_type):
    # Calculate predicted price based on the fit type
    x = df['Projected_Points']
    y = df['Price']
    
    if fit_type == 'linear':
        coef = np.polyfit(x, y, 1)
        df['Predicted_Price'] = np.polyval(coef, x)
    elif fit_type == 'polynomial':
        coef = np.polyfit(x, y, 2)
        df['Predicted_Price'] = np.polyval(coef, x)
    elif fit_type == 'logarithmic':
        coef = np.polyfit(np.log(x), y, 1)
        df['Predicted_Price'] = np.polyval(coef, np.log(x))
    elif fit_type == 'exponential':
        coef = np.polyfit(x, np.log(y), 1)
        df['Predicted_Price'] = np.exp(np.polyval(coef, x))
    
    # Calculate price difference
    df['Price_Difference'] = df['Price'] - df['Predicted_Price']
    
    return df[['Name', 'Team', 'Position', 'Price', 'Predicted_Price', 'Price_Difference', 'Projected_Points']]

def get_starter_quality_threshold(df, position):
    starters = df[(df['Position'] == position) & (df['Starter'] == 'Starter')]
    return starters['Projected_Points'].min()

from itertools import combinations
from collections import defaultdict
from copy import deepcopy

def recommend_trades(teams, players, included_player=None, included_teams=None, num_recommendations=10, num_players=1):
    recommendations = []
    num_players = min(num_players, 2)

    def get_waiver_baselines(teams, all_players):
        rostered_players = set(player[0] for team in teams.values() for pos in team.values() for player in pos)
        available_players = [p for p in all_players if p not in rostered_players]
        baselines = defaultdict(float)
        for player in available_players:
            pos = players[player]['position']
            fpts = player_search(player) - 20
            baselines[pos] = max(baselines[pos], fpts)
        
        if 'FLEX' in POSITIONS:
            baselines['FLEX'] = max([baselines[pos] for pos in FLEX_POSITIONS])
        
        return baselines

    waiver_baselines = get_waiver_baselines(teams, players)

    def evaluate_trade(team1, team2, players1, players2):
        def sort_team(team):
            for pos in POSITIONS:
                team[pos].sort(key=lambda x: x[1], reverse=True)
            
            # Reconfigure FLEX if it's in POSITIONS
            if 'FLEX' in POSITIONS:
                team["FLEX"] = []
                for pos in FLEX_POSITIONS:
                    team["FLEX"].extend(team[pos][NUM_STARTERS[pos]:])
                team["FLEX"].sort(key=lambda x: x[1], reverse=True)

        # Sort original teams
        sort_team(teams[team1])
        sort_team(teams[team2])

        original_score1 = calculate_team_score(teams[team1])
        original_score2 = calculate_team_score(teams[team2])

        new_team1 = deepcopy(teams[team1])
        new_team2 = deepcopy(teams[team2])

        def transfer_player(player, from_team, to_team):
            for pos in POSITIONS:
                if player in [p[0] for p in from_team[pos]]:
                    from_team[pos] = [p for p in from_team[pos] if p[0] != player]
                    to_team[pos].append((player, player_search(player)))
                    break

        # Transfer players
        for player, _ in players1:
            transfer_player(player, new_team1, new_team2)
        for player, _ in players2:
            transfer_player(player, new_team2, new_team1)

        # Sort new teams
        sort_team(new_team1)
        sort_team(new_team2)

        new_score1 = calculate_team_score(new_team1)
        new_score2 = calculate_team_score(new_team2)

        score_changes1 = calculate_score_changes(teams[team1], new_team1)
        score_changes2 = calculate_score_changes(teams[team2], new_team2)

        net_starter_change1 = sum(1 for pos, change in score_changes1.items() if change['starter_change'] > 0) - \
                            sum(1 for pos, change in score_changes1.items() if change['starter_change'] < 0)
        net_starter_change2 = sum(1 for pos, change in score_changes2.items() if change['starter_change'] > 0) - \
                            sum(1 for pos, change in score_changes2.items() if change['starter_change'] < 0)

        a = new_score1 - original_score1
        b = new_score2 - original_score2

        return {
            'team1': {'score_changes': score_changes1, 'net_starter_change': net_starter_change1},
            'team2': {'score_changes': score_changes2, 'net_starter_change': net_starter_change2},
            'total_value': (min((a, b)), (a + b))
        }

    def calculate_team_score(team):
        score = 0
        for position in POSITIONS:
            players = team.get(position, [])
            starters = NUM_STARTERS[position]
            
            # Pad with waiver players if necessary
            while len(players) < starters + 3:
                players.append(("waiver", waiver_baselines[position]))
            
            score += sum(player[1] for player in players[:starters])  # Starters
            
            # Calculate bench scores
            score += players[starters][1] * 0.3  # Bench1
            score += players[starters+1][1] * 0.15  # Bench2
            score += players[starters+2][1] * 0.05  # Bench3
        
        return score

    def calculate_score_changes(old_team, new_team):
        changes = {}
        for position in POSITIONS:
            old_players = old_team.get(position, [])
            new_players = new_team.get(position, [])
            
            # Pad with waiver players if necessary
            while len(old_players) < NUM_STARTERS[position] + 3:
                old_players.append(("waiver", waiver_baselines[position]))
            while len(new_players) < NUM_STARTERS[position] + 3:
                new_players.append(("waiver", waiver_baselines[position]))
            
            old_starters = old_players[:NUM_STARTERS[position]]
            new_starters = new_players[:NUM_STARTERS[position]]
            
            changes[position] = {
                'starter_change': sum(new[1] for new in new_starters) - sum(old[1] for old in old_starters),
                'bench1_change': new_players[NUM_STARTERS[position]][1] - old_players[NUM_STARTERS[position]][1],
                'bench2_change': new_players[NUM_STARTERS[position]+1][1] - old_players[NUM_STARTERS[position]+1][1],
                'bench3_change': new_players[NUM_STARTERS[position]+2][1] - old_players[NUM_STARTERS[position]+2][1]
            }
        return changes

    for team1, team2 in combinations(teams.keys(), 2):
        if included_teams:
            if len({*included_teams}) == 1:
                if included_teams[0] not in (team1, team2):
                    continue
            else:
                if {*included_teams} != {team1, team2}:
                    continue
        for n_players in range(1, num_players + 1):  # 1 to 1 players
            for players1 in combinations([player for position in teams[team1].values() for player in position], n_players):
                for players2 in combinations([player for position in teams[team2].values() for player in position], n_players):
                    if included_player and included_player not in [p[0] for p in players1 + players2]:
                        continue
                    trade_result = evaluate_trade(team1, team2, players1, players2)
                    recommendations.append((team1, team2, players1, players2, trade_result))
                    if len(recommendations) > num_recommendations:
                        recommendations.sort(key=lambda x: x[4]['total_value'], reverse=True)
                        recommendations = recommendations[:num_recommendations]

    # Sort recommendations by total trade value (descending)
    recommendations.sort(key=lambda x: x[4]['total_value'], reverse=True)

    return recommendations[:num_recommendations]