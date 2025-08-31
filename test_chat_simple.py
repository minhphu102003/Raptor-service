#!/usr/bin/env python3
"""
Simple Chat API test script using requests library
Easier to use than the async version
"""

import json
import time
from typing import Any, Dict, Optional

import requests

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/v1/datasets"


class SimpleChatTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session_id = None
        self.dataset_id = None
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Make HTTP request to API endpoint"""
        url = f"{self.base_url}{API_PREFIX}{endpoint}"

        print(f"\n🔍 {method.upper()} {url}")
        if data:
            print(f"📤 Request Data: {json.dumps(data, indent=2)}")
        if params:
            print(f"🔗 Query Params: {params}")

        try:
            response = self.session.request(
                method,
                url,
                json=data if data else None,
                params=params if params else None,
                stream=stream,
            )

            print(f"📊 Status: {response.status_code}")

            if stream:
                return response

            try:
                response_data = response.json()
                print(f"📥 Response: {json.dumps(response_data, indent=2)}")
                return response_data
            except json.JSONDecodeError:
                print(f"📥 Response (raw): {response.text}")
                return {"raw_response": response.text, "status": response.status_code}

        except Exception as e:
            print(f"❌ Request failed: {e}")
            return {"error": str(e)}

    def test_create_session(self) -> bool:
        """Test: Create new chat session"""
        print("\n" + "=" * 60)
        print("🧪 TEST: Create Chat Session")
        print("=" * 60)

        # Use a test dataset ID
        test_dataset_id = "test-dataset-001"

        request_data = {
            "dataset_id": test_dataset_id,
            "title": "Test Chat Session",
            "user_id": "test-user-123",
            "assistant_config": {"model": "DeepSeek-V3", "temperature": 0.7, "max_tokens": 4000},
        }

        response = self.make_request("POST", "/chat/sessions", data=request_data)

        if response.get("code") == 200 and response.get("data"):
            self.session_id = response["data"].get("session_id")
            self.dataset_id = test_dataset_id
            print(f"✅ Session created! ID: {self.session_id}")
            return True
        else:
            print(f"❌ Failed to create session: {response}")
            return False

    def test_list_sessions(self) -> bool:
        """Test: List chat sessions"""
        print("\n" + "=" * 60)
        print("🧪 TEST: List Chat Sessions")
        print("=" * 60)

        # Test without filters
        response = self.make_request("GET", "/chat/sessions")

        if response.get("code") == 200:
            sessions = response.get("data", [])
            print(f"✅ Retrieved {len(sessions)} sessions")

            # Test with filters
            params = {"user_id": "test-user-123", "limit": 10, "offset": 0}

            response_filtered = self.make_request("GET", "/chat/sessions", params=params)

            if response_filtered.get("code") == 200:
                print("✅ Filtered sessions query successful")
                return True

        print(f"❌ Failed to list sessions: {response}")
        return False

    def test_get_session(self) -> bool:
        """Test: Get specific chat session"""
        print("\n" + "=" * 60)
        print("🧪 TEST: Get Chat Session Details")
        print("=" * 60)

        if not self.session_id:
            print("❌ No session ID available")
            return False

        response = self.make_request("GET", f"/chat/sessions/{self.session_id}")

        if response.get("code") == 200:
            print("✅ Session details retrieved successfully")
            return True
        else:
            print(f"❌ Failed to get session: {response}")
            return False

    def test_update_session(self) -> bool:
        """Test: Update chat session"""
        print("\n" + "=" * 60)
        print("🧪 TEST: Update Chat Session")
        print("=" * 60)

        if not self.session_id:
            print("❌ No session ID available")
            return False

        update_data = {
            "title": "Updated Test Session",
            "assistant_config": {"model": "GPT-4o-mini", "temperature": 0.8},
        }

        response = self.make_request("PUT", f"/chat/sessions/{self.session_id}", data=update_data)

        if response.get("code") == 200:
            print("✅ Session updated successfully")
            return True
        else:
            print(f"❌ Failed to update session: {response}")
            return False

    def test_send_message(self) -> bool:
        """Test: Send chat message"""
        print("\n" + "=" * 60)
        print("🧪 TEST: Send Chat Message")
        print("=" * 60)

        if not self.dataset_id:
            print("❌ No dataset ID available")
            return False

        message_data = {
            "query": "Hello! Can you help me understand the documents?",
            "dataset_id": self.dataset_id,
            "session_id": self.session_id,
            "top_k": 5,
            "mode": "tree",
            "answer_model": "DeepSeek-V3",
            "temperature": 0.7,
            "max_tokens": 4000,
            "stream": False,
        }

        response = self.make_request("POST", "/chat/chat", data=message_data)

        if response.get("answer") or response.get("code") == 200:
            print("✅ Message sent successfully")
            return True
        else:
            print(f"❌ Failed to send message: {response}")
            return False

    def test_streaming_message(self) -> bool:
        """Test: Send streaming chat message"""
        print("\n" + "=" * 60)
        print("🧪 TEST: Streaming Chat Message")
        print("=" * 60)

        if not self.dataset_id:
            print("❌ No dataset ID available")
            return False

        message_data = {
            "query": "Tell me about the key concepts in the documents.",
            "dataset_id": self.dataset_id,
            "top_k": 3,
            "mode": "chunk",
            "answer_model": "DeepSeek-V3",
            "temperature": 0.5,
            "max_tokens": 2000,
            "stream": True,
        }

        try:
            response = self.make_request("POST", "/chat/chat", data=message_data, stream=True)

            if hasattr(response, "status_code") and response.status_code == 200:
                print("📥 Streaming Response:")
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        print(chunk.decode("utf-8"), end="", flush=True)
                print("\n✅ Streaming completed successfully")
                return True
            else:
                print(f"❌ Streaming failed: {response}")
                return False

        except Exception as e:
            print(f"❌ Streaming request failed: {e}")
            return False

    def test_get_messages(self) -> bool:
        """Test: Get chat messages"""
        print("\n" + "=" * 60)
        print("🧪 TEST: Get Chat Messages")
        print("=" * 60)

        if not self.session_id:
            print("❌ No session ID available")
            return False

        params = {"limit": 20, "offset": 0}

        response = self.make_request(
            "GET", f"/chat/sessions/{self.session_id}/messages", params=params
        )

        if response.get("code") == 200:
            messages = response.get("data", [])
            print(f"✅ Retrieved {len(messages)} messages")
            return True
        else:
            print(f"❌ Failed to get messages: {response}")
            return False

    def test_delete_session(self) -> bool:
        """Test: Delete chat session"""
        print("\n" + "=" * 60)
        print("🧪 TEST: Delete Chat Session")
        print("=" * 60)

        if not self.session_id:
            print("❌ No session ID available")
            return False

        response = self.make_request("DELETE", f"/chat/sessions/{self.session_id}")

        if response.get("code") == 200:
            print("✅ Session deleted successfully")
            return True
        else:
            print(f"❌ Failed to delete session: {response}")
            return False

    def run_all_tests(self):
        """Run all test cases"""
        print("🚀 Starting Chat API Tests")
        print("=" * 80)

        tests = [
            ("Create Session", self.test_create_session),
            ("List Sessions", self.test_list_sessions),
            ("Get Session", self.test_get_session),
            ("Update Session", self.test_update_session),
            ("Send Message", self.test_send_message),
            ("Get Messages", self.test_get_messages),
            ("Streaming Message", self.test_streaming_message),
            ("Delete Session", self.test_delete_session),
        ]

        results = []

        for test_name, test_func in tests:
            try:
                print(f"\n⏳ Running: {test_name}")
                result = test_func()
                results.append((test_name, result))

                if result:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")

                time.sleep(1)  # Small delay between tests

            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                results.append((test_name, False))

        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:.<40} {status}")

        print(f"\nTotal: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed. Check logs above.")


def main():
    """Main test runner"""
    tester = SimpleChatTester()
    tester.run_all_tests()


if __name__ == "__main__":
    print("Chat API Test Suite (Simple Version)")
    print("Make sure your FastAPI server is running on http://localhost:8000")
    print("Press Ctrl+C to stop\n")

    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
