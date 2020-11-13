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

INTERNET = True
LIST_DF = []
PLATFORM = ['xbl', 'psn', 'atvi', 'battlenet']
REGION = ['us', 'ca']
LIST_URL = []
PAGE_LIMIT = True
LIST_DF = []
PATH = '/home/james/Downloads/chromedriver'
COUNT=0
SAVE_FILE = 'defaultSaveClickOnThis.csv'
LIST_LIFETIME_STATS = []
LIST_MATCH_NUM = []
LIST_RECENT_MATCHES = []
MATCH_RANGE = 6
STUDY_DEPTH = 1#hopouts

def urlExecutorProfiles(urls):
	if len(urls) > 0:						
		with ThreadPoolExecutor(max_workers=30) as executor:    
			checkInternet()
			executor.map(scrapeProfile, urls)

def scrapeListbox(list_box):
	global SAVE_FILE
	all_urls = []	
	list_box_get = list_box.get(0,END)
	for entry in list_box_get:
		print(entry)
		all_urls.append(entry)
	urlExecutorProfiles(all_urls)
	saveLifetimeStats(all_urls)
	urlExecutorMatches(all_urls)
	saveRecentMatches(all_urls)
	extractAdditionalProfiles()
	saveAdditionalProfiles()
	all_urls = profileNoMatches()#for i in range(STUDY_DEPTH),execute below lines
	urlExecutorMatchesLessDetail(all_urls)
	saveRecentMatchesLessDetail(all_urls)
	#extractAdditionalProfiles() #here, i should be saving in root that they're all 1, and then for the profiles i get here, 2, and so on, all the way up to 10 for exp_depth 10
	#saveAdditionalProfiles()
	
def checkInternet():
	global INTERNET
	while INTERNET == False:
		try:
			requests.get("http://google.com")
			INTERNET = True
		except:
			time.sleep(3)
			print('waited')

def scrapeProfile(url):
	global INTERNET
	global LIST_LIFETIME_STATS
	try:
		profile_stats = []
		page = requests.get(url)
		soup = BeautifulSoup(page.content,features = 'lxml')
		mydivs = soup.findAll("div", {"class": "numbers"})
		for div in mydivs:
			profile_stats.append(div.get_text())
	except:
		INTERNET = False
		print('Could not reach profile')
		pass
	LIST_LIFETIME_STATS.append(profile_stats)
	
def saveLifetimeStats(profile_urls):
	global SAVE_FILE
	global LIST_LIFETIME_STATS #lifetime stats need to be matched according to player names, not just placed into the column
	df = pandas.DataFrame()
	df = pandas.DataFrame({'Player' : profile_urls, 'Player Profile' : LIST_LIFETIME_STATS})
	LIST_LIFETIME_STATS = []
	master_df = pandas.read_csv(SAVE_FILE)
	master_df = master_df.combine_first(df)
	master_df.to_csv(SAVE_FILE)
	print('Saved Lifetime Stats')
	
def setFileName(file_name):
	global SAVE_FILE
	SAVE_FILE = file_name
	df = pandas.DataFrame(columns=['Match #','Player','Player Profile','Match Data','Roster Data','Root Match','Same Name'])
	df = df.append({'Match #' : None,'Player' : None, 'Player Profile' : None,'Match Data':None,'Roster Data':None,'Root Match':None,'Same Name':None},  ignore_index = True) 
	df.to_csv(SAVE_FILE)
	print('Initiated Save File')
	
def urlExecutorMatches(urls):
	global LIST_RECENT_MATCHES
	LIST_RECENT_MATCHES = []
	if len(urls) > 0:						
		with ThreadPoolExecutor(max_workers=2) as executor:    
			checkInternet()
			executor.map(scrapeMatch, urls)
			
def scrapeMatch(profile_url):
	global PATH
	global MATCH_RANGE
	global LIST_RECENT_MATCHES
	global INTERNET
	try:
		driver = webdriver.Chrome(PATH)
		url = profile_url.replace('overview','matches')
		driver.get(url)
		for i in range(1):
			element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "match__link")))
			ps = driver.find_elements_by_class_name('match__link')
			element = ps[i]
			match_time = BeautifulSoup(driver.page_source,'lxml').text.split('\n')#match time
			driver.execute_script("arguments[0].click()", element)
			element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "team__info")))
			content = driver.page_source
			team_list = []
			soup = BeautifulSoup(content,'lxml')
			mydivs = soup.findAll("div", {"class": "team card bordered responsive"})
			for div in mydivs:
				team_list_row = []
				team_info_div = div.find("div",{"class":"team__info"})
				team_list_row.append(team_info_div.text)
				team_players_div = div.findAll("div",{"class":"player__info"})
				for player in team_players_div:
					team_list_row.append(player.text)#needs something to check for if its the player themselves, could use match data and match placement
				team_list.append(team_list_row)
			LIST_RECENT_MATCHES.append([i,profile_url,match_time,team_list,'root']) #from the url, get player, match, and the two cols of match data, and then merge this data
			driver.back()
		driver.close()
		

	except:
		INTERNET = False
		
