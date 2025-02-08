# required libraries
import time
import pandas as pd
import requests
import datetime
import configparser
import os

from bs4 import BeautifulSoup
from alive_progress import alive_bar
from pathlib import Path
from io import StringIO  

# pull some variables, paths, and other from a central config.ini file
config = configparser.ConfigParser()
config.read('../src/config.ini')

# the output path is specified in the config.ini file
output = Path(config['paths']['output'])

# for file saving
today = datetime.datetime.now()
today = today.strftime("%Y_%m_%d")

# for the main stat pages every player should have
table_stat_types = ['passing', 'passing_types', 'gca', 'defense', 'possession', 'misc']

table_stat_dict = {
    'passing': ['Date', 'Day', 'Comp', 'Round', 'Venue', 'Result', 'Squad', 'Opponent', 'Start', 'Pos', 'Min', 'Total_Cmp', 
                'Total_Att', 'Total_Cmp%', 'Total_TotDist', 'Total_PrgDist', 'Short_Cmp', 'Short_Att', 'Short_Cmp%', 
                'Med_Cmp', 'Med_Att', 'Med_Cmp%', 'Long_Cmp', 'Long_Att', 'Long_Cmp%', 'Ast', 'xAG', 'xA', 'KP', '1/3', 
                'PPA', 'CrsPA', 'PrgP', 'Match Report'],
    'passing_types': ['Date', 'Day', 'Comp', 'Round', 'Venue', 'Result', 'Squad', 'Opponent', 'Start', 'Pos', 'Min', 'Att', 
                      'PassType_Live', 'PassType_Dead', 'PassType_FK', 'PassType_TB', 'PassType_Sw', 'PassType_Crs', 'PassType_TI', 
                      'PassType_CK', 'Corner_In', 'Corner_Out', 'Corner_Str', 'Outcome_Cmp', 'Outcome_Off', 'Outcome_Blocks', 
                      'Match Report'],
    'gca': ['Date', 'Day', 'Comp', 'Round', 'Venue', 'Result', 'Squad', 'Opponent', 'Start', 'Pos', 'Min', 'SCA_SCA', 
            'SCA_PassLive', 'SCA_PassDead', 'SCA_TO', 'SCA_Sh', 'SCA_Fld', 'SCA_Def', 'GCA_GCA', 'GCA_PassLive', 'GCA_PassDead', 
            'GCA_TO', 'GCA_Sh', 'GCA_Fld', 'GCA_Def', 'Match Report'],
    'defense': ['Date', 'Day', 'Comp', 'Round', 'Venue', 'Result', 'Squad', 'Opponent', 'Start', 'Pos', 'Min', 'Tkl_Tkl', 
               'Tkl_TklW', 'Tkl_Def_3rd', 'Tkl_Mid_3rd', 'Tkl_Att_3rd', 'Chall_Tkl', 'Chall_Att', 'Chall_Tkl%', 'Chall_Lost', 
               'Blk_Blocks', 'Blk_Sh', 'Blk_Pass', 'Int', 'Tkl+Int', 'Clr', 'Err', 'Match_Report'],
    'possession': ['Date', 'Day', 'Comp', 'Round', 'Venue', 'Result', 'Squad', 'Opponent', 'Start', 'Pos', 'Min', 
                   'Touches_Touches', 'Touches_Def_Pen', 'Touches_Def_3rd', 'Touches_Mid_3rd', 'Touches_Att_3rd', 
                   'Touches_Att_Pen', 'Touches_Live', 'TakeOn_Att', 'TakeOn_Succ', 'TakeOn_Succ%', 'TakeOn_Tkld', 
                   'TakeOn_Tkld%', 'Carries_Carries', 'Carries_TotDist', 'Carries_PrgDist', 'Carries_PrgC', 'Carries_1/3', 
                   'Carries_CPA', 'Carries_Mis', 'Carries_Dis', 'Receiving_Rec', 'Receiving_PrgR', 'Match Report'],
    'misc': ['Date', 'Day', 'Comp', 'Round', 'Venue', 'Result', 'Squad', 'Opponent', 'Start', 'Pos', 'Min', 'Perf_CrdY', 
             'Perf_CrdR', 'Perf_2CrdY', 'Perf_Fls', 'Perf_Fld', 'Perf_Off', 'Perf_Crs', 'Perf_Int', 'Perf_TklW', 'Perf_PKwon', 
             'Perf_PKcon', 'Perf_OG', 'Perf_Recov', 'AerialDuel_Won', 'AerialDuel_Lost', 'AerialDuel_Won%', 'Match Report']
    }

