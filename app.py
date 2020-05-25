import json
import threading
import time
import re

import pyttsx3
import speech_recognition as sr
import requests

API_KEY = "tm_473KmsHsg"
PROJECT_TOKEN = "tvJL0QT4jAdF"


class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.params = {
            "api_key": self.api_key
        }
        self.json_data = self.get_data()

    def get_data(self):
        response = requests.get(f"https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data",
                                params=self.params)
        return json.loads(response.text)

    def total_cases(self):
        total = self.json_data["total"]

        for content in total:
            if content["name"] == "Coronavirus Cases:":
                return content["value"]

    def total_deaths(self):
        total = self.json_data["total"]

        for content in total:
            if content["name"] == "Deaths:":
                return content["value"]

    def country_data(self, ctry):
        countries = self.json_data["country"]

        for country in countries:
            if ctry.lower() == country["name"].lower():
                return country if len(country) > 0 else "Country not found."

    def countries_list(self):
        return {countries["name"].lower() for countries in self.json_data["country"]}

    def request_new_data(self):
        requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params)

        thread = threading.Thread(target=self.update_data)
        thread.start()

    def update_data(self):
        # time.sleep(0.2)
        old_data = self.json_data

        while True:
            new_data = self.get_data()
            if new_data != old_data:
                self.json_data = new_data
                print("Data updated.")
                text_to_speech("Data updated.")
                break

            time.sleep(3)


# Voice assistant configurations
def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def speech_to_text():
    rec = sr.Recognizer()
    with sr.Microphone() as source:
        # calibrate the energy threshold for ambient noise levels
        rec.adjust_for_ambient_noise(source)

        try:
            print("Listening...\n")
            # You may not need phrase_time_limit
            audio = rec.listen(source, phrase_time_limit=5)
            recorded = str(rec.recognize_google(audio))

            return recorded.lower()
        except sr.RequestError as re:
            print("Could not request voice results.", re)


# Create Data instance
data = Data(API_KEY, PROJECT_TOKEN)

# Voice commands
STOP_ASSISTANT = "stop"
UPDATE_DATA = "update"

# Commands patterns
TOTAL_PATTERNS = {
    re.compile("[\w\s]+ total [\w\s]+ cases"): data.total_cases,
    re.compile("[\w\s]+ total cases"): data.total_cases,
    re.compile("[\w\s]+ total [\w\s]+ deaths"): data.total_deaths,
    re.compile("[\w\s]+ total deaths"): data.total_deaths()
}

COUNTRY_PATTERNS = {
    re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.country_data(country)["total_cases"],
    re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.country_data(country)["total_deaths"],
}


def app():
    result = ""
    text_to_speech("Hello.")

    while True:
        try:
            query = speech_to_text()
            print(f"Query: {query.capitalize()}.")

            for pattern, function in TOTAL_PATTERNS.items():
                if pattern.match(query):
                    result = function
                    break
            for pattern, function in COUNTRY_PATTERNS.items():
                if pattern.match(query):
                    words = set(query.split(" "))
                    for country in data.countries_list():
                        if country in words:
                            result = function(country)
                            break

            if query == UPDATE_DATA:
                result = "Updating data"
                data.request_new_data()

            if result:
                print(f"Response: {result}.")
                text_to_speech(result)

            # Stop loop
            if query.find(STOP_ASSISTANT) != -1:
                print("Program closed.")
                break
        except sr.UnknownValueError as uve:
            print("Speech Recognition could not understand audio.", str(uve))
        except Exception as e:
            print("TypeError:", str(e))


app()
