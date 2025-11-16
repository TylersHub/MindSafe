"""
Simple script to test the Children's Video Content Evaluator API
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:5001"

def test_health_check():
    """Test the health check endpoint."""
    print("=" * 70)
    print("Testing Health Check Endpoint")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Health check passed!\n")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        return False


def test_evaluate_video(youtube_url, age):
    """Test the video evaluation endpoint."""
    print("=" * 70)
    print("Testing Video Evaluation Endpoint")
    print("=" * 70)
    print(f"URL: {youtube_url}")
    print(f"Age: {age}")
    print()
    
    try:
        # Make request
        print("Sending request...")
        start_time = time.time()
        
        response = requests.get(
            f"{BASE_URL}/evaluate",
            params={
                'url': youtube_url,
                'age': age
            },
            timeout=600  # 10 minute timeout for long videos
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Processing Time: {elapsed_time:.1f} seconds")
        print()
        
        if response.status_code == 200:
            results = response.json()
            
            # Print key results
            print("=" * 70)
            print("EVALUATION RESULTS")
            print("=" * 70)
            print()
            print(f"📺 Video Duration: {results.get('duration_minutes', 'N/A')} minutes")
            print(f"👶 Age Group: {results.get('age_band_name', 'N/A')}")
            print()
            print(f"📊 SCORES:")
            print(f"   Developmental Score: {results.get('dev_score', 'N/A')}/100")
            print(f"   Interpretation: {results.get('dev_interpretation', 'N/A')}")
            print()
            print(f"   Brainrot Index: {results.get('brainrot_index', 'N/A')}/100")
            print(f"   Interpretation: {results.get('brainrot_interpretation', 'N/A')}")
            print()
            print(f"   Overall: {results.get('overall_recommendation', 'N/A')}")
            print()
            
            # Print dimension scores
            print("📈 DIMENSION SCORES:")
            if 'dimension_scores' in results:
                for dimension, score in results['dimension_scores'].items():
                    print(f"   {dimension.capitalize()}: {score}/100")
            print()
            
            # Print strengths and concerns
            if 'strengths' in results and results['strengths']:
                print("✅ STRENGTHS:")
                for strength in results['strengths']:
                    print(f"   • {strength}")
                print()
            
            if 'concerns' in results and results['concerns']:
                print("⚠️  CONCERNS:")
                for concern in results['concerns']:
                    print(f"   • {concern}")
                print()
            
            # Save full results to file
            output_file = "api_test_results.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"💾 Full results saved to: {output_file}")
            print()
            
            print("✅ Video evaluation successful!\n")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>10 minutes)")
        return False
    except Exception as e:
        print(f"❌ Evaluation failed: {e}\n")
        return False


def test_invalid_requests():
    """Test API error handling with invalid requests."""
    print("=" * 70)
    print("Testing Error Handling")
    print("=" * 70)
    
    test_cases = [
        {
            "name": "Missing URL parameter",
            "params": {"age": 4},
            "expected_status": 400
        },
        {
            "name": "Missing age parameter",
            "params": {"url": "https://youtube.com/watch?v=test"},
            "expected_status": 400
        },
        {
            "name": "Invalid age (negative)",
            "params": {"url": "https://youtube.com/watch?v=test", "age": -1},
            "expected_status": 400
        },
        {
            "name": "Invalid age (too high)",
            "params": {"url": "https://youtube.com/watch?v=test", "age": 100},
            "expected_status": 400
        },
        {
            "name": "Invalid age format",
            "params": {"url": "https://youtube.com/watch?v=test", "age": "abc"},
            "expected_status": 400
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        try:
            response = requests.get(f"{BASE_URL}/evaluate", params=test_case['params'])
            if response.status_code == test_case['expected_status']:
                print(f"✅ Correctly returned {response.status_code}")
                print(f"   Error message: {response.json().get('message', 'N/A')}")
            else:
                print(f"❌ Expected {test_case['expected_status']}, got {response.status_code}")
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print()


def main():
    """Run all API tests."""
    print("\n")
    print("=" * 70)
    print("  CHILDREN'S VIDEO CONTENT EVALUATOR - API TESTS")
    print("=" * 70)
    print("\nMake sure the API server is running: python api.py")
    print("Press Ctrl+C to cancel\n")
    
    try:
        input("Press Enter to start tests...")
    except KeyboardInterrupt:
        print("\n\nTests cancelled.")
        return
    
    print()
    
    # Test 1: Health check
    health_ok = test_health_check()
    if not health_ok:
        print("❌ API server is not responding. Make sure it's running!")
        print("   Run: python api.py")
        return
    
    # Test 2: Error handling
    test_invalid_requests()
    
    # Test 3: Actual video evaluation (optional)
    print("=" * 70)
    print("Video Evaluation Test")
    print("=" * 70)
    print("\nThis will download and evaluate a real YouTube video.")
    print("It may take 3-10 minutes depending on video length.")
    print()
    
    try:
        run_eval = input("Run video evaluation test? (y/n): ").lower().strip()
        if run_eval == 'y':
            # Use a short video for testing
            test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Me at the zoo (19 seconds)
            test_age = 4
            test_evaluate_video(test_url, test_age)
        else:
            print("Skipping video evaluation test.")
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        return
    
    print()
    print("=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()

