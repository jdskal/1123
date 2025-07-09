import requests
import json
import time
import os
from datetime import datetime, timedelta

# Get the backend URL from the frontend .env file
def get_backend_url():
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.strip().split('=')[1].strip('"\'')
    raise Exception("Could not find REACT_APP_BACKEND_URL in frontend/.env")

# Base URL for API requests
BASE_URL = f"{get_backend_url()}/api"
print(f"Using API base URL: {BASE_URL}")

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Helper function to record test results
def record_test(name, passed, details=None):
    status = "PASSED" if passed else "FAILED"
    print(f"{status}: {name}")
    if details and not passed:
        print(f"  Details: {details}")
    
    test_results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details
    })
    
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1

# Helper function to make API requests with error handling
def api_request(method, endpoint, data=None, token=None, expected_status=None):
    # Ensure endpoint starts with a slash
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method.lower() == "get":
            response = requests.get(url, headers=headers)
        elif method.lower() == "post":
            response = requests.post(url, json=data, headers=headers)
        elif method.lower() == "put":
            response = requests.put(url, json=data, headers=headers)
        elif method.lower() == "delete":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if expected_status and response.status_code != expected_status:
            return False, f"Expected status {expected_status}, got {response.status_code}: {response.text}"
        
        return True, response
    except Exception as e:
        return False, f"Request error: {str(e)}"

# Test Authentication System
def test_init_admin():
    success, response = api_request("post", "/init-admin")
    
    if not success:
        record_test("Initialize Admin User", False, response)
        return None
    
    if response.status_code == 400 and "Admin user already exists" in response.text:
        record_test("Initialize Admin User", True, "Admin user already exists")
        # Continue with login since admin exists
        return test_login()
    
    if response.status_code == 200:
        record_test("Initialize Admin User", True)
        data = response.json()
        print(f"Admin created: {data.get('email')} / {data.get('password')}")
        # Continue with login using the created admin
        return test_login(data.get('email'), data.get('password'))
    
    record_test("Initialize Admin User", False, f"Unexpected response: {response.status_code} - {response.text}")
    return None

def test_login(email="admin@school.com", password="admin123"):
    login_data = {
        "email": email,
        "password": password
    }
    
    success, response = api_request("post", "/auth/login", login_data)
    
    if not success:
        record_test("Admin Login", False, response)
        return None
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        user = data.get("user")
        record_test("Admin Login", True)
        print(f"Logged in as: {user.get('email')} (Role: {user.get('role')})")
        return token
    
    record_test("Admin Login", False, f"Login failed: {response.status_code} - {response.text}")
    return None

def test_get_current_user(token):
    if not token:
        record_test("Get Current User", False, "No authentication token available")
        return
    
    success, response = api_request("get", "/auth/me", token=token)
    
    if not success:
        record_test("Get Current User", False, response)
        return
    
    if response.status_code == 200:
        user = response.json()
        record_test("Get Current User", True)
        print(f"Current user: {user.get('email')} (Role: {user.get('role')})")
        return user
    
    record_test("Get Current User", False, f"Failed: {response.status_code} - {response.text}")

def test_register_user(token):
    if not token:
        record_test("Register New User", False, "No authentication token available")
        return None
    
    # Create a unique email to avoid conflicts
    timestamp = int(time.time())
    user_data = {
        "email": f"teacher{timestamp}@school.com",
        "full_name": "Test Teacher",
        "password": "password123",
        "role": "editor"
    }
    
    success, response = api_request("post", "/auth/register", user_data, token)
    
    if not success:
        record_test("Register New User", False, response)
        return None
    
    if response.status_code == 200:
        user = response.json()
        record_test("Register New User", True)
        print(f"Created user: {user.get('email')} (Role: {user.get('role')})")
        return user
    
    record_test("Register New User", False, f"Failed: {response.status_code} - {response.text}")
    return None

