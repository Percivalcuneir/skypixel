# builds the android project around index.html (run by github actions)
import os, shutil

FILES = {}

FILES["android/settings.gradle"] = r'''
pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.PREFER_SETTINGS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "SkyPixel"
include ':app'
'''

FILES["android/build.gradle"] = r'''
plugins {
    id 'com.android.application' version '8.5.2' apply false
}
'''

FILES["android/gradle.properties"] = r'''
org.gradle.jvmargs=-Xmx2g
android.nonTransitiveRClass=true
'''

FILES["android/app/build.gradle"] = r'''
plugins {
    id 'com.android.application'
}
android {
    namespace 'com.joel.skypixel'
    compileSdk 34
    defaultConfig {
        applicationId 'com.joel.skypixel'
        minSdk 26
        targetSdk 34
        versionCode 1
        versionName '1.0'
    }
    buildTypes {
        release { minifyEnabled false }
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
}
'''

FILES["android/app/src/main/AndroidManifest.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.USE_FULL_SCREEN_INTENT" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />

    <application
        android:label="SkyPixel"
        android:icon="@drawable/ic_launcher"
        android:theme="@style/AppTheme"
        android:allowBackup="true"
        android:usesCleartextTraffic="false">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:screenOrientation="portrait"
            android:configChanges="orientation|screenSize|keyboardHidden|screenLayout|smallestScreenSize|uiMode">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity
            android:name=".AlarmActivity"
            android:exported="false"
            android:launchMode="singleTop"
            android:taskAffinity=""
            android:excludeFromRecents="true"
            android:screenOrientation="portrait" />

        <receiver android:name=".AlarmReceiver" android:exported="false" />
        <receiver android:name=".OkReceiver" android:exported="false" />
        <receiver android:name=".BootReceiver" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
            </intent-filter>
        </receiver>
    </application>
</manifest>
'''

FILES["android/app/src/main/res/values/styles.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="android:Theme.Material.NoActionBar">
        <item name="android:windowBackground">#000000</item>
        <item name="android:statusBarColor">#000000</item>
        <item name="android:navigationBarColor">#000000</item>
    </style>
</resources>
'''

FILES["android/app/src/main/res/drawable/ic_launcher.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#000000" android:pathData="M0,0h108v108h-108z" />
    <path android:fillColor="#FFF3C9" android:pathData="M26,54a28,28 0 1,0 56,0a28,28 0 1,0 -56,0" />
    <path android:fillColor="#000000" android:pathData="M42,48a24,24 0 1,0 48,0a24,24 0 1,0 -48,0" />
</vector>
'''

JAVA = "android/app/src/main/java/com/joel/skypixel/"

FILES[JAVA + "Alarms.java"] = r'''
package com.joel.skypixel;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.media.AudioAttributes;
import android.media.RingtoneManager;
import android.net.Uri;
import org.json.JSONObject;
import java.util.Map;

public class Alarms {
    static final String PREFS = "sky_alarms";
    static final String CH = "skypixel_alarm_v1";

    static PendingIntent pi(Context c, String id, String title, String body) {
        Intent i = new Intent(c, AlarmReceiver.class);
        i.setAction("com.joel.skypixel.ALARM." + id);
        i.putExtra("id", id);
        i.putExtra("title", title);
        i.putExtra("body", body);
        return PendingIntent.getBroadcast(c, id.hashCode(), i,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    static void schedule(Context c, String id, long at, String title, String body, boolean save) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        PendingIntent show = PendingIntent.getActivity(c, 0, new Intent(c, MainActivity.class),
                PendingIntent.FLAG_IMMUTABLE);
        // alarm clock type: android treats it like a real alarm, even in battery saving
        am.setAlarmClock(new AlarmManager.AlarmClockInfo(at, show), pi(c, id, title, body));
        if (save) {
            try {
                JSONObject o = new JSONObject();
                o.put("t", at);
                o.put("title", title);
                o.put("body", body);
                c.getSharedPreferences(PREFS, 0).edit().putString(id, o.toString()).apply();
            } catch (Exception e) { }
        }
    }

    static void remove(Context c, String id) {
        c.getSharedPreferences(PREFS, 0).edit().remove(id).apply();
    }

    static void rescheduleAll(Context c) {
        SharedPreferences sp = c.getSharedPreferences(PREFS, 0);
        long now = System.currentTimeMillis();
        for (Map.Entry<String, ?> en : sp.getAll().entrySet()) {
            try {
                JSONObject o = new JSONObject((String) en.getValue());
                long t = o.getLong("t");
                if (t > now) schedule(c, en.getKey(), t, o.getString("title"), o.getString("body"), false);
                else remove(c, en.getKey());
            } catch (Exception e) { }
        }
    }

    static void ensureChannel(Context c) {
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm.getNotificationChannel(CH) != null) return;
        NotificationChannel ch = new NotificationChannel(CH, "Sky alarms", NotificationManager.IMPORTANCE_HIGH);
        Uri snd = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
        if (snd == null) snd = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
        ch.setSound(snd, new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_ALARM)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build());
        ch.enableVibration(true);
        ch.setVibrationPattern(new long[]{0, 500, 300, 500, 300, 500});
        ch.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        nm.createNotificationChannel(ch);
    }

    // used when the app is not on screen: floating notification + full screen alarm if the phone is idle/locked
    static void notifyAlarm(Context c, String id, String title, String body) {
        ensureChannel(c);
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        int nid = id.hashCode();

        Intent a = new Intent(c, AlarmActivity.class);
        a.putExtra("id", id);
        a.putExtra("title", title);
        a.putExtra("body", body);
        a.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent full = PendingIntent.getActivity(c, nid, a,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        Intent ok = new Intent(c, OkReceiver.class);
        ok.putExtra("id", id);
        PendingIntent okPi = PendingIntent.getBroadcast(c, nid, ok,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        Notification.Builder b = new Notification.Builder(c, CH)
                .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(new Notification.BigTextStyle().bigText(body))
                .setCategory(Notification.CATEGORY_ALARM)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setAutoCancel(true)
                .setContentIntent(full)
                .setFullScreenIntent(full, true)
                .addAction(new Notification.Action.Builder(0, "OKAY", okPi).build())
                .setTimeoutAfter(120000);
        Notification n = b.build();
        n.flags |= Notification.FLAG_INSISTENT;   // keeps ringing until you tap OKAY
        nm.notify(nid, n);
    }
}
'''

FILES[JAVA + "AlarmReceiver.java"] = r'''
package com.joel.skypixel;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class AlarmReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        String id = intent.getStringExtra("id");
        String title = intent.getStringExtra("title");
        String body = intent.getStringExtra("body");
        if (id == null) return;
        Alarms.remove(ctx, id);
        MainActivity m = MainActivity.visibleInstance;
        if (m != null) {
            m.showInPage(title, body);          // app is open: popup with OKAY inside the app
        } else {
            Alarms.notifyAlarm(ctx, id, title, body);   // app is away: floating notification / full screen alarm
        }
    }
}
'''

FILES[JAVA + "OkReceiver.java"] = r'''
package com.joel.skypixel;

import android.app.NotificationManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class OkReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        String id = intent.getStringExtra("id");
        if (id == null) return;
        ((NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE)).cancel(id.hashCode());
    }
}
'''

FILES[JAVA + "BootReceiver.java"] = r'''
package com.joel.skypixel;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        Alarms.rescheduleAll(ctx);
    }
}
'''

FILES[JAVA + "AlarmActivity.java"] = r'''
package com.joel.skypixel;

