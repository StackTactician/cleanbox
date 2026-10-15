"""
Kinoriss API Client — Reverse-engineered from APK.

Architecture:
  GSLB -> Content API (wefeed-mobile-bff) -> Aliyun VOD (play-info) -> CDN -> Download
"""

import json
import time
import uuid
import hashlib
import hmac
import base64
import ssl
import socket
import threading
from urllib.parse import urlencode, urlparse

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests

from .constants import (
    GSLB_URL, API_HOSTS, ENDPOINTS,
    APP_PACKAGE, APP_VERSION_CODE, APP_VERSION_NAME,
    GATEWAY_SECRET, GATEWAY_KEY_VERSION,
    TLS12Adapter,
)
from .config import get_token


# ---------------------------------------------------------------------------
# TLS Certificate Pinning — SHA256 fingerprint of API server cert
# Fingerprint stored as XOR fragments to resist static extraction.
# To update: fetch new cert and re-encode with the same XOR keys.
# ---------------------------------------------------------------------------

_FP_A0 = [158, 151, 147, 196, 158, 193, 193, 197, 193, 147, 193, 195, 196, 198, 145, 196]
_FP_A1 = [61, 102, 111, 110, 60, 111, 60, 104, 56, 56, 56, 110, 63, 109, 109, 103]
_FP_A2 = [241, 244, 246, 247, 242, 241, 251, 245, 240, 251, 247, 160, 167, 244, 160, 250]
_FP_A3 = [161, 166, 243, 242, 167, 164, 247, 244, 245, 242, 244, 243, 242, 163, 247, 164]
_FP_K = [0xa7, 0x5e, 0xc3, 0x91]

def _get_pinned_fingerprint():
    """Reconstruct the expected cert SHA256 fingerprint from XOR fragments."""
    return ''.join(
        ''.join(chr(b ^ k) for b in chunk)
        for chunk, k in zip([_FP_A0, _FP_A1, _FP_A2, _FP_A3], _FP_K)
    )


def _verify_cert(hostname, port=443):
    """
    Verify server certificate against pinned SHA256 fingerprint.
    Returns True if cert matches or if check cannot be performed.
    Returns False if MITM detected (fingerprint mismatch).
    """
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(5)
            s.connect((hostname, port))
            cert_der = s.getpeercert(binary_form=True)
            actual = hashlib.sha256(cert_der).hexdigest()
            return actual == _get_pinned_fingerprint()
    except Exception:
        # Can't verify (network error, non-HTTPS, etc.) — don't break the app
        return True


# ---------------------------------------------------------------------------
# Device fingerprint generator — mimics a real Transsion device
# ---------------------------------------------------------------------------

def generate_device_id():
    """Generate a plausible device ID (ANDROID_ID format)."""
    return hashlib.md5(uuid.uuid4().bytes).hexdigest()[:16]


def build_headers(device_id=None, token=None, language="en"):
    """
    Build HTTP headers mimicking the Kinoriss app.
    Headers extracted from APK: X-Client-Info, X-Client-Token,
    X-Language, X-VersionCode, X-Country, X-Client-Status
    """
    if device_id is None:
        device_id = generate_device_id()

    headers = {
        "User-Agent": (
            f"okhttp/4.12.0 "
            f"({APP_PACKAGE}; {APP_VERSION_NAME}; Android 12; "
            f"Infinix X6819; en)"
        ),
        "X-Client-Info": json.dumps({
            "packageName": APP_PACKAGE,
            "versionCode": APP_VERSION_CODE,
            "versionName": APP_VERSION_NAME,
            "osVersion": "12",
            "phoneBrand": "Infinix",
            "phoneModel": "X6819",
            "deviceId": device_id,
            "channelId": "gp",
        }, separators=(",", ":")),
        "X-Language": language,
        "X-VersionCode": APP_VERSION_CODE,
        "X-Country": "NG",
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive",
    }

    if token:
        headers["X-Client-Token"] = token

    return headers


# ---------------------------------------------------------------------------
# API Client
# ---------------------------------------------------------------------------

