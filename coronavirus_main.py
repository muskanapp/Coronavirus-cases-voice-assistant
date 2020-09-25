import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import threading
import time

API_KEY='t7Mg-X8B09Gr'
PROJECT_TOKEN='tRw_7STSVYkv'
RUN_TOKEN='ty8W90qFxp5a'


class Data:
	def __init__(self, api_key, project_token):
		self.api_key = api_key
		self.project_token = project_token
		self.params = {
			"api_key": self.api_key
		}
		self.data = self.get_data()
    #get data of most recent run
	def get_data(self):
		response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data', params=self.params)
		data = json.loads(response.text)
		return data
    #get total no of coronavirus cases
	def get_total_cases(self):
		data = self.data['total']

		for content in data:
			if content['name'] == "Coronavirus Cases:":
				return content['value']
    #get total no of coronavirus deaths
	def get_total_deaths(self):
		data = self.data['total']

		for content in data:
			if content['name'] == "Deaths:":
				return content['value']

		return "0"
    #get no of cases and deaths by country
	def get_country_data(self, country):
		data = self.data["country"]

		for content in data:
			if content['name'].lower() == country.lower():
				return content

		return "0"
    # get a list of all the countries for which data is available on the website
	def get_list_of_countries(self):
		countries = []
		for country in self.data['country']:
			countries.append(country['name'].lower())

		return countries
    #update info
	def update_data(self):
		response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params)

		def poll():
			time.sleep(0.1)
			old_data = self.data
			while True:
				new_data = self.get_data()
				if new_data != old_data:  #Check if new data equals old data every 5 seconds
					self.data = new_data
					print("Data updated")
					break
				time.sleep(5)

        # Run the voice assistant on one thread and update the information on another
		t = threading.Thread(target=poll)
		t.start()

#Voice recognition
#Speak
def speak(text):
	engine = pyttsx3.init('sapi5')#initialize the python text to speech engine,either leave it blank or sapi5 in case of windows
	engine.say(text)
	engine.runAndWait()

#Listen
def get_audio():
	r = sr.Recognizer()
	with sr.Microphone() as source:
		audio = r.listen(source)
		said = ""

		try:
			said = r.recognize_google(audio)#Google to recognize the speech input
		except Exception as e:
			print("Exception:", str(e))

	return said.lower()


def main():
	print("Started Program")
	data = Data(API_KEY, PROJECT_TOKEN)
	END_PHRASE = "stop"
	country_list = data.get_list_of_countries()
    #Look for REGEX patterns matching to the words in the voice
	TOTAL_PATTERNS = {
					re.compile("[\w\s]+ total [\w\s]+ cases"):data.get_total_cases,
					re.compile("[\w\s]+ total cases"): data.get_total_cases,
                    re.compile("[\w\s]+ total [\w\s]+ deaths"): data.get_total_deaths,
                    re.compile("[\w\s]+ total deaths"): data.get_total_deaths
					}

	COUNTRY_PATTERNS = {
					re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['total_cases'],
                    re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths'],
					}
    #if you need to update data
	UPDATE_COMMAND = "update"

	while True:
		print("Listening...")
		text = get_audio()
		print(text)
		result = None

		for pattern, func in COUNTRY_PATTERNS.items(): # regex match and function calling for total cases and deaths worldwide
			if pattern.match(text):
				words = set(text.split(" "))
				for country in country_list:
					if country in words:
						result = func(country)
						break

		for pattern, func in TOTAL_PATTERNS.items(): # regex match and function calling for total cases and deaths in the country we input as speech
			if pattern.match(text):
				result = func()
				break

		if text == UPDATE_COMMAND: # when we say update the data gets updated
			result = "Data is being updated. This may take a moment!"
			data.update_data()

		if result:
			speak(result)
            

		if text.find(END_PHRASE) != -1:  # stop loop
			print("Stay Home Stay Safe\nExit")
			break
    
main()