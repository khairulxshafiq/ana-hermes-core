---
name: blogger-publish
description: Publish or edit Tanair Blogger posts via API.
---

# Blogger Publish (Tanair)

Publish and update posts on Blogger API v3 without the `google` Python SDK (system python lacks it; raw HTTP works).

## Targets

| Blog | ID | URL |
|---|---|---|
| Tanair AI Explorer | `<REDACTED_ID>` | tanair-ai.blogspot.com |
| AnaBerahi | `<REDACTED_ID>` | anaberahi.blogspot.com |

## Steps

1. **Refresh access token** (no SDK needed):
```python
tok = json.load(open('${HERMES_HOME}/google_token.json'))
data = urllib.parse.urlencode({'client_id': tok['client_id'], 'client_secret': tok['client_secret'],
    'refresh_token': tok['refresh_token'], 'grant_type': 'refresh_token'}).encode()
at = json.loads(urllib.request.urlopen(urllib.request.Request(
    'https://oauth2.googleapis.com/token', data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'})).read())['access_token']
```

2. **Publish new post** — `python3 /home/ubuntu/scripts/ana_blogger_publish.py <file.md> --labels "AI,Automasi"`.
   Script converts MD→HTML, POSTs to `/blogs/{id}/posts/`, prints `PUBLISHED status=LIVE` + `URL` + `POST_ID`.

3. **Edit existing post** — `PATCH /blogs/{id}/posts/{postId}` with `{"id","title","content"}`.
   Never use `PUT` (returns 404 on this account).

4. **Always append the signature block** (Boss requires it on every article):
```html
<hr />
<p><strong>Khairul Shafiq</strong> — CTO &amp; Founder, TanAir</p>
<p>🔗 GitHub: <a href="https://github.com/khairulxshafiq">github.com/khairulxshafiq</a><br />
🔗 LinkedIn: <a href="https://linkedin.com/in/khairulshafiq">linkedin.com/in/khairulshafiq</a><br />
🌐 Portal: <a href="https://tanair.my">tanair.my</a></p>
<p><em>Ditulis secara autonomi oleh Ana (Autonomous Swarm Lead &amp; Chief of Staff) dari AnaOS.</em></p>
```

5. **Verify publicly** — fetch the post URL with a browser User-Agent and assert `Khairul Shafiq`, `linkedin.com/in/khairulshafiq`, `tanair.my` appear. API success alone is not proof.

## Pitfalls

- **`GET /blogs/{id}` and `GET /blogs/{id}/posts/{postId}` sometimes return 404** even for live posts. Workaround: `GET /blogs/{id}/posts?maxResults=5&fetchBodies=true` (list) works and returns full content.
- **`PUT` post update → 404.** Use `PATCH`.
- **Token dead (`invalid_grant`)** when OAuth consent screen is in *Testing* → refresh token expires every 7 days. Fix: publish the OAuth app (project `<REDACTED_ID>`), then re-authorise.
- Terminal tool may refuse `python3 -c` commands (lifecycle guard `embedded null byte`) — run API work through `execute_code` / subprocess instead.
- Article language and voice: Bahasa Melayu, first person, no AI slop, and do not overclaim in opinion pieces.
