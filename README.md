# Warzone-SBMM-APP-Much-Improved
Warning: this script is semi-broken. It's a web crawler and there have been updates to the website it crawled.

Below is the GUI:

![alt-text](https://github.com/kelmensonj/Warzone-SBMM-APP-Much-Improved/blob/main/sbmm.gif)

I used this web scraping script that I used in October, 2020 in order to take data from the popular website 'COD Tracker'. I'm not saying I caused it, but after I uploaded the video linked below and shared it on reddit, Activision itself revoked API access to third parties and COD Tracker completely revamped their site, thus breaking my web scraping script.

Here's the video: https://www.youtube.com/watch?v=016e0_qIGH8

In order to run the script there are some dependencies. For Ubuntu 21.04 I did:

```
pip3 install BeautifulSoup4
pip3 install selenium
pip3 install pandas
```

I was really proud of this script when I made it. Some features:
* There was fine control over the kind of data you wanted to collect. If you wanted to look at just some player profile data, it was possible. If you wanted to look at players' profiles in your matches, it was straightforward. If you wanted to look at players' profiles from player matches of players that were in your matches, it was easy. There was a field called 'Match Depth' that was pretty difficult to get functioning but once it worked I could study the players who played the players who played the players who played the players who played the players who played you. There's a word for it that web scrapers use when profiling individuals, like looking at friends of friends of friends of friends. Also, just remembered, it's called hopouts.
* Utilized Python, Beautiful Soup, Requests, Pandas, Selenium, and Multiprocessing in order to quickly and efficiently web scrape data on millions of players in the popular online game COD Warzone
* Inspired by a similar study performed by the youtuber Xclusive Ace, where data on just a few matches and players was collected, this study collected data on over 7,000 matches and hundreds of thousands of players. 
* Used requests and multiprocessing in order to scrape html as quickly as possible. 
* A lot of the data was served using AJAX, so I used Selenium in order to scrape the data only available after Javascript rendered. 
* Used an autosaving database. You could pause and restart whenever you want. 
* With the update, I added functionality such as a GUI. Also, the ability to search one player's entire match history, or a few players that you pick. You could also search the entire Leaderboard automatically in order to gather data on thousands of players in just a couple clicks.
* You could end the scrape at any time and pick up where you left off by clicking 'Continue Scrape'. Missing data would be filled in. 
* There was fine control over the kind of data you wanted to collect. If you wanted to look at just some player profile data, it was possible. If you wanted to look at players' profiles in your matches, it was straightforward. If you wanted to look at players' profiles from player matches of players that were in your matches, it was easy. There was a field called 'Match Depth' that was pretty difficult to get functioning but once it worked I could study the players who played the players who played the players who played the players who played the players who played you. There's a word for it that web scrapers use when profiling individuals, like looking at friends of friends of friends of friends. Also, just remembered, it's called hopouts.
* It was fast. I collected a lot of data that I'm happy to share directly. I'll scroll through a csv file below. This csv file contains not only profile data on well over 10,000 players, but also the profile data of all the players they faced (~100 per match) going 5-7 matches back. I used the data below for the video linked above. For just the Leaderboard it was even faster because selenium was not needed. 

![alt-text](https://github.com/kelmensonj/Warzone-SBMM-APP-Much-Improved/blob/main/sbmm_libre.gif)
