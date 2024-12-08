import json
from flask import Flask, request, jsonify
import requests
import datetime

app = Flask(__name__)

# Asana Personal Access Token
personal_access_token = "2/1208851767837894/1208859048533164:96ceacc43f7d5d1f82be460e581c4ebc"
project_gid = "1208851712245970"
headers = {
    "Authorization": f"Bearer {personal_access_token}",
    "Content-Type": "application/json"
}

# Register webhook function
def register_webhook():
    # Webhook registration URL
    url = f"https://app.asana.com/api/1.0/webhooks"

    # Payload for webhook creation
    data = {
        "data": {
            "resource": project_gid,  # The project ID you want to register the webhook for
            "target": "https://8ccc-2401-4900-16ff-59c9-dc15-f5cf-94ac-f596.ngrok-free.app/webhook"

            # The URL where your Flask app is listening (ngrok URL)
        }
    }

    # Register the webhook
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        print("Webhook successfully created.")
    else:
        print(f"Error registering webhook: {response.json()}")


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    # Handle Asana's webhook verification
    if "X-Hook-Secret" in request.headers:
        # Respond with the header required by Asana
        return "", 200, {"X-Hook-Secret": request.headers["X-Hook-Secret"]}

    # Log and acknowledge the incoming data (empty payload `{}` in this case)
    data = request.json
    print("Received data:", data)
    
    # Respond to Asana immediately
    return jsonify({"status": "success"}), 200

    if "events" in data:
        for event in data["events"]:
            # Handle new task creation
            if event["action"] == "added" and event["resource"]["resource_type"] == "task":
                task_gid = event["resource"]["gid"]
                print(f"New task created: {task_gid}")
                task_details = fetch_task_details(task_gid)
                custom_fields = task_details.get("custom_fields", [])
                priority = extract_priority(custom_fields)
                due_date = calculate_due_date(priority)
                if due_date:
                    print(f"Setting due date for task {task_gid}: {due_date}")
                    update_task_due_date(task_gid, due_date)

    return jsonify({"status": "success"}), 200


def fetch_task_details(task_gid):
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", {})
    else:
        print(f"Error fetching task details: {response.json()}")
        return {}


def update_task_due_date(task_gid, due_date):
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}"
    data = {"data": {"due_on": due_date}}
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Task {task_gid} updated with new due date: {due_date}")
    else:
        print(f"Error updating task {task_gid}: {response.json()}")


def calculate_due_date(priority):
    today = datetime.date.today()
    if priority == "high":
        return (today + datetime.timedelta(days=2)).isoformat()
    elif priority == "mid":
        return (today + datetime.timedelta(days=7)).isoformat()
    elif priority == "low":
        return (today + datetime.timedelta(days=14)).isoformat()
    else:
        return None


def extract_priority(custom_fields):
    for field in custom_fields:
        if field.get("name", "").lower() == "priority":
            return field.get("enum_value", {}).get("name", "low").lower()
    return "low"


if __name__ == "__main__":
    # Register webhook when the app starts
   # register_webhook()
    
    # Run Flask application
    app.run(port=5000, debug=True)
