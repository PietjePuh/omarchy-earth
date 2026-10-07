## 2024-05-24 - Gzip Compression for Python HTTP Requests
**Learning:** Using gzip compression via Accept-Encoding header in standard library `urllib` requests significantly reduces data transfer size and time, but is not turned on by default in `urllib`.
**Action:** Adding Accept-Encoding: gzip and `gzip.decompress` reduced runtime of earth-sampler.py from ~7.5s to ~3.4s
