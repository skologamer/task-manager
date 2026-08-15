# App Store & Play Store Packaging Notes

This file summarizes steps and asset requirements to publish the Task Manager app.

## Android (Google Play)

1. Prepare web assets and Capacitor Android project:

```bash
npm install
npm run prepare-web
npx cap init task-manager com.example.taskmanager --web-dir=www
npx cap add android
npx cap copy
npx cap open android
```

2. In Android Studio: build a release `bundle` (recommended) or `apk`.
3. Generate a signing key (keystore):

```bash
keytool -genkey -v -keystore my-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias my-key-alias
```

4. Configure signing in Gradle and produce a signed `AAB`.
5. Play Store assets required:
- App bundle (.aab) or APK
- High-res icon (512x512 PNG)
- Feature graphic (1024x500) optional for store listing
- Screenshots: 1080x1920 recommended (portrait)
- Privacy policy URL

6. Create Play Console listing, upload bundle, assets, and fill metadata.

## iOS (App Store)

1. On macOS, add iOS platform:

```bash
npx cap add ios
npx cap copy
npx cap open ios
```

2. Open Xcode, set the bundle identifier, provisioning profile, and signing team.
3. Create an App Store Connect record and upload using Xcode or Transporter.
4. App Store assets required:
- App icon in various sizes (use export tools or `generate_icons.py` then scale as needed)
- App screenshots for required device sizes (e.g., iPhone 6.5", 5.5")
- Privacy policy and support URL

## Icon & Screenshot Generation
- Run `python -m pip install -r requirements.txt` to install `cairosvg`.
- Run the script to generate PNG icons:

```bash
python scripts/generate_icons.py
```

This writes `store/assets/icon-<size>.png` which you can use as starting icons.

## Signing & CI
- Store keystore/cert securely (do not commit to repo).
- Use CI to automate build and release, signing with encrypted keys.

## Privacy & Permissions
- Declare notification usage in app manifests/Info.plist.
- Add a privacy policy that explains how tasks and calendar data are used.

If you want, I can:
- Generate the Android `android/` project files locally (I cannot run `npx cap add android` here, but I can provide step-by-step scripts),
- Create Play Store listing drafts and store screenshots from the UI for you.
