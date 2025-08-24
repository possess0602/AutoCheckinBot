import requests
import json
import os
import base64
import time
from datetime import datetime
from typing import Dict, Any, Optional

def load_config(config_file: str = "config.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Cannot load config file {config_file}: {e}")
        print("Using default configuration...")
        return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """Get default configuration"""
    return {
        "authentication": {
            "module_session_cookie": "YOUR_MODULE_SESSION_COOKIE_HERE"
        },
        "work_schedule": {
            "punch_in": {"hour": 9, "minute_range": {"min": 10, "max": 20}},
            "punch_out": {"hour": 18, "minute_range": {"min": 10, "max": 30}},
            "work_duration_hours": 9
        },
        "service_settings": {
            "max_retries": 2,
            "timeout_seconds": 30,
            "check_interval_seconds": 30,
            "workdays": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
    }

def load_cookies_from_file(cookie_file: str = "cookies.json") -> Dict[str, str]:
    """Load cookies from JSON file"""
    if os.path.exists(cookie_file):
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return get_default_cookies()

def save_cookies_to_file(cookies: Dict[str, str], cookie_file: str = "cookies.json") -> None:
    """Save cookies to JSON file"""
    try:
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Cannot save cookies to file: {e}")

def get_default_cookies() -> Dict[str, str]:
    """Get default cookies using config file"""
    config = load_config()
    session_cookie = config.get("authentication", {}).get("module_session_cookie", "YOUR_MODULE_SESSION_COOKIE_HERE")
    
    return {
        "visid_incap_3031870": "ikOVvzafQ6SmzJKU6lvbzRP5m2gAAAAAQUIPAAAAAABW/+3GQKNwri2eiKsie5nP",
        "visid_incap_2985417": "nvc/5VIAQM2v2lRd+NKZtCz5m2gAAAAAQUIPAAAAAABkiA4wapasjE4tWeZH3nZV",
        "incap_ses_725_2985417": "xU55Iyr8ITFnA+z0v7cPCiz5m2gAAAAAcDHo0Gcwwm/0pgDwnpC4WQ==",
        "visid_incap_2985428": "ptN/OeS7R0m/Lnbi8P0Voy35m2gAAAAAQUIPAAAAAAAf5xjEd2YeM2mSXI8NvyyE",
        "incap_ses_725_2985428": "bLWJRJZnyz8MBez0v7cPCi35m2gAAAAAbIiBEf3Tg3ToZRp/SD1pqQ==",
        "visid_incap_2985429": "77v/I1FXTteSDaUM7cQymjX5m2gAAAAAQUIPAAAAAABeOBoFLDRZ3hVt7EEVtjCz",
        "incap_ses_725_2985429": "sg0iY08qBQiZDOz0v7cPCjX5m2gAAAAAbFYiMHyv9WAJAKiGvw+aZQ==",
        "nlbi_3031870": "6AMBXvG2s3H3vTuDfPznVgAAAAAkWhJqSg5jbG1LpJFdx0kv",
        "incap_ses_725_3031878": "fWU8atOWLHG0cU/1v7cPCq9enGgAAAAAIMkW/LqiokDxsnDe0u0Tlg==",
        "visid_incap_3031878": "YRI4svO8RSauMcP5dBmi6wkInGgAAAAAQkIPAAAAAADq3uAQc5ribcMjOotnswyQ",
        "_ga": "GA1.1.55338977.1755078335",
        "__ModuleSessionCookie2": "Ok",
        "LoggedInDomain": "apollo.mayohr.com",
        "_gm_lc": "AwcNCAEAAg0ABwQJBgQDAQUFGAABB1cBBgVXHAIDAg8YAAMCUR1XCAAMGAUDCQVaA1UDBFEGVw%3d%3d",
        "incap_ses_725_3031870": "iZ3Rb/UykWpek/xCwrcPCop4omgAAAAA1h3AgPNdqVZCOyMe0TQHOg==",
        "_ga_YZ4TDX0YDN": "GS2.1.s1755478157$o5$g1$t1755478552$j59$l0$h0",
        "__ModuleSessionCookie": session_cookie
    }

def decode_jwt_payload(jwt_token: str) -> Optional[Dict[str, Any]]:
    """Decode JWT payload to check expiration"""
    try:
        parts = jwt_token.split('.')
        if len(parts) != 3:
            return None
        
        payload = parts[1]
        # Add padding for base64 decoding
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded.decode('utf-8'))
    except:
        return None

