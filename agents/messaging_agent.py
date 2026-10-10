import http.client
import os
import urllib.parse
from agents.agent import Agent
from agents.deals import Opportunity


class MessagingAgent(Agent):
    """
    Messaging Agent pushes real-time alert notifications for high-margin deals
    via Pushover (push notification) or Twilio (SMS).
    """

    name = "Messaging Agent"
    color = Agent.WHITE

    def __init__(self):
        self.log("Messaging Agent is initializing")
        self.pushover_user = os.getenv('PUSHOVER_USER')
        self.pushover_token = os.getenv('PUSHOVER_TOKEN')
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_from = os.getenv('TWILIO_FROM')
        self.twilio_to = os.getenv('MY_PHONE_NUMBER')
        self.log("Messaging Agent is ready")

    def push(self, text: str) -> None:
        """Send push notification via Pushover API."""
        if not (self.pushover_user and self.pushover_token):
            self.log("Pushover credentials not configured, skipping push notification")
            return

        self.log("Sending Pushover notification")
        try:
            conn = http.client.HTTPSConnection("api.pushover.net:443", timeout=10)
            payload = urllib.parse.urlencode({
                "token": self.pushover_token,
                "user": self.pushover_user,
                "message": text,
                "sound": "cashregister",
            })
            headers = {"Content-type": "application/x-www-form-urlencoded"}
            conn.request("POST", "/1/messages.json", payload, headers)
            conn.getresponse()
            self.log("Pushover notification delivered")
        except Exception as e:
            self.log(f"Error sending Pushover notification: {e}")

    def sms(self, text: str) -> None:
        """Send SMS message via Twilio API."""
        if not (self.twilio_sid and self.twilio_token and self.twilio_from and self.twilio_to):
            return

        self.log("Sending Twilio SMS")
        try:
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)
            client.messages.create(
                from_=self.twilio_from,
                to=self.twilio_to,
                body=text,
            )
            self.log("Twilio SMS delivered")
        except Exception as e:
            self.log(f"Error sending Twilio SMS: {e}")

    def alert(self, opportunity: Opportunity) -> None:
        """Broadcast an alert for a high-value deal opportunity."""
        text = (
            f"Deal Alert! Listed: ${opportunity.deal.price:.2f}, "
            f"Estimated Value: ${opportunity.estimate:.2f}, "
            f"Discount: ${opportunity.discount:.2f}\n"
            f"Product: {opportunity.deal.product_description[:80]}...\n"
            f"Link: {opportunity.deal.url}"
        )
        self.push(text)
        self.sms(text)
        self.log("Alert broadcast completed")
