#%%
import configparser
import os
import time
import random
import pandas as pd
import requests
import openpyxl
from alive_progress import alive_bar

from io import StringIO
from pathlib import Path
from bs4 import BeautifulSoup

#%%
print('Reading config file...')

config = configparser.ConfigParser()
config.read('../src/config.ini')
    
#%%
# the output path is specified in the config.ini file
output = Path(config['paths']['output'])
# I want data for the 2022 through 2024 season
yearly_directories = [Path(output/f"mls_{year}") for year in range(2022,2025)]

# create output directory and sub-directories if doesnt exist
for directory in yearly_directories+[output]:
    try:
        assert directory.exists()
    except:
        os.mkdir(directory)
        
# %%
# I will be web-scraping alot, so I made this function as a result

def get_html_data(url, parser='html.parser'):
    '''
    Extract html data from specified url and return a bs4 object.
    Parser can be specified if needed. Default is html.parser.
    '''
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, parser)
    
    return soup

#%%
# I ended up using this a lot in the end
def get_table_data_from_html(soup)->list:
    '''
    Extract tables from bs4 object and return a list of dataframes.
    '''
    
    # get all tables in the html
    tables = soup.findAll('table')

    # create dfs for each table and append each one to a list
    dfs_from_tables = []
    for table in tables:
        dfs_from_tables.append(pd.read_html(StringIO(str(table)))[0])
    
    return dfs_from_tables
#%%
from alive_progress import alive_bar
with alive_bar(10, force_tty=True) as bar:
    for i in range(10):
        time.sleep(1)
        bar()
# %%
from alive_progress.styles import showtime 
showtime()
# %%
