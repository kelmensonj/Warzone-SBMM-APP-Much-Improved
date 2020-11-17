from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup 
import pandas
import requests
import time
import os
import re
import datetime
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import font
from pathlib import Path
from tkinter import *

INTERNET = True #there are a bunch of while loops that will scrape the internet while this is true, and wait while its false
LIST_DF = []
PLATFORM = ['xbl', 'psn', 'atvi', 'battlenet'] #you can add and remove platforms here. TODO: include platform selection in GUI
REGION = ['us', 'ca'] #on codtracker there are hundreds of regions. I'm using USA and Canada, but there's Costa Rica and hundreds more
LIST_URL = []
PAGE_LIMIT = True #this global variable is used while scraping the leaderboard. It'll get set to False if you've hit the last page of a leaderboard
LIST_DF = []
PATH = '/home/james/Downloads/chromedriver' #this is important. If you're on windows, you need to swap the slashes and fix this path
COUNT=0
SAVE_FILE = 'defaultSaveClickOnThis.csv' 
LIST_LIFETIME_STATS = []
LIST_MATCH_NUM = []
LIST_RECENT_MATCHES = []
MATCH_RANGE = 6
STUDY_DEPTH = 1 #TODO: really include hopouts. At the moment these are fairly broken, but the idea is to get the players in your match, the players in those
		#players matches, the players in those player's players' matches, and so on. 

def urlExecutorProfiles(urls):
	if len(urls) > 0:						
		with ThreadPoolExecutor(max_workers=30) as executor: #ThreadPoolExecutor objects allow for multithreading 
			checkInternet() #this isnt really needed here but doesn't hurt
			executor.map(scrapeProfile, urls) #very important line. 'urls' will often have lengths in the hundreds of thousands or millions
							  #that entire list is mapped to the scrapeProfile() function. No worries if you need to interrupt
							  #the scrape. You can pretty much pickup where you left off

def scrapeListbox(list_box):
	global SAVE_FILE
	all_urls = []	
	list_box_get = list_box.get(0,END) #using tkinter module to 'get' the contents of 'list_box'
	for entry in list_box_get:
		print(entry)
		all_urls.append(entry)
	urlExecutorProfiles(all_urls) #so this is messy. Its sort of the main function. Each of these functions below populate and alter global variables
	saveLifetimeStats(all_urls) #TODO: convert all the global variables and these functions into classes
	urlExecutorMatches(all_urls)
	saveRecentMatches(all_urls)
	extractAdditionalProfiles() #this line is important
	saveAdditionalProfiles()
	all_urls = profileNoMatches()#for i in range(STUDY_DEPTH),execute below lines. TODO: this line here is where hopout should be inserted
	urlExecutorMatchesLessDetail(all_urls) #so basically, you could do hopout 500 and it would possibly get you every player who's played today
	saveRecentMatchesLessDetail(all_urls)
	#extractAdditionalProfiles() #here, i should be saving in root that they're all 1, and then for the profiles i get here, 2, and so on, all the way up to 10 for exp_depth 10
	#saveAdditionalProfiles()
	
def checkInternet():
	global INTERNET
	while INTERNET == False: #important function here
		try:
			requests.get("http://google.com") #checkInternet() is called when an object fails to parse usually. If the 'requests' library
							  # successfully pings google.com, then the program can chalk the failed parse up to bad data
			INTERNET = True
		except:
			time.sleep(3) #and here, if google.com doesnt ping back, the exception is triggered and we sleep. So we keep sleeping and pinging google
				      #all the while pausing our threads' execution
			print('waited')

