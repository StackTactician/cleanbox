import time, requests, urllib.parse, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from gateway_sign import GATEWAY_HOST, SECRET_ONLINE, sorted_query, build_string_to_sign, hmac_b64
import hashlib

# No sign-in: we test anonymous HMAC-only trust. Server must trust HMAC without JWT.
# If it needs JWT, we will see 401/GW error and can add auto-guest fallback later.

def gateway_test(path="/gateway/sdk/v1/config", query=""):
    method="GET"
    url=f"https://{GATEWAY_HOST}{path}" + (f"?{query}" if query else "")
    headers={"accept":"application/json","content-type":"application/json"}
    body=b""
    # use HmacMD5 default
    from gateway_sign import sign_request
    sig, s = sign_request(method, url, headers, body, SECRET_ONLINE, "HmacMD5")
    headers["x-tr-signature"]=sig
    headers["x-tr-signature-method"]="HmacMD5"
    print(f"StringToSign:\n{s}\n")
    print(f"Header x-tr-signature: {sig}\nURL: {url}\n")
    try:
        r=requests.get(url, headers=headers, timeout=10)
        print(f"Status {r.status_code}")
        print(r.text[:2000])
        if r.status_code==500 and "GW.4410" in r.text:
            print("-> Clock sync needed (time_offset)")
        return r
    except Exception as e:
        print(f"Request failed (TLS hang?): {e}")
        return None

def test_no_auth_vs_hmac():
    print("=== Test 1: HMAC-only (no JWT, no login) ===")
    gateway_test("/gateway/sdk/v1/config", "")
    print("\n=== Test 2: HMAC with sorted query ===")
    gateway_test("/gateway/sdk/v1/config", "a=2&b=1")
    print("\n=== Test 3: No HMAC (should fail if server enforces) ===")
    try:
        r=requests.get(f"https://{GATEWAY_HOST}/gateway/sdk/v1/config", headers={"accept":"application/json"}, timeout=10)
        print(f"Status {r.status_code} {r.text[:1000]}")
    except Exception as e:
        print(e)

if __name__=="__main__":
    test_no_auth_vs_hmac()
