import requests, json
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

#Function that asks the user what team they want odds on, and returns both the team and the gamecode
def userTeamRequest(gameList):
    if len(gameList) == 0: #if there are no games, end it right away
        print('There are no upcoming games in that sport. Please try again with another sport.')
        return 0, 0 #return and empty tuple

    teamList = [] #will make a list with all the team options, will be important later
    print('we have games for: ')
    for gameDict in gameList:
        print(gameDict['awayTeam'] + ' @ ' + gameDict['homeTeam'] + '\n') #print each matchup to show options
        teamList.append(gameDict['awayTeam']) #add both teams to the gamelist
        teamList.append(gameDict['homeTeam'])
         
    print('What team would you like odds on?')
    teamRequest = input('> ')

    while teamRequest not in teamList: #if it's not one of them in the list, ask again
        print('you must pick a team from the list')
        teamRequest = input('> ')
    
    if teamList.count(teamRequest) > 1: #if the team is in the gameList more than once (meaning they are in more than one game)
        oppList = [] #make an empty list, will hold the names of all the teams they play
        for item in gameList: #for each game dictionary in gameDict
            if item["homeTeam"] == teamRequest: #if the team we want is home, get the away team
                oppList.append(item['awayTeam'])
            if item['awayTeam'] == teamRequest: #if the team we want is away, get the home team
                oppList.append(item['homeTeam'])

        print('That team plays multiple games, which team do you want them playing?')
        opponent = input('> ')

        while opponent not in oppList:
            print('you must pick a team that ' + teamRequest + ' plays.')
            print('they play: ' + ', '.join(oppList))
            opponent = input('> ')
        
        #below is a one line forloop that finds the gamecode of the matchup where the teams play each other 
        gameCode = next(gameDict['gameId'] for gameDict in gameList if (gameDict["homeTeam"] == teamRequest or gameDict["awayTeam"] ==teamRequest) and (gameDict["awayTeam"] == opponent or  gameDict["homeTeam"] == opponent))
        #get the game id where the two teams play each other (if the team request is home or away, and the opponent is home or away)
        
    else:
        #this is a one line for loop that find the game that the team plays in
        gameCode = next(gameDict['gameId'] for gameDict in gameList if gameDict["homeTeam"] == teamRequest or gameDict["awayTeam"] == teamRequest )
    return teamRequest, gameCode #retuns tuple with gameId and gameCode

#function that gets the data for a game based on a gameId and team
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
        'highestPayoutBook' : ''
    }

    #add the opposing team:
    if team == gameJsonData['away_team']: #if the team we want odds on is the away team
        gameData['opposingTeam'] = gameJsonData['home_team'] #then the team they are playing is the home team
    else: 
        gameData['opposingTeam'] = gameJsonData['away_team'] #otherwise, they team they are playing is the away team

    #add the book odds from each book:
    for book in gameJsonData['bookmakers']:
        if book['title'] == 'Betfair': #betfair uses weird EU odds that don't work, so skip it if it's there
            continue #skip to the next book
        i = 0
        while book['markets'][0]['outcomes'][i]['name'] != team: #need to find which dict in the list has the odds for the team we want
            i =+ 1 #so while the team we are looking for is not the one we got odds for, look to the next one (there may be three options: homeWin, awayWin, and tie)
        gameData['bookOdds'][book['title']] = book['markets'][0]['outcomes'][i]['price'] #make a new key value in gameData['bookOdds] with the name of the book, the value will be equal to the price of that bet
    
    #find the average win odds
    gameData['avgWinOdds'] = sum(gameData['bookOdds'].values())/len(gameData['bookOdds']) #the sum of all the odds divided by the total number of odds gets us the average odds on the game
    
    #find best win odds
    highestOdds = -9999999999 #make super small to start, will be replaced
    highestOddsBook = ''
    for book in gameData['bookOdds']: #iterates over the key values. For each book we haev odds on
        if gameData['bookOdds'][book] > highestOdds: #see if that book's odds are higher then the highest we have so far
            highestOdds = gameData['bookOdds'][book] #if it is, then that is the new highest
            highestOddsBook = book #and store the name of the book too
    
    gameData['highestPayout'] = highestOdds #now that we have the highest, add that
    gameData['highestPayoutBook'] = highestOddsBook #same for it's corresponding book

    return gameData #return gameJsonData

#function that plots the data in a interactive plotly graph
def plotBooks(gameData):
    oddsPlot = px.scatter(y = gameData['bookOdds'].values(), x = gameData['bookOdds'].keys(), template = 'seaborn') #make the plot with that data
    oddsPlot.update_layout({'title':{'text':'Odds by Sportsbook on ' + gameData['desiredToWin'] + ' win vs ' +  gameData['opposingTeam']}}) #set the title
    oddsPlot.update_yaxes(title_text='Odds') #update y-axis title
    oddsPlot.update_xaxes(title_text='Books') #update x-axis title
    oddsPlot.show() #open the plot in browser

################################ MAIN FUNCTION #####################################
sport = userSportRequest()

jsonData = getJsonData(sport)
gameList = getGameList(jsonData)

gameTuple = userTeamRequest(gameList)
teamRequest = gameTuple[0]
gameCode = gameTuple[1]

if gameCode == 0: #if there is no data move on
    pass

else:
    gameData = getGameData(jsonData, gameCode, teamRequest)

    print('The average sportsbook has ' + str(gameData['avgWinOdds']) + ' odds on ' + gameData['desiredToWin'] + ' winning.')
    print('The best odds are from ' + gameData['highestPayoutBook'] + ' at ' + str(gameData['highestPayout']))

    if len(gameData['bookOdds']) > 1:
        print('would you like to see a chart of all the odds? (Y/N)')
        chartQ = input('> ')
        if chartQ == 'Y':
            plotBooks(gameData)
