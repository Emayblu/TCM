import requests, json, pandas
import plotly.express as px

sportLib = { #library to get the sport keys for the API URL
    "Football": "americanfootball_nfl",
    "Soccer": "soccer_usa_mls",
    "Basketball": "basketball_nba",
    "Hockey": "icehockey_nhl",
    "Baseball": "baseball_mlb",
}

# Function that asks the user what sport they want:
def userSportRequest():  
    sportRequest = ""

    while sportRequest not in sportLib:  # check if it's in that dictionary
        print("What sport do you want odds for: ")
        sportRequest = input("(Football, Soccer, Basketball, Hockey or Baseball) > ")
    return sportLib[sportRequest]

#Function that gets the JSON data from the API given a sport
def getJsonData(sport): 
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?regions=us&markets=h2h&oddsFormat=american&apiKey=XXXXXX"  
    response = requests.get(url)
    response.raise_for_status()  # check for errors
    jsonData = json.loads(response.text)
    return jsonData

#Function that gets the list of games from the JSON data:
def getGameList(jsonData):
    gameList = [] #empty list, will add games to it
    for game in jsonData:
        gameDict = { #for each game, get the id, home team, and away team
            'gameId' : game['id'],
            'homeTeam' : game['home_team'],
            'awayTeam' : game['away_team']
        }
        gameList.append(gameDict) #and add that to a list
    return gameList #return the list of game dictionaries


###Changes: payoutVariance, highestPayoutTimestamp
def getGameData(jsonData, gameID, team): #team is the one you want odds on to win

    for game in jsonData: #need to iterate through them to find the game we want
        if game['id'] == gameID: #if that is the list with the game we want
            gameJsonData = game
    gameData = {          #the game data will have these attributes:
        'gameID' : gameJsonData['id'], #the game ID
        'desiredToWin' : team, #this is the team we want the odds for winning
        'opposingTeam' : '', #tbd, it will store the opposing team
        'bookOdds' : {}, #tdb, will be a library with 'Book Name' as key value and odds and values
        'avgWinOdds' : '',  #tbd, it will store the avergage win odds
        'highestPayout' : 0, #tbd, will find the best win odds
        'highestPayoutBook' : '',
        'highestPayoutTimestamp' : 0,
        'avgImpliedOdds' : 0,
        'extremeImpliedOdds' : 0,
        'extremeVariance' : 0,
        'gameStart' : gameJsonData['commence_time']
        }

    #add the opposing team:
    if team == gameJsonData['away_team']: #if the team we want odds on is the away team
        gameData['opposingTeam'] = gameJsonData['home_team'] #then the team they are playing is the home team
    else: 
        gameData['opposingTeam'] = gameJsonData['away_team'] #otherwise, they team they are playing is the away team

    #add the book odds from each book:
    for book in gameJsonData['bookmakers']:
        if book['title'] == 'Betfair' or book['title'] == 'PointsBet': #betfair uses weird EU odds that don't work, so skip it if it's there
            continue #skip to the next book
        i = 0
        while book['markets'][0]['outcomes'][i]['name'] != team: #need to find which dict in the list has the odds for the team we want
            i =+ 1 #so while the team we are looking for is not the one we got odds for, look to the next one (there may be three options: homeWin, awayWin, and tie)
        gameData['bookOdds'][book['title']] = book['markets'][0]['outcomes'][i]['price'] #make a new key value in gameData['bookOdds] with the name of the book, the value will be equal to the price of that bet
    
    #find the average win odds
    gameData['avgWinOdds'] = sum(gameData['bookOdds'].values())/len(gameData['bookOdds']) #the sum of all the odds divided by the total number of odds gets us the average odds on the game
    
    #find best win odds
    highestOdds = -100000000 #make super small to start, will be replaced
    highestOddsBook = ''
    for book in gameData['bookOdds']: #iterates over the key values. For each book we haev odds on
        if gameData['bookOdds'][book] > highestOdds: #see if that book's odds are higher then the highest we have so far
            highestOdds = gameData['bookOdds'][book] #if it is, then that is the new highest
            highestOddsBook = book #and store the name of the book too
 
    
    gameData['highestPayout'] = highestOdds #now that we have the highest, add that
    gameData['highestPayoutBook'] = highestOddsBook #same for it's corresponding book

    ###find the highest payout timestamp:
    for bookDict in gameJsonData['bookmakers']: #for each book in the Json data for that game
        if bookDict['title'] == gameData['highestPayoutBook']: #if the book is the highest one that we found
            gameData['highestPayoutTimestamp'] = bookDict['last_update']

    #This finds how "extreme" the variance was on the highest one by subtracting the average odds from the highest payout
    #Note: this is a somehwat flawed metric because negative odds and positive odds are not the same. Unfortuantly there isn't really a way to convert between the two.
    gameData['extremeVariance'] = gameData['highestPayout'] - gameData['avgWinOdds'] 

    return gameData #return gameJsonData