# Test News Management
def test_create_news(token):
    if not token:
        record_test("Create News Article", False, "No authentication token available")
        return None
    
    news_data = {
        "title": "Test News Article",
        "content": "This is a test news article created by the automated test suite.",
        "excerpt": "Test news excerpt",
        "status": "draft"
    }
    
    success, response = api_request("post", "/news", news_data, token)
    
    if not success:
        record_test("Create News Article", False, response)
        return None
    
    if response.status_code == 200:
        news = response.json()
        record_test("Create News Article", True)
        print(f"Created news article: {news.get('id')} - {news.get('title')}")
        return news
    
    record_test("Create News Article", False, f"Failed: {response.status_code} - {response.text}")
    return None

def test_get_all_news(token):
    if not token:
        record_test("Get All News Articles", False, "No authentication token available")
        return
    
    success, response = api_request("get", "/news", token=token)
    
    if not success:
        record_test("Get All News Articles", False, response)
        return
    
    if response.status_code == 200:
        news_list = response.json()
        record_test("Get All News Articles", True)
        print(f"Retrieved {len(news_list)} news articles")
        return news_list
    
    record_test("Get All News Articles", False, f"Failed: {response.status_code} - {response.text}")

def test_get_news_by_id(token, news_id):
    if not token:
        record_test("Get News Article by ID", False, "No authentication token available")
        return None
    
    success, response = api_request("get", f"/news/{news_id}", token=token)
    
    if not success:
        record_test("Get News Article by ID", False, response)
        return None
    
    if response.status_code == 200:
        news = response.json()
        record_test("Get News Article by ID", True)
        print(f"Retrieved news article: {news.get('id')} - {news.get('title')}")
        return news
    
    record_test("Get News Article by ID", False, f"Failed: {response.status_code} - {response.text}")
    return None

def test_update_news(token, news_id):
    if not token:
        record_test("Update News Article", False, "No authentication token available")
        return None
    
    update_data = {
        "title": "Updated Test News Article",
        "content": "This news article has been updated by the automated test suite.",
        "status": "published"
    }
    
    success, response = api_request("put", f"/news/{news_id}", update_data, token)
    
    if not success:
        record_test("Update News Article", False, response)
        return None
    
    if response.status_code == 200:
        news = response.json()
        record_test("Update News Article", True)
        print(f"Updated news article: {news.get('id')} - {news.get('title')}")
        return news
    
    record_test("Update News Article", False, f"Failed: {response.status_code} - {response.text}")
    return None

def test_delete_news(token, news_id):
    if not token:
        record_test("Delete News Article", False, "No authentication token available")
        return False
    
    success, response = api_request("delete", f"/news/{news_id}", token=token)
    
    if not success:
        record_test("Delete News Article", False, response)
        return False
    
    if response.status_code == 200:
        record_test("Delete News Article", True)
        print(f"Deleted news article: {news_id}")
        return True
    
    record_test("Delete News Article", False, f"Failed: {response.status_code} - {response.text}")
    return False

# Test User Management
def test_get_all_users(token):
    if not token:
        record_test("Get All Users", False, "No authentication token available")
        return
    
    success, response = api_request("get", "/users", token=token)
    
    if not success:
        record_test("Get All Users", False, response)
        return
    
    if response.status_code == 200:
        users = response.json()
        record_test("Get All Users", True)
        print(f"Retrieved {len(users)} users")
        return users
    
    record_test("Get All Users", False, f"Failed: {response.status_code} - {response.text}")

def test_update_user(token, user_id):
    if not token:
        record_test("Update User", False, "No authentication token available")
        return None
    
    update_data = {
        "full_name": "Updated Test User",
        "role": "moderator"
    }
    
    success, response = api_request("put", f"/users/{user_id}", update_data, token)
    
    if not success:
        record_test("Update User", False, response)
        return None
    
    if response.status_code == 200:
        user = response.json()
        record_test("Update User", True)
        print(f"Updated user: {user.get('id')} - {user.get('full_name')} (Role: {user.get('role')})")
        return user
    
    record_test("Update User", False, f"Failed: {response.status_code} - {response.text}")
    return None

