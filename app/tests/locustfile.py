from locust import HttpUser, between, task
from json import JSONDecodeError
import random

event_id = 3

class Book(HttpUser):
    wait_time = between(1,5)

    @task
    def login(self):
        with self.client.post("/users/login", json={
            "identifier": "moheet",
            "password": "moheet"
        }, catch_response=True) as resp:
            try:
                token = resp.json()["data"]['token']
                self.token = token
            except JSONDecodeError:
                resp.failure("Could not decode response")
                return
            except KeyError:
                resp.failure("Response did not contain data")
                return

            if self.token != None:
                self.getSections()

    def getSections(self):
        if not self.token:
            return
        with self.client.get(
            f"/bookings/{event_id}/sections/",
            headers={
                "Authorization": f"Bearer {self.token}"
            },
            catch_response=True
        ) as resp:
            result = resp.json()
            numSec = len(result["data"])
            if numSec == 0:
                resp.success()
                return
            randInd = random.randint(0, numSec - 1)
            self.selectedSection = result["data"][randInd]["id"]

            if self.selectedSection != None:
                self.getSeat()
    
    def getSeat(self):
        if not self.token:
            return
        with self.client.get(
            f"/bookings/{event_id}/sections/{self.selectedSection}/seats?format=false",
            headers={
                "Authorization": f"Bearer {self.token}"
            },
            catch_response=True
        ) as resp:
            result = resp.json()
            numSea = len(result["data"])
            if numSea == 0:
                resp.success()
                return
            randInd = random.randint(0, numSea - 1)
            self.selectedSeat = result["data"][randInd]["seat_id"]

            if self.selectedSeat != None:
                self.book()
    

    def book(self):
        if not self.token:
            return
        with self.client.post(
            "/bookings/book",
            json={
                "section_id": self.selectedSection,
                "event_id": event_id,
                "seats": [self.selectedSeat]
            },
            headers={
                "Authorization": f"Bearer {self.token}"
            },
            catch_response=True
        ) as resp:
            if resp.status_code in (200, 201):
                print("Seat booked")
                resp.success()
            elif resp.status_code == 400:
                resp.success()
            else:
                resp.failure(f"Unexpected error: {resp.status_code}")

    @task
    def dummy(self):
        pass