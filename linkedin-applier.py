# LinkedBot.py
#
# how this works
#  - there's 'browser' object that persists and gets passed around, content of its browser.page_source changes as we make GET requests
#  - linkedin paginates job pages every 25 listings, the 25 listings don't appear immediately, they are lazy loaded, to get around this JS we scroll to bottom
#  - linkedin GET query: "&start=x*25" is what allows you to load x page, "&f_LF=f_AL" shows only "Easy Apply" listings

import argparse, os, time
import urllib, random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions
from bs4 import BeautifulSoup

url_job_pages = 'https://www.linkedin.com/jobs/search/?distance=25&f_LF=f_AL&keywords=linux%20AND%20python&location=Greater%20Chicago%20Area&locationId=us%3A14'
SCRAPE_RECOMMENDED_JOBS = False

def get_job_links(page):
	links = []
	for link in page.find_all('a'):
		url = link.get('href')
		if url:		
			if '/jobs/view/' in url:
				path = urllib.parse.urlparse(url).path   # extract path from url, e.g. only '/jobs/view/942882320/'
				links.append(path)
	return links

def job_traverse_all_pages(browser, url, current_page=0):
	browser.get(url)
	jsScrollToBottom = '''
		 var jobPane = $(".jobs-search-results");
		 jobPane.animate({scrollTop: jobPane.prop("scrollHeight")}, 1000);
		 '''    										 # linkedin won't show you up to 25 job listings right away due to disgusting JS infested UI design
	browser.execute_script(jsScrollToBottom)
	time.sleep(1.0)
	page = BeautifulSoup(browser.page_source, features="html.parser")

	links = list(set(get_job_links(page)))				 # list(set(foo)) removes duplicates
	url_nextpage = url_job_pages + "&start=" + str(current_page * 25)  # linkedin paginates its jobs every 25 listings
	current_page += 1
	time.sleep(random.uniform(0.2,0.9))                  # random sleep

	if len(links) < 25:									 # if there's less than 25 job listings then we assume there's no next page
		return links
	else:
		return links + job_traverse_all_pages(browser, url_nextpage, current_page)

def job_landing_page(browser):
	url_landing_page = 'https://www.linkedin.com/jobs/'  # among things contains linkedin's recommended jobs
	jobList = []

	if SCRAPE_RECOMMENDED_JOBS:
		browser.get(url_landing_page)
		page = BeautifulSoup(browser.page_source, features="html.parser")
		jobList = get_job_links(page)                    # initial population, from now on we will concat '/jobs/view/*' urls to jobList list

	jobList += job_traverse_all_pages(browser, url_job_pages)

	return jobList

def get_button(browser, tag, button_name):
    ElementsList = browser.find_elements_by_tag_name(tag)
    for x in ElementsList:
        try:
        	if str(x.text) == button_name:
        		return x
        except exceptions.StaleElementReferenceException:
            pass

def job_bot(browser):
	jobList = job_landing_page(browser)
	count = 0

	for job in jobList:
		time.sleep(random.uniform(2.0, 5.0))
		browser.get("https://www.linkedin.com" + job)

		# apply for job
		easyApplyButton = get_button(browser, 'span', 'Easy Apply')
		if easyApplyButton == None:
			continue  # you might have already applied for this job, hence apply button is missing
		easyApplyButton.click()
		time.sleep(0.5)
		#submitButton = browser.find_elements_by_xpath("//*[contains(text(), 'Submit')]")
		submitButton = get_button(browser, 'button', 'Submit application')
		if submitButton == None:
			print("[-] Could not apply for " + job + " | " + browser.title)
			continue
		else:
			submitButton.click()
			count += 1
			print("[+] Applied:  " + browser.title + "\n(" + str(count) + "/" + str(len(jobList)) + ") Applied/Queue)")

		time.sleep(5)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("email", help="linkedin email")
	parser.add_argument("password", help="linkedin password")
	args = parser.parse_args()

	browser = webdriver.Firefox()
	browser.get("https://linkedin.com/uas/login")

	emailElement = browser.find_element_by_id("username")
	emailElement.send_keys(args.email)
	passElement = browser.find_element_by_id("password")
	passElement.send_keys(args.password)
	passElement.submit()
	time.sleep(5)

	os.system('cls')
	print("[+] Logged in")
	job_bot(browser)
	browser.close()

if __name__ == '__main__':
	main()