#function that plots the data in a interactive plotly graph
def plotAllBooks(allOddsDf):
    oddsPlot = px.scatter(
        data_frame = allOddsDf, 
        y = 'extremeVariance', 
        x = 'uniqueId', 
        template = 'seaborn', 
        hover_data = ['extremeVariance', 'winTeam', 'loseTeam', 'timestampUpdated', 'bestBook', 'bestBookOdds', 'avgBookOdds' ]) #include all this data when you hover over it
    oddsPlot.update_layout({'title':{'text':'Odds Improvement from Best Book in Each Game'}}) #set the title
    oddsPlot.update_yaxes(title_text='Odds Improvement') #update y-axis title
    oddsPlot.update_xaxes(title_text='Game+Team') #update x-axis title
    oddsPlot.show() #open the plot in browser


def getAllOddsList(gameList):
    allOddsList = []
    for game in gameList:
        homeOddsDict = {
            'gameId' : game['gameId'],
            'winTeam' : game['homeTeam']
        }
        allOddsList.append(homeOddsDict)
        awayOddsDict = {
            'gameId' : game['gameId'],
            'winTeam' : game['awayTeam']
        }
        allOddsList.append(awayOddsDict)

    return allOddsList
################################ MAIN FUNCTION #####################################

sport = userSportRequest()

jsonData = getJsonData(sport)
gameList = getGameList(jsonData)

allOddsList = getAllOddsList(gameList) #makes a list with one dict for each odds (which had one team and their game code)

for gameOdds in allOddsList: #loop adds the variance of the best odds with the average odds,  the loseing team, and the time
    gameData = getGameData(jsonData, gameOdds['gameId'], gameOdds['winTeam'])

    if gameData['highestPayoutTimestamp'] > gameData['gameStart']: #if the updated time (in utc standard time) is greater than the start time, meaning the game started, then skip that game
        continue

    gameOdds['extremeVariance'] = gameData['extremeVariance']
    gameOdds['loseTeam'] = gameData['opposingTeam']
    gameOdds['timestampUpdated'] = gameData['highestPayoutTimestamp']
    gameOdds['uniqueId'] = gameOdds['winTeam'] + ' (' + str(gameOdds['gameId']) + ')'
    gameOdds['bestBook'] = gameData['highestPayoutBook']
    gameOdds['bestBookOdds'] = gameData['highestPayout']
    gameOdds['avgBookOdds'] = gameData['avgWinOdds']

allOddsDf = pandas.DataFrame.from_dict(allOddsList)

print(allOddsDf.loc[allOddsDf['extremeVariance'].idxmax()]) #gets the row with the highest extreme varinance, and print it out to show it

print('would you like to see a chart of all the odds? (Y/N)')
chartQ = input('> ')
if chartQ == 'Y':
    plotAllBooks(allOddsDf)