def scrapeProfile(url):
	global INTERNET
	global LIST_LIFETIME_STATS
	try:
		profile_stats = []
		page = requests.get(url) #here, this url is codtracker player profile. Their 'overview' page
		soup = BeautifulSoup(page.content,features = 'lxml')
		mydivs = soup.findAll("div", {"class": "numbers"}) #even though the class is 'numbers', you're still going to get the text labels. Wins, K/D, etc
		for div in mydivs:
			profile_stats.append(div.get_text()) #what we've done here is created a long list of individual lifetime stats
	except:
		INTERNET = False
		print('Could not reach profile')
		pass
	LIST_LIFETIME_STATS.append(profile_stats) #and now here we append it LIST_LIFETIME_STATS. I find this method very efficient and straightforward for creating
						  #dataframes. Each sublist is a row. Simple. Still, I'd appreciate if someone could tell me the best practices
	
def saveLifetimeStats(profile_urls):
	global SAVE_FILE
	global LIST_LIFETIME_STATS 
	df = pandas.DataFrame()
	df = pandas.DataFrame({'Player' : profile_urls, 'Player Profile' : LIST_LIFETIME_STATS}) #creating a temporary dataframe
	LIST_LIFETIME_STATS = [] #here we're gonna clear out LIST_LIFETIME_STATS so we can use the variable again when we look up opponent profiles, plus, ya know, hopout
	master_df = pandas.read_csv(SAVE_FILE) #SAVE_FILE is set from user input within the GUI. Regardless of the csv file selected, this should work
	master_df = master_df.combine_first(df) #combine first is a fantastic pandas function. I think its plenty fast. It's like using iloc and matching things up but better
	master_df.to_csv(SAVE_FILE) #now we've updated the save file
	print('Saved Lifetime Stats')
	
def setFileName(file_name):
	global SAVE_FILE
	SAVE_FILE = file_name #danger. This can overwrite your save file. The UI makes this unlikely but it could happen. TODO: detect overwrite and create auto backup
	df = pandas.DataFrame(columns=['Match #','Player','Player Profile','Match Data','Roster Data','Root Match','Same Name'])
	df = df.append({'Match #' : None,'Player' : None, 'Player Profile' : None,'Match Data':None,'Roster Data':None,'Root Match':None,'Same Name':None},  ignore_index = True) 
	df.to_csv(SAVE_FILE) #so, this creates an empty csv in order to make combine first always work, even if you start the scrape, immediately exit, and then continue scrape
	print('Initiated Save File')
	
def urlExecutorMatches(urls):
	global LIST_RECENT_MATCHES
	LIST_RECENT_MATCHES = [] #I clear this global here. I need to be more consistent with clearning globals. TODO: refactor everything into classes
	if len(urls) > 0:						
		with ThreadPoolExecutor(max_workers=2) as executor: #urlExecturoProfiles() is way faster because its just requests and html. For this one, we use 2 workers and selenium
			checkInternet() #kind of a useless line but doesnt really hurt. It would be annoying to start big scrapes and get nothing
			executor.map(scrapeMatch, urls) #extremely important line. This could be a million urls all mapped at once to scrapeMatch()
			
