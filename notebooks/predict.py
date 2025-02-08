import configparser
import os
import time
import random
import pandas as pd
import requests
import openpyxl
import sqlite3
from sklearn.model_selection import train_test_split

from datetime import datetime
from io import StringIO
from pathlib import Path
from bs4 import BeautifulSoup
from alive_progress import alive_bar
from joblib import dump, load

import configparser
import os
import time
import random
import pandas as pd
import requests
import openpyxl
import sqlite3

from datetime import datetime
from io import StringIO
from pathlib import Path
from bs4 import BeautifulSoup
from alive_progress import alive_bar

# some stuff I set up in a config file so I don't have to keep updating certain
# variables in every script
# config = configparser.ConfigParser()
# config.read('./config.ini')
# output = Path(config['paths']['output'])

def combine_player_data(start_year:int, end_year:int) -> pd.DataFrame:
    # initialize empty dataframe
    all_data = pd.DataFrame()
    
    # combine all data into a df that is used for cleaning
    for year in range(start_year, end_year+1):
        player_data = pd.read_csv(config['data'][f'all_player_data_{year}'])
        all_data = pd.concat([all_data, player_data], ignore_index=True)
    
    all_data = adjust_initial_df(all_data)
    
    # switch to MLS data
    all_data.replace('On matchday squad, but did not play', 0, inplace=True)
    
    return all_data[all_data['Comp'] == 'MLS']

def adjust_initial_df(df)->pd.DataFrame:
    correct_col_names = ['Date', 'Day', 'Comp', 'Round', 'Venue', 'Result', 'Squad', 'Opponent',
       'Start', 'Pos', 'Min', 'Gls', 'Ast', 'PK', 'PKatt', 'Sh', 'SoT', 'CrdY',
       'CrdR', 'Touches', 'Tkl', 'Int', 'Blocks', 'xG', 'npxG', 'xAG', 'SCA',
       'GCA', 'Cmp', 'Att', 'Cmp%', 'PrgP', 'Carries', 'PrgC', 'Att_TakeOn', 'Succ',
       'Match Report', 'player_url']
    df.columns = correct_col_names
    game_keys = []
    for index, player in df.iterrows():
        if player['Venue'] == 'Home':
            game_keys.append(f'{player['Date']} {player['Squad']} vs {player['Opponent']}')
        else:
            game_keys.append(f'{player['Date']} {player['Opponent']} vs {player['Squad']}')
    df['game_key'] = game_keys
    return df

def create_match_data(player_data_df):
    player_data_df['game_key'] = player_data_df.apply(create_game_key, axis=1)
    create_dependent_variables(player_data_df)
    
    desired_cols = ['Date', 'Day', 'Round', 'Squad', 'Opponent', 'Result', 'OverallResult', 'home_score', 'home_penalties', 'away_score', 'away_penalties', 'game_key']
    updated_names = ['game_date', 'day', 'round', 'home_team', 'away_team', 'result', 'overall_result', 'home_score', 'home_penalties', 'away_score', 'away_penalties', 'game_key']
    
    player_data_df = player_data_df[desired_cols]
    player_data_df.columns = updated_names
    player_data_df.drop_duplicates(inplace=True)
    
    return player_data_df.sort_values(by=['game_date'])
    
def create_game_key(row):
    if row['Venue'] == 'Home':
        return f'{row['Date']} {row['Squad']} vs {row['Opponent']}'
    else:
        return f'{row['Date']} {row['Opponent']} vs {row['Squad']}'

def create_dependent_variables(df):
    df['Results_Raw'] = df['Result'].apply(lambda x: x.replace(' ', '–').replace('(', '').replace(')', '').split('–'))
    df['OverallResult'] = df['Results_Raw'].apply(lambda x: x[0])
    df['home_score'] = df['Results_Raw'].apply(lambda x: int(x[1]))
    df['home_penalties' ] = df['Results_Raw'].apply(lambda x: int(x[2]) if len(x)==5 else 0)
    df['away_score'] = df['Results_Raw'].apply(lambda x: int(x[3]) if len(x)==5 else int(x[2]))
    df['away_penalties' ] = df['Results_Raw'].apply(lambda x: int(x[4]) if len(x)==5 else 0)
    df['game_key'] = df.apply(lambda x: f'{x['Date']} {x['Squad']} vs {x['Opponent']}', axis=1)
    
def clean_data_for_modeling(player_data, match_data):
    players_numeric_columns = ['Min', 'Gls', 'Ast', 'PK', 'PKatt', 'Sh', 'SoT', 'CrdY',
       'CrdR', 'Touches', 'Tkl', 'Int', 'Blocks', 'xG', 'npxG', 'xAG', 'SCA',
       'GCA', 'Cmp', 'Att', 'Cmp%', 'PrgP', 'Carries', 'PrgC', 'Att_TakeOn',
       'Succ']
    
    
    for col in players_numeric_columns:
        player_data[col] = player_data[col].astype(float)
    
    cleaned_df = pd.DataFrame()

    for match in match_data['game_key']:
        current_match_data = match_data[match_data['game_key'] == match].copy().reset_index()
        current_match_date = current_match_data['game_date'][0]
        current_match_year = int(current_match_data['game_date'][0][-4:])
        home_team = current_match_data['home_team'][0]
        away_team = current_match_data['away_team'][0]
        

        prior_home_stats = player_data.query(f'Date<"{current_match_date}" and Date > "{current_match_year-1}-12-31" and Squad=="{home_team}" and Venue=="Home" and Start!="N"')
        prior_home_stats = prior_home_stats[players_numeric_columns]
        prior_away_stats = player_data.query(f'Date<"{current_match_date}" and Date > "{current_match_year-1}-12-31" and Squad=="{away_team}" and Venue=="Home" and Start!="N"')
        prior_away_stats = prior_away_stats[players_numeric_columns]
        
        prior_home_stats.columns = [f'home_prior_{x}' for x in prior_home_stats.columns]
        prior_away_stats.columns = [f'away_prior_{x}' for x in prior_away_stats.columns]
        
        if prior_home_stats.shape[0]==0:
            temp = prior_home_stats.columns
            prior_home_stats = pd.DataFrame([0]*len(prior_home_stats.columns)).T
            prior_home_stats.columns = temp
            
        if prior_away_stats.shape[0]==0:
            temp = prior_away_stats.columns
            prior_away_stats = pd.DataFrame([0]*len(prior_away_stats.columns)).T
            prior_away_stats.columns = temp

        prior_home_stats = pd.DataFrame(prior_home_stats.describe().T['mean']).T.reset_index()
        prior_away_stats = pd.DataFrame(prior_away_stats.describe().T['mean']).T.reset_index()
        
        final_row = pd.concat([current_match_data, prior_home_stats, prior_away_stats], axis=1)
        
        cleaned_df = pd.concat([cleaned_df, final_row], axis=0)
        
    return cleaned_df