def get_html_data(url:str, parser:str='html.parser') -> BeautifulSoup:
    '''
    Extract html data from specified url and return a bs4 object.
    Parser can be specified if needed. Default is html.parser.
    '''
    time.sleep(int(config['other']['request_time_limit']))

    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, parser)
    
    return soup

def get_all_teams(url:str) -> (pd.DataFrame, str):
    '''
    Given a URL, extract teams and associated team URLs for the MLS league.
    This is currently specific to the MLS league. This will eventually be updated
    to work with additional leagues.
    '''
    soup = get_html_data(url)
    # this gets the associated year for the web-page, including if you run it on
    # prior seasons
    year = soup.find('h1').text[10:14]
    # this gets the team tables
    eastern_conference = soup.find('table', {'id': f'results{year}221Eastern-Conference_overall'})
    western_conference = soup.find('table', {'id': f'results{year}221Western-Conference_overall'})

    # Extract links from each table

    eastern_links = extract_table_links(eastern_conference)
    western_links = extract_table_links(western_conference)

    all_teams = pd.DataFrame(eastern_links + western_links)
    all_teams.columns = ['team', 'team_url']
    all_teams['season'] = year
    
    all_teams.to_csv(output / f"mls_{year}/all_teams_{today}.csv", index=False)

    return (all_teams, year)

def extract_table_links(table) -> list:
    '''
    Provided a table from soup.find('table'), this returns
    a list of the associated links from the table. This is based
    on how the website used is set up.
    '''
    links = []
    if table:
        # get table rows
        rows = table.find_all('tr')
        for row in rows:
            # get links
            link_tag = row.find('a')
            if link_tag:
                links.append((link_tag.text, f"https://fbref.com{link_tag['href']}"))
    return links

def extract_table_links_and_positions(table) -> list:
    '''
    Provided a table from soup.find('table'), this returns
    a list of the associated links and player positions from the table.
    This is based on how the website used is set up.
    '''
    links = []
    if table:
        # get table rows
        rows = table.find_all('tr')
        for row in rows:
            # get links
            link_tag = row.find('a')
            try:
                # get player position(s)
                position = row.find('td',{'data-stat':'position'})
                position = position.text
            except:
                position = None
            if link_tag:
                links.append((link_tag.text, f"https://fbref.com{link_tag['href']}", position))
    return links

def get_team_players(team) -> pd.DataFrame:
    '''
    Used in conjunction with get_all_players().
    This grabs the player name, player url, and position from the associated
    team link.
    '''
    time.sleep(int(config['other']['request_time_limit']))
    # get html data
    soup = get_html_data(team['team_url'])
    players_df = extract_table_links_and_positions(soup.find('table', {'id': 'stats_standard_22'}))
    # build dataframe
    players_df = pd.DataFrame(players_df)
    players_df.columns = ['player_name', 'player_url', 'position']
    players_df['team'] = team['team']
    return players_df

def get_all_players(all_teams_df:pd.DataFrame, year:int) -> pd.DataFrame:
    '''
    Provided a dataframe of all teams, grab all players, urls, and positions
    and concatenate them into one main dataframe.
    '''
    all_team_players = list(all_teams_df.apply(get_team_players,axis=1))

    all_players_df = pd.DataFrame()
    for players in all_team_players:
        all_players_df = pd.concat([all_players_df, players], ignore_index=True)
    all_players_df.drop_duplicates(inplace=True)
    all_players_df['season'] = year

    all_players_df.to_csv(output / f"mls_{year}/all_players_{today}.csv", index=False)

    return all_players_df

def get_teams_and_players(url:str) -> (str, pd.DataFrame, pd.DataFrame):
    '''
    Provided an initial url that contains the teams for the MLS season,
    extract all teams, players, and associated urls and returns them as dataframes.
    '''
    all_teams_df, year = get_all_teams(url)

    all_players_df = get_all_players(all_teams_df, year)

    return (year, all_teams_df, all_players_df)