def scrapeMatch(profile_url):
	global PATH
	global MATCH_RANGE
	global LIST_RECENT_MATCHES
	global INTERNET
	try:
		driver = webdriver.Chrome(PATH) #here we open a browser. I could switch it to headless but I like the look with the browsers open
		url = profile_url.replace('overview','matches') #here we do a replace. Codtracker urls make this easy enough
		driver.get(url)
		for i in range(1): #TODO: get rid of this line. Its here because I used to use this line for match range. So maybe the line should stay
			element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "match__link"))) #important line. Waits until links appear
			ps = driver.find_elements_by_class_name('match__link') #then finds the links
			element = ps[i] #we only need the first match for my specific study, but its in this function you may want to make some alterations
					#I had trouble generalizing my code to whatever possible study you want to perform
					#I'm happy to alter my code, though, if you have a specific study in mind. THe first study I did, the one with the messy
					#code, I would have used for i in range(MATCH_RANGE), where MATCH_RANGE = 6. That way, you could get 6, even 20 recent
					#matches if you wanted. TODO: fix the MATCH_RANGE thing in the GUI and in this function
			match_time = BeautifulSoup(driver.page_source,'lxml').text.split('\n') #although the best data comes next, there's some data on this page
											       #so i grab the current text
			driver.execute_script("arguments[0].click()", element) #now we click that first element. Pretty magical selenium
			element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "team__info"))) #now we're off to a recent match
																 #and we await team__info
			content = driver.page_source #grab the html in the match page
			team_list = [] #for each match we create an empty list that will store that match's data
			soup = BeautifulSoup(content,'lxml')
			mydivs = soup.findAll("div", {"class": "team card bordered responsive"}) #this class works for any game mode, solos, special game modes
			for div in mydivs: #the team card is worthless, its the team__info and player__info we want
				team_list_row = []
				team_info_div = div.find("div",{"class":"team__info"}) #this is team placement, team stats for that match
				team_list_row.append(team_info_div.text) #we store the team__info
				team_players_div = div.findAll("div",{"class":"player__info"}) #now we get the player divs
				for player in team_players_div:
					team_list_row.append(player.text)#and now we add each player to the team_list_row. Each player comes with more match stats
				team_list.append(team_list_row) #and finally, for each team card, we append to the team_list
			LIST_RECENT_MATCHES.append([i,profile_url,match_time,team_list,'root']) #now we use a global to store our row of data, the match number,the url this stuff came from
												#various stats we will finish parsing later, as well as a placeholder 'root'
			driver.back() #selenium is magic and hits the back button, realizing now that this could probably be deleted since the match range is 1
		driver.close() #now the driver closes. We could just get the next url in the current driver, so yeah, driver.back() and driver.close() are pointlessly slowing things down
			       #TODO: check if MATCH_RANGE is 1, if so, dont driver.back(). Also, don't close the driver, get the next url directly from current driver

	except:
		INTERNET = False #if any of the parsing fails then the internet is checked. It's okay if there was some error because the missing data can be filled
				 #in later on another pass while checking for profiles without matches
		
def urlExecutorMatchesLessDetail(urls):
	global LIST_RECENT_MATCHES
	LIST_RECENT_MATCHES = []
	if len(urls) > 0:						
		with ThreadPoolExecutor(max_workers=2) as executor: #for my specific study I wanted match times and placement in order to study player attrition
			checkInternet()		#but you might not need this function
			executor.map(scrapeMatchLessDetail, urls) #TODO: make this a checkbox, getting match times for final hopout
		
def scrapeMatchLessDetail(profile_url):
	global PATH
	global LIST_RECENT_MATCHES
	try:
		driver = webdriver.Chrome(PATH)
		url = profile_url.replace('overview','matches')
		driver.get(url)
		element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "match__link")))
		match_time = BeautifulSoup(driver.page_source,'lxml').text.split('\n') #this is just getting some basic data for the furthest hopped out players
		driver.close() #TODO: don't close drivers if there are still urls qued up, reuse the driver for speed
	except:
		INTERNET = False #if above parse fails internet is checked
	LIST_RECENT_MATCHES.append([profile_url,match_time]) #and here its the typical data preparation for creating the pandas DataFrame
	
		
def saveRecentMatches(profile_urls):
	global LIST_RECENT_MATCHES
	save_file = pandas.read_csv(SAVE_FILE)
	df = pandas.DataFrame(LIST_RECENT_MATCHES,columns=['Match #','Player','Match Data','Roster Data','Root Match']) #creating a temporary DataFrame
	df['Roster Names'] = df['Roster Data'].apply(cleanRosterData)
	df['Match Data'] = df['Match Data'].apply(cleanMatchData) #applying some parsing functions to some columns
	LIST_RECENT_MATCHES = [] #clearing LIST_RECENT_MATCHES
	master_df = pandas.read_csv(SAVE_FILE) #loading the master DataFrame
	master_df = master_df.combine_first(df) #again, that magical combine_first. It basically finds the overlap
	master_df.to_csv(SAVE_FILE)  
	print('Saved Matches')
	