# player_data = combine_player_data(2022, 2024)

# player_data.head()

# matches_df = create_match_data(player_data)

# matches_df.tail()

# cleaned_df = clean_data_for_modeling(player_data, matches_df)

# cleaned_df

# cleaned_df.to_csv(output / 'cleaned_df.csv')

def predict_outcome(home_team, away_team, match_date, day, round):
    season = int(match_date[:4])
    current_match_data = pd.DataFrame([match_date, day, round, home_team, away_team, '', '',0,0,0,0,'']).T
    current_match_data.columns = ['game_date', 'day', 'round', 'home_team', 'away_team', 'result', 'overall_result', 'home_score', 'home_penalties', 'away_score', 'away_penalties', 'game_key']
    current_match_year = int(current_match_data['game_date'][0][:4])

    players_numeric_columns = ['Min', 'Gls', 'Ast', 'PK', 'PKatt', 'Sh', 'SoT', 'CrdY',
       'CrdR', 'Touches', 'Tkl', 'Int', 'Blocks', 'xG', 'npxG', 'xAG', 'SCA',
       'GCA', 'Cmp', 'Att', 'Cmp%', 'PrgP', 'Carries', 'PrgC', 'Att_TakeOn',
       'Succ']

    prior_home_stats = all_players.query(f'Date<"{match_date}" and Date > "{current_match_year-1}-12-31" and Squad=="{home_team}" and Venue=="Home" and Start!="N"')
    prior_home_stats = prior_home_stats[players_numeric_columns]
    prior_away_stats = all_players.query(f'Date<"{match_date}" and Date > "{current_match_year-1}-12-31" and Squad=="{away_team}" and Venue=="Home" and Start!="N"')
    prior_away_stats = prior_away_stats[players_numeric_columns]
    
    prior_home_stats.columns = [f'home_prior_{x}' for x in prior_home_stats.columns]
    prior_away_stats.columns = [f'away_prior_{x}' for x in prior_away_stats.columns]
    
    if prior_home_stats.shape[0]==0:
        temp = prior_home_stats.columns
        prior_home_stats = pd.DataFrame([0]*len(prior_home_stats.columns)).T
        prior_home_stats.columns = temp
        
    if prior_away_stats.shape[0]==0:
        temp = prior_away_stats.columns
        prior_away_stats = pd.DataFrame([0]*len(prior_away_stats.columns)).T
        prior_away_stats.columns = temp

    prior_home_stats = pd.DataFrame(prior_home_stats.describe().T['mean']).T.reset_index()
    prior_away_stats = pd.DataFrame(prior_away_stats.describe().T['mean']).T.reset_index()
    
    final_row = pd.concat([current_match_data, prior_home_stats, prior_away_stats], axis=1)

    final_row.drop(columns = ['index','game_date', 'result', 'overall_result', 'home_score', 'home_penalties', 'away_score', 'away_penalties', 'game_key'], inplace=True)

    final_row = format_data_for_model(final_row)

    model = load(output / 'dtr_mvp.joblib')
    prediction = pd.DataFrame(model.predict(final_row))
    prediction.columns = ['overall_result', 'home_score', 'home_penalties', 'away_score', 'away_penalties']

    return prediction

def format_data_for_model(df):
    # df.drop(columns=['index','game_date', 'result', 'game_key', 'index.1', 'index.2'], inplace=True)
    
    df_nums = format_numerical_variables(df)
    df_cats = format_categorical_variables(df)

    formatted_df = pd.concat([df_nums, df_cats],axis=1)
    return formatted_df
    
def format_categorical_variables(df, use_as_encoder=False):
    df_cats = df.select_dtypes(include='O')
    if use_as_encoder:
        encoder = create_encoder(df)
        # global encoder
    else:
        encoder = load(output / 'encoder_mvp.joblib')
        # global encoder
    df_cats_enc = pd.DataFrame(encoder.transform(df_cats).toarray())
    df_cats_enc.columns = encoder.get_feature_names_out()
    df_cats_enc.index = df_cats.index
    return df_cats_enc
    
def format_numerical_variables(df):
    df_nums = df.select_dtypes(exclude='O')
    return df_nums
    
def create_encoder(df):
    encoder = OneHotEncoder()
    encoder.fit(df)
    return encoder

def result_to_num(result):
    if result == "D":
        return 0
    elif result =="L":
        return -1
    else:
        return 1


