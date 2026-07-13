# Android Shell Plan

The localhost web app is the product core. A future APK should be a thin WebView or Custom Tab shell pointing to `http://127.0.0.1:8010`. It must not duplicate scoring, tracking, or application state logic.
