# FutbolMatchPrediction
I predict futbol matches. I'm starting out with MLS for now. This is a work in progress!

---

## Data
I found data for MLS on [Kaggle](https://www.kaggle.com/datasets/josephvm/major-league-soccer-dataset).
However, I didn't use it yet for 3 reasons:
1. It was messy and I just started.
2. I wanted to try web scraping some data since it only went up to 2022. I would still need 2023 and 2024 data.
I would also need to format this scraped data to the existing dataset instead of formatting it based on what I get.
3. It was messy lol

I web scraped data from [this website.](https://fbref.com/en/comps/22/schedule/Major-League-Soccer-Scores-and-Fixtures)
It has a lot of amazing tables of stats for me to pull in. When scraping, they do limit the number of times you can
pull from the site per minute, so I had to squeeze in a timer to account for this. It ends up taking about 2 hours
to web scrape each year :'))

Anyways, I managed to scrape 77,796 records of player data. Once I did a little bit of cleaning,
I narrowed this down to 59,663 records of player data and 1,525 games related to the MLS league, with additional
cleaning still left to be done. I haven't confirmed if it's the correct number of games yet.

I kept it simple/quick for now and only scraped a couple tables from each page so I can get a quick ML model done. 
I saw an open position for an MLS team so I wanted to slap this project on my resume to get it in as quick as possible,
hopefully increase my chances for an interview!

---

## Current Approach
So since I wanted to get an MVP model done ASAP, my approach is fairly simple. I have some basic data available per match,
such as which is home/away, the day of the week, round, and more. 

In terms of team data, I decided to get current season player stat averages for games that occured before the game date being predicted. 
For example, for the 11/23/24 LAFC vs Seattle game that is upcoming this saturday, I took averages
of player performance for all the previous games the team played in the 2024 season. This is the data we should have in hand
before each game occurs.

Luckily the data I have available is mostly numerical data. For the categorical data, I just one-hot encoded it for now
for simplicity and because most of it nominal data.

I trained a Decision Tree Regressor because I am used to Decision Tree based models from my work experience and I like them now. 
In addition, these kinds of models are really easy to interpret as I could always get the tree itself. I want to experiment
with some path extraction when I get the chance.

The model is currently predicting if Home Wins/Loses/Draws and each team score (including penalties).
Prediction 11/23/24:
* LAFC vs Seattle Sounders FC <br><t><t>Prediction: 6-0 (lol) <br><t><t>Result: 1-2 
* New York City vs NY Red Bulls: <br><t><t>Prediction: 2-2 (penalty winner needs fixing) <br><t><t>Result: 0-2

Prediction 11/24/24:
* Orlando City vs Atlanta United <br><t><t>Prediction: 0-2 <br><t><t>Result: 1-0
* LA Galaxy vs Minnesota <br><t><t>Prediction: 3-2 <br><t><t>Result: 6-2 (lol)

Prediction 11/30/24:
* Orlando City vs NY Red Bulls <br><t><t>Prediction: 0-0 (penalty winner needs fixing) <br><t><t>Result: 0-1
* LA Galaxy vs Seattle Sounders<br><t><t>Prediction: 6-0 (lol)<br><t><t>Result: 1-0

Prediction 12/7/2024:
* LA Galaxy vs NY Red Bulls <br><t><t>Prediction: 3-2 <br><t><t>Result: 2-1

---

## Metrics
TBD

11/23/24
The current predictions line up with predictions found on the web. But the scores look exaggerated.

---

## To-Do
* Improve web scraping to include additional data from the website. It's
always nice to have more data available to use.
* Incorporate additional years. I am still going through the Kaggle data. There's missing data.
I can fill in the blanks through scraping. However, if I'm doing that I might as well scrape all the data myself. This would
probably make it easier to incorporate into my existing code. I'll keep thinking about it as I review the data.
* Find a better way to validate player/match data. I did manual reviews of the data and compared them to game data
available on the web. But it'd be cool if I could automate this in some format.
* Clean, clean, clean...There's currently some pitfalls in my cleaning. For example, I didn't account for the dummy
variable trap in the encoding. I need to go back and review this. Also I need to encapsulate the cleaning. This will
let me easily apply it to any additional years I scrape and will make it easier to modify.
* I want to recreate the cleaning in SQL since I know SQL and it'll be good practice. I will use SQLite since it easily
integrates with Python.
* Incorporate other ML models.
* Incorporate an easy way to make upcoming predictions. I want to place into .py files so I can easily and quickly
run future predictions.


---

## Notes
I wanted to bring attention to the file called **config_example.ini**. This file is what I use to set up frequently used
paths and other important information. I tend to switch between my desktop and laptop a lot, so this gives me a nice
central location to easily make the associated updates. It's really easy to use, and you can also hide sensitive information
in here by making sure you include it in the **.gitignore** file. I like to show other people this when I get the chance
since not everyone knows!

If you're here from the MLS league reviewing my project,

![Hire me please](/src/hire_me.jpg)


---

## Environment
If you want to recreate my environment, run this:

```
conda env create -f environment.yml
```
If you wanted to know how to export any environment (this excludes the "prefix"
which would normally include the path to your environment):
```
conda env export | grep -v "^prefix: " > environment.yml
```

I made a txt file so my friend could follow along but I don't think he even cloned the repo :((