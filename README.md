# CleanBox — MovieBox without predatory ads/premium

Reuses MovieBox 4.0.03 assets, strips:
- mbridge/bytedance/ad SDKs (90 layouts, 14 manifest entries)
- BILLING + subscription activities
- packed shell payload (fresh build, not patched dex)

Build on GitHub via `apktool`. Python trust test in `py_client/`.