def test_delete_user(token, user_id):
    if not token:
        record_test("Delete User", False, "No authentication token available")
        return False
    
    success, response = api_request("delete", f"/users/{user_id}", token=token)
    
    if not success:
        record_test("Delete User", False, response)
        return False
    
    if response.status_code == 200:
        record_test("Delete User", True)
        print(f"Deleted user: {user_id}")
        return True
    
    record_test("Delete User", False, f"Failed: {response.status_code} - {response.text}")
    return False

# Test School Info Management
def test_school_info_crud(token):
    if not token:
        record_test("School Info CRUD", False, "No authentication token available")
        return
    
    # Create
    info_data = {
        "section": "about",
        "title": "About Our School",
        "content": "This is a test school info entry created by the automated test suite.",
        "order": 1
    }
    
    success, response = api_request("post", "/school-info", info_data, token)
    
    if not success:
        record_test("Create School Info", False, response)
        return
    
    if response.status_code == 200:
        info = response.json()
        info_id = info.get("id")
        record_test("Create School Info", True)
        print(f"Created school info: {info_id} - {info.get('title')}")
        
        # Get
        success, response = api_request("get", "/school-info", token=token)
        if success and response.status_code == 200:
            info_list = response.json()
            record_test("Get School Info", True)
            print(f"Retrieved {len(info_list)} school info entries")
        else:
            record_test("Get School Info", False, f"Failed: {response.status_code if success else response}")
        
        # Update
        update_data = {
            "title": "Updated School Info",
            "content": "This school info has been updated by the automated test suite."
        }
        
        success, response = api_request("put", f"/school-info/{info_id}", update_data, token)
        if success and response.status_code == 200:
            updated_info = response.json()
            record_test("Update School Info", True)
            print(f"Updated school info: {updated_info.get('id')} - {updated_info.get('title')}")
        else:
            record_test("Update School Info", False, f"Failed: {response.status_code if success else response}")
        
        # Delete
        success, response = api_request("delete", f"/school-info/{info_id}", token=token)
        if success and response.status_code == 200:
            record_test("Delete School Info", True)
            print(f"Deleted school info: {info_id}")
        else:
            record_test("Delete School Info", False, f"Failed: {response.status_code if success else response}")
    else:
        record_test("Create School Info", False, f"Failed: {response.status_code} - {response.text}")

# Test Gallery Management
def test_gallery_crud(token):
    if not token:
        record_test("Gallery CRUD", False, "No authentication token available")
        return
    
    # Create
    gallery_data = {
        "title": "Test Gallery Item",
        "description": "This is a test gallery item created by the automated test suite.",
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        "category": "test"
    }
    
    success, response = api_request("post", "/gallery", gallery_data, token)
    
    if not success:
        record_test("Create Gallery Item", False, response)
        return
    
    if response.status_code == 200:
        gallery = response.json()
        gallery_id = gallery.get("id")
        record_test("Create Gallery Item", True)
        print(f"Created gallery item: {gallery_id} - {gallery.get('title')}")
        
        # Get
        success, response = api_request("get", "/gallery", token=token)
        if success and response.status_code == 200:
            gallery_list = response.json()
            record_test("Get Gallery Items", True)
            print(f"Retrieved {len(gallery_list)} gallery items")
        else:
            record_test("Get Gallery Items", False, f"Failed: {response.status_code if success else response}")
        
        # Update
        update_data = {
            "title": "Updated Gallery Item",
            "description": "This gallery item has been updated by the automated test suite."
        }
        
        success, response = api_request("put", f"/gallery/{gallery_id}", update_data, token)
        if success and response.status_code == 200:
            updated_gallery = response.json()
            record_test("Update Gallery Item", True)
            print(f"Updated gallery item: {updated_gallery.get('id')} - {updated_gallery.get('title')}")
        else:
            record_test("Update Gallery Item", False, f"Failed: {response.status_code if success else response}")
        
        # Delete
        success, response = api_request("delete", f"/gallery/{gallery_id}", token=token)
        if success and response.status_code == 200:
            record_test("Delete Gallery Item", True)
            print(f"Deleted gallery item: {gallery_id}")
        else:
            record_test("Delete Gallery Item", False, f"Failed: {response.status_code if success else response}")
    else:
        record_test("Create Gallery Item", False, f"Failed: {response.status_code} - {response.text}")

