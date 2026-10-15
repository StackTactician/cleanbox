"""
Kinoriss Constants — Reverse-engineered from APK
"""

import os
import ssl
import base64

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context


# Force TLS 1.2 — the API servers reject TLS 1.3 handshakes
class TLS12Adapter(HTTPAdapter):
    """HTTPS adapter that forces TLS 1.2 with connection pooling."""
    def __init__(self, **kwargs):
        super().__init__(pool_connections=10, pool_maxsize=10, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


# GSLB endpoint — resolves regional API server
GSLB_URL = "https://gslb.shalltry.com/gslb/domain/convert"

# Known API hosts (fallback if GSLB fails)
API_HOSTS = [
    "api4sg.aoneroom.com",
    "api5.aoneroom.com",
    "api3.aoneroom.com",
    "api4.aoneroom.com",
    "api6.aoneroom.com",
    "api6sg.aoneroom.com",
    "api7.aoneroom.com",
    "api8.aoneroom.com",
]

# BFF API prefix (Backend For Frontend — the single monolithic API)
BFF_PREFIX = "/wefeed-mobile-bff"

# Content API endpoints (extracted from DEX strings)
ENDPOINTS = {
    # Search
    "search":           f"{BFF_PREFIX}/subject-api/search/v2",
    "search_suggest":   f"{BFF_PREFIX}/subject-api/search-suggest",
    "search_rank":      f"{BFF_PREFIX}/subject-api/search-rank/v2",
    # Content metadata
    "subject_get":      f"{BFF_PREFIX}/subject-api/get",
    "subject_list":     f"{BFF_PREFIX}/subject-api/list",
    "season_info":      f"{BFF_PREFIX}/subject-api/season-info",
    "filter_items":     f"{BFF_PREFIX}/subject-api/filter-items",
    "trending":         f"{BFF_PREFIX}/subject-api/trending/v2",
    # Playback
    "play_info":        f"{BFF_PREFIX}/subject-api/play-info",
    "resource":         f"{BFF_PREFIX}/subject-api/resource",
    "resource_position": f"{BFF_PREFIX}/subject-api/resource-position",
    "play_related":     f"{BFF_PREFIX}/subject-api/play-related-rec",
    # Download lifecycle
    "start_download":   f"{BFF_PREFIX}/subject-api/start-download-resource",
    "finish_download":  f"{BFF_PREFIX}/subject-api/finish-download-resource",
    # Subtitles
    "subtitle_search":  f"{BFF_PREFIX}/subject-api/subtitle-search",
    "stream_captions":  f"{BFF_PREFIX}/subject-api/get-stream-captions",
    "ext_captions":     f"{BFF_PREFIX}/subject-api/get-ext-captions",
    # UGC video
    "ugc_video_play":   f"{BFF_PREFIX}/ugc/video/play",
    "ugc_download":     f"{BFF_PREFIX}/ugc/video/start-download",
    # App config
    "app_config":       f"{BFF_PREFIX}/app/config",
    "ad_config":        f"{BFF_PREFIX}/ad/config",
    # Auth
    "visitor_login":    f"{BFF_PREFIX}/user-api/visitor-login",
    "login":            f"{BFF_PREFIX}/user-api/login",
    "register":         f"{BFF_PREFIX}/user-api/register",
    "get_sms_code":     f"{BFF_PREFIX}/user-api/get-sms-code",
    "check_mail":       f"{BFF_PREFIX}/user-api/check-mail-account",
    # Subtitle download (external — OpenSubtitles VIP API)
    "opensubtitles":    "https://vip-api.opensubtitles.com/api/v1/download",
}

# App identity (from APK manifest + build config)
APP_PACKAGE = "com.community.oneroom"
APP_VERSION_NAME = "3.0.12"
APP_VERSION_CODE = "30012"

# Video CDN domains (from DEX strings)
VIDEO_CDNS = [
    "vacdn.hakunaymatata.com",
    "vcdn.hakunaymatata.com",
    "v2cdn.hakunaymatata.com",
]

# Gateway API signing (reverse-engineered from GatewayInterceptor / HttpSigner)
# Secret from AndroidManifest meta-data "gateway_secret_online"
GATEWAY_SECRET_B64 = "76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O"
GATEWAY_SECRET = base64.b64decode(GATEWAY_SECRET_B64)
GATEWAY_KEY_VERSION = "2"  # Hardcoded in GatewayInterceptor line 202

# Embedded JWT token (from email registration — expires ~June 2026)
DEFAULT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjIwNjMzNTk2NzU2Njc0NzEzMTIsInV0cCI6MSwiZXhwIjoxNzk5ODQ4MDI5LCJpYXQiOjE3OTIwNzE3Mjl9.lIareVNYKuvsBLWX0NCEKFxeIuw0M2NepQNts9vlWFc"

# Download directory
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Kinoriss_Downloads")
