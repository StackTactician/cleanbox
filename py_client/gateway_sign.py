import base64, hashlib, hmac, time, urllib.parse

GATEWAY_HOST = "apigateway.tmctool.com"
SECRET_ONLINE = "76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O"
SECRET_TEST = "Xqn2nnO41/L92o1iuXhSLHTbXvY4Z5ZZ62m8mSLA"

def sorted_query(query: str) -> str:
    if not query:
        return ""
    m = {}
    for part in query.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            k = urllib.parse.unquote(k)
            v = urllib.parse.unquote(v)
            m[k] = v
        elif part:
            m[urllib.parse.unquote(part)] = ""
    items = sorted(m.items(), key=lambda x: x[0])
    return "&".join(f"{k}={v}" for k,v in items if k != "")

def hmac_b64(secret_b64: str, algo: str, data: str) -> str:
    key = base64.b64decode(secret_b64)
    algo = algo or "HmacMD5"
    # Java Mac names: HmacSHA1, HmacSHA256, HmacMD5
    digest = {"HmacSHA1": hashlib.sha1, "HmacSHA256": hashlib.sha256, "HmacMD5": hashlib.md5}[algo]
    hm = hmac.new(key, data.encode("utf-8"), digest)
    return base64.b64encode(hm.digest()).decode()

def build_string_to_sign(method: str, accept: str, content_type: str, content_length: str, timestamp_ms: int, body_md5: str, path: str, query: str) -> str:
    sq = sorted_query(query)
    full_path = path + ("?" + sq if sq else "")
    parts = [
        method.upper(),
        accept or "",
        content_type or "",
        content_length or "",
        str(timestamp_ms),
        body_md5 or "",
        full_path,
    ]
    return "\n".join(parts)

def sign_request(method, url, headers, body: bytes, secret_b64, algo="HmacMD5", timestamp_ms=None):
    parsed = urllib.parse.urlparse(url)
    path = parsed.path or "/"
    query = parsed.query or ""
    accept = headers.get("accept", "") or headers.get("Accept", "")
    ctype = headers.get("content-type", "") or headers.get("Content-Type", "")
    clen = headers.get("content-length", "") or headers.get("Content-Length", "")
    # fallback like Java: body contentType/length
    if body is not None and not ctype:
        ctype = "application/json"  # caller should set
    if body is not None and not clen:
        clen = str(len(body))
    if timestamp_ms is None:
        # time_offset handling: 0 for now, caller can add server offset
        timestamp_ms = int(time.time()*1000)
    body_md5 = ""
    if body:
        # Java: if >102400, md5 first chunk, else full. We do full for test
        body_md5 = hashlib.md5(body).hexdigest()
    s = build_string_to_sign(method, accept, ctype, clen, timestamp_ms, body_md5, path, query)
    sig = hmac_b64(secret_b64, algo, s)
    header = f"{timestamp_ms}|2|{sig}"
    return header, s