# Test Contact Management
def test_contact_crud(token):
    if not token:
        record_test("Contact CRUD", False, "No authentication token available")
        return
    
    # Create
    contact_data = {
        "type": "email",
        "label": "Test Contact",
        "value": "test@school.com",
        "order": 1
    }
    
    success, response = api_request("post", "/contacts", contact_data, token)
    
    if not success:
        record_test("Create Contact", False, response)
        return
    
    if response.status_code == 200:
        contact = response.json()
        contact_id = contact.get("id")
        record_test("Create Contact", True)
        print(f"Created contact: {contact_id} - {contact.get('label')}")
        
        # Get
        success, response = api_request("get", "/contacts", token=token)
        if success and response.status_code == 200:
            contact_list = response.json()
            record_test("Get Contacts", True)
            print(f"Retrieved {len(contact_list)} contacts")
        else:
            record_test("Get Contacts", False, f"Failed: {response.status_code if success else response}")
        
        # Update
        update_data = {
            "label": "Updated Contact",
            "value": "updated@school.com"
        }
        
        success, response = api_request("put", f"/contacts/{contact_id}", update_data, token)
        if success and response.status_code == 200:
            updated_contact = response.json()
            record_test("Update Contact", True)
            print(f"Updated contact: {updated_contact.get('id')} - {updated_contact.get('label')}")
        else:
            record_test("Update Contact", False, f"Failed: {response.status_code if success else response}")
        
        # Delete
        success, response = api_request("delete", f"/contacts/{contact_id}", token=token)
        if success and response.status_code == 200:
            record_test("Delete Contact", True)
            print(f"Deleted contact: {contact_id}")
        else:
            record_test("Delete Contact", False, f"Failed: {response.status_code if success else response}")
    else:
        record_test("Create Contact", False, f"Failed: {response.status_code} - {response.text}")

# Test Schedule Management
def test_schedule_crud(token):
    if not token:
        record_test("Schedule CRUD", False, "No authentication token available")
        return
    
    # Create
    tomorrow = datetime.utcnow() + timedelta(days=1)
    schedule_data = {
        "title": "Test Schedule Item",
        "description": "This is a test schedule item created by the automated test suite.",
        "date": tomorrow.isoformat(),
        "time": "14:00",
        "location": "Test Location"
    }
    
    success, response = api_request("post", "/schedule", schedule_data, token)
    
    if not success:
        record_test("Create Schedule Item", False, response)
        return
    
    if response.status_code == 200:
        schedule = response.json()
        schedule_id = schedule.get("id")
        record_test("Create Schedule Item", True)
        print(f"Created schedule item: {schedule_id} - {schedule.get('title')}")
        
        # Get
        success, response = api_request("get", "/schedule", token=token)
        if success and response.status_code == 200:
            schedule_list = response.json()
            record_test("Get Schedule Items", True)
            print(f"Retrieved {len(schedule_list)} schedule items")
        else:
            record_test("Get Schedule Items", False, f"Failed: {response.status_code if success else response}")
        
        # Update
        update_data = {
            "title": "Updated Schedule Item",
            "description": "This schedule item has been updated by the automated test suite."
        }
        
        success, response = api_request("put", f"/schedule/{schedule_id}", update_data, token)
        if success and response.status_code == 200:
            updated_schedule = response.json()
            record_test("Update Schedule Item", True)
            print(f"Updated schedule item: {updated_schedule.get('id')} - {updated_schedule.get('title')}")
        else:
            record_test("Update Schedule Item", False, f"Failed: {response.status_code if success else response}")
        
        # Delete
        success, response = api_request("delete", f"/schedule/{schedule_id}", token=token)
        if success and response.status_code == 200:
            record_test("Delete Schedule Item", True)
            print(f"Deleted schedule item: {schedule_id}")
        else:
            record_test("Delete Schedule Item", False, f"Failed: {response.status_code if success else response}")
    else:
        record_test("Create Schedule Item", False, f"Failed: {response.status_code} - {response.text}")

