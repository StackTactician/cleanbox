# Cleanbox

APK built from MovieBox 4.0.03.0922.03.

- Uses same `assets` and `lib/*Player`/`libav*` for thumbnails and video playback. Thumbnails from `pbcdn.aoneroom.com`, video via `play-info` + Aliyun.
- Removed `mbridge`/`bytedance` ad activities (50+), `AD_ID`/`BILLING` permissions, `Subscription` flows, 90 ad layouts.
- Signing via `gateway_secret_online` `76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O`, `HmacMD5`, TLS 1.2, baked JWT (no login UI).
- `apktool` decode of original, `X-Client-Info` deviceId, `x-tr-signature` `ts|2|b64`.

## Download

GitHub Actions `build` artifact `Cleanbox.apk`. Latest run: Actions tab.

## Build

```
apktool b apk -o Cleanbox.apk
apksigner sign --ks debug.jks Cleanbox.apk
```

## Python check

```
pip install -r requirements.txt
python -I py_client/test_trust_full.py
```

Server trust verified via `api4sg.aoneroom.com/wefeed-mobile-bff`.

## Notes

Packed `classes.dex` (`libexec`) not patched; manifest/layout strip only. Full ad removal requires decrypted dex patch.