def saveRecentMatchesLessDetail(profile_urls):
	global LIST_RECENT_MATCHES
	save_file = pandas.read_csv(SAVE_FILE) #TODO: Make these saves better. More based on timing and less based on what code has been executed
	df = pandas.DataFrame(LIST_RECENT_MATCHES,columns=['Player','Match Data']) #so these are just the most hopped out players
	df['Match Data'] = df['Match Data'].apply(cleanMatchData) #and we're cleaning a column
	checkList = df['Match Data'].to_list()
	for i in checkList:
		print(i)
	print(len(checkList))
	master_df = pandas.read_csv(SAVE_FILE)
	master_df = master_df.combine_first(df)
	master_df.to_csv(SAVE_FILE)   
	print('Saved Matches')
	
def cleanMatchData(match_list):
	start_index = [i for i, s in enumerate(match_list) if 'All Modes' in s] #the match list is a bunch of match times and some basic stats, each player will have a list of around 20
	start_index = start_index[0] + 1
	end_index = [i for i, s in enumerate(match_list) if 'Load More Matches' in s] #here we're just finding some indices that fit the pattern of denoting the non useless text data
	end_index = end_index[0]
	match_list = match_list[start_index:end_index] #now we're going from 'All Modes' to 'Load More Matches'. What's in between is numbers
	return match_list
	
def cleanRosterData(roster_data_list):
	roster_names = []
	for row in roster_data_list: #each row is a player and their match performance
		for entry in row[1:]: #the first row is useless text
			name = entry.split('\n')[0].split(']')[-1].replace(' ','') #here we get each player in a team list (separated by newlines) and remove clan tags
			roster_names.append(name) #so we're getting a list of all the names in each roster, plus their match performance 
	return roster_names 
	
def urlExecutorAdditionalProfiles(df_as_tuples):
	print('Extracting')						
	with ThreadPoolExecutor(max_workers=30) as executor: #this function is called when you need more lifetime stat data, but you're not fully hopping out
		checkInternet()
		executor.map(scrapeAdditionalProfile, df_as_tuples)
		
def scrapeAdditionalProfile(row):
	global INTERNET
	global LIST_LIFETIME_STATS
	try:
		profile_stats = []
		page = requests.get(row[0])
		soup = BeautifulSoup(page.content,features = 'lxml')
		mydivs = soup.findAll("div", {"class": "numbers"}) #because this is just requests we're fast here, just getting lifetime stats
		for div in mydivs:
			profile_stats.append(div.get_text())
		if len(profile_stats) > 3:
			row_data = [row[0],profile_stats,row[1]] #we do this so we can check our work later. Creating a column of player names, their lifetime stats, and who's match they played in
			LIST_LIFETIME_STATS.append(row_data)
	except:
		INTERNET = False
		print('Could not reach profile')
		pass
	
def extractAdditionalProfiles():
	global SAVE_FILE
	global LIST_LIFETIME_STATS
	LIST_LIFETIME_STATS = []
	df = pandas.read_csv(SAVE_FILE)
	df = df[['Player','Match #', 'Roster Names']]
	records = df.to_records(index=False) 
	df_as_tuples = list(records) #I did this because I wanted to keep track of what lifetime stats were in who's lobby
	new_lists = []
	for row in df_as_tuples:
		try:
			for player in eval(row[2]):
				for platform in PLATFORM[:3]: #this is where we guess player profile urls
					new_lists.append(["https://cod.tracker.gg/warzone/profile/" + platform + "/" + player + "/overview",[row[0].split('/')[-2], row[1]]])
		except: #each name in the list of roster names may or may not be a real player. This is where we check. So most of these will return url errors
			pass
	print(len(new_lists))
	urlExecutorAdditionalProfiles(new_lists)

