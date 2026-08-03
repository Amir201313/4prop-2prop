[app]

# (str) Title of your application
title = Cornix Winner PRO

# (str) Package name
package.name = cornixwinnerpro

# (str) Package domain (needed for android packaging)
package.domain = com.cornix

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (included images, fonts, json)
source.include_exts = py,png,jpg,jpeg,ttf,json,kv

# (list) List of inclusions using pattern matching
source.include_patterns = fonts/*,*.png,*.jpg,*.jpeg,*.ttf,*.json

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# pillow for PIL, pyjnius for Android native file sharing & permissions
requirements = python3,kivy==2.3.0,pillow,pyjnius,android

# (str) Custom source folders for requirements
# Sets the main entry point
source.main = main.py

# (str) Icon of the application (یک عکس با نام icon.png در کنار main.py قرار دهید)
icon.filename = %(source.dir)s/icon.png

# (str) Presplash of the application (عکس اسپلش اسکرین شروع برنامه)
presplash.filename = %(source.dir)s/Cornix.png

# (list) Permissions
# دسترسی‌های کامل حافظه و اینترنت برای اشتراک‌گذاری و ذخیره‌سازی
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, MANAGE_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible (33 or 34)
android.api = 33

# (int) Minimum API required (API 24 = Android 7.0, API 25 = Android 7.1)
android.minapi = 24

# (int) Android NDK version
android.ndk = 25b

# (bool) Use --private data storage (False allows public storage access)
android.private_storage = False

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (list) Android application meta-data to set (key=value)
# تنظیمات جهت اشتراک‌گذاری فایل‌ها با FileProvider
android.add_src = 

# (bool) Copy library instead of making a lib dir
android.copy_libs = 1

# (str) The Android arch to build for
# پشتیبانی از معماری ۶۴ بیتی و ۳۲ بیتی جدیدترین گوشی‌ها
android.archs = arm64-v8a, armeabi-v7a

# (bool) Enable AndroidX support
android.androidx = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./.buildozer

# (str) Path to build output (where the APK will be saved)
bin_dir = ./bin
