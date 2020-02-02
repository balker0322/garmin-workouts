import json
import re

import requests


class GarminClient(object):
    SSO_LOGIN_URL = "https://sso.garmin.com/sso/signin"
    WORKOUT_SERVICE_URL = "https://connect.garmin.com/modern/proxy/workout-service"

    REQUIRED_HEADERS = {
        "Referer": "https://connect.garmin.com/modern/workouts",
        "nk": "NT"
    }

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):
        self.session = requests.Session()
        self._authenticate()

    def disconnect(self):
        if self.session:
            self.session.close()
            self.session = None

    def list_workouts(self):
        assert self.session

        response = self.session.get(GarminClient.WORKOUT_SERVICE_URL + "/workouts")
        response.raise_for_status()

        return json.loads(response.text)

    def get_workout(self, id):
        assert self.session

        response = self.session.get(GarminClient.WORKOUT_SERVICE_URL + "/workout/%s" % id)
        response.raise_for_status()

        return json.loads(response.text)

    def save_workout(self, workout):
        assert self.session

        response = self.session.post(GarminClient.WORKOUT_SERVICE_URL + "/workout",
                                     headers=GarminClient.REQUIRED_HEADERS, json=workout)
        response.raise_for_status()

        return json.loads(response.text)

    def delete_workout(self, id):
        assert self.session

        response = self.session.delete(GarminClient.WORKOUT_SERVICE_URL + "/workout/%s" % id,
                                       headers=GarminClient.REQUIRED_HEADERS)
        response.raise_for_status()

        return json.loads(response.text)

    def _authenticate(self):
        form_data = {
            "username": self.username,
            "password": self.password,
            "embed": "false"
        }
        request_params = {
            "service": "https://connect.garmin.com/modern"
        }
        headers = {'origin': 'https://sso.garmin.com'}

        auth_response = self.session.post(
            GarminClient.SSO_LOGIN_URL, headers=headers, params=request_params, data=form_data)
        auth_response.raise_for_status()

        auth_ticket_url = self._extract_auth_ticket_url(auth_response.text)

        response = self.session.get(auth_ticket_url)
        response.raise_for_status()

    @staticmethod
    def _extract_auth_ticket_url(auth_response):
        match = re.search(r'response_url\s*=\s*"(https:[^"]+)"', auth_response)
        if not match:
            raise Exception("Unable to extract auth ticket URL from:\n%s" % auth_response)
        auth_ticket_url = match.group(1).replace("\\", "")
        return auth_ticket_url