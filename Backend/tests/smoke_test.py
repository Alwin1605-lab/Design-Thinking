import os
import time
import httpx

BASE = os.getenv("BASE_URL", "http://localhost:8000")

# Minimal smoke test flow:
# - Health
# - Create issue (no images)
# - Request OTP (expects DEBUG_OTP enabled to see code)
# - Verify OTP
# - Fetch analytics
# - Export CSV (requires admin/officer token; skipped if TOKEN missing)

def main():
    with httpx.Client(timeout=20) as client:
        # Health
        r = client.get(f"{BASE}/api/health")
        r.raise_for_status()
        print("Health:", r.json())

        # Create issue
        data = {
            "category": "Roads",
            "description": "Potholes near market road",
            "reporter_name": "Tester",
            "reporter_phone": "+910000000000",
            "gram_panchayat": "TestGP",
            "latitude": "12.34",
            "longitude": "56.78",
            "address": "Main street",
            "voice_description": "",
        }
        r = client.post(f"{BASE}/api/issues", data=data)
        r.raise_for_status()
        issue_id = r.json().get("issue_id")
        print("Created issue:", issue_id)

        # OTP request (debug)
        r = client.post(f"{BASE}/api/auth/request_otp", json={"phone": "+910000000001"})
        r.raise_for_status()
        otp = r.json().get("debug_code")
        if not otp:
            print("No debug OTP returned (enable DEBUG_OTP=true to auto-smoke)")
            return
        # OTP verify
        r = client.post(f"{BASE}/api/auth/verify_otp", json={"phone": "+910000000001", "code": otp, "name": "SmokeUser", "gram_panchayat": "TestGP"})
        r.raise_for_status()
        user = r.json()["user"]
        token = r.json()["token"]
        print("OTP user:", user["_id"])        

        # Analytics
        r = client.get(f"{BASE}/api/analytics")
        r.raise_for_status()
        print("Analytics total:", r.json().get("total_issues"))

        # Export CSV (if admin token provided via env TOKEN)
        admin_token = os.getenv("TOKEN") or token
        headers = {"Authorization": f"Bearer {admin_token}"}
        r = client.get(f"{BASE}/api/admin/export/issues.csv", headers=headers)
        if r.status_code == 200:
            print("Export CSV size:", len(r.content))
        else:
            print("Export failed (likely insufficient role):", r.status_code)


if __name__ == "__main__":
    main()
