"""Example: Using the CodeReview-Agent API."""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def review_code_sync():
    """Example: Synchronous code review."""
    print("="*60)
    print("SYNCHRONOUS CODE REVIEW")
    print("="*60)
    
    code = """
def divide(a, b):
    return a / b  # Potential division by zero

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection
    return execute_query(query)
"""
    
    # Submit review request
    response = requests.post(
        f"{BASE_URL}/review/sync",
        json={
            "code": code,
            "language": "python",
            "options": {
                "check_security": True,
                "check_bugs": True,
                "suggest_refactoring": True
            }
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nReview ID: {result['review_id']}")
        print(f"Status: {result['status']}")
        
        if result.get('result'):
            review_result = result['result']
            print(f"\nQuality Score: {review_result['quality_metrics']['overall_score']}/100")
            print(f"Issues Found: {len(review_result['issues'])}")
            
            print("\nTop Issues:")
            for issue in review_result['issues'][:5]:
                print(f"  - [{issue['severity']}] {issue['title']}")
                print(f"    Line {issue.get('line_start', 'N/A')}: {issue['description']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def review_code_async():
    """Example: Asynchronous code review."""
    print("\n" + "="*60)
    print("ASYNCHRONOUS CODE REVIEW")
    print("="*60)
    
    code = """
import pickle
import os

def load_config(config_file):
    with open(config_file, 'rb') as f:
        config = pickle.load(f)  # Unsafe deserialization
    return config

password = "hardcoded_secret"  # Hardcoded credential
"""
    
    # Submit review request (async)
    response = requests.post(
        f"{BASE_URL}/review",
        json={
            "code": code,
            "language": "python"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        review_id = result['review_id']
        print(f"\nReview submitted: {review_id}")
        print(f"Status: {result['status']}")
        
        # Poll for completion
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(1)
            
            status_response = requests.get(f"{BASE_URL}/review/{review_id}/status")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"Attempt {attempt + 1}: {status_data['status']}")
                
                if status_data['status'] == 'completed':
                    # Get full result
                    result_response = requests.get(f"{BASE_URL}/review/{review_id}")
                    
                    if result_response.status_code == 200:
                        full_result = result_response.json()
                        review_result = full_result['result']
                        
                        print(f"\nReview completed!")
                        print(f"Quality Score: {review_result['quality_metrics']['overall_score']}/100")
                        print(f"Issues Found: {len(review_result['issues'])}")
                    break
                
                elif status_data['status'] == 'failed':
                    print("Review failed!")
                    break
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def get_metrics():
    """Example: Get aggregate metrics."""
    print("\n" + "="*60)
    print("AGGREGATE METRICS")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/metrics")
    
    if response.status_code == 200:
        metrics = response.json()
        print(f"\nTotal Reviews: {metrics['total_reviews']}")
        print(f"Total Issues: {metrics['total_issues']}")
        print(f"Average Quality Score: {metrics['average_quality_score']}")
        
        print("\nIssues by Severity:")
        for severity, count in metrics['issues_by_severity'].items():
            if count > 0:
                print(f"  {severity}: {count}")
        
        print("\nIssues by Category:")
        for category, count in metrics['issues_by_category'].items():
            if count > 0:
                print(f"  {category}: {count}")
    else:
        print(f"Error: {response.status_code}")


def list_recent_reviews():
    """Example: List recent reviews."""
    print("\n" + "="*60)
    print("RECENT REVIEWS")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/reviews?limit=5")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nShowing {len(data['reviews'])} of {data['total']} reviews:")
        
        for review in data['reviews']:
            print(f"\n  Review ID: {review['review_id']}")
            print(f"  Language: {review['language']}")
            print(f"  Quality Score: {review['quality_score']}/100")
            print(f"  Issues: {review['issues_count']}")
            print(f"  Timestamp: {review['timestamp']}")
    else:
        print(f"Error: {response.status_code}")


def main():
    """Run all examples."""
    print("\nMake sure the API server is running:")
    print("  python -m src.api.server\n")
    
    try:
        # Check if server is running
        health_response = requests.get("http://localhost:8000/health")
        if health_response.status_code != 200:
            print("Error: API server is not responding")
            return
        
        # Run examples
        review_code_sync()
        review_code_async()
        get_metrics()
        list_recent_reviews()
        
    except requests.exceptions.ConnectionError:
        print("\nError: Cannot connect to API server")
        print("Please start the server with: python -m src.api.server")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
