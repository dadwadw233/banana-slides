import requests
import time
import sys
import json

BASE_URL = "http://localhost:5000/api"
# Use a random email to avoid collision
EMAIL = f"test_e2e_{int(time.time())}@gmail.com"
PASSWORD = "password123"

def log(msg):
    print(f"[E2E] {msg}")

def check(response, expected_code=None):
    if expected_code and response.status_code != expected_code:
        log(f"FAILED: {response.status_code} != {expected_code}")
        log(f"Response: {response.text}")
        sys.exit(1)
    if response.status_code >= 400:
        log(f"API Error: {response.status_code}")
        log(f"Response: {response.text}")
        sys.exit(1)
    return response.json()

def main():
    try:
        # 1. Register
        log(f"Registering user {EMAIL}...")
        resp = requests.post(f"{BASE_URL}/auth/register", json={"email": EMAIL, "password": PASSWORD})
        # Register returns 201 Created or 200 OK depending on implementation
        if resp.status_code not in [200, 201]:
            log(f"FAILED: {resp.status_code}")
            log(resp.text)
            sys.exit(1)
        data = resp.json()
        token = data['data']['access_token']
        user_id = data['data']['user']['id']
        log(f"User registered: ID={user_id}")

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Check initial quota
        log("Checking quota...")
        resp = requests.get(f"{BASE_URL}/quota/balance", headers=headers)
        data = check(resp, 200)
        balance = data['data']['balance']
        log(f"Initial balance: {balance}")
        
        # 3. Create Project
        log("Creating project...")
        resp = requests.post(f"{BASE_URL}/projects", json={
            "creation_type": "idea",
            "idea_prompt": "A presentation about AI features",
            "template_style": "Minimalist blue style"
        }, headers=headers)
        data = check(resp, 201)
        project_id = data['data']['project_id']
        log(f"Project created: {project_id}")

        # 4. Generate Outline (Free)
        log("Generating outline...")
        resp = requests.post(f"{BASE_URL}/projects/{project_id}/generate/outline", json={
            "idea_prompt": "A presentation about AI features"
        }, headers=headers)
        check(resp, 200)
        log("Outline generated")

        # Check quota didn't change
        resp = requests.get(f"{BASE_URL}/quota/balance", headers=headers)
        new_balance = check(resp)['data']['balance']
        if new_balance != balance:
            log(f"WARNING: Quota changed from {balance} to {new_balance} after outline (should be free)")
        else:
            log("Quota unchanged (correct)")

        # 5. Generate Descriptions
        # First get pages to know count
        resp = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
        project_data = check(resp)['data']
        pages = project_data['pages']
        page_count = len(pages)
        log(f"Project has {page_count} pages")

        log("Generating descriptions...")
        resp = requests.post(f"{BASE_URL}/projects/{project_id}/generate/descriptions", json={}, headers=headers)
        task_data = check(resp, 202)['data']
        task_id = task_data['task_id']
        
        # Poll task
        log(f"Polling description task {task_id}...")
        while True:
            resp = requests.get(f"{BASE_URL}/projects/{project_id}/tasks/{task_id}", headers=headers)
            task = check(resp)['data']
            if task['status'] == 'COMPLETED':
                break
            if task['status'] == 'FAILED':
                log(f"Task failed: {task.get('error_message')}")
                break
            time.sleep(1)
        
        log(f"Descriptions task status: {task['status']}")

        # Check quota consumption
        resp = requests.get(f"{BASE_URL}/quota/balance", headers=headers)
        new_balance_2 = check(resp)['data']['balance']
        log(f"Balance after description: {new_balance_2}")
        consumed = new_balance - new_balance_2
        log(f"Consumed for descriptions: {consumed}")

        # 6. Generate Single Image (1.0)
        if pages:
            page_id = pages[0]['page_id']
            log(f"Generating image for page {page_id}...")
            resp = requests.post(f"{BASE_URL}/projects/{project_id}/pages/{page_id}/generate/image", json={"use_template": False}, headers=headers)
            task_data = check(resp, 202)['data']
            task_id = task_data['task_id']
            
            # Poll task
            log(f"Polling image task {task_id}...")
            while True:
                resp = requests.get(f"{BASE_URL}/projects/{project_id}/tasks/{task_id}", headers=headers)
                task = check(resp)['data']
                if task['status'] == 'COMPLETED':
                    break
                if task['status'] == 'FAILED':
                    log(f"Task failed: {task.get('error_message')}")
                    break
                time.sleep(1)
                
            log(f"Image task status: {task['status']}")
            
            # Check quota
            resp = requests.get(f"{BASE_URL}/quota/balance", headers=headers)
            final_balance = check(resp)['data']['balance']
            log(f"Final balance: {final_balance}")
            
            if task['status'] == 'COMPLETED':
                diff = new_balance_2 - final_balance
                log(f"Consumed for 1 image: {diff}")
                if diff == 1:
                    log("SUCCESS: Image generation consumed 1 quota")
                else:
                    log(f"WARNING: Image generation consumed {diff} quota")
        
    except Exception as e:
        log(f"Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