def urlExecutorMatchesLessDetail(urls):
	global LIST_RECENT_MATCHES
	LIST_RECENT_MATCHES = []
	if len(urls) > 0:						
		with ThreadPoolExecutor(max_workers=2) as executor:    
			checkInternet()
			executor.map(scrapeMatchLessDetail, urls)
		
def scrapeMatchLessDetail(profile_url):
	global PATH
	global LIST_RECENT_MATCHES
	try:
		driver = webdriver.Chrome(PATH)
		url = profile_url.replace('overview','matches')
		driver.get(url)
		element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "match__link")))
		match_time = BeautifulSoup(driver.page_source,'lxml').text.split('\n')
		driver.close()
	except:
		INTERNET = False
	LIST_RECENT_MATCHES.append([profile_url,match_time])
	
		
def saveRecentMatches(profile_urls):
	global LIST_RECENT_MATCHES
	save_file = pandas.read_csv(SAVE_FILE)
	df = pandas.DataFrame(LIST_RECENT_MATCHES,columns=['Match #','Player','Match Data','Roster Data','Root Match'])
	df['Roster Names'] = df['Roster Data'].apply(cleanRosterData)
	df['Match Data'] = df['Match Data'].apply(cleanMatchData)
	LIST_RECENT_MATCHES = []
	master_df = pandas.read_csv(SAVE_FILE)
	master_df = master_df.combine_first(df)
	master_df.to_csv(SAVE_FILE)   #so Ill make the dataframe with lots of empty values and then I'll use the combine first pandas function to update data stored in global variabls
	print('Saved Matches')
	
def saveRecentMatchesLessDetail(profile_urls):
	global LIST_RECENT_MATCHES
	save_file = pandas.read_csv(SAVE_FILE)
	df = pandas.DataFrame(LIST_RECENT_MATCHES,columns=['Player','Match Data'])
	df['Match Data'] = df['Match Data'].apply(cleanMatchData)
	checkList = df['Match Data'].to_list()
	for i in checkList:
		print(i)
	print(len(checkList))
	master_df = pandas.read_csv(SAVE_FILE)
	master_df = master_df.combine_first(df)
	master_df.to_csv(SAVE_FILE)   #so Ill make the dataframe with lots of empty values and then I'll use the combine first pandas function to update data stored in global variabls
	print('Saved Matches')
	
def cleanMatchData(match_list):
	start_index = [i for i, s in enumerate(match_list) if 'All Modes' in s]
	start_index = start_index[0] + 1
	end_index = [i for i, s in enumerate(match_list) if 'Load More Matches' in s]
	end_index = end_index[0]
	match_list = match_list[start_index:end_index]
	return match_list
	
def cleanRosterData(roster_data_list):
	roster_names = []
	for row in roster_data_list:
		for entry in row[1:]:
			name = entry.split('\n')[0].split(']')[-1].replace(' ','')  #here the clan tag is removed
			roster_names.append(name)  
	return roster_names 
	
def urlExecutorAdditionalProfiles(df_as_tuples):
	print('Extracting')						
	with ThreadPoolExecutor(max_workers=30) as executor:    
		checkInternet()
		executor.map(scrapeAdditionalProfile, df_as_tuples)
		
def scrapeAdditionalProfile(row):
	global INTERNET
	global LIST_LIFETIME_STATS
	try:
		profile_stats = []
		page = requests.get(row[0])
		soup = BeautifulSoup(page.content,features = 'lxml')
		mydivs = soup.findAll("div", {"class": "numbers"})
		for div in mydivs:#the main issue that needs fixing is the lifetime stats dont line up, plus the continue scrape buttons and whatnot
			profile_stats.append(div.get_text())
		if len(profile_stats) > 3:
			row_data = [row[0],profile_stats,row[1]]
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
	df_as_tuples = list(records)
	new_lists = []
	for row in df_as_tuples:
		try:
			for player in eval(row[2]):
				for platform in PLATFORM[:3]:
					new_lists.append(["https://cod.tracker.gg/warzone/profile/" + platform + "/" + player + "/overview",[row[0].split('/')[-2], row[1]]])
		except:
			pass
	print(len(new_lists))
	urlExecutorAdditionalProfiles(new_lists)

