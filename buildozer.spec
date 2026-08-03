[app]

# (str) Title of your application
title = Cornix Winner PRO

# (str) Package name
package.name = cornixwinnerpro

# (str) Package domain
package.domain = com.cornix

# (str) Source code location
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,jpeg,ttf,json,kv

# (list) List of inclusions using pattern matching
source.include_patterns = fonts/*,*.png,*.jpg,*.jpeg,*.ttf,*.json

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
requirements = python3,kivy,pillow,pyjnius,android

# (str) Main entry point
source.main = main.py

# (str) Icon & Presplash
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/Cornix.png

# (list) Permissions
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, MANAGE_EXTERNAL_STORAGE

# (bool) Auto-accept SDK license
android.accept_sdk_license = True

# (int) Target & Min API
android.api = 33
android.minapi = 24
android.ndk = 25b

android.private_storage = False
android.logcat_filters = *:S python:D

# (str) The Android arch to build for (معماری استاندارد ۶۴ بیتی)
android.archs = arm64-v8a

android.androidx = True

[buildozer]
log_level = 2
build_dir = ./.buildozer
bin_dir = ./bin
