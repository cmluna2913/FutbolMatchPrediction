import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from alive_progress import alive_bar
import datetime
import configparser
from pathlib import Path
from io import StringIO  

# pull some variables, paths, and other from a central config.ini file
config = configparser.ConfigParser()
config.read('../src/config.ini')

# the output path is specified in the config.ini file
output = Path(config['paths']['output'])

today = datetime.datetime.now()
today = today.strftime("%Y_%m_%d")

def get_html_data(url, parser='html.parser') -> BeautifulSoup:
    '''
    Extract html data from specified url and return a bs4 object.
    Parser can be specified if needed. Default is html.parser.
    '''
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, parser)
    
    return soup

def get_all_teams(url):
    soup = get_html_data(url)
    year = soup.find('h1').text[10:14]
    eastern_conference = soup.find('table', {'id': f'results{year}221Eastern-Conference_overall'})
    western_conference = soup.find('table', {'id': f'results{year}221Western-Conference_overall'})

    # Extract links from each table

    eastern_links = extract_table_links(eastern_conference)
    western_links = extract_table_links(western_conference)

    all_teams = pd.DataFrame(eastern_links + western_links)
    all_teams.columns = ['team', 'team_url']
    all_teams['season'] = year
    
    all_teams.to_csv(output / f"mls_{year}/all_teams_{today}.csv", index=False)

    return all_teams, year

def extract_table_links(table):
    links = []
    if table:
        rows = table.find_all('tr')
        for row in rows:
            link_tag = row.find('a')
            if link_tag:
                links.append((link_tag.text, f"https://fbref.com{link_tag['href']}"))
    return links

def extract_table_links_and_positions(table):
    links = []
    if table:
        rows = table.find_all('tr')
        for row in rows:
            link_tag = row.find('a')
            try:
                position = row.find('td',{'data-stat':'position'})
                position = position.text
            except:
                position = None
            if link_tag:
                links.append((link_tag.text, f"https://fbref.com{link_tag['href']}", position))
    return links

def get_team_players(team):
    time.sleep(int(config['other']['request_time_limit']))
    soup = get_html_data(team['team_url'])
    players_df = extract_table_links_and_positions(soup.find('table', {'id': 'stats_standard_22'}))
    players_df = pd.DataFrame(players_df)
    players_df.columns = ['player_name', 'player_url', 'position']
    players_df['team'] = team['team']
    return players_df

def get_all_players(all_teams_df, year):
    all_team_players = list(all_teams_df.apply(get_team_players,axis=1))

    all_players_df = pd.DataFrame()
    for players in all_team_players:
        all_players_df = pd.concat([all_players_df, players], ignore_index=True)
    all_players_df.drop_duplicates(inplace=True)
    all_players_df['season'] = year

    all_players_df.to_csv(output / f"mls_{year}/all_players_{today}.csv", index=False)

    return all_players_df

def get_teams_and_players(url):
    all_teams_df, year = get_all_teams(url)

    all_players_df = get_all_players(all_teams_df, year)

    return year, all_teams_df, all_players_df

table_stat_types = ['summary', 'passing', 'passing_types', 'gca', 'defense', 'possession', 'misc']

def generate_player_stat_links(player_url, year):
    player_stat_links = []
    for stat_type in table_stat_types:
        temp = player_url.split('/')
        temp.insert(-1, f"matchlogs/{year}/{stat_type}")
        temp = '/'.join(temp)
        player_stat_links.append(temp)

    return player_stat_links

def generate_individual_player_df(player_url, year):
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

def get_all_players_data(players_df, year):
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
        