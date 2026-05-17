# Implementing Riot Sign On (Private Key JWT + Auth Code Flow)

Source URL: https://docs.google.com/document/d/e/2PACX-1vTSthxkWOIqPFe8Xqqjv4Ona5pRa5W3X6bLg4I47X15gJjG9ae-HU5a0by7VIVLWdPMgB9fTr5gvQcY/pub

## Core flow

1. Register an RSO client.
2. Send users to `/authorize` with `response_type=code`.
3. Receive `code` at your redirect URI.
4. Exchange `code` at `/token` for access/id/refresh tokens.
5. Optionally call `/userinfo` using bearer access token.

## Required authorize params

- `redirect_uri`
- `client_id`
- `response_type=code`
- `scope` (must include `openid`)

Optional commonly used params: `offline_access`, `cpid`, `state`, `login_hint`, `ui_locales`.

## Token endpoint notes

- For client secret basic, use `Authorization: Basic base64(client_id:client_secret)`.
- For private key JWT, use client assertion JWT as documented.
- Access tokens are encrypted bearer tokens.
- Refresh tokens can rotate; always persist newest token if one is returned.

## Endpoints referenced

- `https://auth.riotgames.com/authorize`
- `https://auth.riotgames.com/token`
- `https://auth.riotgames.com/jwks.json`
- `https://auth.riotgames.com/userinfo` (optional)