def generate_player_stat_links(player_url:str, year:int) -> list:
    '''
    Using the stat types list, generate the corresponding links for the input
    player url and year. Returns the generated links as a list.
    '''
    player_stat_links = []
    for stat_type in table_stat_types:
        temp = player_url.split('/')
        temp.insert(-1, f"matchlogs/{year}/{stat_type}")
        temp = '/'.join(temp)
        player_stat_links.append(temp)

    return player_stat_links

def generate_individual_player_df(player_url:str, year:int) -> pd.DataFrame:
    '''
    Provided an initial player url, generate a dataframe containing the main
    corresponding stats.
    '''
    player_stat_links = generate_player_stat_links(player_url, year)
    player_df = pd.DataFrame()
    for index, stat_link in enumerate(player_stat_links):
        time.sleep(int(config['other']['request_time_limit']))
        soup = get_html_data(stat_link)
        stat_df = soup.find('table')
        stat_df = pd.read_html(StringIO(str(stat_df)))[0]
        stat_df.columns = [f"{table_stat_types[index]}_{col[1].lower()}" for col in stat_df.columns]
        player_df = pd.concat([player_df, stat_df], axis=1)
    return player_df

def get_all_players_data(players_df, year) -> pd.DataFrame:
    '''
    Provided an dataframe of players and urls, return a dataframe of the main
    corresponding stats and any failed initial player links.
    '''
    all_players_stat_df = pd.DataFrame()
    failed_links = []
    with alive_bar(players_df.shape[0], force_tty=True) as bar:
        for player_url in players_df['player_url']:
            try:
                current_player_df = generate_individual_player_df(player_url, year)
                all_players_stat_df = pd.concat([all_players_stat_df, current_player_df], ignore_index=True)
            except:
                print(f"Could not obtain data for {player_url.split('/')[-1]}")
                failed_links.append(player_url)
            bar()
    return all_players_stat_df, failed_links
        


def save_player_htmls(players_df:pd.DataFrame, year:int):
    '''
    Provided a dataframe of players and urls,
    saves html files to corresponding directories.
    Returns a list of failed indicis and a list of failed links.
    '''
    failed_indices = []
    failed_links = []
    i=0
    with alive_bar(players_df.shape[0], force_tty=True) as bar:
        for index, row in players_df.iterrows():
            time.sleep(int(config['other']['request_time_limit']))
            stat_links = generate_player_stat_links(row['player_url'], year)
            for i, stat_link in enumerate(stat_links):
                try:
                    time.sleep(int(config['other']['request_time_limit']))
                    # print(stat_link)
                    # print(f'{output}/mls_{year}/html_files/{row['player_name']}_{table_stat_types[i]}_{row['team']}.html')
                    page = requests.get(stat_link)
                    with open(f'{output}/mls_{year}/html_files/{row['team']}/{row['player_name']}_{table_stat_types[i]}.html', 'wb+') as f:
                        f.write(page.content)
                except:
                    i+=1
                    print(f'\r{i} failed html requests')
                    failed_indices.append(index)
                    failed_links.append(stat_link)
            bar()
    return (failed_indices, failed_links)

def get_html_stat_file_paths(dir, stat):
    html_files = []
    for roots, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(f'_{stat}.html'):
                html_files.append(f"{roots}\\{file}")
    return html_files

def create_df_for_stat(html_files, stat):
    stat_df = pd.DataFrame()
    failed_files = []
    with alive_bar(len(html_files), force_tty=True) as bar:
        for file in html_files:
            try:
                with open(file) as fp:
                    player_name_index = len(stat) + len('_.html')
                    player_name = file.split('\\')[-1][:-player_name_index]

                    soup = BeautifulSoup(fp, 'html.parser')
                    
                    temp_df = pd.read_html(StringIO(str(soup)))[0]
                    # print(len(temp_df.columns))
                    temp_df.columns = table_stat_dict[stat]

                    temp_df['PlayerName'] = player_name
                    temp_df['FileName'] = file
                    
                    stat_df = pd.concat([stat_df, temp_df], ignore_index=True)
            except:
                failed_files.append(file)
            bar()


    return stat_df, failed_files