import android.app.Activity;
import android.app.NotificationManager;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class AlarmActivity extends Activity {
    String id;

    int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density);
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        if (Build.VERSION.SDK_INT >= 27) {
            setShowWhenLocked(true);
            setTurnScreenOn(true);
        } else {
            getWindow().addFlags(WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
                    | WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON);
        }
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        id = getIntent().getStringExtra("id");
        String title = getIntent().getStringExtra("title");
        String body = getIntent().getStringExtra("body");

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(Color.BLACK);
        root.setPadding(dp(24), dp(24), dp(24), dp(24));

        TextView kind = new TextView(this);
        kind.setText("SKY ALARM");
        kind.setTextColor(Color.parseColor("#FF7EB6"));
        kind.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        kind.setTextSize(16);
        kind.setGravity(Gravity.CENTER);

        TextView t = new TextView(this);
        t.setText(title);
        t.setTextColor(Color.parseColor("#FFD84D"));
        t.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        t.setTextSize(28);
        t.setGravity(Gravity.CENTER);
        t.setPadding(0, dp(18), 0, dp(12));

        TextView d = new TextView(this);
        d.setText(body);
        d.setTextColor(Color.parseColor("#FFF3C9"));
        d.setTypeface(Typeface.MONOSPACE);
        d.setTextSize(19);
        d.setGravity(Gravity.CENTER);
        d.setPadding(0, 0, 0, dp(32));

        Button ok = new Button(this);
        ok.setText("OKAY");
        ok.setTextSize(20);
        ok.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        ok.setTextColor(Color.BLACK);
        ok.setBackgroundColor(Color.parseColor("#7CF5C4"));
        ok.setPadding(dp(48), dp(14), dp(48), dp(14));
        ok.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                stopAlarm();
            }
        });

        root.addView(kind);
        root.addView(t);
        root.addView(d);
        root.addView(ok);
        setContentView(root);
    }

    void stopAlarm() {
        if (id != null) {
            ((NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE)).cancel(id.hashCode());
        }
        finish();
    }

    @Override
    public void onBackPressed() {
        stopAlarm();
    }
}
'''

FILES[JAVA + "MainActivity.java"] = r'''
package com.joel.skypixel;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import org.json.JSONObject;

