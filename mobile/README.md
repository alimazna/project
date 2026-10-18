# TrendCipher Mobile (Expo / React Native)

Stage 6 of the TrendCipher product: a native iOS/Android client for the
TrendCipher backend (FastAPI). It shares the same API contract as the web app
and adds device-level push registration for alert notifications.

## Stack

- Expo SDK 58, React Native 0.88, TypeScript strict
- Expo Router (file-based navigation under `src/app/`)
- `react-native-svg` candlestick chart (browser/web build uses
  TradingView lightweight-charts on the web frontend)
- `expo-notifications` + `expo-secure-store` (push registration, token storage)

## Getting started

```bash
npm install
cp .env.example .env   # set EXPO_PUBLIC_API_BASE_URL to your backend
npx expo start         # scan the QR with Expo Go, or press a/i for simulator
```

In Expo Go the phone and the backend must be on the same network; use your
machine's LAN IP, e.g. `http://192.168.1.20:8000/api/v1`.

## Screens

| Route                 | Purpose                                             |
| --------------------- | --------------------------------------------------- |
| `/login`, `/register` | Auth (first registered user becomes admin)          |
| `/(tabs)` (dashboard) | Live tickers from connected exchanges               |
| `/(tabs)/watchlist`   | User watchlists                                     |
| `/(tabs)/scenarios`   | Saved deterministic analyses                        |
| `/(tabs)/alerts`      | Price/volume alert management                       |
| `/(tabs)/account`     | Profile, push registration, notification prefs      |
| `/asset/[symbol]`     | Candlestick chart + run analysis + add to watchlist |
| `/analysis/[id]`      | Full evidence list + decision matrix                |

## Push notifications (status: partially verifiable here)

`src/lib/notifications.ts` implements real Expo push token registration
(`getExpoPushTokenAsync`) and the backend records devices via
`POST /api/v1/devices`. Actual remote delivery through Expo's push service
requires:

- a **development build** (`npx expo run:ios|android` or `eas build --profile
  development`) — Expo Go does not reliably deliver remote push to a token
- push credentials configured in the Expo/EAS project
- `PUSH_PROVIDER=expo` on the backend plus a real Expo access token in the
  `ExpoPushProvider` configuration

With the default `PUSH_PROVIDER=log` the backend records delivery attempts but
does not contact a remote push service — that is the expected behavior in the
default dev setup.

## Verification

```bash
npx tsc --noEmit      # typecheck
npx expo lint         # lint (add eslint-config-expo when configured)
npx expo-doctor       # dependency/config sanity
```

## Notes

- Routes live in `src/app/`; non-route code lives in `src/`.
- Keep the backend running (`cd backend && uvicorn app.main:app --port 8000`).
- The web app remains the canonical product surface; the mobile client mirrors
  the core read screens and alert flows.