# Test Comment Management
def test_comment_crud(token, news_id):
    if not news_id:
        record_test("Comment CRUD", False, "No news article available for comments")
        return
    
    # Create (public endpoint)
    comment_data = {
        "content": "This is a test comment created by the automated test suite.",
        "author_name": "Test User",
        "author_email": "test@example.com",
        "news_id": news_id
    }
    
    success, response = api_request("post", "/comments", comment_data)
    
    if not success:
        record_test("Create Comment", False, response)
        return
    
    if response.status_code == 200:
        comment = response.json()
        comment_id = comment.get("id")
        record_test("Create Comment", True)
        print(f"Created comment: {comment_id} for news: {news_id}")
        
        # Get (requires authentication)
        if token:
            success, response = api_request("get", f"/comments?news_id={news_id}", token=token)
            if success and response.status_code == 200:
                comment_list = response.json()
                record_test("Get Comments", True)
                print(f"Retrieved {len(comment_list)} comments")
            else:
                record_test("Get Comments", False, f"Failed: {response.status_code if success else response}")
            
            # Update (approve comment)
            update_data = {
                "is_approved": True
            }
            
            success, response = api_request("put", f"/comments/{comment_id}", update_data, token)
            if success and response.status_code == 200:
                updated_comment = response.json()
                record_test("Update Comment", True)
                print(f"Updated comment: {updated_comment.get('id')} - Approved: {updated_comment.get('is_approved')}")
            else:
                record_test("Update Comment", False, f"Failed: {response.status_code if success else response}")
            
            # Delete
            success, response = api_request("delete", f"/comments/{comment_id}", token=token)
            if success and response.status_code == 200:
                record_test("Delete Comment", True)
                print(f"Deleted comment: {comment_id}")
            else:
                record_test("Delete Comment", False, f"Failed: {response.status_code if success else response}")
        else:
            record_test("Get/Update/Delete Comments", False, "No authentication token available")
    else:
        record_test("Create Comment", False, f"Failed: {response.status_code} - {response.text}")

# Test Statistics
def test_get_stats(token):
    if not token:
        record_test("Get Site Statistics", False, "No authentication token available")
        return
    
    success, response = api_request("get", "/stats", token=token)
    
    if not success:
        record_test("Get Site Statistics", False, response)
        return
    
    if response.status_code == 200:
        stats = response.json()
        record_test("Get Site Statistics", True)
        print(f"Site statistics: {json.dumps(stats, indent=2)}")
        return stats
    
    record_test("Get Site Statistics", False, f"Failed: {response.status_code} - {response.text}")

# Run all tests
def run_tests():
    print("Starting API tests...")
    print(f"API Base URL: {BASE_URL}")
    
    # Authentication flow
    token = test_init_admin()
    if not token:
        print("Authentication failed, cannot continue with tests")
        return
    
    # Get current user
    current_user = test_get_current_user(token)
    
    # Register a new user
    new_user = test_register_user(token)
    
    # News management
    news = test_create_news(token)
    test_get_all_news(token)
    
    if news:
        news_id = news.get("id")
        test_get_news_by_id(token, news_id)
        test_update_news(token, news_id)
        
        # Test comments with the news article
        test_comment_crud(token, news_id)
        
        # Don't delete the news article yet, we'll do that at the end
    
    # User management
    test_get_all_users(token)
    
    if new_user:
        user_id = new_user.get("id")
        test_update_user(token, user_id)
        # Don't delete the user yet, we'll do that at the end
    
    # Content management
    test_school_info_crud(token)
    test_gallery_crud(token)
    test_contact_crud(token)
    test_schedule_crud(token)
    
    # Statistics
    test_get_stats(token)
    
    # Cleanup - delete the news article and user we created
    if news:
        test_delete_news(token, news.get("id"))
    
    if new_user:
        test_delete_user(token, new_user.get("id"))
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Total tests: {test_results['passed'] + test_results['failed']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    
    if test_results['failed'] > 0:
        print("\nFailed tests:")
        for test in test_results['tests']:
            if not test['passed']:
                print(f"- {test['name']}: {test['details']}")

if __name__ == "__main__":
    run_tests()