public class MainActivity extends Activity {
    static MainActivity visibleInstance;
    WebView web;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        web = new WebView(this);
        web.setBackgroundColor(Color.BLACK);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowFileAccessFromFileURLs(true);
        s.setAllowUniversalAccessFromFileURLs(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setTextZoom(100);

        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient());
        web.addJavascriptInterface(new Bridge(), "SkyNative");
        web.loadUrl("file:///android_asset/index.html");

        askNotifyPermission();
    }

    void askNotifyPermission() {
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
        }
    }

    // called by the alarm when the app is open: shows the popup inside the page
    void showInPage(final String title, final String body) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                web.evaluateJavascript("window.notifyNow&&window.notifyNow("
                        + JSONObject.quote(title) + "," + JSONObject.quote(body) + ")", null);
            }
        });
    }

    class Bridge {
        @JavascriptInterface
        public void schedule(String id, String at, String title, String body) {
            try {
                Alarms.schedule(MainActivity.this, id, Long.parseLong(at), title, body, true);
            } catch (Exception e) { }
        }

        @JavascriptInterface
        public void askPermission() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    askNotifyPermission();
                }
            });
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        visibleInstance = this;
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (visibleInstance == this) visibleInstance = null;
    }

    @Override
    public void onBackPressed() {
        web.evaluateJavascript(
                "(function(){try{return window.__back?!!window.__back():false}catch(e){return false}})()",
                new android.webkit.ValueCallback<String>() {
                    @Override
                    public void onReceiveValue(String v) {
                        if (!"true".equals(v)) moveTaskToBack(true);
                    }
                });
    }
}
'''

# ---- write everything ----
for path, text in FILES.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.lstrip("\n"))

assets = "android/app/src/main/assets"
os.makedirs(assets, exist_ok=True)
shutil.copy("index.html", assets + "/index.html")
print("android project ready")