def saveAdditionalProfiles():
	global SAVE_FILE
	master_df = pandas.read_csv(SAVE_FILE)
	df = pandas.DataFrame(LIST_LIFETIME_STATS,columns =['Player','Player Profile','Root Match'])
	master_df = master_df.combine_first(df)
	master_df.to_csv(SAVE_FILE)
	print('Saved Opponent Profiles')
	
def profileNoMatches():
	global SAVE_FILE
	df = pandas.read_csv(SAVE_FILE)
	check_list = df['Player'].to_list()#should drop duplicate rows here
	df = df.loc[(df['Root Match'] != 'root')]
	df = df.drop_duplicates(subset='Player Profile', keep="first")
	profiles_needing_matches = df['Player'].to_list()
	return profiles_needing_matches
	
def leaderboardLister(percentage,listbox):
	leaderboard_list = []
	print('Getting Leaderboard')
	global REGION
	global PLATFORM
	for region in REGION:
		print(region)
		for platform in PLATFORM:
			list_url = []
			print(platform)
			for i in range(1,750):
				list_url.append('https://cod.tracker.gg/warzone/leaderboards/battle-royale/' + platform + '/KdRatio?country=' + region + '&page=' + str(i))
			partial_leaderboard_list = scrapeLeaderboard(list_url)
			leaderboard_list += partial_leaderboard_list
	saveLeaderboardData(leaderboard_list,listbox)
	
def saveLeaderboardData(leaderboard_list,listbox):
	global SAVE_FILE
	df = pandas.DataFrame(leaderboard_list,columns=['Rank', 'Player', 'K/D', 'Matches', 'Platform', 'Region'])
	df.to_csv(SAVE_FILE)
	print('Saved Leaderboard')
	loadUrls(listbox)


def scrapeLeaderboard(list_url):
	global COUNT
	partial_leaderboard_list = []
	for url in list_url:
		page = requests.get(url)
		soup = BeautifulSoup(page.content,features = 'lxml')
		table_rows = soup.find_all('tr')
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
			partial_leaderboard_list.append(row)
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
		listbox.insert(END, transformPlayerPlatform(player,platform,'overview'))
		
def popper(player_list):
	n = 100
	split_list = [player_list[index : index + n] for index in range(0, len(player_list), n)]
	scrape_list = []
	for sub_list in split_list:
		player = sub_list.pop()
		scrape_list.append(player)
	return scrape_list
	
	
def continueScrape(file_name,list_box):
	global LIST_LIFETIME_STATS
	global LIST_RECENT_MATCHES
	list_box.delete(0,END)
	df = pandas.read_csv(file_name)
	df = df.sort_values('K/D')
	players = df['Player'].to_list()
	platforms = df['Platform'].to_list()
	for start in range(2,len(players)//15):#can change start value here
		LIST_LIFETIME_STATS = []
		LIST_RECENT_MATCHES = []
		setFileName('AAAslicedStudy' + str(start) + '.csv')
		list_box.delete(0,END)
		for i in range(start,len(players),len(players)//15):
			player = players[i]
			platform = platforms[i]
			list_box.insert(END, transformPlayerPlatform(player,platform,'overview'))
		scrapeListbox(list_box)
	
	
	
	
	
	
	




























#########################################################APP##############################################################

def findSaveFiles(list_box):
	csv_s = [pth for pth in Path.cwd().iterdir() if pth.suffix == '.csv']
	for csv in csv_s:
		list_box.insert(END, str(csv).split('/')[-1])
		
def transformPlayerPlatform(player,platform,tag):
	player = player.replace('#','%23',1)
	return "https://cod.tracker.gg/warzone/profile/" + platform + "/" + player + "/" + tag
	
def playerOfInterest(player_name,platform_index,list_box):
	player_of_interest = player_name.get()
	list_box.insert(END, transformPlayerPlatform(player_of_interest,PLATFORM[platform_index],'overview'))
	
def setNumMatches(str_input):
	global MATCH_RANGE
	MATCH_RANGE = int(str_input)

def setExpDepth(str_input):
	global STUDY_DEPTH
	STUDY_DEPTH = int(str_input)
	
def delete(listbox):
	sel = listbox.curselection()
	for index in sel[::-1]:
		listbox.delete(index)

def startExp():
	small_font = font.Font(size=5)
	clearCanvas()
	
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
	select_button.pack()

def clearCanvas():
	global CANVAS
	CANVAS.destroy()
	CANVAS = Canvas(APP)
	CANVAS.pack()
	
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