def is_jwt_expired(jwt_token: str) -> bool:
    """Check if JWT token is expired"""
    payload = decode_jwt_payload(jwt_token)
    if not payload:
        return True
    
    exp_time = payload.get('exp')
    if not exp_time:
        return True
    
    current_time = int(time.time())
    return current_time >= exp_time

def is_cookie_expired(response, cookies: Dict[str, str]) -> bool:
    """Enhanced cookie expiration check including JWT validation"""
    
    # First check JWT expiration
    session_cookie = cookies.get('__ModuleSessionCookie')
    if session_cookie and is_jwt_expired(session_cookie):
        print("JWT token is expired based on 'exp' claim")
        return True
    
    # Check HTTP response indicators
    if response.status_code == 401:
        return True
    
    try:
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            error_indicators = [
                'unauthorized', 'expired', 'invalid token', 
                'authentication', 'login required', 'session',
                'access denied', 'forbidden'
            ]
            response_text = str(data).lower()
            return any(indicator in response_text for indicator in error_indicators)
    except:
        pass
    
    # Check if redirected to login page
    if response.status_code in [302, 303, 307, 308]:
        location = response.headers.get('location', '')
        if 'login' in location.lower() or 'auth' in location.lower():
            return True
    
    return False

def refresh_session_cookies() -> Optional[Dict[str, str]]:
    """Attempt to refresh session cookies - limited effectiveness with JWT"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
        }
        
        # Visit main page to get session cookies (won't refresh JWT)
        session = requests.Session()
        response = session.get("https://apollo.mayohr.com/", headers=headers, timeout=30)
        
        if response.status_code == 200:
            cookies = {}
            for cookie in session.cookies:
                cookies[cookie.name] = cookie.value
            
            if cookies:
                # Only save non-JWT cookies, preserve existing JWT
                current_cookies = load_cookies_from_file()
                
                # Don't overwrite JWT token with potentially empty value
                jwt_cookie = current_cookies.get('__ModuleSessionCookie')
                cookies.update(current_cookies)  # Merge with existing
                
                if jwt_cookie:
                    cookies['__ModuleSessionCookie'] = jwt_cookie
                
                save_cookies_to_file(cookies)
                return cookies
    except Exception as e:
        print(f"Failed to refresh cookies: {e}")
    
    return None

def punch_attendance(attendance_type: int = 1, is_override: bool = False, max_retries: int = None) -> Dict[str, Any]:
    """Punch attendance with enhanced JWT-aware cookie handling"""
    # Load configuration
    config = load_config()
    
    # Get settings from config
    if max_retries is None:
        max_retries = config.get("service_settings", {}).get("max_retries", 2)
    timeout = config.get("service_settings", {}).get("timeout_seconds", 30)
    
    url = "https://apollo.mayohr.com/backend/pt/api/checkIn/punch/web"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
        "accept": "*/*",
        "accept-language": "zh-tw",
        "actioncode": "Default",
        "functioncode": "PunchCard",
        "origin": "https://apollo.mayohr.com",
        "referer": "https://apollo.mayohr.com/ta?id=webpunch",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }
    
    payload = {
        "AttendanceType": attendance_type,
        "IsOverride": is_override
    }
    
    cookies = load_cookies_from_file()
    
    # Pre-check JWT expiration
    jwt_token = cookies.get('__ModuleSessionCookie')
    if jwt_token and is_jwt_expired(jwt_token):
        payload_data = decode_jwt_payload(jwt_token)
        if payload_data and 'exp' in payload_data:
            exp_time = datetime.fromtimestamp(payload_data['exp'])
            return {
                "success": False,
                "error": f"JWT token expired at {exp_time}. Manual login required for new token.",
                "jwt_expired": True
            }
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                url=url,
                headers=headers,
                cookies=cookies,
                json=payload,
                timeout=timeout
            )
            
            # Check if cookies are expired (JWT-aware)
            if is_cookie_expired(response, cookies):
                if attempt < max_retries:
                    print(f"Cookie expired, attempting to refresh... (attempt {attempt + 1}/{max_retries})")
                    fresh_cookies = refresh_session_cookies()
                    if fresh_cookies:
                        cookies = fresh_cookies
                        continue
                    else:
                        # Fall back to default cookies
                        cookies = get_default_cookies()
                        continue
                else:
                    error_msg = "Cookie expired and refresh failed. JWT token likely needs manual renewal."
                    if jwt_token and is_jwt_expired(jwt_token):
                        error_msg += " JWT token is expired - please login again to get new token."
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "status_code": response.status_code,
                        "jwt_expired": jwt_token and is_jwt_expired(jwt_token)
                    }
            
            # Check HTTP status code
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "data": data
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "data": response.text
                    }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                continue
            return {
                "success": False,
                "error": "Request timeout"
            }
        except requests.exceptions.ConnectionError:
            if attempt < max_retries:
                continue
            return {
                "success": False,
                "error": "Connection error"
            }
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                continue
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    return {
        "success": False,
        "error": "All retry attempts failed"
    }


def analyze_jwt_token():
    """Analyze current JWT token expiration and info"""
    print("JWT Token Analysis")
    print("=" * 25)
    
    cookies = load_cookies_from_file()
    jwt_token = cookies.get('__ModuleSessionCookie')
    
    if not jwt_token:
        print("No __ModuleSessionCookie found")
        return True
    
    print(f"JWT Token (first 50 chars): {jwt_token[:50]}...")
    print()
    
    payload = decode_jwt_payload(jwt_token)
    if not payload:
        print("Failed to decode JWT payload")
        return True
    
    current_time = int(time.time())
    is_expired = False
    
    if 'exp' in payload:
        exp_time = payload['exp']
        exp_datetime = datetime.fromtimestamp(exp_time)
        is_expired = current_time >= exp_time
        
        print(f"Expires at: {exp_datetime}")
        if is_expired:
            print("Status: EXPIRED")
        else:
            remaining = exp_time - current_time
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            print(f"Status: Valid (expires in {hours}h {minutes}m)")
    else:
        print("No expiration time found")
        is_expired = True
    
    if 'iat' in payload:
        iat_datetime = datetime.fromtimestamp(payload['iat'])
        print(f"Issued at: {iat_datetime}")
    
    print()
    return is_expired

def update_session_cookie_interactive():
    """Interactive cookie update utility"""
    print("Cookie Update Utility")
    print("========================")
    print()
    
    print("Please provide the new __ModuleSessionCookie value:")
    print("(Copy from browser developer tools -> Application -> Cookies)")
    print("Type 'exit' to quit")
    print()
    
    while True:
        user_input = input("Enter new __ModuleSessionCookie value: ").strip()
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            return
        
        if not user_input:
            print("Empty input. Please try again.")
            continue
        
        try:
            # Update cookie
            current_cookies = load_cookies_from_file()
            current_cookies['__ModuleSessionCookie'] = user_input
            save_cookies_to_file(current_cookies)
            
            print("Session cookie updated successfully!")
            
            # Test the updated cookie
            print("Testing updated cookie...")
            result = punch_attendance(attendance_type=1)
            if result.get("success", False):
                print("Cookie update successful! Attendance system is working.")
            else:
                print("Cookie updated but test failed. Please check the cookie value.")
                print(f"Error: {result.get('error', 'Unknown error')}")
            
            break
            
        except Exception as e:
            print(f"Failed to update cookie: {e}")
            continue

def show_cookie_extraction_guide():
    """Show guide for extracting cookies from browser"""
    print("\nHow to extract cookies from your browser:")
    print("=" * 50)
    print("1. Open your browser and login to apollo.mayohr.com")
    print("2. Press F12 to open Developer Tools")
    print("3. Go to Application tab -> Storage -> Cookies -> apollo.mayohr.com")
    print("4. Find '__ModuleSessionCookie' and copy its value")
    print("5. Or go to Network tab, perform a punch action, and copy cookies from request")
    print()

def main():
    """Main function with interactive menu"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ['analyze', 'check', 'jwt']:
            analyze_jwt_token()
            return
        elif command in ['update', 'cookie', 'refresh']:
            show_cookie_extraction_guide()
            update_session_cookie_interactive()
            return
        elif command in ['checkin', 'in', '1']:
            attendance_type = 1
        elif command in ['checkout', 'out', '2']:
            attendance_type = 2
        else:
            print("Usage:")
            print("  python manual_punch.py [checkin|checkout|analyze|update]")
            print("  python manual_punch.py 1      # Check-in")
            print("  python manual_punch.py 2      # Check-out") 
            print("  python manual_punch.py analyze # Analyze JWT token")
            print("  python manual_punch.py update  # Update cookies")
            return
    else:
        # Default test
        print("Testing punch...")
        attendance_type = 2
    
    result = punch_attendance(attendance_type)
    
    if result["success"]:
        action = "Check-in" if attendance_type == 1 else "Check-out"
        print(f"{action} successful!")
        print(f"Response: {result['data']}")
    else:
        print("Punch failed!")
        print(f"Error: {result['error']}")
        if result.get('jwt_expired'):
            print("JWT token expired")
            print("Solutions:")
            print("1. Run: python manual_punch.py update")
            print("2. Or manually update cookies.json file")


if __name__ == "__main__":
    main()
