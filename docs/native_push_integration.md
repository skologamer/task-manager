# Native Push Integration (Capacitor + Firebase / APNs)

Short guide to get push notifications working in native builds.

## Android (Firebase)
- Add Firebase to your Android app and download `google-services.json` from Firebase Console.
- Place `google-services.json` in `android/app/` before building.
- Install Capacitor Push plugin: `npm install @capacitor/push-notifications` and run `npx cap sync android`.
- Ensure `android/build.gradle` and `android/app/build.gradle` apply the Google services plugin (standard Firebase setup).
- On first run, call `window.initPush()` from the web app (we include `static/push_client.js` which posts the device token to `/api/register_token`).

## iOS (APNs + Firebase optional)
- For APNs, enable Push Notifications capability and add the proper entitlements to your Xcode project.
- If using Firebase Cloud Messaging for iOS, upload your APNs key/cert to Firebase and follow Firebase iOS setup; download `GoogleService-Info.plist` and add to `ios/App/App`.
- Install Capacitor Push plugin and `npx cap sync ios`.

## Server (Flask) requirements
- Set `FCM_SERVER_KEY` environment variable (server-side) for sending via FCM HTTP v1 or legacy endpoint.
- Devices should POST their token to `/api/register_token` (endpoint exists in `app.py`) with bearer token or session auth.
- The server's scheduler (`APScheduler` in `app.py`) can send scheduled reminders via `send_push_via_fcm(token, title, body)`.

## Notes
- Local testing on Android: use a physical device or emulator with Google Play services.
- For iOS, push requires a real device and proper provisioning.
- Capacitor plugin setup and platform builds must be done on macOS for iOS builds.