class KinorissAPI:
    """Client for the Kinoriss wefeed-mobile-bff API."""

    # In-memory response cache: key -> (timestamp, data)
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, language="en", country="NG"):
        self.session = requests.Session()
        self.session.mount("https://", TLS12Adapter())
        self.device_id = generate_device_id()
        self.language = language
        self.country = country
        self.base_url = f"https://{API_HOSTS[0]}"
        self.token = None
        self._time_offset = 0  # Server clock offset (ms), corrected on GW.4410
        self._cache = {}
        self.session.headers.update(
            build_headers(self.device_id, language=language)
        )
        self.session.verify = False  # Match app's TrustAllCerts behavior
        self.set_token(get_token(), quiet=True)
        # Warm up TLS connection in background (non-blocking)
        threading.Thread(target=self._warmup, daemon=True).start()

    def _warmup(self):
        """Background TLS warmup — establishes connection pool."""
        try:
            self.session.head(self.base_url, timeout=(2, 2))
        except Exception:
            for h in API_HOSTS[1:3]:
                try:
                    self.base_url = f"https://{h}"
                    self.session.head(self.base_url, timeout=(2, 2))
                    return
                except Exception:
                    continue

    def login_email(self, email, password=None):
        """Login or register via email."""
        # Import here to avoid circular dependency — console comes from cli
        from .cli import console, Prompt
        try:
            check = self._api("check_mail", method="POST", json_body={
                "mail": email, "cc": "+234", "authType": 1,
            })
            if check is None:
                console.print("  [red]Connection failed. Check your internet.[/]")
                return False
            exists = check.get("data", {}).get("exists", False)

            console.print(f"  [dim]Sending verification code to {email}...[/]")
            result = self._api("get_sms_code", method="POST", json_body={
                "mail": email, "cc": "+234", "authType": 1, "type": 1,
            })
            if not result or result.get("code") != 0:
                console.print("  [red]Failed to send verification code[/]")
                return False

            try:
                code = Prompt.ask("  Verification code from email")
            except (EOFError, KeyboardInterrupt):
                return False
            if not code:
                return False

            if password is None:
                try:
                    if exists:
                        password = Prompt.ask("  Password")
                    else:
                        password = Prompt.ask("  Choose a password")
                except (EOFError, KeyboardInterrupt):
                    return False

            endpoint = "login" if exists else "register"
            body = {
                "mail": email, "cc": "+234", "authType": 1,
                "verificationCode": code, "password": password,
                "package_name": APP_PACKAGE, "type": 0,
            }
            resp = self._api(endpoint, method="POST", json_body=body)
            if resp and resp.get("code") == 0:
                data = resp.get("data", {})
                token = data.get("token")
                if token:
                    self.token = token
                    self.session.headers["Authorization"] = f"Bearer {self.token}"
                    console.print(f"  [green]Logged in![/] Token expires in ~90 days")
                    console.print(f"  [dim]Token: {self.token[:40]}...[/]")
                    return True
            console.print(f"  [red]Auth failed[/]")
            return False
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            console.print("  [red]No internet connection[/]")
            return False
        except Exception as e:
            console.print(f"  [red]Login error: {e}[/]")
            return False

    def set_token(self, token, quiet=False):
        """Set a previously obtained JWT token."""
        self.token = token
        self.session.headers["Authorization"] = f"Bearer {token}"
        if not quiet:
            print("[+] Token set.")

    def resolve_api_host(self):
        """Use GSLB to resolve the best API endpoint for our region."""
        print("[*] Resolving API host via GSLB...")
        try:
            resp = self.session.get(GSLB_URL, params={
                "packageName": APP_PACKAGE,
                "versionCode": APP_VERSION_CODE,
            }, timeout=10)
            if resp.ok:
                data = resp.json()
                if "data" in data and data["data"]:
                    host = data["data"]
                    if isinstance(host, dict):
                        host = host.get("domain", host.get("host", ""))
                    if host:
                        self.base_url = f"https://{host}" if not host.startswith("http") else host
                        print(f"[+] GSLB resolved: {self.base_url}")
                        return
        except Exception as e:
            print(f"[!] GSLB failed: {e}")

        # Fallback to first known host
        self.base_url = f"https://{API_HOSTS[0]}"
        print(f"[*] Using fallback API host: {self.base_url}")

    def _sign_request(self, method, url, body=None, headers=None):
        """
        Sign request per Transsion API Gateway protocol.

        Reverse-engineered from:
          - com.transsion.api.gateway.interceptor.GatewayInterceptor.doGzipOrSign()
          - com.transsion.api.gateway.sercurity.a (HMAC signer)
          - com.transsion.infra.gateway.core.sercurity.HttpSigner

        Signing string format:
          METHOD\\n
          accept\\n
          content-type\\n
          content-length\\n
          timestamp\\n
          body_md5_hex\\n
          /path?sorted_query_params

        Algorithm: HmacMD5 (default from GatewayInterceptor line 200)
        Key: Base64-decoded gateway_secret_online
        Output: Base64-encoded HMAC result
        Header: x-tr-signature: {timestamp}|{keyVersion}|{hmac_b64}
        """
        timestamp = int(time.time() * 1000) + self._time_offset

        parsed = urlparse(url)
        accept = (headers or {}).get("Accept", "")
        content_type = (headers or {}).get("Content-Type", "")

        # Body handling — MD5 hex of body, empty string if no body
        body_md5 = ""
        content_length = ""
        if body:
            body_bytes = body.encode("utf-8") if isinstance(body, str) else body
            content_length = str(len(body_bytes))
            # If body > 102400 bytes, only hash first 102400
            to_hash = body_bytes[:102400] if len(body_bytes) > 102400 else body_bytes
            body_md5 = hashlib.md5(to_hash).hexdigest()

        # Build URL part: path + sorted query params
        path = parsed.path
        url_part = path
        if parsed.query:
            # Sort query params alphabetically by key (URL-decoded)
            from urllib.parse import parse_qsl
            params_list = parse_qsl(parsed.query, keep_blank_values=True)
            params_list.sort(key=lambda x: x[0])
            sorted_query = "&".join(f"{k}={v}" for k, v in params_list)
            url_part = f"{path}?{sorted_query}"

        # Build signing string
        sign_parts = [
            method.upper(),
            accept,
            content_type,
            content_length,
            str(timestamp),
            body_md5,
            url_part,
        ]
        sign_string = "\n".join(sign_parts)

        # HMAC-MD5, key is base64-decoded secret, result is base64-encoded
        mac = hmac.new(GATEWAY_SECRET, sign_string.encode("utf-8"), hashlib.md5)
        sig_b64 = base64.b64encode(mac.digest()).decode()

        return f"{timestamp}|{GATEWAY_KEY_VERSION}|{sig_b64}"

    def _api(self, endpoint_key, method="GET", params=None, json_body=None):
        """Make a signed API request to the BFF. Returns dict or None on any failure."""
        try:
            if self.base_url is None:
                self.resolve_api_host()

            # Certificate pinning check
            try:
                host = urlparse(self.base_url).hostname
                if host and not _verify_cert(host):
                    return None
            except Exception:
                pass

            endpoint = ENDPOINTS.get(endpoint_key)
            if not endpoint:
                return None

            url = self.base_url + endpoint
            qs = urlencode(params) if params else ""
            sign_url = f"{url}?{qs}" if qs else url

            body_str = None
            if json_body is not None:
                body_str = json.dumps(json_body, separators=(",", ":"))

            sig = self._sign_request(
                method, sign_url, body=body_str, headers=dict(self.session.headers)
            )
            extra_headers = {"x-tr-signature": sig}

            for attempt in range(min(3, len(API_HOSTS))):
                if attempt > 0:
                    self.base_url = f"https://{API_HOSTS[attempt]}"
                    url = self.base_url + endpoint
                    sign_url = f"{url}?{qs}" if qs else url
                    sig = self._sign_request(
                        method, sign_url, body=body_str, headers=dict(self.session.headers)
                    )
                    extra_headers = {"x-tr-signature": sig}

                try:
                    if method == "GET":
                        resp = self.session.get(url, params=params, headers=extra_headers, timeout=(3, 6))
                    else:
                        resp = self.session.post(url, data=body_str, params=params, headers=extra_headers, timeout=(3, 6))

                    # Clock sync on GW.4410
                    if resp.status_code == 500:
                        try:
                            err_data = resp.json()
                            if err_data.get("errorCode") == "GW.4410":
                                server_time = json.loads(err_data.get("errorMsg", "{}")).get("time", 0)
                                if server_time > 0:
                                    self._time_offset = server_time - int(time.time() * 1000)
                                    return self._api(endpoint_key, method, params, json_body)
                        except (json.JSONDecodeError, KeyError, ValueError):
                            pass

                    if not resp.ok:
                        return None

                    try:
                        return resp.json()
                    except (json.JSONDecodeError, ValueError):
                        return None

                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                        requests.exceptions.SSLError, ConnectionResetError, OSError):
                    if attempt < 2:
                        continue
                    return None
                except Exception:
                    return None
        except Exception:
            return None

    def _cached_api(self, cache_key, endpoint_key, method="GET", params=None, json_body=None):
        """Wrapper around _api with in-memory TTL cache."""
        now = time.time()
        if cache_key in self._cache:
            ts, data = self._cache[cache_key]
            if now - ts < self.CACHE_TTL:
                return data

        data = self._api(endpoint_key, method=method, params=params, json_body=json_body)
        if data is not None:
            self._cache[cache_key] = (now, data)
        return data

    # --- Search ---

    def search(self, keyword, page=1, page_size=20):
        """Search for movies/shows/content."""
        data = self._api("search", method="POST", json_body={
            "keyword": keyword,
            "page": page,
            "size": page_size,
        })
        return data

    def search_suggest(self, keyword):
        """Get search suggestions/autocomplete."""
        return self._api("search_suggest", method="POST", json_body={"keyword": keyword})

    def get_trending(self, page=1):
        """Get trending content."""
        return self._api("trending", method="POST", json_body={"page": page})

    # --- Content Details ---

    def get_subject(self, subject_id):
        """Get full details for a movie/show (cached)."""
        return self._cached_api(
            f"subject:{subject_id}",
            "subject_get", params={"subjectId": subject_id},
        )

    def get_season_info(self, subject_id, season=1):
        """Get season/episode listing."""
        return self._api("season_info", params={
            "subjectId": subject_id,
            "se": season,
        })

    def get_resource(self, subject_id, episode=1, season=1):
        """Get resource info for a specific episode."""
        return self._api("resource", params={
            "subjectId": subject_id,
            "ep": episode,
            "se": season,
        })

    def get_resource_position(self, subject_id, episode=1, season=1):
        """Get resource position (available qualities)."""
        return self._api("resource_position", params={
            "subjectId": subject_id,
            "ep": episode,
            "se": season,
        })

    # --- Playback / Download ---

    def get_play_info(self, subject_id, episode=1, season=1, definition=None):
        """
        Get play info — this is the critical endpoint that returns
        either a playAuth token, STS credentials, or direct URL.
        """
        params = {
            "subjectId": subject_id,
            "ep": episode,
            "se": season,
        }
        if definition:
            params["definition"] = definition

        return self._api("play_info", params=params)

    def notify_download_start(self, subject_id, episode=1, season=1):
        """Notify server that download is starting (analytics). Non-critical."""
        try:
            self._api("start_download", method="POST", json_body={
                "subjectId": subject_id, "ep": episode, "se": season,
            })
        except Exception:
            pass

    def notify_download_finish(self, subject_id, episode=1, season=1):
        """Notify server that download finished (analytics). Non-critical."""
        try:
            self._api("finish_download", method="POST", json_body={
                "subjectId": subject_id, "ep": episode, "se": season,
            })
        except Exception:
            pass

    # --- Subtitles ---

    def search_subtitles(self, subject_id, episode=1, season=1):
        """Search for available subtitles."""
        return self._api("subtitle_search", params={
            "subjectId": subject_id,
            "ep": episode,
            "se": season,
        })

    def get_stream_captions(self, subject_id, episode=1, season=1):
        """Get captions embedded in stream."""
        return self._api("stream_captions", params={
            "subjectId": subject_id,
            "ep": episode,
            "se": season,
        })

    def get_ext_captions(self, subject_id, episode=1, season=1):
        """Get external caption files."""
        return self._api("ext_captions", params={
            "subjectId": subject_id,
            "ep": episode,
            "se": season,
        })