def saveAdditionalProfiles():
	global SAVE_FILE
	master_df = pandas.read_csv(SAVE_FILE)
	df = pandas.DataFrame(LIST_LIFETIME_STATS,columns =['Player','Player Profile','Root Match'])
	master_df = master_df.combine_first(df) #similar to a function before, just referencing different columns
	master_df.to_csv(SAVE_FILE)
	print('Saved Opponent Profiles')
	
def profileNoMatches():
	global SAVE_FILE
	df = pandas.read_csv(SAVE_FILE)
	check_list = df['Player'].to_list()
	df = df.loc[(df['Root Match'] != 'root')]
	df = df.drop_duplicates(subset='Player Profile', keep="first")
	profiles_needing_matches = df['Player'].to_list()
	return profiles_needing_matches #here we're returning a list of all the players who aren't 'root' tagged
	
def leaderboardLister(percentage,listbox):
	leaderboard_list = []
	print('Getting Leaderboard')
	global REGION
	global PLATFORM
	for region in REGION:
		print(region)
		for platform in PLATFORM: #this function will get you leaderboard data for whatever REGION list and PLATFORM list you want
			list_url = []
			print(platform)
			for i in range(1,750): #the highest page number on codtracker for leaderboards is around 500 but could go up
				list_url.append('https://cod.tracker.gg/warzone/leaderboards/battle-royale/' + platform + '/KdRatio?country=' + region + '&page=' + str(i))
			partial_leaderboard_list = scrapeLeaderboard(list_url) #I made this single threaded, its still fast
			leaderboard_list += partial_leaderboard_list
	saveLeaderboardData(leaderboard_list,listbox)
	
def saveLeaderboardData(leaderboard_list,listbox):
	global SAVE_FILE
	df = pandas.DataFrame(leaderboard_list,columns=['Rank', 'Player', 'K/D', 'Matches', 'Platform', 'Region'])
	df.to_csv(SAVE_FILE)
	print('Saved Leaderboard') #again, similar to before
	loadUrls(listbox) #this line is weird but it will allow you to do a huge scrape


def scrapeLeaderboard(list_url):
	global COUNT
	partial_leaderboard_list = []
	for url in list_url:
		page = requests.get(url)
		soup = BeautifulSoup(page.content,features = 'lxml') #typical parsing in this function
		table_rows = soup.find_all('tr') #leaderboards on codtracker are neat
		if len(table_rows) == 0:
			print('Breaking')
			break
				
		for tr in table_rows[1:]:
			td = tr.find_all('td')
			row = [i.text for i in td]
			row = [i.replace('\n', ' ').replace('\r', '').replace(' ', '') for i in row]
			del row[2]
			row.append(url.split('/')[-2])
			row.append(url.split('&')[0][-2:])
			partial_leaderboard_list.append(row) #basic cleaning and parsing here. Sure it could be faster
			COUNT+=1
			print(COUNT) 
			
	return partial_leaderboard_list
	
def loadUrls(listbox):
	global SAVE_FILE
	df = pandas.read_csv(SAVE_FILE)
	df = df.sort_values('K/D')
	players = df['Player'].to_list()
	platforms = df['Platform'].to_list()
	for i in range(1,len(players),30):
		player = players[i]
		platform = platforms[i]
		listbox.insert(END, transformPlayerPlatform(player,platform,'overview')) #this function is called after scraping your leaderboards, and prepares you
											 #to scrape every leaderboard player's more complete match data
		
def popper(player_list):
	n = 100
	split_list = [player_list[index : index + n] for index in range(0, len(player_list), n)]
	scrape_list = []
	for sub_list in split_list: #TODO: include this as a button so you can select a sample from the leaderboard for more in depth data scraping
		player = sub_list.pop()
		scrape_list.append(player) #this function isn't used for anything, but the intention is to allow you to scrape, say, every thousandth player on the leaderboard's match data
	return scrape_list
	
	
