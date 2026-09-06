from locust import HttpUser, task
from json import JSONDecodeError
import random

class Book(HttpUser):
    def on_start(self) -> None:
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
                self.book()

    def book(self):
        if not self.token:
            return
        with self.client.post(
            "/bookings/book",
            json={
                "section_id": 1,
                "event_id": 1,
                "seats": [3]
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