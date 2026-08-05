[app]

title = Cornix Winner PRO
package.name = cornixwinnerpro
package.domain = com.cornix
source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,json,kv
source.include_patterns = fonts/*,*.png,*.jpg,*.jpeg,*.ttf,*.json
version = 1.0.0

# غیرفعال کردن حالت تمام صفحه (برای ظاهر شدن دکمه‌های پایین و بالای گوشی)
fullscreen = 0

# فعال‌سازی سنسور چرخش خودکار و حالت عمودی/افقی
orientation = all
android.manifest.orientation = fullSensor

# استفاده از شاخه اصلی python-for-android جهت دریافت لینک‌های جدید دانلود
#p4a.branch = master

requirements = python3,kivy,pillow,pyjnius,android

source.main = main.py
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/Cornix.png

android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, MANAGE_EXTERNAL_STORAGE
android.accept_sdk_license = True

android.api = 33
android.minapi = 24
android.ndk = 25b

android.private_storage = False
android.logcat_filters = *:S python:D
android.archs = arm64-v8a
android.androidx = True

[buildozer]
log_level = 2
build_dir = ./.buildozer
bin_dir = ./bin