def continueScrape(file_name,list_box):
	global LIST_LIFETIME_STATS
	global LIST_RECENT_MATCHES
	list_box.delete(0,END)
	df = pandas.read_csv(file_name)
	df = df.sort_values('K/D')
	players = df['Player'].to_list()
	platforms = df['Platform'].to_list()
	for start in range(2,len(players)//15): #the continueScrape() function only really works if you've broken up your scrape into the leaderboard scrape, and the match scrape
		LIST_LIFETIME_STATS = [] #TODO: make the continueScrape() function more generalized
		LIST_RECENT_MATCHES = []
		setFileName('AAAslicedStudy' + str(start) + '.csv')
		list_box.delete(0,END)
		for i in range(start,len(players),len(players)//15):
			player = players[i]
			platform = platforms[i]
			list_box.insert(END, transformPlayerPlatform(player,platform,'overview'))
		scrapeListbox(list_box) # back to scrapeListbox(), treats the leaderboard urls as if you inputted them manually
	
	
	
	
	
	
	




























#########################################################APP##############################################################

def findSaveFiles(list_box):
	csv_s = [pth for pth in Path.cwd().iterdir() if pth.suffix == '.csv']
	for csv in csv_s:
		list_box.insert(END, str(csv).split('/')[-1]) #this function is fun, just adds to the listbox all the files in your current directory that end in '.csv'
		
def transformPlayerPlatform(player,platform,tag):
	player = player.replace('#','%23',1) #when querying a url you need to replace the '#' in player names with '%23'
	return "https://cod.tracker.gg/warzone/profile/" + platform + "/" + player + "/" + tag
	
def playerOfInterest(player_name,platform_index,list_box):
	player_of_interest = player_name.get()
	list_box.insert(END, transformPlayerPlatform(player_of_interest,PLATFORM[platform_index],'overview')) #just taking your typed input in the GUI and displaying it in listbox
	
def setNumMatches(str_input):
	global MATCH_RANGE
	MATCH_RANGE = int(str_input) #not really useful, but could be. TODO: make this work, make MATCH_RANGE work

def setExpDepth(str_input):
	global STUDY_DEPTH
	STUDY_DEPTH = int(str_input) #this is where you would set hopout. TODO: make hopout work, its cool
	
def delete(listbox):
	sel = listbox.curselection()
	for index in sel[::-1]: #iterates backwards
		listbox.delete(index) #you can delete what you've added in case of typos

def startExp(): #this is basic tkinter GUI stuff, just buttons, listboxes, and entry fields
	small_font = font.Font(size=5)
	clearCanvas() #I use clearCanvas() in order to refresh and clear out the UI
	
	project_name = StringVar()
	project_name_label = Label(CANVAS, text='Enter File Name', font=('bold', 12))
	project_name_label.pack()
	project_name_entry = Entry(CANVAS, textvariable=project_name)
	project_name_entry.pack()
	
	confirm_save_file_btn = Button(CANVAS, text='Confirm Save File', width=12, command=lambda: setFileName(project_name.get()))
	confirm_save_file_btn.pack()
	
	player_name = StringVar()
	player_name_label = Label(CANVAS, text='Player Name', font=('bold', 12))
	player_name_label.pack()
	player_name_entry = Entry(CANVAS, textvariable=player_name)
	player_name_entry.pack()
			
	xbox_btn = Button(CANVAS, text='Xbox', width=12, command=lambda: playerOfInterest(player_name,0,listbox))
	xbox_btn.pack()

	ps4_btn = Button(CANVAS, text='PlayStation', width=12, command=lambda: playerOfInterest(player_name,1,listbox))
	ps4_btn.pack()

	activision_btn = Button(CANVAS, text='Activision', width=12, command=lambda: playerOfInterest(player_name,2,listbox))
	activision_btn.pack()
			
	battlenet_btn = Button(CANVAS, text='Battlenet', width=12, command=lambda: playerOfInterest(player_name,3,listbox))
	battlenet_btn.pack()
	
	listbox = Listbox(CANVAS)
	listbox.config(width=60, height=15,selectmode=MULTIPLE,font=small_font)
	listbox.pack()
	
	scrollbar = Scrollbar(CANVAS)  
	scrollbar.pack(side = RIGHT, fill = BOTH) 
	listbox.config(yscrollcommand = scrollbar.set) 
	scrollbar.config(command = listbox.yview) 

	delete_btn = Button(CANVAS, text = 'Delete Selection', command=lambda: delete(listbox))
	delete_btn.pack()
	
	leaderboard_btn = Button(CANVAS, text='Leaderboard', width=12, command=lambda: leaderboardLister(1.0,listbox)) #this scrapes the leaderboard
	leaderboard_btn.pack()
	
	scrape_btn = Button(CANVAS, text='New Scrape', command=lambda: scrapeListbox(listbox)) #this scrapes the listbox
	scrape_btn.pack()
	
	num_matches = StringVar()
	num_matches_label = Label(CANVAS, text='Enter # of Matches', font=('bold', 12))
	num_matches_label.pack()
	num_matches_entry = Entry(CANVAS, textvariable=num_matches) # add buttons confirming that set globals
	num_matches_entry.pack()
	
	num_matches_btn = Button(CANVAS, text='Confirm # of Matches', command=lambda: setNumMatches(num_matches.get())) #this scrapes the listbox
	num_matches_btn.pack()
	
	experiment_depth = StringVar()
	experiment_depth_label = Label(CANVAS, text='Enter Experiment Depth', font=('bold', 12))
	experiment_depth_label.pack()
	experiment_depth_entry = Entry(CANVAS, textvariable=experiment_depth)
	experiment_depth_entry.pack()
	depth_btn = Button(CANVAS, text='Confirm Experiment Depth', command=lambda: setExpDepth(experiment_depth.get())) #this scrapes the listbox
	depth_btn.pack()
	
	
def loadExp():
	clearCanvas()
	small_font = font.Font(size=5)
	instruction_select_label = Label(CANVAS, text='Select the file you want to continue', font=('bold', 12))
	instruction_select_label.pack()
	listbox = Listbox(CANVAS)
	listbox.config(width=60, height=15,font=small_font)
	listbox.pack()
	scrollbar = Scrollbar(CANVAS)  
	scrollbar.pack(side = RIGHT, fill = BOTH) 
	listbox.config(yscrollcommand = scrollbar.set) 
	scrollbar.config(command = listbox.yview) 
	findSaveFiles(listbox)
	select_button = Button(CANVAS, text='Load Save and Continue Scraping', width=30,height=5,font=('bold', 12), command=lambda: continueScrape(listbox.get(ANCHOR),listbox))
	select_button.pack() #ANCHOR is a tkinter name, it refers to the current selection in the listbox

def clearCanvas():
	global CANVAS
	CANVAS.destroy()
	CANVAS = Canvas(APP)
	CANVAS.pack() #this function clears the UI and primes the APP for new buttons
	
def homeReset():
	global CANVAS
	global TOP_BUTTON
	global BOTTOM_BUTTON
	clearCanvas()
	TOP_BUTTON = Button(CANVAS, text='Start New Experiment', command=startExp)
	TOP_BUTTON.pack()

	BOTTOM_BUTTON = Button(CANVAS, text='Load Experiment', command=loadExp)
	BOTTOM_BUTTON.pack() 

APP = Tk()
CANVAS = Canvas(APP)
CANVAS.pack()
APP.title('SBMM Scraper')
APP.geometry('700x1200')
MENUBAR = Menu(APP)
MENUBAR.add_command(label="Home", command=homeReset)
APP.config(menu=MENUBAR)

TOP_BUTTON = Button(CANVAS, text='Start New Experiment', command=startExp)
TOP_BUTTON.pack()

BOTTOM_BUTTON = Button(CANVAS, text='Load Experiment', command=loadExp)
BOTTOM_BUTTON.pack()

APP.mainloop()

master = Tk()
