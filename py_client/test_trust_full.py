import json, time, hashlib, hmac, base64, ssl, requests
from urllib.parse import urlencode, urlparse, parse_qsl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from kinoriss_constants import API_HOSTS, GSLB_URL, ENDPOINTS, APP_PACKAGE, APP_VERSION_CODE, APP_VERSION_NAME, GATEWAY_SECRET, GATEWAY_KEY_VERSION, DEFAULT_TOKEN

class TLS12Adapter(HTTPAdapter):
    def init_poolmanager(self, *a, **kw):
        ctx = create_urllib3_context()
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kw["ssl_context"] = ctx
        return super().init_poolmanager(*a, **kw)

def gen_device():
    import uuid
    return hashlib.md5(uuid.uuid4().bytes).hexdigest()[:16]

def build_headers(device_id, token=None):
    return {
        "User-Agent": f"okhttp/4.12.0 ({APP_PACKAGE}; {APP_VERSION_NAME}; Android 12; Infinix X6819; en)",
        "X-Client-Info": json.dumps({"packageName":APP_PACKAGE,"versionCode":APP_VERSION_CODE,"versionName":APP_VERSION_NAME,"osVersion":"12","phoneBrand":"Infinix","phoneModel":"X6819","deviceId":device_id,"channelId":"gp"}, separators=(",",":")),
        "X-Language":"en","X-VersionCode":APP_VERSION_CODE,"X-Country":"NG",
        "Content-Type":"application/json; charset=utf-8","Accept":"application/json",
        "Authorization": f"Bearer {token}" if token else ""
    }

def sign(method, url, body_str, headers):
    ts = int(time.time()*1000)
    parsed = urlparse(url)
    accept = headers.get("Accept","")
    ctype = headers.get("Content-Type","")
    body_md5=""
    clen=""
    if body_str:
        b = body_str.encode()
        clen=str(len(b))
        to_hash = b[:102400] if len(b)>102400 else b
        body_md5=hashlib.md5(to_hash).hexdigest()
    path=parsed.path
    url_part=path
    if parsed.query:
        lst=parse_qsl(parsed.query, keep_blank_values=True)
        lst.sort(key=lambda x: x[0])
        sq="&".join(f"{k}={v}" for k,v in lst)
        url_part=f"{path}?{sq}"
    parts=[method.upper(), accept, ctype, clen, str(ts), body_md5, url_part]
    s="\n".join(parts)
    mac=hmac.new(GATEWAY_SECRET, s.encode(), hashlib.md5)
    sig=base64.b64encode(mac.digest()).decode()
    return f"{ts}|{GATEWAY_KEY_VERSION}|{sig}", s

# test without sign-in: use DEFAULT_TOKEN, no email verification
device=gen_device()
headers=build_headers(device, DEFAULT_TOKEN)
sess=requests.Session()
sess.mount("https://", TLS12Adapter())
sess.verify=False
sess.headers.update(headers)

# try GSLB first
print(f"Device {device} Token {DEFAULT_TOKEN[:30]}...")
# direct to fallback host to avoid GSLB extra
base=f"https://{API_HOSTS[0]}"
for endpoint_key in ["search","trending","subject_get"]:
    endpoint=ENDPOINTS[endpoint_key]
    if endpoint_key=="search":
        params=None
        body=json.dumps({"keyword":"avengers","page":1,"size":5}, separators=(",",":"))
        method="POST"
    elif endpoint_key=="trending":
        params=None
        body=json.dumps({"page":1}, separators=(",",":"))
        method="POST"
    else:
        params={"subjectId":"123"}
        body=None
        method="GET"
    url=base+endpoint
    qs=urlencode(params) if params else ""
    sign_url=f"{url}?{qs}" if qs else url
    sig,s = sign(method, sign_url, body, headers)
    extra={"x-tr-signature":sig}
    print(f"\n=== {endpoint_key} {method} {endpoint} ===")
    print(f"Sign string:\n{s}\nSig {sig[:50]}...")
    try:
        if method=="GET":
            r=sess.get(url, params=params, headers=extra, timeout=(5,10))
        else:
            r=sess.post(url, data=body, params=params, headers=extra, timeout=(5,10))
        print(f"Status {r.status_code}")
        print(r.text[:2000])
        if r.ok and r.json().get("code")==0:
            print(f"TRUSTED without sign-in: {endpoint_key} passed")
        else:
            print(f"not trusted or error")
    except Exception as e:
        print(f"fail {e}")

# also test visitor-login with auto deviceId (no email) to see if anonymous works
print("\n=== visitor-login test (no email, deviceId only) ===")
body=json.dumps({"deviceId":device}, separators=(",",":"))
url=base+ENDPOINTS["visitor_login"]
sig,s = sign("POST", url, body, headers)
extra={"x-tr-signature":sig}
try:
    r=sess.post(url, data=body, headers=extra, timeout=(5,10))
    print(f"Status {r.status_code} {r.text[:2000]}")
    if r.ok:
        print("visitor-login trusted")
except Exception as e:
    print(e)
