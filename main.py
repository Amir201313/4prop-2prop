
# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

import sys
import math
import os
import json
import datetime
import platform as py_platform
import webbrowser
import re
import kivy.resources as resources

APP_ROTATION = 0
is_windows = py_platform.system() == 'Windows'

# تنظیمات ابتدایی کیوی (فقط برای ویندوز ابعاد ثابت تعیین می‌شود)
try:
    from kivy.config import Config
    if is_windows:
        Config.set('graphics', 'resizable', False)
        Config.set('graphics', 'width', '800')
        Config.set('graphics', 'height', '450')
    else:
        Config.set('graphics', 'resizable', True)
except Exception:
    pass

# فراخوانی کتابخانه‌های اصلی Kivy (حتماً باید وجود داشته باشند)
try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.widget import Widget
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.popup import Popup
    from kivy.uix.textinput import TextInput
    from kivy.uix.image import Image as KivyImage
    from kivy.core.window import Window
    from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, PushMatrix, PopMatrix, Rotate, Translate
    from kivy.graphics.texture import Texture
    from kivy.properties import NumericProperty, StringProperty, ListProperty, BooleanProperty
    from kivy.metrics import dp, Metrics
    from kivy.clock import Clock
except ModuleNotFoundError:
    print("\n[Error] Kivy library is not installed.")
    sys.exit(1)

# تنظیمات اندازه پنجره فقط در سیستم‌عامل ویندوز
if is_windows:
    try:
        dpi = Metrics.dpi if (hasattr(Metrics, 'dpi') and Metrics.dpi > 0) else 96
        win_w = int(6.10 * dpi)
        win_h = int(3.43 * dpi)
        Window.size = (win_w, win_h)
        Window.rotation = APP_ROTATION
    except Exception:
        Window.size = (800, 450)

try:
    from kivy.core.text import LabelBase
    dejavu_path = resources.resource_find('fonts/DejaVuSans.ttf') or resources.resource_find('DejaVuSans.ttf')
    if dejavu_path:
        LabelBase.register(name='Roboto', fn_regular=dejavu_path, fn_bold=dejavu_path)
except Exception:
    pass

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    try:
        RESAMPLE_FILTER = Image.Resampling.BILINEAR
    except AttributeError:
        RESAMPLE_FILTER = Image.BILINEAR
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageFilter = None
    RESAMPLE_FILTER = None


class KeypadPopup(Popup):
    def __init__(self, target_widget, callback, **kwargs):
        self.target_widget = target_widget
        self.callback = callback
        super().__init__(**kwargs)
        self.title = "Enter Value"
        self.size_hint = (0.8, 0.7)
        self.auto_dismiss = False
        
        content = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(10))
        initial_val = ""
        
        self.txt_input = TextInput(
            text=initial_val, 
            multiline=False, 
            font_size='18sp', 
            size_hint_y=0.2,
            input_filter='float',
            halign='center'
        )
        content.add_widget(self.txt_input)
        
        grid = GridLayout(cols=3, spacing=dp(5), size_hint_y=0.65)
        buttons = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '0', 'C']
        for b_text in buttons:
            btn = Button(text=b_text, font_size='16sp')
            btn.bind(on_release=self.on_btn_press)
            grid.add_widget(btn)
        content.add_widget(grid)
        
        bot_box = BoxLayout(spacing=dp(5), size_hint_y=0.15)
        btn_ok = Button(text="OK", background_color=[0.1, 0.6, 0.2, 1])
        btn_cancel = Button(text="Cancel", background_color=[0.8, 0.2, 0.2, 1])
        btn_ok.bind(on_release=self.on_ok)
        btn_cancel.bind(on_release=self.dismiss)
        bot_box.add_widget(btn_cancel)
        bot_box.add_widget(btn_ok)
        content.add_widget(bot_box)
        self.content = content
        
    def on_btn_press(self, instance):
        val = instance.text
        if val == 'C':
            self.txt_input.text = ""
        else:
            self.txt_input.text += val
            
    def on_ok(self, *args):
        self.dismiss()
        if self.callback:
            self.callback(self.target_widget, self.txt_input.text)


class KeyboardDisplayLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = '18sp'
        self.color = [0.95, 0.95, 0.1, 1]
        self.bold = True
        self.halign = 'center'
        self.valign = 'middle'
        self.bind(size=self.update_graphics, pos=self.update_graphics)

    def update_graphics(self, *args):
        self.text_size = self.size
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 1, 1, 0.2)
            RoundedRectangle(pos=(self.x, self.y - dp(1)), size=self.size, radius=[dp(5)])
            Color(0.1, 0.1, 0.1, 1)
            RoundedRectangle(pos=(self.x + dp(1), self.y + dp(1)), size=(self.width - dp(2), self.height - dp(2)), radius=[dp(5)])
            Color(0, 0, 0, 0.6)
            Line(points=[self.x + dp(2), self.y + self.height - dp(2), self.x + self.width - dp(2), self.y + self.height - dp(2)], width=1.1)


class VirtualKeyboardPopup(Popup):
    def __init__(self, title, callback, default_text="", **kwargs):
        self.callback = callback
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.95, 0.75)
        self.auto_dismiss = False
        self.is_caps = False
        
        content = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(8))
        
        self.txt_input = KeyboardDisplayLabel(text=default_text, size_hint_y=0.15)
        content.add_widget(self.txt_input)
        
        self.grid = GridLayout(cols=10, spacing=dp(4), size_hint_y=0.68)
        
        self.keys_row1 = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        self.keys_row2 = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p']
        self.keys_row3 = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', '_']
        self.keys_row4 = ['Shi', 'z', 'x', 'c', 'v', 'b', 'n', 'm', '-', '<']
        
        self.build_keyboard_grid()
        content.add_widget(self.grid)
        
        bot_box = BoxLayout(spacing=dp(5), size_hint_y=0.17)
        btn_cancel = Button(text="Cancel", background_color=[0.8, 0.2, 0.2, 1], font_size='14sp', bold=True)
        btn_clear = Button(text="Clear", background_color=[0.7, 0.5, 0.1, 1], font_size='14sp', bold=True)
        btn_space = Button(text="Space", background_color=[0.4, 0.4, 0.4, 1], font_size='14sp', bold=True, size_hint_x=1.5)
        btn_ok = Button(text="OK", background_color=[0.1, 0.6, 0.2, 1], font_size='14sp', bold=True)
        
        btn_cancel.bind(on_release=self.dismiss)
        btn_clear.bind(on_release=self.on_clear)
        btn_space.bind(on_release=self.on_space)
        btn_ok.bind(on_release=self.on_ok)
        
        bot_box.add_widget(btn_cancel)
        bot_box.add_widget(btn_clear)
        bot_box.add_widget(btn_space)
        bot_box.add_widget(btn_ok)
        
        content.add_widget(bot_box)
        self.content = content
        
    def build_keyboard_grid(self):
        self.grid.clear_widgets()
        rows = [self.keys_row1, self.keys_row2, self.keys_row3, self.keys_row4]
        for row in rows:
            for char in row:
                display_char = char
                if len(char) == 1 and char.isalpha():
                    display_char = char.upper() if self.is_caps else char.lower()
                    
                btn = Button(text=display_char, font_size='16sp', bold=True)
                btn.bind(on_release=self.on_key_press)
                self.grid.add_widget(btn)
                
    def on_key_press(self, instance):
        val = instance.text
        if val == 'Shi':
            self.is_caps = not self.is_caps
            self.build_keyboard_grid()
        elif val == '<':
            if len(self.txt_input.text) > 0:
                self.txt_input.text = self.txt_input.text[:-1]
        else:
            self.txt_input.text += val
            
    def on_clear(self, *args):
        self.txt_input.text = ""
        
    def on_space(self, *args):
        self.txt_input.text += " "
        
    def on_ok(self, *args):
        self.dismiss()
        if self.callback:
            self.callback(self.txt_input.text)


def create_vertical_gradient(color_top, color_bottom):
    texture = Texture.create(size=(1, 2), colorfmt='rgba')
    buf = bytes([
        int(color_bottom[0]*255), int(color_bottom[1]*255), int(color_bottom[2]*255), int(color_bottom[3]*255),
        int(color_top[0]*255), int(color_top[1]*255), int(color_top[2]*255), int(color_top[3]*255)
    ])
    texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
    return texture


class RotatedLabel(Label):
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas, angle=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            PushMatrix()
            Translate(self.center_x, self.center_y)
            Rotate(angle=self.angle, axis=(0, 0, 1))
            Translate(-self.center_x, -self.center_y)
        self.canvas.after.clear()
        with self.canvas.after:
            PopMatrix()


class MarqueeLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = '18sp'
        self.bold = True
        self.color = [0.15, 0.15, 0.15, 1]
        self.halign = 'center'
        self.valign = 'middle'
        self.text = ""
        self.full_text = "Cornix Winner PRO"
        self.state = "writing"
        self.char_idx = 0
        self.hold_timer = 0.0
        self.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        self.bind(pos=self.draw_bg, size=self.draw_bg)
        Clock.schedule_interval(self.animate, 0.05)

    def draw_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 1, 1, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5)])
            Color(0.8, 0.8, 0.8, 1)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(5)), width=1.1)

    def animate(self, dt):
        if self.state == "writing":
            self.hold_timer += dt
            if self.hold_timer >= 0.15:
                self.hold_timer = 0.0
                self.char_idx += 1
                self.text = self.full_text[:self.char_idx]
                if self.char_idx >= len(self.full_text):
                    self.state = "holding"
                    self.hold_timer = 0.0
        elif self.state == "holding":
            self.hold_timer += dt
            if self.hold_timer >= 5.0:
                self.state = "erasing1"
                self.char_idx = 0
                self.hold_timer = 0.0
        elif self.state == "erasing1":
            self.char_idx += 1
            self.text = self.full_text[self.char_idx:]
            if self.char_idx >= len(self.full_text):
                self.text = self.full_text
                self.state = "flash_delay"
                self.hold_timer = 0.0
        elif self.state == "flash_delay":
            self.hold_timer += dt
            if self.hold_timer >= 0.15:
                self.state = "erasing2"
                self.char_idx = 0
                self.hold_timer = 0.0
        elif self.state == "erasing2":
            self.char_idx += 1
            self.text = self.full_text[self.char_idx:]
            if self.char_idx >= len(self.full_text):
                self.state = "writing"
                self.char_idx = 0
                self.hold_timer = 0.0
                self.text = ""


class PlasticButton(Button):
    btn_color = ListProperty([0.5, 0.5, 0.5, 1])
    btn_pressed_color = ListProperty([0.4, 0.4, 0.4, 1])
    is_active = BooleanProperty(False)

    def __init__(self, btn_color=None, btn_pressed_color=None, **kwargs):
        super().__init__(**kwargs)
        
        if btn_color is not None:
            self.btn_color = btn_color
            
        c_base = self.btn_color
        self.top_color = [min(c + 0.12, 1.0) for c in c_base[:3]] + [c_base[3]]
        self.bottom_color = [max(c - 0.12, 0.0) for c in c_base[:3]] + [c_base[3]]

        if btn_pressed_color is not None:
            self.btn_pressed_color = btn_pressed_color
        else:
            self.btn_pressed_color = [max(c - 0.2, 0) for c in c_base[:3]] + [c_base[3]]

        self.background_color = [0, 0, 0, 0]
        self.font_size = '10sp'
        self.bold = True
        self.color = [0.1, 0.1, 0.1, 1] if sum(self.btn_color[:3])/3 > 0.7 else [1, 1, 1, 1]
        self.halign = 'center'
        self.valign = 'middle'
        
        self.bind(size=self._update_text_size)
        self.normal_texture = create_vertical_gradient(self.top_color, self.bottom_color)
        p_top = [max(c - 0.1, 0) for c in self.btn_pressed_color[:3]] + [1]
        p_bottom = [max(c - 0.25, 0) for c in self.btn_pressed_color[:3]] + [1]
        self.pressed_texture = create_vertical_gradient(p_top, p_bottom)
        
        self.bind(pos=self.draw_button, size=self.draw_button, state=self.draw_button, is_active=self.draw_button)

    def _update_text_size(self, instance, value):
        self.text_size = value

    def draw_button(self, *args):
        if not hasattr(self, 'normal_texture') or not hasattr(self, 'pressed_texture'):
            return
            
        self.canvas.before.clear()
        effectively_pressed = (self.state == 'down' or self.is_active)
        with self.canvas.before:
            if not effectively_pressed:
                Color(0.05, 0.05, 0.05, 0.7)
                RoundedRectangle(pos=(self.x + dp(1), self.y - dp(5)), size=(self.width - dp(2), self.height), radius=[dp(8)])
            Color(0, 0, 0, 0.5) if effectively_pressed else Color(1, 1, 1, 0.35)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            if not effectively_pressed:
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=(self.x + dp(2), self.y + dp(4)), size=(self.width - dp(4), self.height - dp(6)), radius=[dp(7)], texture=self.normal_texture)
            else:
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=(self.x + dp(3), self.y + dp(1)), size=(self.width - dp(6), self.height - dp(6)), radius=[dp(7)], texture=self.pressed_texture)


class RecessedInput(Button):
    value_text = StringProperty("")
    label_text = StringProperty("")
    status_text = StringProperty("")
    bg_color = ListProperty([0.1, 0.1, 0.1, 1])
    text_color = ListProperty([0.95, 0.95, 0.1, 1])
    label_color_hex = StringProperty("#8c8c8c")

    def __init__(self, label_text="", value_text="", bg_color=None, text_color=None, label_color_hex="#8c8c8c", **kwargs):
        super().__init__(**kwargs)
        self.label_text = label_text
        self.value_text = value_text
        if bg_color is not None:
            self.bg_color = bg_color
        if text_color is not None:
            self.text_color = text_color
        self.label_color_hex = label_color_hex
        
        self.background_color = [0, 0, 0, 0]
        self.font_size = '11sp'
        self.bold = True
        self.color = self.text_color
        self.halign = 'center'
        self.valign = 'middle'
        self.bind(pos=self.update_graphics, size=self.update_graphics, value_text=self.update_text, status_text=self.update_text, bg_color=self.update_graphics)
        self.update_text()

    def update_text(self, *args):
        app = App.get_running_app()
        label = self.label_text
        val = self.value_text
        st = f"{self.status_text}\n" if self.status_text else ""
        self.text = f"{st}[size=10sp][color={self.label_color_hex}]{label}[/color][/size]\n{val}"
        self.markup = True

    def update_graphics(self, *args):
        self.text_size = self.size
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 1, 1, 0.25)
            RoundedRectangle(pos=(self.x, self.y - dp(1)), size=self.size, radius=[dp(5)])
            Color(*self.bg_color)
            RoundedRectangle(pos=(self.x + dp(1), self.y + dp(1)), size=(self.width - dp(2), self.height - dp(2)), radius=[dp(5)])
            Color(0, 0, 0, 0.6)
            Line(points=[self.x + dp(2), self.y + self.height - dp(2), self.x + self.width - dp(2), self.y + self.height - dp(2)], width=1.1)


class SplashScreen(FloatLayout):
    def __init__(self, on_dismiss, **kwargs):
        super().__init__(**kwargs)
        self.on_dismiss = on_dismiss
        
        import kivy.resources as resources
        
        bg_img = None
        for ext in ['.jpg', '.png', '.jpeg']:
            found = resources.resource_find(f'Cornix{ext}')
            if found and os.path.exists(found):
                bg_img = found
                break
                
        if not bg_img:
            for ext in ['.jpg', '.png', '.jpeg']:
                if os.path.exists(f'Cornix{ext}'):
                    bg_img = f'Cornix{ext}'
                    break
        
        if bg_img:
            from kivy.uix.image import Image as KivyImage
            self.bg = KivyImage(source=bg_img, allow_stretch=True, keep_ratio=False, size_hint=(1, 1))
            self.add_widget(self.bg)
        else:
            self.bind(pos=self._draw_fallback, size=self._draw_fallback)
            self._draw_fallback()

        Clock.schedule_once(self.dismiss_splash, 7.0)

    def _draw_fallback(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.12, 0.08, 0.04, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.84, 0.68, 0.24, 0.3)
            Line(rectangle=(self.x + dp(10), self.y + dp(10), self.width - dp(20), self.height - dp(20)), width=dp(2))

    def dismiss_splash(self, dt):
        if self.on_dismiss:
            self.on_dismiss()


class MainMenuScreen(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.orientation = 'vertical'
        self.spacing = dp(15)
        self.padding = dp(25)
        self.bind(pos=self.draw_bg, size=self.draw_bg)
        self.rebuild()

    def draw_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.72, 0.72, 0.72, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.65, 0.65, 0.65, 0.2)
            for i in range(0, int(self.height), int(dp(9))):
                Line(points=[self.x, self.y+i, self.x+self.width, self.y+i], width=1)

    def rebuild(self):
        self.clear_widgets()
        
        self.btn_1 = PlasticButton(text="4 Prop Scan", btn_color=[0.56, 0.85, 0.56, 1])
        self.btn_1.bind(on_release=lambda x: self.app.select_mode("4-prop"))
        
        self.btn_3 = PlasticButton(text="Products", btn_color=[0.18, 0.65, 0.28, 1])
        self.btn_3.bind(on_release=self.app.show_products_popup)
        
        self.btn_4 = PlasticButton(text="Contact Us", btn_color=[0.9, 0.7, 0.1, 1])
        self.btn_4.bind(on_release=self.app.show_contact_popup)
        
        self.btn_exit = PlasticButton(text="Exit", btn_color=[0.84, 0.17, 0.12, 1])
        self.btn_exit.bind(on_release=lambda x: sys.exit(0))
        
        self.add_widget(self.btn_1)
        self.add_widget(self.btn_3)
        self.add_widget(self.btn_4)
        self.add_widget(self.btn_exit)


class MonitorView(FloatLayout):
    width_val = NumericProperty(5.0)
    length_val = NumericProperty(5.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lbl_p1 = Label(text="[b]P1[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='11sp', size_hint=(None, None), size=(dp(20), dp(20)))
        self.lbl_p2 = Label(text="[b]P2[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='11sp', size_hint=(None, None), size=(dp(20), dp(20)))
        self.lbl_p3 = Label(text="[b]P3[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='11sp', size_hint=(None, None), size=(dp(20), dp(20)))
        self.lbl_p4 = Label(text="[b]P4[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='11sp', size_hint=(None, None), size=(dp(20), dp(20)))
        self.lbl_y = Label(text="[b]Y[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='15sp', size_hint=(None, None), size=(dp(20), dp(20)))
        self.lbl_x = Label(text="[b]X[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='15sp', size_hint=(None, None), size=(dp(20), dp(20)))
        
        self.lbl_p1p2 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))
        self.lbl_p2p4 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))
        self.lbl_p4p3 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))
        self.lbl_p3p1 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))
        self.lbl_p1p4 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))
        self.lbl_p2p3 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))

        self.lbl_filename = Label(text="", color=[0.1, 0.1, 0.1, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(150), dp(25)), halign='left', valign='middle')
        self.lbl_filename.bind(size=lambda inst, val: setattr(inst, 'text_size', val))

        self.watermark_layout = FloatLayout(size_hint=(1, 1))
        self.watermark_lbl = Label(text="[color=#00000012]Cornix\nWinner PRO[/color]", markup=True, bold=True, halign='center', valign='middle', size_hint=(None, None))
        self.watermark_layout.add_widget(self.watermark_lbl)

        self.btn_help = PlasticButton(text="Help", btn_color=[0.11, 0.51, 0.84, 1], size_hint=(None, None), size=(dp(90), dp(33)))
        self.btn_help.bind(on_release=self.on_help_click)
        self.btn_help.opacity = 0
        self.btn_help.disabled = True
        
        for w in [self.watermark_layout, self.lbl_p1, self.lbl_p2, self.lbl_p3, self.lbl_p4, self.lbl_y, self.lbl_x,
                  self.lbl_p1p2, self.lbl_p2p4, self.lbl_p4p3, self.lbl_p3p1, self.lbl_p1p4, self.lbl_p2p3, self.lbl_filename,
                  self.btn_help]:
            self.add_widget(w)
        self.bind(pos=self.redraw, size=self.redraw, width_val=self.redraw, length_val=self.redraw)

    def on_help_click(self, instance):
        app = App.get_running_app()
        if app:
            app.show_contamination_help()

    def redraw(self, *args):
        self.canvas.before.clear()
        
        margin_left = dp(26)
        margin_right = dp(26)
        margin_bottom = dp(26)
        
        app = App.get_running_app()
        if app and app.loaded_scan_name:
            margin_top = dp(34)
        else:
            margin_top = dp(26)
        
        max_w = max(dp(10), self.width - margin_left - margin_right)
        max_h = max(dp(10), self.height - margin_bottom - margin_top)
        
        if app:
            self.width_val = app.width_val
            self.length_val = app.length_val
            
        aspect_ratio = self.width_val / max(self.length_val, 0.1)
        if aspect_ratio > (max_w / max_h):
            rect_w = max_w
            rect_h = max_w / aspect_ratio
        else:
            rect_h = max_h
            rect_w = max_h * aspect_ratio
            
        rect_x = self.x + margin_left + (max_w - rect_w) / 2
        rect_y = self.y + margin_bottom + (max_h - rect_h) / 2
        
        self.lbl_p1.pos = (rect_x - self.lbl_p1.width - dp(2), rect_y - self.lbl_p1.height - dp(2))
        self.lbl_p2.pos = (rect_x + rect_w + dp(2), rect_y - self.lbl_p2.height - dp(2))
        self.lbl_p3.pos = (rect_x - self.lbl_p3.width - dp(2), rect_y + rect_h + dp(2))
        self.lbl_p4.pos = (rect_x + rect_w + dp(2), rect_y + rect_h + dp(2))
        
        if app:
            e = app.ui_entry_values
            self.lbl_p1p2.text = e.get("p1p2", "")
            self.lbl_p2p4.text = e.get("p2p4", "")
            self.lbl_p4p3.text = e.get("p4p3", "")
            self.lbl_p3p1.text = e.get("p3p1", "")
            self.lbl_p1p4.text = e.get("p1p4", "")
            self.lbl_p2p3.text = e.get("p2p3", "")
        
        self.lbl_p1p2.pos = (rect_x + rect_w / 2 - self.lbl_p1p2.width / 2, rect_y - self.lbl_p1p2.height + dp(2))
        self.lbl_p4p3.pos = (rect_x + rect_w / 2 - self.lbl_p4p3.width / 2, rect_y + rect_h + dp(1))

        self.lbl_p1p2.angle = 0
        self.lbl_p4p3.angle = 0
        self.lbl_p2p4.angle = 270
        self.lbl_p3p1.angle = 90
        
        theta = math.atan2(rect_h, rect_w)
        self.lbl_p1p4.angle = math.degrees(theta)
        self.lbl_p2p3.angle = -math.degrees(theta)

        if app and app.loaded_scan_name:
            self.lbl_filename.text = app.loaded_scan_name
            p4p3_w = self.lbl_p4p3.width if self.lbl_p4p3.width > 0 else dp(40)
            start_x = rect_x + dp(12)
            end_x = rect_x + rect_w / 2 - p4p3_w / 2 - dp(8)
            available_width = max(dp(50), end_x - start_x)
            name_len = len(app.loaded_scan_name) if len(app.loaded_scan_name) > 0 else 1
            calc_font_size = available_width / (name_len * 0.65)
            font_size_dp = min(dp(13), max(dp(8), calc_font_size))
            self.lbl_filename.font_size = font_size_dp
            self.lbl_filename.size = (available_width, dp(25))
            self.lbl_filename.pos = (start_x, rect_y + rect_h + dp(3))
            self.lbl_filename.opacity = 1
        else:
            self.lbl_filename.text = ""
            self.lbl_filename.opacity = 0
        
        self.lbl_p2p4.center_x = rect_x + rect_w + dp(12)
        self.lbl_p2p4.center_y = rect_y + rect_h / 2
        self.lbl_p3p1.center_x = rect_x - dp(12)
        self.lbl_p3p1.center_y = rect_y + rect_h / 2
        
        shift_chord_dist = dp(10) + dp(3)
        dx = - shift_chord_dist * math.sin(theta)
        dy = shift_chord_dist * math.cos(theta)
        
        self.lbl_p1p4.center_x = rect_x + rect_w * 0.33 + dx
        self.lbl_p1p4.center_y = rect_y + rect_h * 0.33 + dy
        self.lbl_p2p3.center_x = rect_x + rect_w * 0.67 - dx
        self.lbl_p2p3.center_y = rect_y + rect_h * 0.33 + dy

        target_w = rect_w - dp(100)
        target_h = rect_h - dp(100)
        S_w = target_w / 3.9
        S_h = target_h / 2.4
        S = max(dp(12), min(S_w, S_h))
        
        self.watermark_lbl.font_size = f"{int(S)}dp"
        self.watermark_lbl.pos = (rect_x, rect_y + dp(15))
        self.watermark_lbl.size = (rect_w, rect_h)
        self.watermark_lbl.text_size = (rect_w, rect_h)

        self.watermark_layout.canvas.before.clear()
        self.watermark_layout.canvas.after.clear()
            
        with self.canvas.before:
            Color(0.85, 0.85, 0.85, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.78, 0.78, 0.78, 0.4)
            for i in range(0, int(self.height), int(dp(6))):
                Line(points=[self.x, self.y + i, self.x + self.width, self.y + i], width=0.8)
            
            if app:
                text = app.get_render_texture()
                if text:
                    Color(1, 1, 1, 1)
                    Rectangle(pos=(rect_x, rect_y), size=(rect_w, rect_h), texture=text)
                    self.watermark_lbl.opacity = 0
                else:
                    Color(0, 0, 0, 1)
                    Line(rectangle=(rect_x, rect_y, rect_w, rect_h), width=2)
                    self.draw_dashed(rect_x, rect_y, rect_x + rect_w, rect_y + rect_h)
                    self.draw_dashed(rect_x, rect_y + rect_h, rect_x + rect_w, rect_y)
                    self.watermark_lbl.opacity = 1
            else:
                Color(0, 0, 0, 1)
                Line(rectangle=(rect_x, rect_y, rect_w, rect_h), width=2)
                self.watermark_lbl.opacity = 1
                
            Color(0, 0, 0, 1)
            for px, py in [(rect_x, rect_y), (rect_x + rect_w, rect_y), (rect_x, rect_y + rect_h), (rect_x + rect_w, rect_y + rect_h)]:
                Line(circle=(px, py, 4), width=1.8)
            
            ax_y = self.y + dp(12)
            Line(points=[rect_x, ax_y, rect_x + dp(30), ax_y], width=1.5)
            Line(points=[rect_x + dp(24), ax_y - dp(4), rect_x + dp(30), ax_y, rect_x + dp(24), ax_y + dp(4)], width=1.5)
            
            ay_x = self.x + dp(12)
            Line(points=[ay_x, rect_y, ay_x, rect_y + dp(30)], width=1.5)
            Line(points=[ay_x - dp(4), rect_y + dp(24), ay_x, rect_y + dp(30), ay_x + dp(4), rect_y + dp(24)], width=1.5)

            if app and app.active_mode == "4-prop" and app.warning_arrows and not app.soil_contaminated and not app.gpr_active and not app.fibo_active and not app.compare_active:
                Color(0, 0, 0, 1)
                for arr in app.warning_arrows:
                    side_key = arr.get("side_key")
                    if not side_key:
                        continue
                    if side_key == "p1p2":
                        ax = rect_x + rect_w / 3.0
                        ay_start = rect_y - dp(2)
                        ay_end = rect_y - dp(14)
                        Line(points=[ax, ay_start, ax, ay_end], width=1.5)
                        Line(points=[ax - dp(3), ay_end + dp(3), ax, ay_end, ax + dp(3), ay_end + dp(3)], width=1.5)
                    elif side_key == "p4p3":
                        ax = rect_x + rect_w / 3.0
                        ay_start = rect_y + rect_h + dp(2)
                        ay_end = rect_y + rect_h + dp(14)
                        Line(points=[ax, ay_start, ax, ay_end], width=1.5)
                        Line(points=[ax - dp(3), ay_end - dp(3), ax, ay_end, ax + dp(3), ay_end - dp(3)], width=1.5)
                    elif side_key == "p3p1":
                        ax_start = rect_x - dp(2)
                        ax_end = rect_x - dp(14)
                        ay = rect_y + rect_h / 3.0
                        Line(points=[ax_start, ay, ax_end, ay], width=1.5)
                        Line(points=[ax_end + dp(3), ay - dp(3), ax_end, ay, ax_end + dp(3), ay + dp(3)], width=1.5)
                    elif side_key == "p2p4":
                        ax_start = rect_x + rect_w + dp(2)
                        ax_end = rect_x + rect_w + dp(14)
                        ay = rect_y + rect_h / 3.0
                        Line(points=[ax_start, ay, ax_end, ay], width=1.5)
                        Line(points=[ax_end - dp(3), ay - dp(3), ax_end, ay, ax_end - dp(3), ay + dp(3)], width=1.5)

        self.lbl_x.pos = (rect_x + dp(32), ax_y - dp(10))
        self.lbl_y.pos = (ay_x - dp(10), rect_y + dp(32))

        if app and app.soil_contaminated and not app.get_cut_segments():
            self.btn_help.text = "Help"
            self.btn_help.opacity = 1
            self.btn_help.disabled = False
            face_center_y = rect_y + rect_h / 2
            face_radius_y = rect_h * 0.15
            self.btn_help.center_x = rect_x + rect_w / 2
            self.btn_help.top = face_center_y - face_radius_y - dp(15)
        else:
            self.btn_help.opacity = 0
            self.btn_help.disabled = True

    def draw_dashed(self, x1, y1, x2, y2):
        dist = math.hypot(x2-x1, y2-y1)
        if dist == 0:
            return
        ux, uy = (x2-x1)/dist, (y2-y1)/dist
        for i in range(int(dist // 15)):
            sx, sy = x1 + i*15*ux, y1 + i*15*uy
            ex, ey = sx + 9*ux, sy + 9*uy
            Line(points=[sx, sy, ex, ey], width=1.2)


class TwoPropMonitor(FloatLayout):
    def __init__(self, screen, **kwargs):
        super().__init__(**kwargs)
        self.screen = screen
        self.lbl_p1 = Label(text="[b]P1[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='11sp', size_hint=(None, None), size=(dp(20), dp(20)))
        self.lbl_p2 = Label(text="[b]P2[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='11sp', size_hint=(None, None), size=(dp(20), dp(20)))
        self.lbl_p3 = Label(text="[b]P3[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='11sp', size_hint=(None, None), size=(dp(20), dp(20)))
        self.lbl_p4 = Label(text="[b]P4[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='11sp', size_hint=(None, None), size=(dp(20), dp(20)))
        self.lbl_y = Label(text="[b]Y[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='15sp', size_hint=(None, None), size=(dp(20), dp(20)))
        self.lbl_x = Label(text="[b]X[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='15sp', size_hint=(None, None), size=(dp(20), dp(20)))
        
        self.lbl_filename = Label(text="", color=[0.1, 0.1, 0.1, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(150), dp(25)), halign='left', valign='middle')
        self.lbl_filename.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        
        for w in [self.lbl_p1, self.lbl_p2, self.lbl_p3, self.lbl_p4, self.lbl_x, self.lbl_y, self.lbl_filename]:
            self.add_widget(w)
        self.bind(pos=self.redraw, size=self.redraw)

    def redraw(self, *args):
        self.canvas.before.clear()
        
        margin_left = dp(7)
        margin_right = dp(31)
        margin_bottom = dp(7)
        margin_top = dp(31)
        
        max_w = max(dp(10), self.width - margin_left - margin_right)
        max_h = max(dp(10), self.height - margin_bottom - margin_top)
        
        aspect_ratio = self.screen.width_val / max(self.screen.length_val, 0.1)
        if aspect_ratio > (max_w / max_h):
            rect_w = max_w
            rect_h = max_w / aspect_ratio
        else:
            rect_h = max_h
            rect_w = max_h * aspect_ratio
            
        rect_x = self.x + self.width - margin_right - rect_w
        rect_y = self.y + self.height - margin_top - rect_h
        
        font_dots = self.screen.app.get_pil_font(12, bold=True)
        max_tw_y = 0
        for idx, val in self.screen.line_values_y.items():
            lbl_text = f"Lin {idx}  {val:.1f}"
            try:
                img_dummy = Image.new("RGBA", (1, 1))
                draw_dummy = ImageDraw.Draw(img_dummy)
                bbox = draw_dummy.textbbox((0, 0), lbl_text, font=font_dots)
                tw = bbox[2] - bbox[0]
            except Exception:
                try:
                    img_dummy = Image.new("RGBA", (1, 1))
                    draw_dummy = ImageDraw.Draw(img_dummy)
                    tw, _ = draw_dummy.textsize(lbl_text, font=font_dots)
                except Exception:
                    tw = len(lbl_text) * 7.5
            if tw > max_tw_y:
                max_tw_y = tw
        if max_tw_y == 0:
            max_tw_y = 90.0

        max_tw_x = 0
        for idx, val in self.screen.line_values_x.items():
            lbl_text = f"Lin {idx}  {val:.1f}"
            try:
                img_dummy = Image.new("RGBA", (1, 1))
                draw_dummy = ImageDraw.Draw(img_dummy)
                bbox = draw_dummy.textbbox((0, 0), lbl_text, font=font_dots)
                tw = bbox[2] - bbox[0]
            except Exception:
                try:
                    img_dummy = Image.new("RGBA", (1, 1))
                    draw_dummy = ImageDraw.Draw(img_dummy)
                    tw, _ = draw_dummy.textsize(lbl_text, font=font_dots)
                except Exception:
                    tw = len(lbl_text) * 7.5
            if tw > max_tw_x:
                max_tw_x = tw
        if max_tw_x == 0:
            max_tw_x = 90.0

        margin_left_pil = 60.0 + max_tw_y / 2.0
        margin_right_pil = 40.0
        margin_top_pil = 40.0
        margin_bottom_pil = margin_left_pil
        
        max_w_pil = 800.0 - margin_left_pil - margin_right_pil
        max_h_pil = 800.0 - margin_bottom_pil - margin_top_pil
        
        if aspect_ratio > (max_w_pil / max_h_pil):
            qw_pil = max_w_pil
            qh_pil = max_w_pil / aspect_ratio
        else:
            qh_pil = max_h_pil
            qw_pil = max_h_pil * aspect_ratio
            
        qx_pil = margin_left_pil
        qy_pil = 800.0 - margin_bottom_pil - qh_pil
        
        rx_ratio = qx_pil / 800.0
        rw_ratio = qw_pil / 800.0
        ry_ratio = (800.0 - (qy_pil + qh_pil)) / 800.0
        rh_ratio = qh_pil / 800.0
        
        quad_x = rect_x + rx_ratio * rect_w
        quad_y = rect_y + ry_ratio * rect_h
        quad_w = rw_ratio * rect_w
        quad_h = rh_ratio * rect_h
        
        self.lbl_p1.pos = (quad_x - self.lbl_p1.width - dp(10), quad_y - self.lbl_p1.height - dp(12))
        self.lbl_p2.pos = (quad_x + quad_w + dp(2), quad_y - self.lbl_p2.height - dp(12))
        self.lbl_p3.pos = (quad_x - self.lbl_p3.width - dp(2), quad_y + quad_h + dp(2))
        self.lbl_p4.pos = (quad_x + quad_w + dp(2), quad_y + quad_h + dp(2))
        
        if self.screen.app and self.screen.app.loaded_scan_name:
            self.lbl_filename.text = self.screen.app.loaded_scan_name
            start_x = quad_x + dp(12)
            end_x = quad_x + quad_w / 2 - dp(20)
            available_width = max(dp(50), end_x - start_x)
            name_len = len(self.screen.app.loaded_scan_name) if len(self.screen.app.loaded_scan_name) > 0 else 1
            calc_font_size = available_width / (name_len * 0.65)
            font_size_dp = min(dp(13), max(dp(8), calc_font_size))
            self.lbl_filename.font_size = font_size_dp
            self.lbl_filename.size = (available_width, dp(25))
            self.lbl_filename.pos = (start_x, quad_y + quad_h + dp(3))
            self.lbl_filename.opacity = 1
        else:
            self.lbl_filename.text = ""
            self.lbl_filename.opacity = 0
            
        with self.canvas.before:
            Color(0.85, 0.85, 0.85, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            tex = self.screen.get_render_texture()
            if tex:
                Color(1, 1, 1, 1)
                Rectangle(pos=(rect_x, rect_y), size=(rect_w, rect_h), texture=tex)
                self.lbl_x.opacity = 0
                self.lbl_y.opacity = 0
            else:
                self.lbl_x.opacity = 1
                self.lbl_y.opacity = 1
                
                Color(0, 0, 0, 1)
                Line(points=[quad_x, quad_y, quad_x + quad_w, quad_y], width=2)
                Line(points=[quad_x + quad_w, quad_y, quad_x + quad_w, quad_y + quad_h], width=2)
                Line(points=[quad_x + quad_w, quad_y + quad_h, quad_x, quad_y + quad_h], width=2)
                Line(points=[quad_x, quad_y + quad_h, quad_x, quad_y], width=2)
                
                if self.screen.show_grid_lines_and_targets:
                    N_x = self.screen.inpuls_x
                    if N_x > 0:
                        for i in range(N_x):
                            dx = i * (quad_w / max(1, N_x - 1)) if N_x > 1 else 0
                            Color(0, 0, 0, 1)
                            Line(circle=(quad_x + dx, quad_y, 4), width=1.5)
                            Line(circle=(quad_x + dx, quad_y + quad_h, 4), width=1.5)
                            
                    N_y = self.screen.inpuls_y
                    if N_y > 0:
                        for j in range(N_y):
                            dy = j * (quad_h / max(1, N_y - 1)) if N_y > 1 else 0
                            Color(0, 0, 0, 1)
                            Line(circle=(quad_x, quad_y + dy, 4), width=1.5)
                            Line(circle=(quad_x + quad_w, quad_y + dy, 4), width=1.5)
                            
                    for idx, val in self.screen.line_values_x.items():
                        if idx <= N_x:
                            dx = (idx - 1) * (quad_w / max(1, N_x - 1)) if N_x > 1 else 0
                            if idx == self.screen.active_line_x:
                                Color(1, 0, 0, 1)
                            else:
                                Color(0, 0, 0, 0.4)
                            Line(points=[quad_x + dx, quad_y, quad_x + dx, quad_y + quad_h], width=1.2)
                            
                    for idx, val in self.screen.line_values_y.items():
                        if idx <= N_y:
                            dy = (idx - 1) * (quad_h / max(1, N_y - 1)) if N_y > 1 else 0
                            if idx == self.screen.active_line_y:
                                Color(1, 0, 0, 1)
                            else:
                                Color(0, 0, 0, 0.4)
                            Line(points=[quad_x, quad_y + dy, quad_x + quad_w, quad_y + dy], width=1.2)

                ax_y = quad_y - dp(16)
                ax_start = quad_x + dp(4)
                ax_end = quad_x + dp(34)
                Line(points=[ax_start, ax_y, ax_end, ax_y], width=1.5)
                Line(points=[ax_end - dp(5), ax_y - dp(3.5), ax_end, ax_y, ax_end - dp(5), ax_y + dp(3.5)], width=1.5)
                
                ay_x = quad_x - dp(16)
                ay_start = quad_y + dp(4)
                ay_end = quad_y + dp(34)
                Line(points=[ay_x, ay_start, ay_x, ay_end], width=1.5)
                Line(points=[ay_x - dp(3.5), ay_end - dp(5), ay_x, ay_end, ay_x + dp(3.5), ay_end - dp(5)], width=1.5)
                
                self.lbl_x.pos = (quad_x + dp(36), quad_y - dp(26))
                self.lbl_y.pos = (quad_x - dp(26), quad_y + dp(36))

            all_lines = {}
            for k, v in self.screen.line_values_x.items():
                all_lines[('x', k)] = v
            for k, v in self.screen.line_values_y.items():
                all_lines[('y', k)] = v
                
            if all_lines:
                N_x = self.screen.inpuls_x
                N_y = self.screen.inpuls_y
                ref = getattr(self.screen, 'ref_soil_val', 600.0)
                
                sides_to_draw = set()
                
                min_item = min(all_lines.items(), key=lambda t: t[1])
                min_type, min_idx = min_item[0]
                if (min_type == 'x' and min_idx in (1, N_x)) or (min_type == 'y' and min_idx in (1, N_y)):
                    sides_to_draw.add((min_type, min_idx))
                    
                outer_adj_pairs = []
                if N_x >= 2:
                    outer_adj_pairs.append(('x', 1, 2))
                    outer_adj_pairs.append(('x', N_x, N_x - 1))
                if N_y >= 2:
                    outer_adj_pairs.append(('y', 1, 2))
                    outer_adj_pairs.append(('y', N_y, N_y - 1))
                    
                for side_type, outer_idx, adj_idx in outer_adj_pairs:
                    val_outer = self.screen.line_values_x.get(outer_idx) if side_type == 'x' else self.screen.line_values_y.get(outer_idx)
                    val_adj = self.screen.line_values_x.get(adj_idx) if side_type == 'x' else self.screen.line_values_y.get(adj_idx)
                    
                    if val_outer is not None and val_adj is not None:
                        if self.screen.app and hasattr(self.screen.app, 'normalize_value_to_600'):
                            norm_outer = self.screen.app.normalize_value_to_600(val_outer, ref)
                            norm_adj = self.screen.app.normalize_value_to_600(val_adj, ref)
                        else:
                            norm_outer = val_outer
                            norm_adj = val_adj
                            
                        if norm_outer <= 500.0 and (norm_adj - norm_outer) >= 100.0:
                            sides_to_draw.add((side_type, outer_idx))
                            
                for side_type, outer_idx in sides_to_draw:
                    Color(1, 0, 0, 1)
                    if side_type == 'x':
                        dx = (outer_idx - 1) * (quad_w / max(1, N_x - 1)) if N_x > 1 else quad_w / 2.0
                        ax = quad_x + dx
                        ay_mid = quad_y + quad_h / 2.0
                        if outer_idx == 1:
                            Line(points=[ax + dp(18), ay_mid, ax + dp(2), ay_mid], width=2)
                            Line(points=[ax + dp(8), ay_mid - dp(5), ax + dp(2), ay_mid, ax + dp(8), ay_mid + dp(5)], width=2)
                        else:
                            Line(points=[ax - dp(18), ay_mid, ax - dp(2), ay_mid], width=2)
                            Line(points=[ax - dp(8), ay_mid - dp(5), ax - dp(2), ay_mid, ax - dp(8), ay_mid + dp(5)], width=2)
                    else:
                        dy = (outer_idx - 1) * (quad_h / max(1, N_y - 1)) if N_y > 1 else quad_h / 2.0
                        ay = quad_y + dy
                        ax_mid = quad_x + quad_w / 2.0
                        if outer_idx == 1:
                            Line(points=[ax_mid, ay + dp(18), ax_mid, ay + dp(2)], width=2)
                            Line(points=[ax_mid - dp(5), ay + dp(8), ax_mid, ay + dp(2), ax_mid + dp(5), ay + dp(8)], width=2)
                        else:
                            Line(points=[ax_mid, ay - dp(18), ax_mid, ay - dp(2)], width=2)
                            Line(points=[ax_mid - dp(5), ay - dp(8), ax_mid, ay - dp(2), ax_mid + dp(5), ay - dp(8)], width=2)


class TwoPropScreen(BoxLayout):
    show_grid_lines_and_targets = BooleanProperty(True)

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.orientation = 'vertical'
        self.spacing = dp(6)
        self.padding = dp(6)
        
        self.width_val = 5.0
        self.length_val = 5.0
        self.ref_soil_val = 600.0
        self.inpuls_x = 10
        self.inpuls_y = 10
        
        self.active_line_x = 1
        self.active_line_y = 1
        
        self.line_values_x = {}
        self.line_values_y = {}
        
        self.detected_targets = []
        self.heatmap_grid = None
        self.tunnel_region = None
        self._cached_render_texture = None
        self.is_analyzed = False
        self.active_box = "x"

        self.monitor = TwoPropMonitor(screen=self)
        self.control_panel = BoxLayout(orientation='vertical', spacing=dp(4))
        
        self.targets_layout = BoxLayout(orientation='horizontal', spacing=dp(4), size_hint_y=0.35)
        
        self.inputs_row = BoxLayout(spacing=dp(3), size_hint_y=0.15)
        self.in_w = RecessedInput(label_text="Width", value_text="5.0 M", size_hint_x=0.2)
        self.in_l = RecessedInput(label_text="Lenght", value_text="5.0 M", size_hint_x=0.2)
        self.in_ref = RecessedInput(label_text="Soil Ref", value_text="600", size_hint_x=0.2)
        self.in_inpuls_x = RecessedInput(label_text="Inpuls X", value_text="10", size_hint_x=0.2)
        self.in_inpuls_y = RecessedInput(label_text="Inpuls Y", value_text="10", size_hint_x=0.2)
        
        for i in [self.in_w, self.in_l, self.in_ref, self.in_inpuls_x, self.in_inpuls_y]:
            i.bind(on_release=self.open_keypad)
            
        self.inputs_row.add_widget(self.in_w)
        self.inputs_row.add_widget(self.in_l)
        self.inputs_row.add_widget(self.in_ref)
        self.inputs_row.add_widget(self.in_inpuls_x)
        self.inputs_row.add_widget(self.in_inpuls_y)
        
        self.lines_row = BoxLayout(spacing=dp(3), size_hint_y=0.28)
        
        self.box_input_x_container = BoxLayout(orientation='vertical', spacing=dp(1), size_hint_x=0.25)
        self.in_x_line = RecessedInput(label_text="input X\nLine", value_text="Line 1 (0.0)")
        self.in_x_line.bind(on_release=self.touch_x_line)
        
        self.arrows_x_layout = BoxLayout(spacing=dp(2), size_hint_y=0.55)
        self.btn_left_x = Button(text="<", font_size='16sp')
        self.btn_right_x = Button(text=">", font_size='16sp')
        self.btn_left_x.bind(on_release=self.shift_left_x)
        self.btn_right_x.bind(on_release=self.shift_right_x)
        self.arrows_x_layout.add_widget(self.btn_left_x)
        self.arrows_x_layout.add_widget(self.btn_right_x)
        
        self.box_input_x_container.add_widget(self.in_x_line)
        self.box_input_x_container.add_widget(self.arrows_x_layout)
        
        self.box_input_y_container = BoxLayout(orientation='vertical', spacing=dp(1), size_hint_x=0.25)
        self.in_y_line = RecessedInput(label_text="input Y\nLine", value_text="Line 1 (0.0)")
        self.in_y_line.bind(on_release=self.touch_y_line)
        
        self.arrows_y_layout = BoxLayout(spacing=dp(2), size_hint_y=0.55)
        self.btn_left_y = Button(text="v", font_size='16sp')
        self.btn_right_y = Button(text="^", font_size='16sp')
        self.btn_left_y.bind(on_release=self.shift_left_y)
        self.btn_right_y.bind(on_release=self.shift_right_y)
        self.arrows_y_layout.add_widget(self.btn_left_y)
        self.arrows_y_layout.add_widget(self.btn_right_y)
        
        self.box_input_y_container.add_widget(self.in_y_line)
        self.box_input_y_container.add_widget(self.arrows_y_layout)
        
        self.btn_start = PlasticButton(text="Start\n for\n analysis", btn_color=[0.9, 0.2, 0.45, 1], size_hint_x=0.3)
        self.btn_start.font_size = '18sp'
        self.btn_start.bold = True
        self.btn_start.outline_width = 1.5
        self.btn_start.outline_color = [0, 0, 0, 1]
        self.btn_start.bind(on_release=self.run_twoprop_scan)
        
        self.lines_row.add_widget(self.box_input_x_container)
        self.lines_row.add_widget(self.box_input_y_container)
        self.lines_row.add_widget(self.btn_start)
        
        self.action_row_top = BoxLayout(spacing=dp(3), size_hint_y=0.11)
        self.btn_reset = PlasticButton(text="Reset", btn_color=[0.9, 0.7, 0.1, 1])
        self.btn_reset.bind(on_release=self.reset_twoprop)
        
        self.btn_grid = PlasticButton(text="Mesh    Off / On", btn_color=[0.11, 0.6, 0.6, 1])
        self.btn_grid.bind(on_release=self.toggle_grid)
        self.btn_grid.is_active = True
        
        self.btn_back = PlasticButton(text="4 Prop Scan", btn_color=[0.5, 0.5, 0.5, 1])
        self.btn_back.bind(on_release=lambda x: self.app.switch_to_fourprop())
        
        self.action_row_top.add_widget(self.btn_reset)
        self.action_row_top.add_widget(self.btn_grid)
        self.action_row_top.add_widget(self.btn_back)
        
        self.action_row_mid = BoxLayout(spacing=dp(3), size_hint_y=0.11)
        self.btn_save = PlasticButton(text="Save", btn_color=[0.1, 0.6, 0.2, 1])
        self.btn_save.bind(on_release=self.show_combined_save_popup)
        self.btn_recall = PlasticButton(text="Recall", btn_color=[1, 0.4, 0.7, 1])
        self.btn_recall.bind(on_release=self.show_combined_recall_popup)
        self.action_row_mid.add_widget(self.btn_save)
        self.action_row_mid.add_widget(self.btn_recall)
        
        self.control_panel.add_widget(self.targets_layout)
        self.control_panel.add_widget(self.inputs_row)
        self.control_panel.add_widget(self.lines_row)
        self.control_panel.add_widget(self.action_row_top)
        self.control_panel.add_widget(self.action_row_mid)
        
        self.add_widget(self.monitor)
        self.add_widget(self.control_panel)
        
        self.bind(pos=self.on_resize, size=self.on_resize)
        self.update_active_box_ui()
        self.update_line_input_labels()
        self.update_target_boxes()

    def update_active_box_ui(self):
        if getattr(self, 'active_box', 'x') == "x":
            self.in_x_line.bg_color = [0.1, 0.1, 0.1, 1]
            self.in_x_line.status_text = "[color=#FF0000][size=9sp]Press the Start[/size][/color]"
            self.btn_left_x.disabled = False
            self.btn_right_x.disabled = False
            self.btn_left_x.opacity = 1.0
            self.btn_right_x.opacity = 1.0

            self.in_y_line.bg_color = [0.35, 0.35, 0.35, 1]
            self.in_y_line.status_text = ""
            self.btn_left_y.disabled = True
            self.btn_right_y.disabled = True
            self.btn_left_y.opacity = 0.4
            self.btn_right_y.opacity = 0.4
        else:
            self.in_x_line.bg_color = [0.35, 0.35, 0.35, 1]
            self.in_x_line.status_text = ""
            self.btn_left_x.disabled = True
            self.btn_right_x.disabled = True
            self.btn_left_x.opacity = 0.4
            self.btn_right_x.opacity = 0.4

            self.in_y_line.bg_color = [0.1, 0.1, 0.1, 1]
            self.in_y_line.status_text = "[color=#FF0000][size=9sp]Press the Start[/size][/color]"
            self.btn_left_y.disabled = False
            self.btn_right_y.disabled = False
            self.btn_left_y.opacity = 1.0
            self.btn_right_y.opacity = 1.0

        self.in_x_line.update_graphics()
        self.in_y_line.update_graphics()

    def touch_x_line(self, *args):
        if self.active_box != "x":
            self.active_box = "x"
            self.update_active_box_ui()
        else:
            self.open_x_line_keypad(self.in_x_line)

    def touch_y_line(self, *args):
        if self.active_box != "y":
            self.active_box = "y"
            self.update_active_box_ui()
        else:
            self.open_y_line_keypad(self.in_y_line)

    def toggle_grid(self, *args):
        self.show_grid_lines_and_targets = not self.show_grid_lines_and_targets
        self.btn_grid.is_active = self.show_grid_lines_and_targets
        self.invalidate_render_cache()
        self.monitor.redraw()

    def show_combined_save_popup(self, *args):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        btn_save_file = PlasticButton(text="Save file Scan", btn_color=[0.1, 0.5, 0.8, 1], size_hint_y=0.33)
        btn_save_pic = PlasticButton(text="Save picture Scan", btn_color=[0.1, 0.6, 0.2, 1], size_hint_y=0.33)
        btn_cancel = PlasticButton(text="Cancel", btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.33)
        
        popup = Popup(title="Save Options", content=content, size_hint=(0.85, 0.45))
        
        def save_file_act(*a):
            popup.dismiss()
            self.save_memory_click()
            
        def save_pic_act(*a):
            popup.dismiss()
            self.save_picture_click()
            
        btn_save_file.bind(on_release=save_file_act)
        btn_save_pic.bind(on_release=save_pic_act)
        btn_cancel.bind(on_release=popup.dismiss)
        
        content.add_widget(btn_save_file)
        content.add_widget(btn_save_pic)
        content.add_widget(btn_cancel)
        self.app.register_popup(popup)
        popup.open()

    def show_combined_recall_popup(self, *args):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        btn_recall_file = PlasticButton(text="Recall file Scan", btn_color=[1, 0.4, 0.7, 1], size_hint_y=0.33)
        btn_recall_pic = PlasticButton(text="Recall picture Scan", btn_color=[0.5, 0.0, 0.5, 1], size_hint_y=0.33)
        btn_cancel = PlasticButton(text="Cancel", btn_color=[0.5, 0.5, 0.5, 1], size_hint_y=0.33)
        
        popup = Popup(title="Recall Options", content=content, size_hint=(0.85, 0.45))
        
        def recall_file_act(*a):
            popup.dismiss()
            self.recall_memory_click()

        def recall_pic_act(*a):
            popup.dismiss()
            self.recall_picture_click()
        
        btn_recall_file.bind(on_release=recall_file_act)
        btn_recall_pic.bind(on_release=self.recall_picture_click)
        btn_cancel.bind(on_release=popup.dismiss)
        
        content.add_widget(btn_recall_file)
        content.add_widget(btn_recall_pic)
        content.add_widget(btn_cancel)
        self.app.register_popup(popup)
        popup.open()

    def on_resize(self, *args):
        if Window.width > Window.height:
            self.orientation = 'horizontal'
            self.monitor.size_hint = (0.48, 1)
            self.control_panel.size_hint = (0.52, 1)
        else:
            self.orientation = 'vertical'
            self.monitor.size_hint = (1, 0.48)
            self.control_panel.size_hint = (1, 0.52)
        self.draw_background()
        self.monitor.redraw()

    def draw_background(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.72, 0.72, 0.72, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.65, 0.65, 0.65, 0.2)
            for i in range(0, int(self.height), int(dp(9))):
                Line(points=[self.x, self.y+i, self.x+self.width, self.y+i], width=1)

    def _update_target_bg(self, i, v=None):
        i.canvas.before.clear()
        with i.canvas.before:
            Color(1.0, 1.0, 1.0, 1.0)
            RoundedRectangle(pos=(i.x+dp(1), i.y+dp(1)), size=(i.width-dp(2), i.height-dp(2)), radius=[dp(5)])
            Color(0, 0, 0, 0.15)
            Line(points=[i.x+dp(2), i.y+i.height-dp(2), i.x+i.width-dp(2), i.y+i.height-dp(2)], width=1)

    def open_keypad(self, i):
        p = KeypadPopup(target_widget=i, callback=self.keypad_callback)
        self.app.register_popup(p)
        p.open()
        
    def keypad_callback(self, t, v):
        try:
            val = float(v)
        except ValueError:
            return
        if t == self.in_w:
            self.width_val = val
            t.value_text = f"{val} M"
        elif t == self.in_l:
            self.length_val = val
            t.value_text = f"{val} M"
        elif t == self.in_ref:
            self.ref_soil_val = val
            t.value_text = f"{int(val)}"
        elif t == self.in_inpuls_x:
            self.inpuls_x = int(val)
            t.value_text = f"{int(val)}"
            self.active_line_x = min(self.active_line_x, self.inpuls_x)
            self.update_line_input_labels()
        elif t == self.in_inpuls_y:
            self.inpuls_y = int(val)
            t.value_text = f"{int(val)}"
            self.active_line_y = min(self.active_line_y, self.inpuls_y)
            self.update_line_input_labels()
        self.invalidate_render_cache()
        self.monitor.redraw()

    def open_x_line_keypad(self, i):
        p = KeypadPopup(target_widget=i, callback=self.x_line_callback)
        self.app.register_popup(p)
        p.open()
        
    def x_line_callback(self, t, v):
        try:
            val = float(v)
        except ValueError:
            return
        self.line_values_x[self.active_line_x] = val
        if self.active_line_x < self.inpuls_x:
            self.active_line_x += 1
        self.update_line_input_labels()
        self.invalidate_render_cache()
        self.monitor.redraw()

    def open_y_line_keypad(self, i):
        p = KeypadPopup(target_widget=i, callback=self.y_line_callback)
        self.app.register_popup(p)
        p.open()
        
    def y_line_callback(self, t, v):
        try:
            val = float(v)
        except ValueError:
            return
        self.line_values_y[self.active_line_y] = val
        if self.active_line_y < self.inpuls_y:
            self.active_line_y += 1
        self.update_line_input_labels()
        self.invalidate_render_cache()
        self.monitor.redraw()

    def update_line_input_labels(self):
        val_x = self.line_values_x.get(self.active_line_x, None)
        val_y = self.line_values_y.get(self.active_line_y, None)
        str_x = f"{val_x:.1f}" if val_x is not None else "—"
        str_y = f"{val_y:.1f}" if val_y is not None else "—"
        self.in_x_line.value_text = f"Line {self.active_line_x} ({str_x})"
        self.in_y_line.value_text = f"Line {self.active_line_y} ({str_y})"

    def shift_left_x(self, *args):
        if self.active_line_x > 1:
            self.active_line_x -= 1
            self.update_line_input_labels()
            self.invalidate_render_cache()
            self.monitor.redraw()
            
    def shift_right_x(self, *args):
        if self.active_line_x < self.inpuls_x:
            self.active_line_x += 1
            self.update_line_input_labels()
            self.invalidate_render_cache()
            self.monitor.redraw()
            
    def shift_left_y(self, *args):
        if self.active_line_y > 1:
            self.active_line_y -= 1
            self.update_line_input_labels()
            self.invalidate_render_cache()
            self.monitor.redraw()
            
    def shift_right_y(self, *args):
        if self.active_line_y < self.inpuls_y:
            self.active_line_y += 1
            self.update_line_input_labels()
            self.invalidate_render_cache()
            self.monitor.redraw()

    def reset_twoprop(self, *args):
        self.width_val = 5.0
        self.length_val = 5.0
        self.ref_soil_val = 600.0
        self.inpuls_x = 10
        self.inpuls_y = 10
        
        self.in_w.value_text = "5.0 M"
        self.in_l.value_text = "5.0 M"
        self.in_ref.value_text = "600"
        self.in_inpuls_x.value_text = "10"
        self.in_inpuls_y.value_text = "10"
        
        self.active_line_x = 1
        self.active_line_y = 1
        
        self.line_values_x.clear()
        self.line_values_y.clear()
        self.update_line_input_labels()
        
        self.detected_targets.clear()
        self.heatmap_grid = None
        self.tunnel_region = None
        self.show_grid_lines_and_targets = True
        self.btn_grid.is_active = True
        self.app.loaded_scan_name = ""
        self.is_analyzed = False
        self.active_box = "x"
        self.update_active_box_ui()
        self.update_target_boxes()
        self.invalidate_render_cache()
        self.monitor.redraw()

    def get_1d_peaks(self, line_dict, mode='min', threshold_min=0.0, threshold_max=500.0):
        if not line_dict:
            return []
        all_items = sorted(line_dict.items(), key=lambda x: x[0])
        indices = [k for k, v in all_items]
        vals = [v for k, v in all_items]
        n = len(vals)

        local_peaks = []
        for i in range(n):
            v = vals[i]
            if mode == 'min':
                if not (threshold_min <= v <= threshold_max):
                    continue
                left_ok = (i == 0) or (v <= vals[i-1])
                right_ok = (i == n - 1) or (v <= vals[i+1])
                if left_ok and right_ok:
                    local_peaks.append((indices[i], v, i))
            else:
                if not (threshold_min <= v <= threshold_max):
                    continue
                left_ok = (i == 0) or (v >= vals[i-1])
                right_ok = (i == n - 1) or (v >= vals[i+1])
                if left_ok and right_ok:
                    local_peaks.append((indices[i], v, i))

        filtered = []
        for line_k, val, idx in local_peaks:
            if not filtered:
                filtered.append((line_k, val, idx))
            else:
                prev_k, prev_val, prev_idx = filtered[-1]
                between_vals = vals[prev_idx+1 : idx]
                if between_vals:
                    if mode == 'min':
                        max_between = max(between_vals)
                        if max_between > prev_val and max_between > val:
                            filtered.append((line_k, val, idx))
                        else:
                            if val < prev_val:
                                filtered[-1] = (line_k, val, idx)
                    else:
                        min_between = min(between_vals)
                        if min_between < prev_val and min_between < val:
                            filtered.append((line_k, val, idx))
                        else:
                            if val > prev_val:
                                filtered[-1] = (line_k, val, idx)
        return [(k, v) for k, v, idx in filtered]

    def are_classes_compatible(self, v1, v2):
        label1, _, _ = self.app.classify_target(v1, 600.0)
        label2, _, _ = self.app.classify_target(v2, 600.0)
        if label1 == "No Target" or label2 == "No Target":
            return False
        if label1 == label2:
            return True
        precious = {"silver", "gold"}
        if label1 in precious and label2 in precious:
            return True
        metals = {"silver", "gold", "copper", "brass", "iron"}
        if label1 in metals and label2 in metals:
            return True
        voids = {"Small Void", "Medium Void", "Big Void"}
        if label1 in voids and label2 in voids:
            return True
        return False

    def get_range_peaks(self, line_dict, mode='min', threshold_min=0.0, threshold_max=500.0):
        if not line_dict:
            return []
        lines = sorted([(k, v) for k, v in line_dict.items() if threshold_min <= v <= threshold_max], key=lambda x: x[0])
        if not lines:
            return []
        groups = []
        curr_group = [lines[0]]
        for i in range(1, len(lines)):
            prev_k = curr_group[-1][0]
            curr_k = lines[i][0]
            if curr_k == prev_k + 1:
                curr_group.append(lines[i])
            else:
                groups.append(curr_group)
                curr_group = [lines[i]]
        if curr_group:
            groups.append(curr_group)
        peaks = []
        for g in groups:
            if mode == 'min':
                best = min(g, key=lambda x: x[1])
            else:
                best = max(g, key=lambda x: x[1])
            peaks.append(best)
        return peaks

    def run_twoprop_scan(self, *args):
        self.is_analyzed = True
        ref = self.ref_soil_val if hasattr(self, 'ref_soil_val') else 600.0
        ref_norm = 600.0
        
        corrected_x = {k: self.app.normalize_value_to_600(v, ref) for k, v in self.line_values_x.items()}
        corrected_y = {k: self.app.normalize_value_to_600(v, ref) for k, v in self.line_values_y.items()}

        detected = []

        # --- 1. Metals Detection ---
        x_metal_peaks = self.get_1d_peaks(corrected_x, mode='min', threshold_min=0.0, threshold_max=500.0)
        if not x_metal_peaks:
            x_metal_peaks = self.get_range_peaks(corrected_x, mode='min', threshold_min=0.0, threshold_max=500.0)

        y_metal_peaks = self.get_1d_peaks(corrected_y, mode='min', threshold_min=0.0, threshold_max=500.0)
        if not y_metal_peaks:
            y_metal_peaks = self.get_range_peaks(corrected_y, mode='min', threshold_min=0.0, threshold_max=500.0)

        if x_metal_peaks and y_metal_peaks:
            for xk, xv in x_metal_peaks:
                for yk, yv in y_metal_peaks:
                    if self.are_classes_compatible(xv, yv):
                        val = min(xv, yv)
                        cx_r = (xk - 1) / max(1, self.inpuls_x - 1) if self.inpuls_x > 1 else 0.5
                        cy_r = (yk - 1) / max(1, self.inpuls_y - 1) if self.inpuls_y > 1 else 0.5
                        label, fill_color, text_color = self.app.classify_target(val, 600.0)
                        depth = 1.2 + (abs(val - ref_norm) / max(1.0, ref_norm)) * 3.5
                        detected.append({
                            "center_x_ratio": cx_r,
                            "center_y_ratio": cy_r,
                            "target_value": val,
                            "label": label,
                            "fill_color": fill_color,
                            "text_color": text_color,
                            "depth": depth,
                            "diameter_m": 0.40,
                            "x_line": xk,
                            "y_line": yk
                        })

        # --- 2. Water Detection ---
        x_water_peaks = self.get_range_peaks(corrected_x, mode='min', threshold_min=700.0, threshold_max=1100.0)
        if not x_water_peaks:
            x_water_peaks = self.get_1d_peaks(corrected_x, mode='min', threshold_min=700.0, threshold_max=1100.0)
        if not x_water_peaks:
            x_water_peaks = self.get_1d_peaks(corrected_x, mode='max', threshold_min=700.0, threshold_max=1100.0)

        y_water_peaks = self.get_range_peaks(corrected_y, mode='min', threshold_min=700.0, threshold_max=1100.0)
        if not y_water_peaks:
            y_water_peaks = self.get_1d_peaks(corrected_y, mode='min', threshold_min=700.0, threshold_max=1100.0)
        if not y_water_peaks:
            y_water_peaks = self.get_1d_peaks(corrected_y, mode='max', threshold_min=700.0, threshold_max=1100.0)

        if x_water_peaks and y_water_peaks:
            for xk, xv in x_water_peaks:
                for yk, yv in y_water_peaks:
                    val = min(xv, yv)
                    cx_r = (xk - 1) / max(1, self.inpuls_x - 1) if self.inpuls_x > 1 else 0.5
                    cy_r = (yk - 1) / max(1, self.inpuls_y - 1) if self.inpuls_y > 1 else 0.5
                    label, fill_color, text_color = self.app.classify_target(val, 600.0)
                    depth = 1.2 + (abs(val - ref_norm) / max(1.0, ref_norm)) * 3.5
                    detected.append({
                        "center_x_ratio": cx_r,
                        "center_y_ratio": cy_r,
                        "target_value": val,
                        "label": label,
                        "fill_color": fill_color,
                        "text_color": text_color,
                        "depth": depth,
                        "diameter_m": 0.38,
                        "x_line": xk,
                        "y_line": yk
                    })

        # --- 3. Void Detection ---
        x_void_peaks = self.get_1d_peaks(corrected_x, mode='max', threshold_min=3000.0, threshold_max=100000.0)
        if not x_void_peaks:
            x_void_peaks = self.get_range_peaks(corrected_x, mode='max', threshold_min=3000.0, threshold_max=100000.0)

        y_void_peaks = self.get_1d_peaks(corrected_y, mode='max', threshold_min=3000.0, threshold_max=100000.0)
        if not y_void_peaks:
            y_void_peaks = self.get_range_peaks(corrected_y, mode='max', threshold_min=3000.0, threshold_max=100000.0)

        if x_void_peaks and y_void_peaks:
            for xk, xv in x_void_peaks:
                for yk, yv in y_void_peaks:
                    val = max(xv, yv)
                    cx_r = (xk - 1) / max(1, self.inpuls_x - 1) if self.inpuls_x > 1 else 0.5
                    cy_r = (yk - 1) / max(1, self.inpuls_y - 1) if self.inpuls_y > 1 else 0.5
                    label, fill_color, text_color = self.app.classify_target(val, 600.0)
                    depth = 1.2 + (abs(val - ref_norm) / max(1.0, ref_norm)) * 3.5
                    detected.append({
                        "center_x_ratio": cx_r,
                        "center_y_ratio": cy_r,
                        "target_value": val,
                        "label": label,
                        "fill_color": fill_color,
                        "text_color": text_color,
                        "depth": depth,
                        "diameter_m": 0.45,
                        "x_line": xk,
                        "y_line": yk
                    })

        unique_detected = []
        seen_coords = set()
        for t in detected:
            coord_key = (t["x_line"], t["y_line"])
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                unique_detected.append(t)

        unique_detected.sort(key=lambda t: t["target_value"])
        self.detected_targets = unique_detected
        self.app.detected_circles = self.detected_targets

        self.heatmap_grid = None

        self.update_target_boxes()
        self.invalidate_render_cache()
        self.monitor.redraw()

    def update_target_boxes(self):
        self.targets_layout.clear_widgets()
        num_targets = len(self.detected_targets)
        
        col1 = BoxLayout(orientation='vertical', spacing=dp(4))
        col2 = BoxLayout(orientation='vertical', spacing=dp(4))
        
        if num_targets == 0:
            font_size = '11sp'
            for idx in range(6):
                text = f"Target {idx+1}:  [b][size={font_size}]—[/size][/b]\n—\n—"
                lbl = Label(
                    text=text,
                    font_size=font_size,
                    bold=True,
                    color=[0.5, 0.5, 0.5, 1],
                    markup=True,
                    halign='left',
                    valign='middle',
                    padding=[dp(15), 0]
                )
                lbl.bind(pos=self._update_target_bg, size=self._update_target_bg)
                lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
                
                if idx % 2 == 0:
                    col1.add_widget(lbl)
                else:
                    col2.add_widget(lbl)
        else:
            font_size = '11sp' if num_targets <= 4 else '9sp'
            padding_x = dp(15) if num_targets <= 4 else dp(8)
            
            for idx, target in enumerate(self.detected_targets):
                material = target["label"]
                val = target["target_value"]
                x_m = target["center_x_ratio"] * self.width_val
                y_m = target["center_y_ratio"] * self.length_val
                depth = target["depth"]
                
                text = f"Target {idx+1}:  [b][size={font_size}]{material}[/b][/size]      Value: {val:.0f}\nX = {x_m:.2f} m        Y = {y_m:.2f} m\nDepth (H) = {depth:.2f} m"
                
                lbl = Label(
                    text=text,
                    font_size=font_size,
                    bold=True,
                    color=[0.1, 0.1, 0.1, 1],
                    markup=True,
                    halign='left',
                    valign='middle',
                    padding=[padding_x, 0]
                )
                lbl.bind(pos=self._update_target_bg, size=self._update_target_bg)
                lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
                
                if idx % 2 == 0:
                    col1.add_widget(lbl)
                else:
                    col2.add_widget(lbl)
                    
        self.targets_layout.add_widget(col1)
        self.targets_layout.add_widget(col2)

    def save_memory_click(self, *args):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text="Save Memory to:", size_hint_y=0.3, font_size='14sp', bold=True)
        content.add_widget(lbl)
        btn_internal = PlasticButton(text="Internal Storage", btn_color=[0.1, 0.5, 0.8, 1], size_hint_y=0.35)
        btn_cancel = PlasticButton(text="Cancel", btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.35)
        content.add_widget(btn_internal)
        content.add_widget(btn_cancel)
        popup_loc = Popup(title="Save Memory", content=content, size_hint=(0.85, 0.4))
        
        def choose_internal(*args):
            popup_loc.dismiss()
            self.ask_filename_and_save(is_internal=True, save_type="json")
            
        btn_internal.bind(on_release=choose_internal)
        btn_cancel.bind(on_release=popup_loc.dismiss)
        self.app.register_popup(popup_loc)
        popup_loc.open()

    def ask_filename_and_save(self, is_internal, save_type):
        default_name = f"2prop_"
        title = "Enter Filename"
        
        def on_name_entered(typed_name):
            sanitized = self.app.sanitize_filename(typed_name)
            if save_type == "json":
                self.execute_save_memory(is_internal, sanitized)
            elif save_type == "png":
                self.execute_save_picture(is_internal, sanitized)
                
        p = VirtualKeyboardPopup(title=title, callback=on_name_entered, default_text=default_name)
        self.app.register_popup(p)
        p.open()

    def execute_save_memory(self, is_internal, filename):
        if not filename.startswith("2prop_"):
            filename = "2prop_" + filename
        if not filename.endswith(".json"):
            filename += ".json"
        state = {
            "type": "2prop",
            "width": str(self.width_val),
            "height": str(self.length_val),
            "ref_soil": str(self.ref_soil_val),
            "inpuls_x": self.inpuls_x,
            "inpuls_y": self.inpuls_y,
            "line_values_x": self.line_values_x,
            "line_values_y": self.line_values_y
        }
        try:
            root_dir = self.app.get_storage_root(is_internal)
            folder = os.path.join(root_dir, "Cornix Winner", "2 prop Scan", "File Scan")
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
            self.app.show_popup("Success", f"Scan saved successfully to:\n{filepath}")
        except Exception as e:
            self.app.show_popup("Error", f"Could not save file:\n{e}")

    def recall_memory_click(self, *args):
        files_map = {}
        search_dirs = [
            os.path.join(self.app.get_storage_root(is_internal=True), "Cornix Winner", "2 prop Scan", "File Scan"),
            os.path.join(self.app.get_storage_root(is_internal=True), "Documents", "Cornix Winner PRO", "File scan"),
            os.path.join(self.app.user_data_dir, "Cornix Winner", "2 prop Scan", "File Scan"),
            os.path.join(self.app.user_data_dir, "Documents", "Cornix Winner PRO", "File scan")
        ]
        
        for d in search_dirs:
            try:
                if os.path.exists(d):
                    for f in os.listdir(d):
                        if f.endswith(".json"):
                            files_map[f] = os.path.join(d, f)
            except Exception:
                pass

        twoprop_files_map = {}
        for f, path in files_map.items():
            if f.startswith("2prop_"):
                twoprop_files_map[f] = path
            else:
                try:
                    with open(path, 'r', encoding='utf-8') as js_f:
                        data = json.load(js_f)
                        if data.get("type") == "2prop":
                            twoprop_files_map[f] = path
                except Exception:
                    pass

        if not twoprop_files_map:
            self.app.show_popup("Recall", "No saved 2 prop\nMesh Scan")
            return

        self.recall_files_list = list(twoprop_files_map.keys())
        self.recall_files_map = twoprop_files_map
        self.current_search_query = ""
        self.delete_mode = False
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        search_row = BoxLayout(spacing=dp(5), size_hint_y=0.15)
        self.btn_search_trigger = PlasticButton(text="Search: [Click to type]", btn_color=[0.2, 0.4, 0.4, 1])
        btn_clear_search = PlasticButton(text="X", btn_color=[0.7, 0.2, 0.2, 1], size_hint_x=0.2)
        search_row.add_widget(self.btn_search_trigger)
        search_row.add_widget(btn_clear_search)
        content.add_widget(search_row)

        from kivy.uix.scrollview import ScrollView
        sv = ScrollView(size_hint_y=0.7)
        self.file_list_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.file_list_grid.bind(minimum_height=self.file_list_grid.setter('height'))
        sv.add_widget(self.file_list_grid)
        content.add_widget(sv)

        bottom_row = BoxLayout(spacing=dp(3), size_hint_y=0.15)
        self.btn_delete_mode = PlasticButton(text="Delete Mode", btn_color=[0.8, 0.2, 0.2, 1])
        btn_cancel_select = PlasticButton(text="Cancel", btn_color=[0.5, 0.5, 0.5, 1])
        
        bottom_row.add_widget(btn_cancel_select)
        bottom_row.add_widget(self.btn_delete_mode)
        content.add_widget(bottom_row)

        self.recall_select_popup = Popup(title="Select Scan File", content=content, size_hint=(0.85, 0.8))
        btn_cancel_select.bind(on_release=self.recall_select_popup.dismiss)

        def populate_file_list(query=""):
            self.file_list_grid.clear_widgets()
            filtered_files = [f for f in self.recall_files_list if not query or query.lower() in f.lower()]
            if not filtered_files:
                self.file_list_grid.add_widget(Label(text="No matches found", size_hint_y=None, height=dp(40)))
                return
            for f in filtered_files:
                display_name = f"🗑 {f}" if self.delete_mode else f
                btn_clr = [0.6, 0.1, 0.1, 1] if self.delete_mode else [0.3, 0.3, 0.3, 1]
                btn = PlasticButton(text=display_name, btn_color=btn_clr, size_hint_y=None, height=dp(40))
                btn.bind(on_release=lambda instance, fn=f: on_file_click(fn))
                self.file_list_grid.add_widget(btn)

        def on_file_click(filename):
            if self.delete_mode:
                file_path = self.recall_files_map.get(filename)
                try:
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                    self.recall_files_list.remove(filename)
                    self.recall_files_map.pop(filename, None)
                except Exception as e:
                    print(e)
                populate_file_list(self.current_search_query)
            else:
                self.show_scan_options_popup(filename)

        def toggle_delete_mode(*args):
            self.delete_mode = not self.delete_mode
            self.btn_delete_mode.text = "Exit Delete" if self.delete_mode else "Delete Mode"
            self.btn_delete_mode.btn_color = [0.1, 0.6, 0.2, 1] if self.delete_mode else [0.8, 0.2, 0.2, 1]
            populate_file_list(self.current_search_query)

        self.btn_delete_mode.bind(on_release=toggle_delete_mode)
        
        def on_search_keyboard(*args):
            p = VirtualKeyboardPopup(title="Type query", callback=lambda q: populate_after_search(q), default_text=self.current_search_query)
            self.app.register_popup(p)
            p.open()
            
        def populate_after_search(q):
            self.current_search_query = q
            populate_file_list(q)

        self.btn_search_trigger.bind(on_release=on_search_keyboard)
        btn_clear_search.bind(on_release=lambda x: populate_after_search(""))
        
        populate_file_list()
        self.app.register_popup(self.recall_select_popup)
        self.recall_select_popup.open()

    def show_scan_options_popup(self, filename):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=filename, font_size='14sp', bold=True, size_hint_y=0.4, color=[1, 1, 1, 1])
        content.add_widget(lbl)
        
        btn_box = BoxLayout(spacing=5, size_hint_y=0.6)
        btn_load = PlasticButton(text="Load", btn_color=[0.18, 0.65, 0.28, 1])
        btn_delete = PlasticButton(text="Delete", btn_color=[0.8, 0.2, 0.2, 1])
        btn_share = PlasticButton(text="Share", btn_color=[0.5, 0.0, 0.5, 1])
        btn_cancel = PlasticButton(text="Cancel", btn_color=[0.5, 0.5, 0.5, 1])
        
        btn_box.add_widget(btn_load)
        btn_box.add_widget(btn_delete)
        btn_box.add_widget(btn_share)
        btn_box.add_widget(btn_cancel)
        content.add_widget(btn_box)
        
        popup = Popup(title="Select Scan File", content=content, size_hint=(0.85, 0.45), auto_dismiss=False)
        
        def on_load(*args):
            popup.dismiss()
            if hasattr(self, 'recall_select_popup') and self.recall_select_popup:
                self.recall_select_popup.dismiss()
            self.load_from_json(self.recall_files_map[filename])
            
        def on_delete(*args):
            file_path = self.recall_files_map.get(filename)
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                self.recall_files_list.remove(filename)
                self.recall_files_map.pop(filename, None)
            except Exception as e:
                print(f"Error: {e}")
            popup.dismiss()
            if hasattr(self, 'recall_select_popup') and self.recall_select_popup:
                self.recall_select_popup.dismiss()
            self.recall_memory_click()

        def on_share(*args):
            self.app.share_file_native(self.recall_files_map[filename], "application/json")
            
        btn_load.bind(on_release=on_load)
        btn_delete.bind(on_release=on_delete)
        btn_share.bind(on_release=on_share)
        btn_cancel.bind(on_release=popup.dismiss)
        self.app.register_popup(popup)
        popup.open()

    def load_from_json(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.width_val = float(data.get("width", 5.0))
            self.length_val = float(data.get("height", 5.0))
            self.ref_soil_val = float(data.get("ref_soil", 600.0))
            self.inpuls_x = int(data.get("inpuls_x", 10))
            self.inpuls_y = int(data.get("inpuls_y", 10))
            
            self.line_values_x = {int(k): float(v) for k, v in data.get("line_values_x", {}).items()}
            self.line_values_y = {int(k): float(v) for k, v in data.get("line_values_y", {}).items()}
            
            self.in_w.value_text = f"{self.width_val} M"
            self.in_l.value_text = f"{self.length_val} M"
            self.in_ref.value_text = f"{int(self.ref_soil_val)}"
            self.in_inpuls_x.value_text = f"{self.inpuls_x}"
            self.in_inpuls_y.value_text = f"{self.inpuls_y}"
            
            self.active_line_x = min(self.inpuls_x, len(self.line_values_x) + 1)
            self.active_line_y = min(self.inpuls_y, len(self.line_values_y) + 1)
            self.update_line_input_labels()
            
            self.app.loaded_scan_name = os.path.splitext(os.path.basename(filepath))[0]
            self.invalidate_render_cache()
            self.run_twoprop_scan()
            self.monitor.redraw()
            self.app.show_popup("Success", "Scan recalled successfully!")
        except Exception as e:
            self.app.show_popup("Error", f"Failed to load scan:\n{e}")

    def save_picture_click(self, *args):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text="Save Image to:", size_hint_y=0.3, font_size='14sp', bold=True)
        content.add_widget(lbl)
        btn_internal = PlasticButton(text="Internal Storage", btn_color=[0.1, 0.6, 0.2, 1], size_hint_y=0.35)
        btn_cancel = PlasticButton(text="Cancel", btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.35)
        content.add_widget(btn_internal)
        content.add_widget(btn_cancel)
        popup_loc = Popup(title="Save Image", content=content, size_hint=(0.85, 0.4))
        
        def choose_internal(*args):
            popup_loc.dismiss()
            self.ask_filename_and_save(is_internal=True, save_type="png")
            
        btn_internal.bind(on_release=choose_internal)
        btn_cancel.bind(on_release=popup_loc.dismiss)
        self.app.register_popup(popup_loc)
        popup_loc.open()

    def execute_save_picture(self, is_internal, filename):
        if not filename.startswith("2prop_"):
            filename = "2prop_" + filename
        if not filename.endswith(".png"):
            filename += ".png"
        try:
            folder = self.app.get_writable_folder(os.path.join("Cornix Winner", "2 prop Scan", "picture Scan"))
            filepath = os.path.join(folder, filename)
            self.monitor.export_to_png(filepath)
            self.app.show_popup("Success", f"Screenshot saved successfully to:\n{filepath}")
        except Exception as e:
            self.app.show_popup("Error", f"Could not save file:\n{e}")

    def recall_picture_click(self, *args):
        files_map = {}
        search_dirs = [
            os.path.join(self.app.get_storage_root(is_internal=True), "Cornix Winner", "2 prop Scan", "picture Scan"),
            os.path.join(self.app.get_storage_root(is_internal=True), "Pictures", "Cornix Winner PRO", "picture scan"),
            os.path.join(self.app.user_data_dir, "Cornix Winner", "2 prop Scan", "picture Scan"),
            os.path.join(self.app.user_data_dir, "Pictures", "Cornix Winner PRO", "picture scan")
        ]
        
        for d in search_dirs:
            try:
                if os.path.exists(d):
                    for f in os.listdir(d):
                        if f.lower().endswith(('.png', '.jpg', '.jpeg')) and f.startswith("2prop_"):
                            files_map[f] = os.path.join(d, f)
            except Exception:
                pass

        if not files_map:
            self.app.show_popup("Recall Picture", "No saved images found")
            return

        self.recall_pic_files_list = list(files_map.keys())
        self.recall_pic_files_map = files_map
        self.current_pic_search_query = ""
        self.pic_delete_mode = False
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        search_row = BoxLayout(spacing=dp(5), size_hint_y=0.15)
        self.btn_pic_search_trigger = PlasticButton(text="Search: [Click to type]", btn_color=[0.2, 0.4, 0.4, 1])
        btn_clear_pic_search = PlasticButton(text="X", btn_color=[0.7, 0.2, 0.2, 1], size_hint_x=0.2)
        search_row.add_widget(self.btn_pic_search_trigger)
        search_row.add_widget(btn_clear_pic_search)
        content.add_widget(search_row)

        from kivy.uix.scrollview import ScrollView
        sv = ScrollView(size_hint_y=0.7)
        self.pic_file_list_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.pic_file_list_grid.bind(minimum_height=self.pic_file_list_grid.setter('height'))
        sv.add_widget(self.pic_file_list_grid)
        content.add_widget(sv)

        bottom_row = BoxLayout(spacing=dp(3), size_hint_y=0.15)
        self.btn_pic_delet_toggle = PlasticButton(text="Delete Mode", btn_color=[0.8, 0.2, 0.2, 1])
        btn_cancel_select = PlasticButton(text="Cancel", btn_color=[0.5, 0.5, 0.5, 1])
        
        bottom_row.add_widget(btn_cancel_select)
        bottom_row.add_widget(self.btn_pic_delet_toggle)
        content.add_widget(bottom_row)

        self.recall_pic_popup = Popup(title="Recall Picture", content=content, size_hint=(0.85, 0.8))
        btn_cancel_select.bind(on_release=self.recall_pic_popup.dismiss)

        def populate_pic_file_list(query=""):
            self.pic_file_list_grid.clear_widgets()
            filtered_files = [f for f in self.recall_pic_files_list if not query or query.lower() in f.lower()]
            if not filtered_files:
                self.pic_file_list_grid.add_widget(Label(text="No matches found", size_hint_y=None, height=dp(40)))
                return
            for f in filtered_files:
                display_name = f"🗑 {f}" if self.pic_delete_mode else f
                btn_clr = [0.6, 0.1, 0.1, 1] if self.pic_delete_mode else [0.3, 0.3, 0.3, 1]
                btn = PlasticButton(text=display_name, btn_color=btn_clr, size_hint_y=None, height=dp(40))
                btn.bind(on_release=lambda instance, fn=f: on_file_click(fn))
                self.pic_file_list_grid.add_widget(btn)

        def on_file_click(filename):
            if self.pic_delete_mode:
                file_path = self.recall_pic_files_map.get(filename)
                try:
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                    self.recall_pic_files_list.remove(filename)
                    self.recall_pic_files_map.pop(filename, None)
                except Exception as e:
                    print(e)
                populate_pic_file_list(self.current_pic_search_query)
            else:
                self.recall_pic_popup.dismiss()
                self.show_image_viewer(self.recall_pic_files_map[filename])

        def toggle_pic_delete_mode(*args):
            self.pic_delete_mode = not self.pic_delete_mode
            self.btn_pic_delet_toggle.text = "Exit Delete" if self.pic_delete_mode else "Delete Mode"
            self.btn_pic_delet_toggle.btn_color = [0.1, 0.6, 0.2, 1] if self.pic_delete_mode else [0.8, 0.2, 0.2, 1]
            populate_pic_file_list(self.current_pic_search_query)

        self.btn_pic_delet_toggle.bind(on_release=toggle_pic_delete_mode)
        
        def open_search(*args):
            p = VirtualKeyboardPopup(
                title="Type query", 
                callback=lambda q: (setattr(self, 'current_pic_search_query', q), populate_pic_file_list(q)), 
                default_text=self.current_pic_search_query
            )
            self.app.register_popup(p)
            p.open()
            
        self.btn_pic_search_trigger.bind(on_release=open_search)
        btn_clear_pic_search.bind(on_release=lambda x: (setattr(self, 'current_pic_search_query', ""), populate_pic_file_list("")))
        
        populate_pic_file_list()
        self.app.register_popup(self.recall_pic_popup)
        self.recall_pic_popup.open()

    def show_image_viewer(self, filepath):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        img_widget = KivyImage(source=filepath, allow_stretch=True, keep_ratio=True)
        content.add_widget(img_widget)
        
        btn_layout = BoxLayout(spacing=dp(5), size_hint_y=0.15)
        btn_close = PlasticButton(text="Close", btn_color=[0.11, 0.51, 0.84, 1])
        btn_delete = PlasticButton(text="Delete", btn_color=[0.8, 0.2, 0.2, 1])
        btn_share = PlasticButton(text="Share", btn_color=[0.5, 0.0, 0.5, 1])
        
        btn_layout.add_widget(btn_close)
        btn_layout.add_widget(btn_delete)
        btn_layout.add_widget(btn_share)
        content.add_widget(btn_layout)
        
        viewer_popup = Popup(title=os.path.basename(filepath), content=content, size_hint=(0.9, 0.9), auto_dismiss=False)
        
        def on_close(*args):
            viewer_popup.dismiss()
            self.recall_picture_click()
            
        def on_delete(*args):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                viewer_popup.dismiss()
                self.app.show_popup("Success", "File deleted successfully!")
                self.recall_picture_click()
            except Exception as e:
                self.app.show_popup("Error", str(e))
                
        def on_share(*args):
            self.app.share_file_native(filepath, "image/png")
            
        btn_close.bind(on_release=on_close)
        btn_delete.bind(on_release=on_delete)
        btn_share.bind(on_release=on_share)
        
        self.app.register_popup(viewer_popup)
        viewer_popup.open()

    def get_render_texture(self):
        if hasattr(self, '_cached_render_texture') and self._cached_render_texture is not None:
            return self._cached_render_texture
        img = self.generate_visualization_image()
        if img is None:
            return None
        try:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
            data = img.tobytes("raw", "RGBA")
            tex = Texture.create(size=img.size, colorfmt="rgba")
            tex.blit_buffer(data, colorfmt="rgba", bufferfmt="ubyte")
            self._cached_render_texture = tex
            return tex
        except Exception as e:
            print("Texture generation failed:", e)
            return None
            
    def invalidate_render_cache(self):
        self._cached_render_texture = None

    def draw_pil_double_arrow_dashed(self, draw, x0, y0, x1, y1, color=(0, 0, 0, 255), width=2, dash=(6, 4)):
        if hasattr(self.app, 'draw_pil_dashed_line'):
            self.app.draw_pil_dashed_line(draw, x0, y0, x1, y1, color, width, dash)
        else:
            draw.line([x0, y0, x1, y1], fill=color, width=width)
        
        angle = math.atan2(y0 - y1, x0 - x1)
        arrow_size = 10
        p1 = (x0 - arrow_size * math.cos(angle - math.pi/6), y0 - arrow_size * math.sin(angle - math.pi/6))
        p2 = (x0 - arrow_size * math.cos(angle + math.pi/6), y0 - arrow_size * math.sin(angle + math.pi/6))
        draw.polygon([(x0, y0), p1, p2], fill=color)
        
        angle2 = math.atan2(y1 - y0, x1 - x0)
        p3 = (x1 - arrow_size * math.cos(angle2 - math.pi/6), y1 - arrow_size * math.sin(angle2 - math.pi/6))
        p4 = (x1 - arrow_size * math.cos(angle2 + math.pi/6), y1 - arrow_size * math.sin(angle2 + math.pi/6))
        draw.polygon([(x1, y1), p3, p4], fill=color)

    def generate_visualization_image(self, w=800, h=800):
        if Image is None or ImageDraw is None:
            return None
        
        aspect_ratio = self.width_val / max(self.length_val, 0.1)
        
        font_dots = self.app.get_pil_font(12, bold=True)
        max_tw_y = 0
        for idx, val in self.line_values_y.items():
            lbl_text = f"Lin {idx}  {val:.0f}"
            try:
                img_dummy = Image.new("RGBA", (1, 1))
                draw_dummy = ImageDraw.Draw(img_dummy)
                bbox = draw_dummy.textbbox((0, 0), lbl_text, font=font_dots)
                tw = bbox[2] - bbox[0]
            except Exception:
                try:
                    img_dummy = Image.new("RGBA", (1, 1))
                    draw_dummy = ImageDraw.Draw(img_dummy)
                    tw, _ = draw_dummy.textsize(lbl_text, font=font_dots)
                except Exception:
                    tw = len(lbl_text) * 7.5
            if tw > max_tw_y:
                max_tw_y = tw
        if max_tw_y == 0:
            max_tw_y = 90.0

        max_tw_x = 0
        for idx, val in self.line_values_x.items():
            lbl_text = f"Lin {idx}  {val:.0f}"
            try:
                img_dummy = Image.new("RGBA", (1, 1))
                draw_dummy = ImageDraw.Draw(img_dummy)
                bbox = draw_dummy.textbbox((0, 0), lbl_text, font=font_dots)
                tw = bbox[2] - bbox[0]
            except Exception:
                try:
                    img_dummy = Image.new("RGBA", (1, 1))
                    draw_dummy = ImageDraw.Draw(img_dummy)
                    tw, _ = draw_dummy.textsize(lbl_text, font=font_dots)
                except Exception:
                    tw = len(lbl_text) * 7.5
            if tw > max_tw_x:
                max_tw_x = tw
        if max_tw_x == 0:
            max_tw_x = 90.0

        margin_left_pil = 60.0 + max_tw_y / 2.0
        margin_right_pil = 40.0
        margin_top_pil = 40.0
        margin_bottom_pil = margin_left_pil
        
        max_qw = 800.0 - margin_left_pil - margin_right_pil
        max_qh = 800.0 - margin_bottom_pil - margin_top_pil
        
        if aspect_ratio > (max_qw / max_qh):
            qw = max_qw
            qh = max_qw / aspect_ratio
        else:
            qh = max_qh
            qw = max_qh * aspect_ratio
            
        qx = margin_left_pil
        qy = 800.0 - margin_bottom_pil - qh

        img = Image.new("RGBA", (w, h), (217, 217, 217, 255))
        draw = ImageDraw.Draw(img)
        
        if getattr(self, 'is_analyzed', False):
            bg_green = (0, 195, 55)
            nx, ny = 140, 140
            grid_vals = [[600.0 for _ in range(nx)] for _ in range(ny)]
            
            ref = self.ref_soil_val if hasattr(self, 'ref_soil_val') else 600.0
            corrected_x = {k: self.app.normalize_value_to_600(v, ref) for k, v in self.line_values_x.items()}
            corrected_y = {k: self.app.normalize_value_to_600(v, ref) for k, v in self.line_values_y.items()}

            heatmap_img = Image.new("RGBA", (nx, ny), bg_green + (255,))

            targets_info = []

            if self.detected_targets:
                step_x = 1.0 / max(1, self.inpuls_x - 1) if self.inpuls_x > 1 else 0.1
                step_y = 1.0 / max(1, self.inpuls_y - 1) if self.inpuls_y > 1 else 0.1

                for idx_t, t in enumerate(self.detected_targets):
                    val = t["target_value"]
                    cx = t["center_x_ratio"]
                    cy = t["center_y_ratio"]
                    best_x = t.get("x_line", 1)
                    best_y = t.get("y_line", 1)

                    is_void = (val >= 2200.0)

                    v_left = corrected_x.get(best_x - 1, val)
                    v_right = corrected_x.get(best_x + 1, val)
                    v_down = corrected_y.get(best_y - 1, val)
                    v_up = corrected_y.get(best_y + 1, val)

                    if not is_void:
                        dir_x = (v_left - v_right)
                        dir_y = (v_down - v_up)
                    else:
                        dir_x = (v_right - v_left)
                        dir_y = (v_up - v_down)

                    if abs(dir_x) < 1e-5 and abs(dir_y) < 1e-5:
                        theta_bias = 0.785
                    else:
                        theta_bias = math.atan2(dir_y, dir_x)

                    hex_c = t["fill_color"]
                    rgb_t = (int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16))

                    r_target = (t.get("diameter_m", 0.40) / 2.0) / max(min(self.width_val, self.length_val), 1e-9)
                    r_base = max(r_target * 0.90, max(step_x, step_y) * 0.42)
                    fade_margin = r_base * 2.20

                    targets_info.append({
                        "cx": cx,
                        "cy": cy,
                        "r_base": r_base,
                        "fade_margin": fade_margin,
                        "theta_bias": theta_bias,
                        "target_idx": idx_t,
                        "val": val,
                        "rgb": rgb_t
                    })

            for j in range(ny):
                yr = j / (ny - 1) if ny > 1 else 0.5
                for i in range(nx):
                    xr = i / (nx - 1) if nx > 1 else 0.5

                    r_c, g_c, b_c = float(bg_green[0]), float(bg_green[1]), float(bg_green[2])
                    val_sum = 600.0

                    for t_info in targets_info:
                        cx, cy = t_info["cx"], t_info["cy"]
                        r_base = t_info["r_base"]
                        fade_m = t_info["fade_margin"]
                        theta_b = t_info["theta_bias"]
                        idx_t = t_info["target_idx"]

                        dx = xr - cx
                        dy = yr - cy
                        dist = math.hypot(dx, dy)

                        if dist < (r_base + fade_m) * 2.2:
                            theta = math.atan2(dy, dx)
                            shape_harmonic = 1.0 + 0.22 * math.cos(3.0 * theta + idx_t * 1.5) - 0.16 * math.sin(2.0 * theta)
                            skew_factor = 0.38 * math.cos(theta - theta_b)
                            
                            r_boundary = r_base * (shape_harmonic + skew_factor)

                            if dist <= r_boundary:
                                weight = 1.0
                            elif dist < r_boundary + fade_m:
                                w = 1.0 - ((dist - r_boundary) / fade_m)
                                weight = w * w * (3.0 - 2.0 * w)
                            else:
                                weight = 0.0

                            if weight > 0.0:
                                rgb_target = t_info["rgb"]
                                val_sum += (t_info["val"] - 600.0) * weight

                                r_c = self.app._lerp(r_c, rgb_target[0], weight)
                                g_c = self.app._lerp(g_c, rgb_target[1], weight)
                                b_c = self.app._lerp(b_c, rgb_target[2], weight)

                    grid_vals[j][i] = val_sum

                    r_final = int(self.app.clamp(r_c, 0, 255))
                    g_final = int(self.app.clamp(g_c, 0, 255))
                    b_final = int(self.app.clamp(b_c, 0, 255))

                    heatmap_img.putpixel((i, ny - 1 - j), (r_final, g_final, b_final, 255))

            img.paste(heatmap_img.resize((int(qw), int(qh)), RESAMPLE_FILTER), (int(qx), int(qy)))
            draw.rectangle([qx, qy, qx + qw, qy + qh], outline="black", width=3)

            contour_levels = []
            if self.detected_targets:
                for t in self.detected_targets:
                    tv = t["target_value"]
                    for step in [1, 2]:
                        lev = 600.0 + (tv - 600.0) * (step / 2.2)
                        contour_levels.append(lev)

            if contour_levels:
                def interp_p(p1, p2, v1, v2, level):
                    if abs(v2 - v1) < 1e-12:
                        return p1
                    tt = max(0.0, min(1.0, (level - v1) / (v2 - v1)))
                    return (p1[0] + tt * (p2[0] - p1[0]), p1[1] + tt * (p2[1] - p1[1]))

                for j in range(ny - 1):
                    for i in range(nx - 1):
                        v1 = grid_vals[j][i]
                        v2 = grid_vals[j][i+1]
                        v3 = grid_vals[j+1][i]
                        v4 = grid_vals[j+1][i+1]

                        dv_dx = v2 - v1
                        dv_dy = v3 - v1
                        tx_dir = -dv_dy
                        ty_dir = dv_dx

                        for level in contour_levels:
                            segments = []
                            if (v1 >= level) != (v2 >= level):
                                segments.append(interp_p((i/(nx-1), j/(ny-1)), ((i+1)/(nx-1), j/(ny-1)), v1, v2, level))
                            if (v2 >= level) != (v4 >= level):
                                segments.append(interp_p(((i+1)/(nx-1), j/(ny-1)), ((i+1)/(nx-1), (j+1)/(ny-1)), v2, v4, level))
                            if (v4 >= level) != (v3 >= level):
                                segments.append(interp_p(((i+1)/(nx-1), (j+1)/(ny-1)), (i/(nx-1), (j+1)/(ny-1)), v4, v3, level))
                            if (v3 >= level) != (v1 >= level):
                                segments.append(interp_p((i/(nx-1), (j+1)/(ny-1)), (i/(nx-1), j/(ny-1)), v3, v1, level))

                            if len(segments) >= 2:
                                p1_x = qx + segments[0][0] * qw
                                p1_y = qy + qh - segments[0][1] * qh
                                p2_x = qx + segments[1][0] * qw
                                p2_y = qy + qh - segments[1][1] * qh

                                dx_seg = p2_x - p1_x
                                dy_seg = p2_y - p1_y

                                if (dx_seg * tx_dir + dy_seg * ty_dir) < 0:
                                    p1_x, p2_x = p2_x, p1_x
                                    p1_y, p2_y = p2_y, p1_y
                                    dx_seg, dy_seg = -dx_seg, -dy_seg

                                draw.line([p1_x, p1_y, p2_x, p2_y], fill=(40, 40, 40, 255), width=1)

                                seg_len = math.hypot(dx_seg, dy_seg)
                                if seg_len > 1.2 and ((i * 3 + j * 7) % 9 == 0):
                                    ux = dx_seg / seg_len
                                    uy = dy_seg / seg_len
                                    px = -uy
                                    py = ux
                                    mx = (p1_x + p2_x) / 2.0
                                    my = (p1_y + p2_y) / 2.0
                                    arr_s = 4.0
                                    w1 = (mx - arr_s * ux + arr_s * 0.55 * px, my - arr_s * uy + arr_s * 0.55 * py)
                                    w2 = (mx - arr_s * ux - arr_s * 0.55 * px, my - arr_s * uy - arr_s * 0.55 * py)
                                    draw.polygon([(mx, my), w1, w2], fill=(20, 20, 20, 255))

        else:
            draw.rectangle([qx, qy, qx + qw, qy + qh], fill=(230, 230, 230, 255), outline="black", width=3)
        
        N_x = self.inpuls_x
        N_y = self.inpuls_y

        if self.show_grid_lines_and_targets:
            if N_x > 0:
                for i in range(N_x):
                    dx = i * (qw / max(1, N_x - 1)) if N_x > 1 else 0
                    draw.ellipse([qx + dx - 5, qy + qh - 5, qx + dx + 5, qy + qh + 5], fill="black")
                    draw.ellipse([qx + dx - 5, qy - 5, qx + dx + 5, qy + 5], fill="black")
                    
            if N_y > 0:
                for j in range(N_y):
                    dy = j * (qh / max(1, N_y - 1)) if N_y > 1 else 0
                    draw.ellipse([qx - 5, qy + qh - dy - 5, qx + 5, qy + qh - dy + 5], fill="black")
                    draw.ellipse([qx + qw - 5, qy + qh - dy - 5, qx + qw + 5, qy + qh - dy + 5], fill="black")

            if N_x > 1:
                span_intervals = min(4.0, float(N_x - 1))
                idx1 = (N_x - 1) / 2.0 - span_intervals / 2.0
                idx2 = (N_x - 1) / 2.0 + span_intervals / 2.0
                
                x1_new = qx + idx1 * (qw / (N_x - 1))
                x2_new = qx + idx2 * (qw / (N_x - 1))
                
                y_arrow = qy - 12
                y_text = y_arrow - 16
                
                self.draw_pil_double_arrow_dashed(draw, x1_new, y_arrow, x2_new, y_arrow, color=(0, 0, 0, 255), width=2, dash=(6, 4))
                
                r_dot = 4
                draw.ellipse([x1_new - 4 - r_dot, y_arrow - r_dot, x1_new - 4 + r_dot, y_arrow + r_dot], fill="black")
                draw.ellipse([x2_new + 4 - r_dot, y_arrow - r_dot, x2_new + 4 + r_dot, y_arrow + r_dot], fill="black")

                dx_val = (self.width_val * 100.0) / max(1, N_x - 1)
                dx_text = f"{dx_val:.1f} cm"
                font_dist = self.app.get_pil_font(24, bold=True)
                self.app.draw_rotated_text(img, dx_text, (int((x1_new + x2_new) / 2), int(y_text)), 0, font_dist, (0, 0, 0, 255))
                
            if N_y > 1:
                span_intervals_y = min(4.0, float(N_y - 1))
                idy1 = (N_y - 1) / 2.0 - span_intervals_y / 2.0
                idy2 = (N_y - 1) / 2.0 + span_intervals_y / 2.0
                
                dy1 = idy1 * (qh / (N_y - 1))
                dy2 = idy2 * (qh / (N_y - 1))
                y1_new = qy + qh - dy1
                y2_new = qy + qh - dy2
                
                x_arrow = qx + qw + 12
                x_text = x_arrow + 18
                
                self.draw_pil_double_arrow_dashed(draw, x_arrow, y1_new, x_arrow, y2_new, color=(0, 0, 0, 255), width=2, dash=(6, 4))
                
                r_dot = 4
                draw.ellipse([x_arrow - r_dot, y1_new + 4 - r_dot, x_arrow + r_dot, y1_new + 4 + r_dot], fill="black")
                draw.ellipse([x_arrow - r_dot, y2_new - 4 - r_dot, x_arrow + r_dot, y2_new - 4 + r_dot], fill="black")

                dy_val = (self.length_val * 100.0) / max(1, N_y - 1)
                dy_text = f"{dy_val:.1f} cm"
                font_dist = self.app.get_pil_font(24, bold=True)
                self.app.draw_rotated_text(img, dy_text, (int(x_text), int((y1_new + y2_new) / 2)), 270, font_dist, (0, 0, 0, 255))
                    
            for idx, val in self.line_values_x.items():
                if idx <= N_x:
                    dx = (idx - 1) * (qw / max(1, N_x - 1)) if N_x > 1 else 0
                    x_pos = qx + dx
                    is_active = (idx == self.active_line_x)
                    line_color = (255, 0, 0, 255) if is_active else (0, 0, 0, 100)
                    draw.line([x_pos, qy, x_pos, qy + qh], fill=line_color, width=1 if not is_active else 2)
                    lbl_text = f"Lin {idx}  {val:.0f}"
                    self.app.draw_rotated_text(img, lbl_text, (int(x_pos), int(qy + qh + 50)), 270, font_dots, (0, 0, 0, 255))
                    
            for idx, val in self.line_values_y.items():
                if idx <= N_y:
                    dy = (idx - 1) * (qh / max(1, N_y - 1)) if N_y > 1 else 0
                    y_pos = qy + qh - dy
                    is_active = (idx == self.active_line_y)
                    line_color = (255, 0, 0, 255) if is_active else (0, 0, 0, 100)
                    draw.line([qx, y_pos, qx + qw, y_pos], fill=line_color, width=1 if not is_active else 2)
                    lbl_text = f"Lin {idx}  {val:.0f}"
                    self.app.draw_rotated_text(img, lbl_text, (int(qx - 55), int(y_pos)), 0, font_dots, (0, 0, 0, 255))
                    
            px_per_m = qw / max(self.width_val, 1e-9)
            for idx, target in enumerate(self.detected_targets):
                cx = qx + target["center_x_ratio"] * qw
                cy = qy + (1.0 - target["center_y_ratio"]) * qh
                radius = max(16.0, (target["diameter_m"] * px_per_m) / 2.0)
                
                fill_hex = target["fill_color"]
                fill_rgb = (int(fill_hex[1:3], 16), int(fill_hex[3:5], 16), int(fill_hex[5:7], 16), 255)
                draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=fill_rgb, outline=(0,0,0,255), width=2)
                
                f_txt = self.app.get_pil_font(18, bold=True)
                text_col = (255, 255, 255, 255) if sum(fill_rgb[:3])/3 < 128 else (0,0,0,255)
                self.draw_centered_text(draw, (cx, cy), str(idx + 1), f_txt, text_col)
            
        cx = qx + qw / 2.0
        cy = qy + qh / 2.0
        
        target_w = qw * 0.70
        target_h = qh * 0.70
        
        font_sz = 80
        for fs in range(250, 10, -5):
            f_test = self.app.get_pil_font(fs, bold=True)
            if not f_test:
                continue
            try:
                test_img = Image.new("RGBA", (1, 1))
                test_draw = ImageDraw.Draw(test_img)
                if hasattr(test_draw, 'textbbox'):
                    box = test_draw.textbbox((0, 0), "Cornix\nWinner PRO", font=f_test)
                    tw = box[2] - box[0]
                    th = box[3] - box[1]
                else:
                    tw, th = test_draw.multiline_textsize("Cornix\nWinner PRO", font=f_test)
                if tw <= target_w and th <= target_h:
                    font_sz = fs
                    break
            except Exception:
                tw = 6 * fs * 0.65
                th = fs * 2.3
                if tw <= target_w and th <= target_h:
                    font_sz = fs
                    break

        font_watermark_screen = self.app.get_pil_font(font_sz, bold=True)
        if font_watermark_screen:
            self.app.draw_rotated_text(img, "Cornix\nWinner PRO", (int(cx), int(cy)), 0, font_watermark_screen, (0, 0, 0, 25))
        
        draw.line([15, 790, 55, 790], fill=(0, 0, 0, 255), width=2)
        draw.polygon([(55, 790), (47, 786), (47, 794)], fill=(0, 0, 0, 255))
        self.app.draw_rotated_text(img, "X", (70, 790), 0, font_dots, (0, 0, 0, 255))
        
        draw.line([15, 790, 15, 750], fill=(0, 0, 0, 255), width=2)
        draw.polygon([(15, 750), (11, 758), (19, 758)], fill=(0, 0, 0, 255))
        self.app.draw_rotated_text(img, "Y", (15, 735), 0, font_dots, (0, 0, 0, 255))
        
        return img

    def draw_centered_text(self, draw, position, text, font, fill):
        self.app.draw_centered_text(draw, position, text, font, fill)


class MainApp(App):
    width_val = NumericProperty(5.0)
    length_val = NumericProperty(5.0)

    def lerp(self, a, b, t):
        return self._lerp(a, b, t)

    def on_start(self):
        try:
            from kivy.utils import platform
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.READ_MEDIA_IMAGES
                ])
        except Exception as e:
            print("Permission request failed:", e)

    def get_writable_folder(self, folder_subpath):
        try:
            root = self.get_storage_root(is_internal=True)
            folder = os.path.join(root, folder_subpath)
            os.makedirs(folder, exist_ok=True)
            test_file = os.path.join(folder, ".perm_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            return folder
        except Exception:
            pass

        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            ext_dir = context.getExternalFilesDir(None)
            if ext_dir:
                folder = os.path.join(ext_dir.getAbsolutePath(), folder_subpath)
                os.makedirs(folder, exist_ok=True)
                return folder
        except Exception:
            pass

        folder = os.path.join(self.user_data_dir, folder_subpath)
        os.makedirs(folder, exist_ok=True)
        return folder

    def build(self):
        self._cached_render_texture = None
        self.edge_keys = ["p1p2", "p2p4", "p4p3", "p3p1", "p1p4", "p2p3"]
        self.side_keys = ["p1p2", "p2p4", "p4p3", "p3p1"]
        self.diag_keys = ["p1p4", "p2p3"]
        self.active_popups = []
        
        self.entry_values = {k: "" for k in self.edge_keys}
        self.ui_entry_values = {k: "" for k in self.edge_keys}
        self.ui_width_val = 5.0
        self.ui_length_val = 5.0
        self.ui_ref_soil_val = 600.0
        
        self.chord_pull = 35.0
        self.void_pull = 50.0
        self.min_diameter = 0.10
        self.max_diameter = 0.50
        self.PURPLE = "#8000FF"
        
        self.heatmap_data = None
        self.min_point = None
        self.max_point = None
        self.detected_circles = []
        self.warning_arrows = []
        
        self.ref_soil_val = 600.0
        self.soil_contaminated = False
        self.center_red_focus_mode = False
        self.show_depth_overlay = True
        self.gpr_active = False
        self.fibo_active = False
        self.compare_active = False
        self.show_geo_var = True
        
        self.scanning = False
        self.scan_cols = 45
        self.scan_rows = 45
        self.scan_grid = None
        self.scan_current_col = 0
        self.scan_current_row = 0
        self.scan_direction_up = True
        self.sampled_points = []
        self.final_min_points = []
        self.transition_step = 0
        self.gpr_fibo_skeleton_visible = False
        
        self.expand_pos_count = 0
        self.expand_neg_count = 0
        self.expansion_level = 0
        self.signal_correction_level = 0
        
        self.history = []
        self.history_index = -1
        self.loaded_scan_name = ""
        self.active_mode = "4-prop"

        self.root_layout = BoxLayout(orientation='vertical', padding=dp(6), spacing=dp(6))
        self.root_layout.size_hint = (1, 1)
        
        self.root_layout.bind(pos=self.on_resize, size=self.on_resize)
        
        Window.bind(on_size=self.on_resize)
        Window.bind(on_keyboard=self.on_keyboard)
        
        self.monitor = MonitorView()
        self.control_panel = BoxLayout(orientation='vertical', spacing=dp(4))
        
        self.setup_ui()
        self.push_state()
        
        self.blink_state = True
        Clock.schedule_interval(self.toggle_blink, 0.5)

        self.main_container = FloatLayout()
        
        self.menu_screen = MainMenuScreen(self)
        self.splash = SplashScreen(on_dismiss=self.show_menu_screen)
        self.main_container.add_widget(self.splash)
        
        Clock.schedule_once(lambda dt: self.on_resize(), 0.05)

        return self.main_container

    def show_menu_screen(self):
        self.main_container.clear_widgets()
        if hasattr(self, 'menu_screen') and self.menu_screen:
            self.menu_screen.rebuild()
            self.main_container.add_widget(self.menu_screen)

    def show_main_app(self):
        self.main_container.clear_widgets()
        self.main_container.add_widget(self.root_layout)
        self.root_layout.bind(size=self.on_resize)
        Clock.schedule_once(lambda dt: self.on_resize(), 0.05)

    def compute_gpr_fibonacci_value(self, rx, ry, vmin, vmax, min_xr, min_yr):
        phi = 1.61803398875
        centers = []
        if self.detected_circles:
            for circ in self.detected_circles:
                centers.append((circ["center_x_ratio"], circ["center_y_ratio"]))
        if not centers:
            centers.append((min_xr, min_yr))
        final_t_list = []
        for cx, cy in centers:
            dx = (rx - cx) * self.width_val
            dy = (ry - cy) * self.length_val
            r = math.hypot(dx, dy)
            fib_radii = [0.13, 0.21, 0.34, 0.55, 0.89, 1.44, 2.33, 3.77]
            wave_sum = 0.0
            weight_sum = 0.0
            for idx, fib_r in enumerate(fib_radii):
                w_i = 1.0 / (phi ** idx)
                diff = r - fib_r
                wave_width = 0.05 * fib_r + 0.02
                wave_val = math.exp(-(diff * diff) / (2.0 * (wave_width) ** 2))
                wave_sum += w_i * wave_val
                weight_sum += w_i
            normalized_wave = (wave_sum / weight_sum) if weight_sum > 0 else 0.0
            theta = math.atan2(dy, dx)
            try:
                wave_spiral_phase = math.cos(3.0 * theta - 4.0 * math.log(r + 0.05))
            except Exception:
                wave_spiral_phase = 0.0
            base_t = 1.0 - math.exp(-r / 0.9)
            final_t = self.clamp(base_t - 0.35 * normalized_wave * (1.0 + 0.25 * wave_spiral_phase), 0.0, 1.0)
            final_t_list.append(final_t)
        min_final_t = min(final_t_list)
        bg_noise = 0.06 * math.sin(rx * 14.5 + ry * 10.3) + 0.04 * math.cos(rx * 27.2 - ry * 23.4) + 0.02 * math.sin(rx * 58.1 + ry * 44.9)
        fibo_t = self.clamp(min_final_t + bg_noise, 0.0, 1.0)
        return vmin + fibo_t * (vmax - vmin)

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            if hasattr(self, 'active_popups') and self.active_popups:
                self.active_popups[-1].dismiss()
                return True
            if self.main_container.children and self.main_container.children[0] != self.root_layout:
                if hasattr(self, 'twoprop_screen') and self.main_container.children[0] == self.twoprop_screen:
                    self.switch_to_fourprop()
                else:
                    self.show_menu_screen()
                return True
            return False
        return False

    def switch_to_twoprop(self):
        if not hasattr(self, 'twoprop_screen'):
            self.twoprop_screen = TwoPropScreen(app=self)
        self.main_container.clear_widgets()
        self.main_container.add_widget(self.twoprop_screen)

    def switch_to_fourprop(self):
        self.main_container.clear_widgets()
        self.main_container.add_widget(self.root_layout)

    def select_mode(self, mode):
        self.active_mode = mode
        self.r4_container.clear_widgets()
        if mode == "4-prop":
            for b in self.segs:
                self.r4_container.add_widget(b)
        else:
            self.r4_container.add_widget(Widget())
        self.show_main_app()

    def toggle_blink(self, dt):
        if self.get_cut_segments():
            self.blink_state = not self.blink_state
            self.invalidate_render_cache()
            if hasattr(self, 'monitor') and self.monitor:
                self.monitor.redraw()

    def get_cut_segments(self):
        cuts = []
        for key in self.edge_keys:
            val = self.safe_float(self.ui_entry_values.get(key, ""))
            if val is not None and val > 100000:
                cuts.append(key)
        return cuts

    def check_cuts_and_warn(self):
        if self.get_cut_segments():
            self.show_popup("Error", "Cannot scan. Probe is disconnected.")
            return True
        return False

    def convert_digits(self, text):
        return text

    def translate(self, text):
        if not text:
            return ""
        if text == "copper":
            return "Cooper"
        return text

    def invalidate_render_cache(self):
        self._cached_render_texture = None

    def on_resize(self, *args):
        width = Window.width
        height = Window.height
        if width > height:
            self.root_layout.orientation = 'horizontal'
            self.monitor.size_hint = (0.48, 1)
            self.control_panel.size_hint = (0.52, 1)
        else:
            self.root_layout.orientation = 'vertical'
            self.monitor.size_hint = (1, 0.48)
            self.control_panel.size_hint = (1, 0.52)
        self._update_bg()
        if hasattr(self, 'monitor') and self.monitor:
            self.monitor.redraw()

    def setup_ui(self):
        mid = GridLayout(cols=2, spacing=dp(4), size_hint_y=0.4)
        l_sub = BoxLayout(orientation='vertical', spacing=dp(3))
       
        self.t1 = Label(text="Target 1:\nX=                         Y=\nDepth (H) = —", font_size='10sp', bold=True, color=[0.1, 0.1, 0.1, 1], markup=True, halign='left', valign='middle', padding=[dp(15), 0])
        self.t2 = Label(text="Target 2:\nX=                         Y=\nDepth (H) = —", font_size='10sp', bold=True, color=[0.1, 0.1, 0.1, 1], markup=True, halign='left', valign='middle', padding=[dp(15), 0])
        for t in [self.t1, self.t2]:
            t.bind(pos=self._update_target_bg, size=self._update_target_bg)
            t.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            l_sub.add_widget(t)
        
        self.marquee_label = MarqueeLabel(size_hint_y=0.4)
        l_sub.add_widget(self.marquee_label)
        
        r_sub = BoxLayout(orientation='vertical', spacing=dp(3))
        deep_compare_layout = BoxLayout(spacing=dp(3))
        self.btn_compare = PlasticButton(text="Compare\n 3 Scans", btn_color=[0.5, 0.4, 0.6, 1], size_hint_x=0.5)
        self.btn_compare.bind(on_release=self.compare_click)
        self.btn_report = PlasticButton(text="Work\nReport", btn_color=[0.31, 0.45, 0.58, 1], size_hint_x=0.5)
        self.btn_report.bind(on_release=self.show_report_popup)
        deep_compare_layout.add_widget(self.btn_compare)
        deep_compare_layout.add_widget(self.btn_report)
        r_sub.add_widget(deep_compare_layout)
        
        s_row = BoxLayout(spacing=dp(3))
        pm = BoxLayout(orientation='vertical', spacing=dp(3))
        self.btn_minus = PlasticButton(text="—", btn_color=[0.11, 0.51, 0.84, 1])
        self.btn_minus.bind(on_release=self.minus_click)
        self.btn_plus = PlasticButton(text="+", btn_color=[0.84, 0.17, 0.12, 1])
        self.btn_plus.bind(on_release=self.plus_click)
        pm.add_widget(self.btn_plus)
        pm.add_widget(self.btn_minus)
        
        self.btn_start = PlasticButton(text="Press the\nSTART\nFor Scan", btn_color=[0.84, 0.17, 0.12, 1])
        self.btn_start.bind(on_release=self.refresh_scan)
        s_row.add_widget(pm)
        s_row.add_widget(self.btn_start)
        r_sub.add_widget(s_row)
        mid.add_widget(l_sub)
        mid.add_widget(r_sub)
        self.control_panel.add_widget(mid)

        r3 = BoxLayout(spacing=dp(3), size_hint_y=0.18)
        self.in_w = RecessedInput(label_text="Width", value_text="5.0 M", size_hint_x=0.13)
        self.in_l = RecessedInput(label_text="Lenght", value_text="5.0 M", size_hint_x=0.13)
        self.in_ref = RecessedInput(label_text="Soil Ref", value_text="600", size_hint_x=0.15)
        for i in [self.in_w, self.in_l, self.in_ref]:
            i.bind(on_release=self.open_keypad)
        r3.add_widget(self.in_w)
        r3.add_widget(self.in_l)
        r3.add_widget(self.in_ref)
        
        self.btn_geo = PlasticButton(text="GEO Scan", btn_color=[0.2, 0.4, 0.4, 1], size_hint_x=0.196)
        self.btn_geo.bind(on_release=self.geo_click)
        self.btn_geo.is_active = True
        self.btn_fibo = PlasticButton(text="Fibo Scan", btn_color=[0.4, 0.2, 0.4, 1], size_hint_x=0.196)
        self.btn_fibo.bind(on_release=self.fibo_click)
        self.btn_gpr = PlasticButton(text="GPR Scan", btn_color=[0.4, 0.4, 0.2, 1], size_hint_x=0.196)
        self.btn_gpr.bind(on_release=self.gpr_click)
        r3.add_widget(self.btn_geo)
        r3.add_widget(self.btn_fibo)
        r3.add_widget(self.btn_gpr)
        self.control_panel.add_widget(r3)

        self.r4_container = BoxLayout(spacing=dp(2), size_hint_y=0.13)
        self.segs = []
        for s in ["P1P2", "P2P4", "P4P3", "P3P1", "P1P4", "P2P3"]:
            b = RecessedInput(label_text=s, bg_color=[1, 1, 1, 1], text_color=[0.1, 0.1, 0.1, 1], label_color_hex="#444444")
            b.bind(on_release=self.open_keypad)
            self.segs.append(b)
            self.r4_container.add_widget(b)
        self.control_panel.add_widget(self.r4_container)

        r5 = BoxLayout(spacing=dp(3), size_hint_y=0.14)
        self.btn_menu = PlasticButton(text="2prop Scan Point Target", btn_color=[0.5, 0.5, 0.5, 1])
        self.btn_menu.bind(on_release=lambda x: self.switch_to_twoprop())
        r5.add_widget(self.btn_menu)
        
        self.btn_reset = PlasticButton(text="Reset", btn_color=[0.9, 0.7, 0.1, 1])
        self.btn_reset.bind(on_release=self.reset_all)
        self.btn_save = PlasticButton(text="Save", btn_color=[0.1, 0.6, 0.2, 1])
        self.btn_save.bind(on_release=self.show_combined_save_popup)
        self.btn_recall = PlasticButton(text="Recall", btn_color=[1, 0.4, 0.7, 1])
        self.btn_recall.bind(on_release=self.show_combined_recall_popup)
        
        r5.add_widget(self.btn_reset)
        r5.add_widget(self.btn_save)
        r5.add_widget(self.btn_recall)
        self.control_panel.add_widget(r5)

        r6 = BoxLayout(spacing=dp(3), size_hint_y=0.14)
        
        self.btn_undo = PlasticButton(text="< Back Scan", btn_color=[0.8, 0.4, 0.1, 1], size_hint_x=0.4)
        self.btn_undo.bind(on_release=self.undo_click)
        
        self.btn_menu_main = PlasticButton(text="Menu", btn_color=[0.5, 0.5, 0.5, 1], size_hint_x=0.2)
        self.btn_menu_main.bind(on_release=lambda x: self.show_menu_screen())
        
        self.btn_redo = PlasticButton(text="Forward Scan >", btn_color=[0.1, 0.5, 0.8, 1], size_hint_x=0.4)
        self.btn_redo.bind(on_release=self.redo_click)
        
        r6.add_widget(self.btn_undo)
        r6.add_widget(self.btn_menu_main)
        r6.add_widget(self.btn_redo)
        
        self.control_panel.add_widget(r6)

        self.root_layout.add_widget(self.monitor)
        self.root_layout.add_widget(self.control_panel)

    def show_contact_popup(self, *args):
        import webbrowser
        from kivy.uix.scrollview import ScrollView
        
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        
        sv = ScrollView(size_hint_y=0.8)
        list_box = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        list_box.bind(minimum_height=list_box.setter('height'))
        
        tel2_text = "Mobile : 09151001371"
        btn_tel2 = PlasticButton(text=tel2_text, btn_color=[0.18, 0.65, 0.28, 1], size_hint_y=None, height=dp(40))
        btn_tel2.bind(on_release=lambda x: webbrowser.open("tel:09151001371"))
        list_box.add_widget(btn_tel2)
        
        sv.add_widget(list_box)
        content.add_widget(sv)
        
        btn_close = PlasticButton(text="Close", btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.15)
        
        popup = Popup(
            title="Contact Us",
            content=content,
            size_hint=(0.85, 0.75),
            auto_dismiss=True
        )
        btn_close.bind(on_release=popup.dismiss)
        content.add_widget(btn_close)
        popup.open()

    def show_products_popup(self, *args):
        products_data = [
            {
                "title": "1. Winner PRO",
                "desc": "Smart and powerful scanner for detecting metals, water, and voids at high depths, featuring AI target size identification.",
                "img_name": "winner_pro"
            },
            {
                "title": "2. Zeuse",
                "desc": "Powerful long-range locator, reverse-engineered from the powerful Navigator system.",
                "img_name": "zeuse"
            },
            {
                "title": "3. Winner",
                "desc": "Smart scanner for detecting metals, water, and voids.",
                "img_name": "winner"
            },
            {
                "title": "4. Trojan",
                "desc": "Portable and powerful locator with Low and Medium frequencies.",
                "img_name": "trojan"
            }
        ]
        
        self.current_product_idx = 0
        
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        
        from kivy.uix.scrollview import ScrollView
        sv_desc = ScrollView(size_hint_y=0.25)
        lbl_desc = Label(
            text="", 
            markup=True, 
            font_size='13sp', 
            color=[1, 1, 1, 1], 
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        lbl_desc.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
        lbl_desc.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        sv_desc.add_widget(lbl_desc)
        content.add_widget(sv_desc)
        
        img_container = BoxLayout(size_hint_y=0.6, padding=[0, dp(5), 0, dp(5)])
        img_widget = KivyImage(
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 1)
        )
        img_container.add_widget(img_widget)
        content.add_widget(img_container)
        
        nav_row = BoxLayout(spacing=dp(6), size_hint_y=0.15)
        
        btn_prev = PlasticButton(text="Prev", btn_color=[0.11, 0.51, 0.84, 1])
        btn_close = PlasticButton(text="Close", btn_color=[0.8, 0.2, 0.2, 1])
        btn_next = PlasticButton(text="Next", btn_color=[0.18, 0.65, 0.28, 1])
        
        nav_row.add_widget(btn_prev)
        nav_row.add_widget(btn_close)
        nav_row.add_widget(btn_next)
        content.add_widget(nav_row)
        
        popup = Popup(
            title="Products",
            content=content,
            size_hint=(0.94, 0.90),
            auto_dismiss=False
        )
        
        import kivy.resources as resources
        
        def update_view():
            prod = products_data[self.current_product_idx]
            full_text = f"[b][color=#FFD700]{prod['title']}[/color][/b]\n{prod['desc']}"
            
            lbl_desc.text = full_text
            lbl_desc.halign = 'left'
            
            img_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                found = resources.resource_find(f"{prod['img_name']}{ext}")
                if found and os.path.exists(found):
                    img_path = found
                    break
                elif os.path.exists(f"{prod['img_name']}{ext}"):
                    img_path = f"{prod['img_name']}{ext}"
                    break
            
            if img_path:
                img_widget.source = img_path
                img_widget.opacity = 1
            else:
                img_widget.source = ""
                img_widget.opacity = 0
                
        def next_prod(*args):
            self.current_product_idx = (self.current_product_idx + 1) % len(products_data)
            update_view()
            
        def prev_prod(*args):
            self.current_product_idx = (self.current_product_idx - 1) % len(products_data)
            update_view()
            
        btn_next.bind(on_release=next_prod)
        btn_prev.bind(on_release=prev_prod)
        btn_close.bind(on_release=popup.dismiss)
        
        update_view()
        self.register_popup(popup)
        popup.open()

    def show_combined_save_popup(self, *args):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        btn_save_file = PlasticButton(text="Save file Scan", btn_color=[0.1, 0.5, 0.8, 1], size_hint_y=0.33)
        btn_save_pic = PlasticButton(text="Save picture Scan", btn_color=[0.1, 0.6, 0.2, 1], size_hint_y=0.33)
        btn_cancel = PlasticButton(text="Cancel", btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.33)
        
        popup = Popup(title="Save Options", content=content, size_hint=(0.85, 0.45))
        
        def save_file_act(*a):
            popup.dismiss()
            self.save_memory_click()
            
        def save_pic_act(*a):
            popup.dismiss()
            self.save_jpeg_click()
            
        btn_save_file.bind(on_release=save_file_act)
        btn_save_pic.bind(on_release=save_pic_act)
        btn_cancel.bind(on_release=popup.dismiss)
        
        content.add_widget(btn_save_file)
        content.add_widget(btn_save_pic)
        content.add_widget(btn_cancel)
        self.register_popup(popup)
        popup.open()

    def show_combined_recall_popup(self, *args):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        btn_recall_file = PlasticButton(text="Recall file Scan", btn_color=[1, 0.4, 0.7, 1], size_hint_y=0.33)
        btn_recall_pic = PlasticButton(text="Recall picture Scan", btn_color=[0.5, 0.0, 0.5, 1], size_hint_y=0.33)
        btn_cancel = PlasticButton(text="Cancel", btn_color=[0.5, 0.5, 0.5, 1], size_hint_y=0.33)
        
        popup = Popup(title="Recall Options", content=content, size_hint=(0.85, 0.45))
        
        def recall_file_act(*a):
            popup.dismiss()
            self.recall_memory_click()
            
        def recall_pic_act(*a):
            popup.dismiss()
            self.recall_jpeg_click()
            
        btn_recall_file.bind(on_release=recall_file_act)
        btn_recall_pic.bind(on_release=recall_pic_act)
        btn_cancel.bind(on_release=popup.dismiss)
        
        content.add_widget(btn_recall_file)
        content.add_widget(btn_recall_pic)
        content.add_widget(btn_cancel)
        self.register_popup(popup)
        popup.open()

    def register_popup(self, popup):
        if not hasattr(self, 'active_popups'):
            self.active_popups = []
        self.active_popups.append(popup)
        popup.bind(on_dismiss=lambda x: self.active_popups.remove(popup) if popup in self.active_popups else None)

    def _update_bg(self, *args):
        self.root_layout.canvas.before.clear()
        with self.root_layout.canvas.before:
            Color(0.72, 0.72, 0.72, 1)
            Rectangle(pos=self.root_layout.pos, size=self.root_layout.size)
            Color(0.65, 0.65, 0.65, 0.2)
            for i in range(0, int(self.root_layout.height), int(dp(9))):
                Line(points=[self.root_layout.x, self.root_layout.y+i, self.root_layout.x+self.root_layout.width, self.root_layout.y+i], width=1)

    def _update_target_bg(self, i, v=None):
        i.canvas.before.clear()
        with i.canvas.before:
            if self.compare_active or self.get_cut_segments():
                Color(1.0, 1.0, 1.0, 1.0)
            else:
                Color(0.92, 0.83, 0.48, 1)
            RoundedRectangle(pos=(i.x+dp(1), i.y+dp(1)), size=(i.width-dp(2), i.height-dp(2)), radius=[dp(5)])
            if self.compare_active or self.get_cut_segments():
                Color(0, 0, 0, 0.15)
            else:
                Color(0, 0, 0, 0.2)
            Line(points=[i.x+dp(2), i.y+i.height-dp(2), i.x+i.width-dp(2), i.y+i.height-dp(2)], width=1)

    def open_keypad(self, i):
        p = KeypadPopup(target_widget=i, callback=self.keypad_callback)
        self.register_popup(p)
        p.open()

    def keypad_callback(self, t, v):
        if t in self.segs:
            t.value_text = v
            for key, b in zip(self.edge_keys, self.segs):
                if b == t:
                    self.ui_entry_values[key] = v
        else:
            if t == self.in_ref:
                t.value_text = v
                try:
                    self.ui_ref_soil_val = float(v)
                except Exception:
                    pass
            else:
                t.value_text = f"{v} M"
                try:
                    if t == self.in_w:
                        self.ui_width_val = float(v)
                    elif t == self.in_l:
                        self.ui_length_val = float(v)
                except Exception:
                    pass
        self.push_state()
        if self.get_cut_segments():
            self.scanning = False
            self.fibo_active = False
            self.gpr_active = False
        self.monitor.redraw()

    def safe_float(self, value):
        try:
            return float(value)
        except Exception:
            return None

    def clamp(self, value, lo, hi):
        return max(lo, min(hi, value))

    def _lerp(self, a, b, t):
        return a + (b - a) * t

    def normalize_value_to_600(self, R_meas, R_ref):
        if R_meas is None:
            return None
        try:
            R_m = float(R_meas)
            R_r = float(R_ref)
        except (ValueError, TypeError):
            return R_meas

        if R_r <= 0:
            R_r = 600.0

        if R_m < R_r:
            inv_target = (1.0 / R_m) - (1.0 / R_r)
            if inv_target <= 0:
                R_target = 1e-6
            else:
                R_target = 1.0 / inv_target
            
            inv_norm = (1.0 / 600.0) + (1.0 / R_target)
            return 1.0 / inv_norm
        else:
            return R_m * (600.0 / R_r)

    def hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        vx = x2 - x1
        vy = y2 - y1
        wx = px - x1
        wy = py - y1
        c1 = vx * wx + vy * wy
        if c1 <= 0:
            return math.hypot(px - x1, py - y1)
        c2 = vx * vx + vy * vy
        if c2 <= 1e-12:
            return math.hypot(px - x1, py - y1)
        t = c1 / (vx * vx + vy * vy)
        if t >= 1:
            return math.hypot(px - x2, py - y2)
        projx = x1 + t * vx
        projy = y1 + t * vy
        return math.hypot(px - projx, py - projy)

    def project_point_to_segment(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        seg_len2 = dx * dx + dy * dy
        if seg_len2 <= 1e-12:
            return x1, y1
        t = ((px - x1) * dx + (py - y1) * dy) / seg_len2
        t = self.clamp(t, 0.0, 1.0)
        return x1 + t * dx, y1 + t * dy

    def is_value_in_main_range(self, v):
        return v is not None and 0 <= v <= 100000

    def should_allow_circle_rendering(self, vals):
        return any(self.is_value_in_main_range(vals.get(k)) for k in self.edge_keys)

    def filter_circles_for_display(self, circles, vals):
        if not circles:
            return []
        if not self.should_allow_circle_rendering(vals):
            return []
        return circles

    def valid_entries_dict(self):
        vals = {}
        ref_soil = getattr(self, 'ref_soil_val', 600.0)
        if ref_soil <= 0:
            ref_soil = 600.0
        for key in self.edge_keys:
            raw_v = self.safe_float(self.entry_values.get(key, ""))
            if raw_v is not None:
                corrected_v = self.normalize_value_to_600(raw_v, ref_soil)
                vals[key] = corrected_v
            else:
                vals[key] = None
        return vals

    def color_from_stops(self, value, vmin, vmax, stops):
        if abs(vmax - vmin) < 1e-12:
            t = 0.5
        else:
            t = self.clamp((value - vmin) / (vmax - vmin), 0.0, 1.0)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                u = (t - t0) / (t1 - t0) if abs(t1 - t0) > 1e-12 else 0.0
                r = int(self._lerp(c0[0], c1[0], u))
                g = int(self._lerp(c0[1], c1[1], u))
                b = int(self._lerp(c0[2], c1[2], u))
                return (r, g, b)
        rr, gg, bb = stops[-1][1]
        return (rr, gg, bb)

    def classify_target(self, v, ref_soil=600.0):
        if v is None or v < 0 or v > 100000:
            return ("natural", "#00AA00", "#FFFFFF")
            
        norm_v = self.normalize_value_to_600(v, ref_soil)
        if norm_v is None:
            return ("No Target", "#D3D3D3", "#000000")

        if 0 <= norm_v <= 100:
            return ("silver", "#808080", "#FFFFFF")
        elif 100 < norm_v <= 150:
            return ("gold", "#FF0000", "#FFFFFF")
        elif 150 < norm_v <= 250:
            return ("copper", "#FFA500", "#000000")
        elif 250 < norm_v <= 350:
            return ("brass", "#FFD700", "#000000")
        elif 350 < norm_v <= 500:
            return ("iron", "#8B4513", "#FFFFFF")
        elif 500 < norm_v < 700:
            return ("No Target", "#D3D3D3", "#000000")
        elif 700 <= norm_v <= 1100:
            return ("water", "#0000FF", "#FFFFFF")
        elif 1100 < norm_v < 3000:
            return ("No Target", "#D3D3D3", "#000000")
        elif 3000 <= norm_v <= 15000:
            return ("Small Void", self.PURPLE, "#FFFFFF")
        elif 15000 < norm_v <= 25000:
            return ("Medium Void", self.PURPLE, "#FFFFFF")
        elif 25000 < norm_v <= 100000:
            return ("Big Void", self.PURPLE, "#FFFFFF")
        return ("No Target", "#D3D3D3", "#000000")

    def has_void_circle(self):
        for c in self.detected_circles:
            if c.get("label") in ["Void", "Small Void", "Medium Void", "Big Void"]:
                return True
        return False

    def get_closest_edge_or_chord_value(self, xr, yr, vals):
        sides = {
            "p1p2": (0.0, 0.0, 1.0, 0.0),
            "p2p4": (1.0, 0.0, 1.0, 1.0),
            "p4p3": (1.0, 1.0, 0.0, 1.0),
            "p3p1": (0.0, 1.0, 0.0, 0.0)
        }
        chords = {
            "p1p4": (0.0, 0.0, 1.0, 1.0),
            "p2p3": (1.0, 0.0, 0.0, 1.0)
        }
        best_side_dist = float('inf')
        closest_side_key = None
        for key, (x1, y1, x2, y2) in sides.items():
            v = vals.get(key)
            if v is None or not self.is_value_in_main_range(v):
                continue
            dist = self.point_to_segment_distance(xr, yr, x1, y1, x2, y2)
            if dist < best_side_dist:
                best_side_dist = dist
                closest_side_key = key

        best_chord_dist = float('inf')
        closest_chord_key = None
        for key, (x1, y1, x2, y2) in chords.items():
            v = vals.get(key)
            if v is None or not self.is_value_in_main_range(v):
                continue
            dist = self.point_to_segment_distance(xr, yr, x1, y1, x2, y2)
            if dist < best_chord_dist:
                best_chord_dist = dist
                closest_chord_key = key

        side_val = vals.get(closest_side_key) if closest_side_key else None
        chord_val = vals.get(closest_chord_key) if closest_chord_key else None

        if side_val is not None and chord_val is not None:
            return side_val if side_val < chord_val else chord_val
        elif side_val is not None:
            return side_val
        elif chord_val is not None:
            return chord_val
        return None

    def get_closest_line_key(self, cx, cy):
        best_key = None
        min_dist = float('inf')
        for key in self.edge_keys:
            endpoints = self.get_segment_endpoints(key)
            if endpoints[0] is not None and endpoints[1] is not None:
                d = self.point_to_segment_distance(cx, cy, endpoints[0][0], endpoints[0][1], endpoints[1][0], endpoints[1][1])
                if d < min_dist:
                    min_dist = d
                    best_key = key
        return best_key

    def evaluate_skeleton_or_chamber(self, circ):
        val = circ.get("target_value", 0.0)
        label = circ.get("label", "")
        if label in ["water", "natural", "Void", "Small Void", "Medium Void", "Big Void"]:
            return None
        
        cx = circ.get("center_x_ratio", 0.5)
        cy = circ.get("center_y_ratio", 0.5)
        lk = self.get_closest_line_key(cx, cy)
        if not lk:
            return None
            
        vals = self.valid_entries_dict()
        lk_val = vals.get(lk)
        if lk_val is None or not (0 <= lk_val <= 500):
            return None
            
        neighbors = self.line_neighbors().get(lk, [])
        neighbor_vals = [vals.get(nk) for nk in neighbors if vals.get(nk) is not None]
        
        count_700_3000 = sum(1 for v in neighbor_vals if 700 <= v <= 3000)
        count_3000_100000 = sum(1 for v in neighbor_vals if 3000 < v <= 100000)
        
        if count_3000_100000 >= 3:
            return "chamber"
        elif (count_700_3000 >= 3) or (count_700_3000 + count_3000_100000 >= 3):
            return "skeleton"
            
        return None

    def get_closest_matching_input_value(self, xr, yr, vals, target_label, target_value):
        segment_dists = []
        for key in self.edge_keys:
            v = vals.get(key)
            if v is None or not self.is_value_in_main_range(v):
                continue
            endpoints = self.get_segment_endpoints(key)
            if endpoints[0] is not None and endpoints[1] is not None:
                dist = self.point_to_segment_distance(xr, yr, endpoints[0][0], endpoints[0][1], endpoints[1][0], endpoints[1][1])
                segment_dists.append((dist, v, key))
        if not segment_dists:
            return target_value
        segment_dists.sort(key=lambda x: x[0])
        min_dist = segment_dists[0][0]
        candidates = [item for item in segment_dists if item[0] <= min_dist + 0.15]
        candidate_values = [item[1] for item in candidates]
        is_void = (target_value is not None and target_value >= 3000) or (target_label in ["Void", "Small Void", "Medium Void", "Big Void"])
        if is_void:
            return max(candidate_values)
        else:
            return min(candidate_values)

    def resistance_relative_palette_color(self, value, vmin, vmax, invert_for_void=False, x_ratio=None, y_ratio=None):
        if value < 0 or value > 100000:
            return (0, 170, 0)
        if abs(vmax - vmin) < 1e-12:
            t = 0.5
        else:
            t = self.clamp((value - vmin) / (vmax - vmin), 0.0, 1.0)

        if self.expansion_level != 0:
            if self.expansion_level < 0:
                t_green = 0.5
                factor = max(0.0, 1.0 - 0.10 * abs(self.expansion_level))
                t = t_green + (t - t_green) * factor
            else:
                has_void_or_water = False
                if self.detected_circles:
                    for circ in self.detected_circles:
                        if circ.get("label") in ["Void", "Small Void", "Medium Void", "Big Void", "water"]:
                            has_void_or_water = True
                            break
                spatial_bias = 1.0
                if x_ratio is not None and y_ratio is not None:
                    vals = self.valid_entries_dict()
                    if has_void_or_water:
                        largest_edge_key = self.get_largest_edge_key(vals)
                        if largest_edge_key:
                            a, b = self.get_segment_endpoints(largest_edge_key)
                            if a is not None and b is not None:
                                dist_to_edge = self.point_to_segment_distance(x_ratio, y_ratio, a[0], a[1], b[0], b[1])
                                spatial_bias = 1.3 - 0.6 * dist_to_edge
                    else:
                        smallest_side_key = None
                        min_side_val = float('inf')
                        for k in self.side_keys:
                            v = vals.get(k)
                            if v is not None and v < min_side_val:
                                min_side_val = v
                                smallest_side_key = k
                        if smallest_side_key:
                            a, b = self.get_segment_endpoints(smallest_side_key)
                            if a is not None and b is not None:
                                dist_to_edge = self.point_to_segment_distance(x_ratio, y_ratio, a[0], a[1], b[0], b[1])
                                spatial_bias = 1.3 - 0.6 * dist_to_edge
                shift = 0.10 * self.expansion_level * spatial_bias
                if has_void_or_water:
                    t = self.clamp(t + shift, 0.0, 1.0)
                else:
                    t = self.clamp(t - shift, 0.0, 1.0)

        t_smooth = t * t * (3.0 - 2.0 * t)

        stops = []
        if self.fibo_active:
            label_max, color_max, _ = self.classify_target(vmax, 600.0)
            
            if label_max in ["Void", "Small Void", "Medium Void", "Big Void"]:
                stops = [
                    (0.00, (0, 100, 30)),     
                    (0.15, (0, 150, 40)),     
                    (0.40, (0, 195, 55)),     
                    (0.60, (110, 210, 50)),   
                    (0.75, (235, 235, 0)),    
                    (0.88, (230, 200, 80)),   
                    (0.95, (220, 180, 230)),  
                    (1.00, (210, 170, 255))   
                ]
            else:
                stops = [
                    (0.00, (0, 100, 30)),
                    (0.03, (0, 120, 35)),
                    (0.07, (0, 140, 40)),
                    (0.15, (0, 160, 45)),
                    (0.35, (0, 195, 55)),
                    (0.50, (0, 220, 75)),
                    (0.60, (0, 195, 55)),
                    (0.70, (0, 205, 65)),     
                    (0.82, (0, 185, 50)),     
                    (0.90, (110, 210, 50)),   
                    (0.97, (130, 180, 45)),   
                    (1.00, (140, 160, 40))    
                ]
            
            rgb_min = (0, 120, 35)
            has_custom_min = False
            if x_ratio is not None and y_ratio is not None and self.detected_circles:
                total_weight = 0.0
                r_sum, g_sum, b_sum = 0.0, 0.0, 0.0
                for circ in self.detected_circles:
                    if circ.get("label") in ["Void", "Small Void", "Medium Void", "Big Void", "natural"]:
                        continue
                    cx, cy = circ["center_x_ratio"], circ["center_y_ratio"]
                    dist = math.hypot(x_ratio - cx, y_ratio - cy)
                    weight = 1.0 / (dist * dist + 1e-4)
                    c_rgb = self.hex_to_rgb(circ.get("fill_color", "#FF0000"))
                    r_sum += c_rgb[0] * weight
                    g_sum += c_rgb[1] * weight
                    b_sum += c_rgb[2] * weight
                    total_weight += weight
                if total_weight > 0.0:
                    rgb_min = (int(r_sum / total_weight), int(g_sum / total_weight), int(b_sum / total_weight))
                    has_custom_min = True

            if not has_custom_min:
                label_min, color_min, _ = self.classify_target(vmin, 600.0)
                if label_min in ["silver", "gold", "copper", "brass", "iron", "water", "Unknown", "No Target"]:
                    rgb_min = self.hex_to_rgb(color_min)
                    has_custom_min = True

            if has_custom_min:
                stops[0] = (0.00, (max(0, int(rgb_min[0] * 0.5)), max(0, int(rgb_min[1] * 0.5)), max(0, int(rgb_min[2] * 0.5))))
                stops[1] = (0.03, rgb_min)
                stops[2] = (0.07, (max(0, int(self._lerp(rgb_min[0], 255, 0.4))), max(0, int(self._lerp(rgb_min[1], 90, 0.4))), max(0, int(self._lerp(rgb_min[2], 0, 0.4)))))

        elif 700 <= vmin <= 1100:
            stops = [
                (0.00, (0, 0, 150)),
                (0.05, (0, 120, 255)),
                (0.15, (0, 195, 55)),
                (0.50, (0, 205, 75)),
                (1.00, (30, 150, 30))
            ]
        else:
            stops = [
                (0.00, (115, 0, 0)),
                (0.03, (235, 0, 0)),
                (0.07, (255, 90, 0)),
                (0.12, (255, 215, 0)),
                (0.18, (150, 230, 0)),
                (0.50, (0, 195, 55)),
                (0.88, (0, 205, 75)),
                (0.93, (0, 175, 235)),
                (0.96, (0, 65, 220)),
                (0.98, (60, 0, 180)),
                (1.00, (95, 0, 145))
            ]
            rgb_min = (235, 0, 0)
            has_custom_min = False
            if x_ratio is not None and y_ratio is not None and self.detected_circles:
                total_weight = 0.0
                r_sum, g_sum, b_sum = 0.0, 0.0, 0.0
                for circ in self.detected_circles:
                    if circ.get("label") in ["Void", "Small Void", "Medium Void", "Big Void", "natural"]:
                        continue
                    cx, cy = circ["center_x_ratio"], circ["center_y_ratio"]
                    dist = math.hypot(x_ratio - cx, y_ratio - cy)
                    weight = 1.0 / (dist * dist + 1e-4)
                    c_rgb = self.hex_to_rgb(circ.get("fill_color", "#FF0000"))
                    r_sum += c_rgb[0] * weight
                    g_sum += c_rgb[1] * weight
                    b_sum += c_rgb[2] * weight
                    total_weight += weight
                if total_weight > 0.0:
                    rgb_min = (int(r_sum / total_weight), int(g_sum / total_weight), int(b_sum / total_weight))
                    has_custom_min = True

            if not has_custom_min:
                label_min, color_min, _ = self.classify_target(vmin, 600.0)
                if label_min in ["silver", "gold", "copper", "brass", "iron", "water", "Unknown", "No Target"]:
                    rgb_min = self.hex_to_rgb(color_min)
                    has_custom_min = True

            if has_custom_min:
                stops[0] = (0.00, (max(0, int(rgb_min[0] * 0.5)), max(0, int(rgb_min[1] * 0.5)), max(0, int(rgb_min[2] * 0.5))))
                stops[1] = (0.03, rgb_min)
                stops[2] = (0.07, (max(0, int(self._lerp(rgb_min[0], 255, 0.4))), max(0, int(self._lerp(rgb_min[1], 90, 0.4))), max(0, int(self._lerp(rgb_min[2], 0, 0.4)))))

            if not self.fibo_active:
                label_max, color_max, _ = self.classify_target(vmax, 600.0)
                if label_max in ["Void", "Small Void", "Medium Void", "Big Void"]:
                    rgb_max = self.hex_to_rgb(color_max)
                    stops[-2] = (0.98, rgb_max)
                    stops[-1] = (1.00, (max(0, int(rgb_max[0] * 0.6)), max(0, int(rgb_max[1] * 0.6)), max(0, int(rgb_max[2] * 0.6))))

        return self.color_from_stops(t_smooth, 0.0, 1.0, stops)

    def build_gaussian_kernel_1d(self, sigma):
        sigma = max(0.01, float(sigma))
        radius = max(1, int(3.0 * sigma))
        kernel = []
        s2 = sigma * sigma
        for i in range(-radius, radius + 1):
            kernel.append(math.exp(-(i * i) / (2.0 * s2)))
        total = sum(kernel)
        return [k / total for k in kernel]

    def gaussian_blur_2d(self, grid, sigma):
        if sigma <= 0.01:
            return [row[:] for row in grid]
        kernel = self.build_gaussian_kernel_1d(sigma)
        radius = len(kernel) // 2
        ny = len(grid)
        nx = len(grid[0]) if ny > 0 else 0
        temp = [[0.0 for _ in range(nx)] for _ in range(ny)]
        for y in range(ny):
            for x in range(nx):
                s = 0.0
                for k in range(-radius, radius + 1):
                    xx = int(self.clamp(x + k, 0, nx - 1))
                    s += grid[y][xx] * kernel[k + radius]
                temp[y][x] = s
        out = [[0.0 for _ in range(nx)] for _ in range(ny)]
        
        for y in range(ny):
            for x in range(nx):
                s = 0.0
                for k in range(-radius, radius + 1):
                    yy = int(self.clamp(y + k, 0, ny - 1))
                    s += temp[yy][x] * kernel[k + radius]
                out[y][x] = s
        return out

    def line_neighbors(self):
        return {
            "p1p4": ["p1p2", "p3p1", "p2p4", "p4p3"],
            "p2p3": ["p1p2", "p2p4", "p3p1", "p4p3"],
            "p1p2": ["p3p1", "p2p4", "p1p4", "p2p3"],
            "p2p4": ["p1p2", "p4p3", "p1p4", "p2p3"],
            "p4p3": ["p2p4", "p3p1", "p1p4", "p2p3"],         
            "p3p1": ["p1p2", "p4p3", "p1p4", "p2p3"],
        }

    def side_diag_relation(self):
        return {
            "p1p2": ["p1p4", "p2p3"], "p2p4": ["p1p4", "p2p3"],
            "p4p3": ["p1p4", "p2p3"], "p3p1": ["p1p4", "p2p3"],
        }

    def is_center_red_focus_condition(self, vals):
        d1 = vals.get("p1p4")
        d2 = vals.get("p2p3")
        if not self.is_value_in_main_range(d1) or not self.is_value_in_main_range(d2):
            return False
        side_vals = [vals.get(k) for k in self.side_keys if self.is_value_in_main_range(vals.get(k))]
        if not side_vals:
            return False
        side_min = min(side_vals)
        side_avg = sum(side_vals) / len(side_vals)
        diag_avg = (d1 + d2) / 2.0
        return (d1 < side_min) and (d2 < side_min) and (side_avg > diag_avg)

    def should_allow_circle_rendering_for_mode(self):
        if self.active_mode == "2-prop":
            return False
        return True

    def should_use_center_red_focus(self, vals):
        if not self.is_center_red_focus_condition(vals):
            return False
        side_case = self.get_small_side_candidate_when_diags_dominate(vals)
        if side_case is None:
            return True
        side_val = side_case["side_value"]
        diag_min = side_case["diag_min"]
        if side_val > diag_min:
            return False
        return True

    def values_are_in_same_class_range(self, a, b):
        if not self.is_value_in_main_range(a) or not self.is_value_in_main_range(b):
            return False
        la, _, _ = self.classify_target(a, 600.0)
        lb, _, _ = self.classify_target(b, 600.0)
        return la == lb

    def diagonal_side_support(self, diag_key, vals):
        if diag_key == "p1p4":
            group_a, group_b = ["p3p1", "p4p3"], ["p1p2", "p2p4"]
        elif diag_key == "p2p3":
            group_a, group_b = ["p1p2", "p3p1"], ["p2p4", "p4p3"]
        else:
            return {"a": 0.0, "b": 0.0}
        valid_vals = [vv for vv in vals.values() if self.is_value_in_main_range(vv)]
        if not valid_vals:
            return {"a": 0.0, "b": 0.0}
        vmin, vmax = min(valid_vals), max(valid_vals)
        if abs(vmax - vmin) < 1e-12:
            return {"a": 0.0, "b": 0.0}
        def avg_low(group):
            arr = [vals.get(k) for k in group if self.is_value_in_main_range(vals.get(k))]
            if not arr:
                return 0.0
            t = self.clamp((sum(arr)/len(arr) - vmin) / (vmax - vmin), 0.0, 1.0)
            return 1.0 - t
        return {"a": avg_low(group_a), "b": avg_low(group_b)}

    def get_void_special_center_pos(self, vals):
        for k in self.edge_keys:
            v = vals.get(k)
            if v is None or not (3000 <= v <= 100000):
                return None
        v_side = {k: vals[k] for k in self.side_keys}
        v_diag = {k: vals[k] for k in self.diag_keys}
        max_side_val = max(v_side.values())
        if v_diag["p1p4"] <= max_side_val or v_diag["p2p3"] <= max_side_val:
            return None
        d1, d2 = v_diag["p1p4"], v_diag["p2p3"]
        if abs(d1 - d2) < 1e-5:
            return 0.5, 0.5
        largest_side_key = max(v_side, key=v_side.get)
        midpoints = {"p1p2": (0.5, 0.0), "p2p4": (1.0, 0.5), "p4p3": (0.5, 1.0), "p3p1": (0.0, 0.5)}
        mx, my = midpoints[largest_side_key]
        cx = 0.5 + (mx - 0.5) * 0.18
        cy = 0.5 + (my - 0.5) * 0.18
        return self.clamp(cx, 0.05, 0.95), self.clamp(cy, 0.05, 0.95)

    def build_line_sources(self, vals):
        p1, p2, p3, p4 = (0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)
        mapping = [
            ("p1p2", p1, p2, 1.00, 0.10), ("p2p4", p2, p4, 1.00, 0.10),
            ("p4p3", p4, p3, 1.00, 0.10), ("p3p1", p3, p1, 1.00, 0.10),
            ("p1p4", p1, p4, 1.20, 0.085), ("p2p3", p2, p3, 1.20, 0.085),
        ]
        valid_vals = [v for v in vals.values() if self.is_value_in_main_range(v)]
        if not valid_vals:
            return None
        vmin, vmax = min(valid_vals), max(valid_vals)
        neighbors = self.line_neighbors()
        side_diag_map = self.side_diag_relation()
        is_void_spec = (self.get_void_special_center_pos(vals) is not None)
        sources = []
        for key, a, b, base_weight, sigma in mapping:
            v = vals.get(key)
            if not self.is_value_in_main_range(v):
                continue
            effective_value = v
            no_circle_on_edge = False
            if key in self.side_keys:
                related_diags = side_diag_map.get(key, [])
                matched_diags = []
                if not is_void_spec:
                    for dk in related_diags:
                        dv = vals.get(dk)
                        if self.values_are_in_same_class_range(v, dv):
                            matched_diags.append(dv)
                if matched_diags:
                    no_circle_on_edge = True
                    effective_value = (v + sum(matched_diags) / len(matched_diags)) / 2.0
            t = 0.0 if abs(vmax - vmin) < 1e-12 else self.clamp((effective_value - vmin) / (vmax - vmin), 0.0, 1.0)
            relative_low = 1.0 - t
            neighbors_list = neighbors.get(key, [])
            neighbor_vals = []
            for nk in neighbors_list:
                nv = vals.get(nk)
                if self.is_value_in_main_range(nv):
                    if key in self.side_keys and self.values_are_in_same_class_range(v, nv):
                        neighbor_vals.append((v + nv) / 2.0)
                    else:
                        neighbor_vals.append(nv)
            if neighbor_vals and abs(vmax - vmin) > 1e-12:
                neighbor_avg = sum(neighbor_vals) / len(neighbor_vals)
                neighbor_low = 1.0 - self.clamp((neighbor_avg - vmin) / (vmax - vmin), 0.0, 1.0)
            else:
                neighbor_low = relative_low
            
            diag_boost = 1.0
            diag_side_support = {"a": 0.0, "b": 0.0}
            if key in self.diag_keys and relative_low > 0.6:
                diag_boost = 1.20
                diag_side_support = self.diagonal_side_support(key, vals)
            sources.append({
                "key": key, "a": a, "b": b, "value": v, "effective_value": effective_value,
                "base_weight": base_weight * diag_boost, "sigma": sigma,
                "relative_low": relative_low, "neighbor_low": neighbor_low,
                "no_circle_on_edge": no_circle_on_edge, "diag_side_support": diag_side_support,
            })
        return sources, vmin, vmax

    def build_center_red_focus_grid(self, nx, ny, vals, vmin, vmax):
        d1 = vals.get("p1p4")
        d2 = vals.get("p2p3")
        side_vals = [vals[k] for k in self.side_keys if self.is_value_in_main_range(vals.get(k))]
        diag_min = min(d1, d2)
        side_avg = sum(side_vals) / max(1, len(side_vals))
        outer_target = self.clamp(max(side_avg, diag_min + 0.55 * max(1.0, vmax - vmin)), vmin, vmax)
        s1, s2 = 1.0/max(d1, 1e-9), 1.0/max(d2, 1e-9)
        w1, w2 = (s1/(s1+s2), s2/(s1+s2)) if (s1+s2) > 1e-12 else (0.5, 0.5)
        proj1 = self.project_point_to_segment(0.5, 0.5, 0.0, 0.0, 1.0, 1.0)
        bx, by = w1 * proj1[0] + w2 * proj1[0], w1 * proj1[1] + w2 * proj1[1]
        smaller_diag = "p1p4" if d1 <= d2 else "p2p3"
        larger_diag = "p2p3" if d1 <= d2 else "p1p4"
        a1, b1 = self.get_segment_endpoints(smaller_diag)
        a2, b2 = self.get_segment_endpoints(larger_diag)
        p1x, p1y = self.project_point_to_segment(bx, by, a1[0], a1[1], b1[0], b1[1])
        p2x, p2y = self.project_point_to_segment(bx, by, a2[0], a2[1], b2[0], b2[1])
        t = self.clamp((vals.get(larger_diag) or 0.0) / max((vals.get(smaller_diag) or 0.0) + (vals.get(larger_diag) or 0.0), 1e-9), 0.0, 1.0)
        focus_x = self._lerp(p2x, p1x, t)
        focus_y = self._lerp(p2y, p1y, t)
        phi = 1.6180339887
        grid = []
        for j in range(ny):
            row = []
            y = j / (ny - 1) if ny > 1 else 0.5
            for i in range(nx):
                x = i / (nx - 1) if nx > 1 else 0.5
                if self.fibo_active:
                    dx = x + 0.03 * math.sin(phi * 5.0 * y)
                    dy = y + 0.03 * math.cos(phi * 5.0 * x)
                    r = math.hypot(dx - focus_x, dy - focus_y)
                    core = math.pow(phi, -(r * r) / (2.0 * 0.22 * 0.22))
                else:
                    dx = x + 0.045 * math.sin(3.6 * y + 0.8) + 0.03 * math.cos(5.2 * y)
                    dy = y
                    r = math.hypot(dx - focus_x, dy - focus_y)
                    core = math.exp(-(r * r) / (2.0 * 0.22 * 0.22))
                edge_bias = self.clamp(((abs(dx - 0.5) / 0.5) + (abs(dy - 0.5) / 0.5)) / 2.0, 0.0, 1.0)
                row.append(self._lerp(self._lerp(outer_target, vmax, 0.20 * edge_bias), diag_min, core))
            grid.append(row)
        return self.gaussian_blur_2d(grid, 1.2)

    def diagonal_half_plane_weight(self, key, x, y):
        s = (y - x) if key == "p1p4" else (y + x - 1.0)
        band = 0.06
        if s >= band:
            return 1.0, 0.0
        if s <= -band:
            return 0.0, 1.0
        t = (s + band) / (2.0 * band + 1e-9)
        return t, 1.0 - t

    def compute_cell_value(self, x, y, sources, global_vmin, global_vmax):
        if not sources:
            return 15000.0
        dx = x + 0.045 * math.sin(3.6 * y + 0.8) + 0.02 * math.cos(5.2 * x)
        dy = y + 0.045 * math.sin(3.6 * x + 1.2) + 0.02 * math.cos(5.2 * y)
        low_corners = []
        vals = self.valid_entries_dict()
        sides = {k: vals.get(k) for k in self.side_keys}
        if not any(v is None for v in sides.values()):
            min_side_val = min(sides.values())
            all_vals = [v for v in vals.values() if v is not None]
            v_span = max(all_vals) - min(all_vals) if all_vals else 1.0
            tolerance = max(35.0, 0.25 * v_span)
            if abs(sides["p1p2"] - min_side_val) <= tolerance and abs(sides["p3p1"] - min_side_val) <= tolerance:
                low_corners.append({"vertex": (0.0, 0.0), "sides": ["p1p2", "p3p1"]})
            if abs(sides["p1p2"] - min_side_val) <= tolerance and abs(sides["p2p4"] - min_side_val) <= tolerance:
                low_corners.append({"vertex": (1.0, 0.0), "sides": ["p1p2", "p2p4"]})
            if abs(sides["p2p4"] - min_side_val) <= tolerance and abs(sides["p4p3"] - min_side_val) <= tolerance:
                low_corners.append({"vertex": (1.0, 1.0), "sides": ["p2p4", "p4p3"]})
            if abs(sides["p4p3"] - min_side_val) <= tolerance and abs(sides["p3p1"] - min_side_val) <= tolerance:
                low_corners.append({"vertex": (0.0, 1.0), "sides": ["p4p3", "p3p1"]})
        sum_val = 0.0
        sum_w = 0.0
        for src in sources:
            dist_a = math.hypot(dx - src["a"][0], dy - src["a"][1])
            dist_b = math.hypot(dx - src["b"][0], dy - src["b"][1])
            d = dist_a + dist_b - math.hypot(src["a"][0] - src["b"][0], src["a"][1] - src["b"][1])
            effective_sigma = src["sigma"] * 1.55 if src["key"] in self.diag_keys else src["sigma"] * 1.25
            w = math.exp(-(d * d) / (2.0 * effective_sigma * effective_sigma)) * src["base_weight"]
            local_pull = 0.70 * src["relative_low"] + 0.30 * src["neighbor_low"]
            for corner in low_corners:
                if src["key"] in corner["sides"]:
                    d_v = math.hypot(dx - corner["vertex"][0], dy - corner["vertex"][1])
                    if d_v < 0.40:
                        damping = 0.15 + 0.85 * ((d_v/0.40)**2)
                        w *= damping
                        local_pull *= damping
            if src["key"] in self.diag_keys:
                supp = src.get("diag_side_support", {"a": 0.0, "b": 0.0})
                wa, wb = self.diagonal_half_plane_weight(src["key"], dx, dy)
                gate = self.clamp(0.15 + 0.85 * (wa * supp.get("a", 0.0) + wb * supp.get("b", 0.0)), 0.15, 1.0)
                local_pull *= gate
                w *= (0.45 + 0.55 * gate)
            sum_val += w * self._lerp(src["effective_value"], global_vmin, 0.52 * local_pull)
            sum_w += w
        return (sum_val / sum_w) if sum_w > 1e-12 else (global_vmin + global_vmax) / 2.0

    def compute_cluster_compact_diameter(self, cluster_set, nx, ny):
        cluster_list = list(cluster_set)
        if not cluster_list:
            return 0.0
        boundary = []
        for (x, y) in cluster_list:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                xx, yy = x + dx, y + dy
                if not (0 <= xx < nx and 0 <= yy < ny) or ((xx, yy) not in cluster_set):
                    boundary.append((x, y))
                    break
        if not boundary:
            boundary = cluster_list[:]
        if len(boundary) > 260:
            boundary = boundary[::max(1, len(boundary) // 260)]
        pts = cluster_list[:]
        if len(pts) > 900:
            pts = pts[::max(1, len(pts) // 900)]
        sum_min_dist = 0.0
        for (x, y) in pts:
            best = min(math.hypot(x - bx, y - by) for (bx, by) in boundary)
            sum_min_dist += best
        diag = math.hypot(nx - 1, ny - 1)
        return (sum_min_dist / max(1, len(pts))) / diag if diag > 1e-9 else 0.0

    def get_cluster_boundary_points(self, cluster_set, nx, ny):
        boundary = []
        for (x, y) in cluster_set:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if not (0 <= x+dx < nx and 0 <= cy+dy < ny) or ((x+dx, y+dy) not in cluster_set):
                    boundary.append((x, y))
                    break
        return boundary if boundary else list(cluster_set)

    def repel_circle_from_edges(self, xr, yr, radius_ratio):
        safe_margin = max(0.04, radius_ratio * 1.0)
        return self.clamp(xr, safe_margin, 1.0 - safe_margin), self.clamp(yr, safe_margin, 1.0 - safe_margin)

    def shift_towards_nearest_line(self, cx, cy, diameter_m):
        d_bottom = cy
        d_top = 1.0 - cy
        d_left = cx
        d_right = 1.0 - cx
        min_d = min(d_bottom, d_top, d_left, d_right)
        shift_amount = 0.12
        dx, dy = 0.0, 0.0
        if min_d == d_bottom:
            dy = -shift_amount
        elif min_d == d_top:
            dy = shift_amount
        elif min_d == d_left:
            dx = -shift_amount
        elif min_d == d_right:
            dx = shift_amount
        new_cx = cx + dx
        new_cy = cy + dy
        radius_ratio = (diameter_m / 2.0) / max(min(self.width_val, self.length_val), 1e-9)
        return self.repel_circle_from_edges(new_cx, new_cy, radius_ratio)

    def get_side_segment(self, key):
        segs = {"p1p2": (0.0, 0.0, 1.0, 0.0), "p2p4": (1.0, 0.0, 1.0, 1.0), "p4p3": (1.0, 1.0, 0.0, 1.0), "p3p1": (0.0, 1.0, 0.0, 0.0)}
        return segs.get(key)

    def get_segment_endpoints(self, key):
        seg = self.get_side_segment(key) or ( (0.0,0.0,1.0,1.0) if key=="p1p4" else ((1.0,0.0,0.0,1.0) if key=="p2p3" else None) )
        return ((seg[0], seg[1]), (seg[2], seg[3])) if seg else (None, None)

    def get_smallest_chord_key(self, vals):
        candidates = [(vals.get(k), k) for k in self.diag_keys if self.is_value_in_main_range(vals.get(k))]
        return min(candidates, key=lambda t: t[0])[1] if candidates else None

    def get_largest_edge_key(self, vals):
        candidates = [(vals.get(k), k) for k in self.edge_keys if vals.get(k) is not None and self.is_value_in_main_range(vals.get(k))]
        return max(candidates, key=lambda t: t[0])[1] if candidates else None

    def move_void_toward_largest_edge(self, x, y, vals, pull_percent):
        largest_key = self.get_largest_edge_key(vals)
        if not largest_key:
            return x, y
        a, b = self.get_segment_endpoints(largest_key)
        if not a or not b:
            return x, y
        px, py = self.project_point_to_segment(x, y, a[0], a[1], b[0], b[1])
        pull_t = self.clamp(pull_percent / 100.0, 0.0, 1.0)
        return self.clamp(self._lerp(x, px, pull_t), 0.0, 1.0), self.clamp(self._lerp(y, py, pull_t), 0.0, 1.0)

    def move_point_toward_chord_only(self, x, y, chord_key, pull_percent):
        if not chord_key:
            return x, y
        a, b = self.get_segment_endpoints(chord_key)
        if not a or not b:
            return x, y
        px, py = self.project_point_to_segment(x, y, a[0], a[1], b[0], b[1])
        pull_t = self.clamp(pull_percent / 100.0, 0.0, 1.0)
        return self.clamp(self._lerp(x, px, pull_t), 0.0, 1.0), self.clamp(self._lerp(y, py, pull_t), 0.0, 1.0)

    def detect_soil_contamination(self, vals):
        valid_vals = [vals.get(k) for k in self.edge_keys if self.is_value_in_main_range(vals.get(k))]
        if len(valid_vals) < len(self.edge_keys):
            return False
        if self.width_val <= 3.0 or self.length_val <= 3.0:
            return False
        diff = max(valid_vals) - min(valid_vals)
        return diff <= 100.0

    def get_two_smallest_diagonals_condition(self, vals):
        d1 = vals.get("p1p4")
        d2 = vals.get("p2p3")
        if not self.is_value_in_main_range(d1) or not self.is_value_in_main_range(d2):
            return None
        side_vals = []
        for k in self.side_keys:
            v = vals.get(k)
            if not self.is_value_in_main_range(v):
                return None
            side_vals.append(v)
        if not side_vals:
            return None
        side_min = min(side_vals)
        if d1 < side_min and d2 < side_min:
            return {
                "p1p4": d1,
                "p2p3": d2,
                "smaller_diag": "p1p4" if d1 <= d2 else "p2p3",
                "larger_diag": "p2p3" if d1 <= d2 else "p1p4"
            }
        return None

    def get_small_side_candidate_when_diags_dominate(self, vals):
        d1, d2 = vals.get("p1p4"), vals.get("p2p3")
        
        if not self.is_value_in_main_range(d1) or not self.is_value_in_main_range(d2):
            return None
        diag_min, diag_max = min(d1, d2), max(d1, d2)
        valid_sides = sorted([(vals.get(k), k) for k in self.side_keys if self.is_value_in_main_range(vals.get(k))], key=lambda x: x[0])
        if not valid_sides:
            return None
        all_vals = [v for v in vals.values() if self.is_value_in_main_range(v)]
        span = max(all_vals) - min(all_vals) if all_vals else 0
        threshold = diag_max + 0.45 * span
        for side_v, side_k in valid_sides:
            if diag_min < side_v <= threshold:
                return {"side_key": side_k, "side_value": side_v, "diag_min": diag_min, "diag_max": diag_max}
        return {"side_key": valid_sides[0][1], "side_value": valid_sides[0][0], "diag_min": diag_min, "diag_max": diag_max}

    def get_side_direction_vector(self, side_key):
        dirs = {
            "p1p2": ((0.0, -1.0), (0.5, 0.12)), 
            "p2p4": ((1.0, 0.0), (0.88, 0.5)), 
            "p4p3": ((0.0, 1.0), (0.5, 0.88)), 
            "p3p1": ((-1.0, 0.0), (0.12, 0.5))
        }
        return dirs.get(side_key, ((0.0, 0.0), (0.5, 0.5)))

    def is_red_present_at_ratio(self, xr, yr):
        if not self.heatmap_data:
            return False
        grid, nx, ny = self.heatmap_data["grid"], self.heatmap_data["nx"], self.heatmap_data["ny"]
        vmin, vmax = self.heatmap_data["min"], self.heatmap_data["max"]
        ix = int(round(self.clamp(xr, 0.0, 1.0) * (nx - 1)))
        iy = int(round(self.clamp(xr, 0.0, 1.0) * (ny - 1)))
        return False if (vmax - vmin) <= 1e-12 else (self.clamp((grid[iy][ix] - vmin)/(vmax - vmin), 0.0, 1.0) <= 0.18)

    def is_red_present_in_center_and_side(self, side_key):
        return self.is_red_present_at_ratio(0.5, 0.5) and self.is_red_present_at_ratio(*self.get_side_direction_vector(side_key)[1])

    def build_balanced_side_circle_position(self, side_key, vals):
        side_val = vals.get(side_key)
        if not self.is_value_in_main_range(side_val):
            return 0.5, 0.5
        diags = [vals.get(k) for k in self.diag_keys if self.is_value_in_main_range(vals.get(k))]
        if not diags:
            return self.get_side_direction_vector(side_key)[1]
        diag_min = min(diags)
        all_vals = [v for v in vals.values() if self.is_value_in_main_range(v)]
        span = max(all_vals) - min(all_vals) if all_vals else 1e-9
        closeness = 1.0 - self.clamp((side_val - diag_min)/(0.35 * span), 0.0, 1.0)
        _, anchor = self.get_side_direction_vector(side_key)
        sc_key = self.get_smallest_chord_key(vals)
        if not sc_key:
            return anchor
        a, b = self.get_segment_endpoints(sc_key)
        if not a or not b:
            return anchor
        c_proj_x, c_proj_y = self.project_point_to_segment(anchor[0], anchor[1], a[0], a[1], b[0], b[1])
        mid_x = self._lerp(anchor[0], c_proj_x, (self.chord_pull/100.0) * (0.25 + 0.75*closeness))
        mid_y = self._lerp(anchor[1], c_proj_y, (self.chord_pull/100.0) * (0.25 + 0.75*closeness))
        side_shift = 0.0
        left_k, right_k = ("p3p1", "p2p4") if side_key in ["p1p2", "p4p3"] else ("p1p2", "p4p3")
        if self.is_value_in_main_range(vals.get(left_k)) and self.is_value_in_main_range(vals.get(right_k)):
            side_shift = 0.10 * self.expansion_level * self.clamp((vals[left_k] - vals[right_k]) / (vals[left_k] + vals[right_k] + 1e-4), -1.0, 1.0)
        if side_key in ["p1p2", "p4p3"]:
            mid_x += side_shift
        else:
            mid_y += side_shift
        return self.clamp(mid_x, 0.05, 0.95), self.clamp(mid_y, 0.05, 0.95)

    def build_warning_arrow_for_edge(self, side_key, color=(17, 17, 255)):
        direction, anchor = self.get_side_direction_vector(side_key)
        sx = anchor[0] * 0.82 + 0.09
        sy = anchor[1] * 0.82 + 0.09
        return {
            "start_x_ratio": self.clamp(sx, 0.06, 0.94), "start_y_ratio": self.clamp(sy, 0.06, 0.94),
            "end_x_ratio": self.clamp(sx + direction[0]*0.10, 0.02, 0.98), "end_y_ratio": self.clamp(sy + direction[1]*0.10, 0.02, 0.98),
            "side_key": side_key, "color": color
        }

    def detect_low_res_zones_multi(self, grid, nx, ny):
        flat = [vv for row in grid for vv in row]
        if not flat:
            return []
        gmin = min(flat)
        vmax = max(flat)
        span = vmax - gmin
        if span <= 1e-12:
            return []
        threshold = gmin + 0.08 * span
        mask = [[grid[j][i] <= threshold for i in range(nx)] for j in range(ny)]
        visited = [[False for _ in range(nx)] for _ in range(ny)]
        clusters = []
        for j in range(ny):
            for i in range(nx):
                if mask[j][i] and not visited[j][i]:
                    cluster = []
                    q = [(i, j)]
                    visited[j][i] = True
                    qi = 0
                    while qi < len(q):
                        cx, cy = q[qi]
                        qi += 1
                        cluster.append((cx, cy))
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            xx, yy = cx + dx, cy + dy
                            if 0 <= xx < nx and 0 <= yy < ny and mask[yy][xx] and not visited[yy][xx]:
                                visited[yy][xx] = True
                                q.append((xx, yy))
                    if len(cluster) > 15:
                        clusters.append(cluster)
        clusters.sort(key=len, reverse=True)
        clusters = clusters[:8]
        min_d = self.min_diameter
        max_d = self.max_diameter
        if max_d < min_d:
            max_d = min_d
        results = []
        for cluster in clusters:
            cluster_set = set(cluster)
            avg_x = sum(p[0] for p in cluster) / len(cluster)
            avg_y = sum(p[1] for p in cluster) / len(cluster)
            peak_p = min(cluster, key=lambda p: grid[p[1]][p[0]])
            min_cluster_val = grid[peak_p[1]][peak_p[0]]
            xr = avg_x / (nx - 1) if (nx > 1) else 0.5
            yr = avg_y / (ny - 1) if (ny > 1) else 0.5
            min_cluster_x = min(p[0] for p in cluster) / (nx - 1) if nx > 1 else 0.0
            max_cluster_x = max(p[0] for p in cluster) / (nx - 1) if nx > 1 else 1.0
            min_cluster_y = min(p[1] for p in cluster) / (ny - 1) if ny > 1 else 0.0
            max_cluster_y = max(p[1] for p in cluster) / (ny - 1) if ny > 1 else 1.0
            zw = (max_cluster_x - min_cluster_x) * self.width_val
            zh = (max_cluster_y - min_cluster_y) * self.length_val
            border_bbox = (zw + zh) / 2.0
            compact_ratio = self.compute_cluster_compact_diameter(cluster_set, nx, ny)
            avg_dim_m = (self.width_val + self.length_val) / 2.0
            border_compact = (compact_ratio * avg_dim_m) * 2.2
            diameter_m = self.clamp(0.55 * border_bbox + 0.45 * border_compact, min_d, max_d)
            radius_ratio = (diameter_m / 2.0) / max(min(self.width_val, self.length_val), 1e-9)
            xr, yr = self.repel_circle_from_edges(xr, yr, radius_ratio)
            local_val = min_cluster_val
            label, fill_color, text_color = self.classify_target(local_val, 600.0)
            results.append({
                "center_x_ratio": xr, "center_y_ratio": yr, "diameter_m": diameter_m, "target_value": local_val,
                "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "cluster",
                "cluster_bounds": {"min_cluster_x": min_cluster_x, "max_cluster_x": max_cluster_x, "min_cluster_y": min_cluster_y, "max_cluster_y": max_cluster_y}
            })
        results.sort(key=lambda c: c["target_value"])
        return results

    def detect_high_res_zones_multi(self, grid, nx, ny):
        flat = [vv for row in grid for vv in row]
        if not flat:
            return []
        gmin, vmax = min(flat), max(flat)
        span = vmax - gmin
        if span <= 1e-12:
            return []
        threshold = vmax - 0.18 * span
        mask = [[grid[j][i] >= threshold for i in range(nx)] for j in range(ny)]
        visited = [[False for _ in range(nx)] for _ in range(ny)]
        clusters = []
        for i in range(ny):
            for j in range(nx):
                if mask[i][j] and not visited[i][j]:
                    cluster, q = [], [(j, i)]
                    visited[i][j] = True
                    qi = 0
                    while qi < len(q):
                        cx, cy = q[qi]
                        qi += 1
                        cluster.append((cx, cy))
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            if 0 <= cx+dx < nx and 0 <= cy+dy < ny and mask[cy+dy][cx+dx] and not visited[cy+dy][cx+dx]:
                                visited[cy+dy][cx+dx] = True
                                q.append((cx+dx, cy+dy))
                        if len(cluster) > 15:
                            clusters.append(cluster)
        clusters.sort(key=len, reverse=True)
        clusters = clusters[:8]
        min_d = self.min_diameter
        max_d = self.max_diameter
        if max_d < min_d:
            max_d = min_d
        results = []
        for cluster in clusters:
            cluster_set = set(cluster)
            avg_x = sum(p[0] for p in cluster) / len(cluster)
            text_avg_y = sum(p[1] for p in cluster) / len(cluster)
            avg_y = text_avg_y
            peak_p = max(cluster, key=lambda p: grid[p[1]][p[0]])
            max_cluster_val = grid[peak_p[1]][peak_p[0]]
            xr = avg_x / (nx - 1) if (nx > 1) else 0.5
            yr = avg_y / (ny - 1) if (ny > 1) else 0.5
            min_cx = min(p[0] for p in cluster)/(nx-1)
            max_cx = max(p[0] for p in cluster)/(nx-1)
            min_cy = min(p[1] for p in cluster)/(ny-1)
            max_cy = max(p[1] for p in cluster)/(ny-1)
            diameter_m = self.clamp(0.55*((max_cx-min_cx)*self.width_val + (max_cy-min_cy)*self.length_val) + 0.45*(self.compute_cluster_compact_diameter(cluster_set, nx, ny)*(self.width_val+self.length_val))*2.2, min_d, max_d)
            xr, yr = self.repel_circle_from_edges(xr, yr, (diameter_m/2.0)/max(min(self.width_val, self.length_val), 1e-9))
            label, fill_color, text_color = self.classify_target(max_cluster_val, 600.0)
            results.append({
                "center_x_ratio": xr, "center_y_ratio": yr, "diameter_m": diameter_m, "target_value": max_cluster_val,
                "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "cluster",
                "cluster_bounds": {"min_cx": min_cx, "max_cx": max_cx, "min_cy": min_cy, "max_cy": max_cy}
            })
        results.sort(key=lambda c: c["target_value"], reverse=True)
        return results

    def get_min_value_in_circle(self, cx_ratio, cy_ratio, radius_ratio):
        if not self.heatmap_data:
            return 0.0
        grid = self.heatmap_data["grid"]
        grid_ny = len(grid)
        grid_nx = len(grid[0]) if grid_ny > 0 else 0
        min_val = float('inf')
        for j in range(grid_ny):
            ry = j / (grid_ny - 1) if grid_ny > 1 else 0.5
            for i in range(grid_nx):
                rx = i / (grid_nx - 1) if grid_nx > 1 else 0.5
                if math.hypot(rx - cx_ratio, ry - cy_ratio) <= radius_ratio:
                    if grid[j][i] < min_val:
                        min_val = grid[j][i]
        return min_val if min_val != float('inf') else 0.0

    def get_max_value_in_circle(self, cx_ratio, cy_ratio, radius_ratio):
        if not self.heatmap_data:
            return 0.0
        grid = self.heatmap_data["grid"]
        grid_ny = len(grid)
        grid_nx = len(grid[0]) if grid_ny > 0 else 0
        max_val = float('-inf')
        for j in range(grid_ny):
            ry = j / (grid_ny - 1) if grid_ny > 1 else 0.5
            for i in range(grid_nx):
                rx = i / (grid_nx - 1) if grid_nx > 1 else 0.5
                if math.hypot(rx - cx_ratio, ry - cy_ratio) <= radius_ratio:
                    if grid[j][i] > max_val:
                        max_val = grid[j][i]
        return max_val if max_val != float('-inf') else 0.0

    def compute_triangle_weights(self, vals, side_key, chord1_key, chord2_key, is_void):
        v_s = self.safe_float(vals.get(side_key))
        v_c1 = self.safe_float(vals.get(chord1_key))
        v_c2 = self.safe_float(vals.get(chord2_key))
        v_s = v_s if (v_s is not None and 0 <= v_s <= 100000) else 600.0
        v_c1 = v_c1 if (v_c1 is not None and 0 <= v_c1 <= 100000) else 600.0
        v_c2 = v_c2 if (v_c2 is not None and 0 <= v_c2 <= 100000) else 600.0
        v_s = max(1.0, v_s)
        v_c1 = max(1.0, v_c1)
        v_c2 = max(1.0, v_c2)
        if is_void:
            u_s = v_s
            u_c1 = v_c1
            u_c2 = v_c2
        else:
            u_s = 1.0 / v_s
            u_c1 = 1.0 / v_c1
            u_c2 = 1.0 / v_c2
        total = u_s + u_c1 + u_c2
        if total <= 1e-9:
            return 0.333, 0.333, 0.333
        return u_s / total, u_c1 / total, u_c2 / total

    def refine_target_positions(self, dt):
        if not self.detected_circles:
            return
        vals = self.valid_entries_dict()
        for circ in self.detected_circles:
            if circ.get("source_type") == "special_void_triangle":
                continue
            cx = circ["center_x_ratio"]
            cy = circ["center_y_ratio"]
            diameter_m = circ["diameter_m"]
            d_p1p2 = cy
            d_p2p4 = 1.0 - cx
            d_p4p3 = 1.0 - cy
            d_p3p1 = cx
            sides_dists = [
                (d_p1p2, "p1p2", (0.0, 0.0, 1.0, 0.0)),
                (d_p2p4, "p2p4", (1.0, 0.0, 1.0, 1.0)),
                (d_p4p3, "p4p3", (1.0, 1.0, 0.0, 1.0)),
                (d_p3p1, "p3p1", (0.0, 1.0, 0.0, 0.0))
            ]
            sides_dists.sort(key=lambda x: x[0])
            closest_side_dist, side_key, side_coords = sides_dists[0]
            is_void = circ.get("target_value", 0.0) >= 3000 or circ.get("label") in ["Void", "Small Void", "Medium Void", "Big Void"]
            w_s, w_c1, w_c2 = self.compute_triangle_weights(vals, side_key, "p1p4", "p2p3", is_void)
            proj_x_s, proj_y_s = self.project_point_to_segment(cx, cy, *side_coords)
            proj_x_c1, proj_y_c1 = self.project_point_to_segment(cx, cy, 0.0, 0.0, 1.0, 1.0)
            proj_x_c2, proj_y_c2 = self.project_point_to_segment(cx, cy, 1.0, 0.0, 0.0, 1.0)
            weighted_x = w_s * proj_x_s + w_c1 * proj_x_c1 + w_c2 * proj_x_c2
            weighted_y = w_s * proj_y_s + w_c1 * proj_y_c1 + w_c2 * proj_y_c2
            cx = self._lerp(cx, weighted_x, 0.35)
            cy = self._lerp(cy, weighted_y, 0.35)
            radius_ratio = (diameter_m / 2.0) / max(min(self.width_val, self.length_val), 1e-9)
            circ["center_x_ratio"], circ["center_y_ratio"] = self.repel_circle_from_edges(cx, cy, radius_ratio)
        self.update_target_boxes()
        self.invalidate_render_cache()
        if hasattr(self, 'monitor') and self.monitor:
            self.monitor.redraw()

    def start_gpr_zigzag_scan(self):
        if self.check_cuts_and_warn():
            self.scanning = False
            self.fibo_active = False
            self.gpr_active = False
            return
        self.loaded_scan_name = ""
        self.scanning = True
        self.width_val = self.ui_width_val
        self.length_val = self.ui_length_val
        self.ref_soil_val = self.ui_ref_soil_val
        self.entry_values = self.ui_entry_values.copy()
        self.calculate_geophysics_heatmap()
        self.scan_cols = 45
        self.scan_rows = 45
        self.scan_grid = [[None for _ in range(self.scan_cols)] for _ in range(self.scan_rows)]
        self.scan_current_col = 0
        self.scan_current_row = 0
        self.scan_direction_up = True
        self.sampled_points = []
        self.final_min_points = []
        self.transition_step = 0
        self.gpr_fibo_skeleton_visible = False
        Clock.schedule_once(self.run_scan_step, 0.015)

    def run_scan_step(self, dt):
        if not self.scanning:
            return
        if self.check_cuts_and_warn():
            self.scanning = False
            self.fibo_active = False
            self.gpr_active = False
            self.monitor.redraw()
            return
        steps_per_tick = 15
        for _ in range(steps_per_tick):
            if not self.scanning:
                break
            rx = self.scan_current_col / (self.scan_cols - 1) if self.scan_cols > 1 else 0.5
            ry = self.scan_current_row / (self.scan_rows - 1) if self.scan_rows > 1 else 0.5
            if self.heatmap_data is not None:
                vmin = self.heatmap_data["min"]
                vmax = self.heatmap_data["max"]
                min_xr = self.min_point["x_ratio"] if self.min_point else 0.5
                min_yr = self.min_point["y_ratio"] if self.min_point else 0.5
                if self.fibo_active:
                    val = self.compute_gpr_fibonacci_value(rx, ry, vmin, vmax, min_xr, min_yr)
                else:
                    grid = self.heatmap_data["grid"]
                    g_ny = len(grid)
                    g_nx = len(grid[0]) if g_ny > 0 else 1
                    ix = int(self.clamp(rx * (g_nx - 1), 0, g_nx - 1))
                    iy = int(self.clamp(ry * (g_ny - 1), 0, g_ny - 1))
                    val = grid[iy][ix]
                self.scan_grid[self.scan_current_col][self.scan_current_row] = val
                self.sampled_points.append((rx, ry, val))
            if self.scan_direction_up:
                self.scan_current_col += 1
                if self.scan_current_col >= self.scan_cols:
                    self.scan_current_col = self.scan_cols - 1
                    self.scan_current_row += 1
                    self.scan_direction_up = False
            else:
                self.scan_current_col -= 1
                if self.scan_current_col < 0:
                    self.scan_current_col = 0
                    self.scan_current_row += 1
                    self.scan_direction_up = True
            if self.scan_current_row >= self.scan_rows:
                self.finish_scan()
                break
        self.invalidate_render_cache()
        self.monitor.redraw()
        if self.scanning:
            Clock.schedule_once(self.run_scan_step, 0.015)

    def finish_scan(self):
        self.scanning = False
        self.transition_step = 1
        self.invalidate_render_cache()
        self.monitor.redraw()
        Clock.schedule_once(self.auto_transition_step_2, 0.04)

    def auto_transition_step_2(self, dt):
        if not self.scanning:
            self.transition_step = 2
            self.invalidate_render_cache()
            self.monitor.redraw()
            if self.fibo_active:
                Clock.schedule_once(self.enable_gpr_fibo_skeleton, 1.0)
            else:
                Clock.schedule_once(self.auto_transition_step_3, 0.04)

    def auto_transition_step_3(self, dt):
        if not self.scanning:
            self.transition_step = 3
            self.invalidate_render_cache()
            self.monitor.redraw()
            Clock.schedule_once(self.enable_gpr_fibo_skeleton, 1.0)

    def enable_gpr_fibo_skeleton(self, dt):
        self.gpr_fibo_skeleton_visible = True
        self.invalidate_render_cache()
        if hasattr(self, 'monitor') and self.monitor:
            self.monitor.redraw()

    def safe_draw_ellipse(self, draw, box, fill=None, outline=None, width=1):
        try:
            draw.ellipse(box, fill=fill, outline=outline, width=width)
        except TypeError:
            draw.ellipse(box, fill=fill, outline=outline)

    def safe_draw_rectangle(self, draw, box, fill=None, outline=None, width=1):
        try:
            draw.rectangle(box, fill=fill, outline=outline, width=width)
        except TypeError:
            draw.rectangle(box, fill=fill, outline=outline)

    def safe_draw_rounded_rectangle(self, draw, box, radius=5, fill=None, outline=None, width=1):
        try:
            draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
        except AttributeError:
            try:
                draw.rectangle(box, fill=fill, outline=outline, width=width)
            except TypeError:
                draw.rectangle(box, fill=fill, outline=outline)

    def get_render_texture(self):
        if hasattr(self, '_cached_render_texture') and self._cached_render_texture is not None:
            return self._cached_render_texture
        img = self.generate_visualization_image()
        if img is None:
            return None
        try:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
            data = img.tobytes("raw", "RGBA")
            tex = Texture.create(size=img.size, colorfmt="rgba")
            tex.blit_buffer(data, colorfmt="rgba", bufferfmt="ubyte")
            self._cached_render_texture = tex
            return tex
        except Exception as e:
            print("Texture generation failed:", e)
            return None

    def draw_pil_arrow_head_custom(self, draw, px, py, dx, dy, color, size=12):
        bx = px - size * dx
        by = py - size * dy
        perp_x = -dy
        perp_y = dx
        lx = bx + size * 0.4 * perp_x
        ly = by + size * 0.4 * perp_y
        rx = bx - size * 0.4 * perp_x
        ry = bx - size * 0.4 * perp_y
        draw.polygon([(px, py), (lx, ly), (rx, ry)], fill=color)

    def draw_irregular_stone(self, draw, cx, cy, r_avg, index, fill_rgb, outline_rgb, alpha):
        vertices = []
        num_pts = 6
        for i in range(num_pts):
            angle = 2 * math.pi * i / num_pts
            noise_factor = 0.75 + 0.25 * math.sin(index * 1.7 + i * 2.3)
            size_variation = 0.8 + 0.4 * math.cos(index * 3.1)
            r = r_avg * noise_factor * size_variation
            rx = cx + r * math.cos(angle)
            ry = cy + r * math.sin(angle)
            vertices.append((rx, ry))
        draw.polygon(vertices, fill=fill_rgb + (alpha,), outline=outline_rgb + (alpha,))

    def draw_river_pebble(self, draw, cx, cy, r_avg, index, fill_rgb, outline_rgb, alpha):
        vertices = []
        num_pts = 8
        for i in range(num_pts):
            angle = 2 * math.pi * i / num_pts
            noise_factor = 0.82 + 0.18 * math.sin(index * 1.9 + i * 1.3)
            size_variation = 0.85 + 0.3 * math.cos(index * 2.7)
            r = r_avg * noise_factor * size_variation
            rx = cx + r * math.cos(angle)
            ry = cy + r * math.sin(angle)
            vertices.append((rx, ry))
        draw.polygon(vertices, fill=fill_rgb + (alpha,), outline=outline_rgb + (alpha,))

    def draw_centered_text(self, draw, position, text, font, fill):
        cx, cy = position
        try:
            draw.text((cx, cy), text, fill=fill, font=font, anchor="mm")
        except TypeError:
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                draw.text((cx - tw/2, cy - th/2 - bbox[1]/2), text, fill=fill, font=font)
            except AttributeError:
                try:
                    tw, th = draw.textsize(text, font=font)
                    draw.text((cx - tw/2, cy - th/2), text, fill=fill, font=font)
                except AttributeError:
                    tw = len(text) * (font.size * 0.6 if font else 8)
                    th = (font.size if font else 12)
                    draw.text((cx - tw/2, cy - th/2), text, fill=fill, font=font)

    def draw_pil_sad_sticker(self, draw, w, h):
        cx, cy = w / 2.0, h / 2.0
        radius_sz = w * 0.15
        self.safe_draw_ellipse(draw, [cx - radius_sz, cy - radius_sz, cx + radius_sz, cy + radius_sz], fill=(255, 213, 74, 255), outline=(17, 17, 17, 255), width=2)
        eye_r, eye_dx, eye_dy = max(2.0, radius_sz * 0.08), radius_sz * 0.28, radius_sz * 0.18
        self.safe_draw_ellipse(draw, [cx - eye_dx - eye_r, cy - eye_dy - eye_r, cx - eye_dx + eye_r, cy - eye_dy + eye_r], fill=(17, 17, 17, 255))
        self.safe_draw_ellipse(draw, [cx + eye_dx - eye_r, cy - eye_dy - eye_r, cx + eye_dx + eye_r, cy - eye_dy + eye_r], fill=(17, 17, 17, 255))
        try:
            draw.arc([cx - radius_sz*0.55/2, cy + radius_sz*0.34 - radius_sz*0.32/2, cx + radius_sz*0.55/2, cy + radius_sz*0.34 + radius_sz*0.32/2], 180, 360, fill=(17, 17, 17, 255), width=max(2, int(radius_sz*0.06)))
        except TypeError:
            draw.arc([cx - radius_sz*0.55/2, cy + radius_sz*0.34 - radius_sz*0.32/2, cx + radius_sz*0.55/2, cy + radius_sz*0.34 + radius_sz*0.32/2], 180, 360, fill=(17, 17, 17, 255))

    def generate_visualization_image(self, w=800, h=800):
        if Image is None or ImageDraw is None:
            return None
        cuts = self.get_cut_segments()
        if cuts and self.active_mode == "4-prop":
            img = Image.new("RGBA", (w, h), (230, 230, 230, 255))
            draw = ImageDraw.Draw(img)
            self.safe_draw_rectangle(draw, [0, 0, w, h], outline="black", width=4)
            for cx_corner, cy_corner in [(0, h), (w, h), (0, 0), (w, 0)]:
                draw.ellipse([cx_corner-6, cy_corner-6, cx_corner+6, cy_corner+6], fill="black")
            margin = 12
            seg_points = {
                "p1p2": ((margin, h - margin), (w - margin, h - margin)),
                "p2p4": ((w - margin, h - margin), (w - margin, margin)),
                "p4p3": ((w - margin, margin), (margin, margin)),
                "p3p1": ((margin, margin), (margin, h - margin)),
                "p1p4": ((margin, h - margin), (w - margin, margin)),
                "p2p3": ((w - margin, h - margin), (margin, margin))
            }
            for key, (A, B) in seg_points.items():
                if key in cuts:
                    dx = B[0] - A[0]
                    dy = B[1] - A[1]
                    L = math.hypot(dx, dy)
                    ux, uy = dx / L, dy / L
                    split_ratio = 0.25 if key in ["p1p4", "p2p3"] else 0.5
                    cx = A[0] + L * split_ratio * ux
                    cy = A[1] + L * split_ratio * uy
                    gap_len = 108.0
                    c1x = cx - (gap_len / 2.0) * ux
                    c1y = cy - (gap_len / 2.0) * uy
                    c2x = cx + (gap_len / 2.0) * ux
                    c2y = cy + (gap_len / 2.0) * uy
                    line_color = (255, 255, 255, 255) if self.blink_state else (0, 0, 0, 255)
                    draw.line([A[0], A[1], c1x, c1y], fill=line_color, width=6)
                    draw.line([c2x, c2y, B[0], B[1]], fill=line_color, width=6)
                    if self.blink_state:
                        self.draw_pil_arrow_head_custom(draw, c1x, c1y, ux, uy, (255, 0, 0, 255), size=26)
                        self.draw_pil_arrow_head_custom(draw, c2x, c2y, -ux, -uy, (255, 0, 0, 255), size=26)
                    draw.ellipse([c1x - 8, c1y - 8, c1x + 8, c1y + 8], fill=(255, 0, 0, 255))
                    draw.ellipse([c2x - 8, c2y - 8, c2x + 8, c2y + 8], fill=(255, 0, 0, 255))
                    warn_size = 28
                    w_pts = [
                        (cx, cy - warn_size),
                        (cx - warn_size * 1.1, cy + warn_size * 0.9),
                        (cx + warn_size * 1.1, cy + warn_size * 0.9)
                    ]
                    draw.polygon(w_pts, fill=(255, 193, 7, 255), outline=(0, 0, 0, 255))
                    try:
                        draw.text((cx - 6, cy - 10), "!", fill=(0, 0, 0, 255), font=self.get_pil_font(24, bold=True))
                    except Exception:
                        pass
                    warn_text = "Probe Disconnected"
                    f_warn = self.get_pil_font(22, bold=True)
                    try:
                        bbox = draw.textbbox((0, 0), warn_text, font=f_warn)
                        tw = bbox[2] - bbox[0]
                        th = bbox[3] - bbox[1]
                    except AttributeError:
                        tw, th = len(warn_text) * 12, 24
                    draw.text((cx - tw / 2, cy - warn_size - th - 10), warn_text, fill=(200, 0, 0, 255), font=f_warn)
                else:
                    if key in ["p1p4", "p2p3"]:
                        self.draw_pil_dashed_line(draw, A[0], A[1], B[0], B[1], (0, 0, 0, 255), width=2, dash=(10, 8))
                    else:
                        draw.line([A[0], A[1], B[0], B[1]], fill=(0, 0, 0, 255), width=3)
            return img

        img = Image.new("RGBA", (w, h), (230, 230, 230, 255))
        draw = ImageDraw.Draw(img)

        if self.show_geo_var and self.heatmap_data is not None and not self.gpr_active and not self.fibo_active and not self.compare_active:
            grid, nx, ny = self.heatmap_data["grid"], self.heatmap_data["nx"], self.heatmap_data["ny"]
            vmin, vmax = self.heatmap_data["min"], self.heatmap_data["max"]
            invert_for_void = self.has_void_circle()
            heatmap_img = Image.new("RGB", (nx, ny))
            for j in range(ny):
                yr = j / (ny - 1) if ny > 1 else 0.5
                for i in range(nx):
                    xr = i / (nx - 1) if nx > 1 else 0.5
                    rgb_color = self.resistance_relative_palette_color(grid[j][i], vmin, vmax, invert_for_void, xr, yr)
                    heatmap_img.putpixel((i, ny - 1 - j), rgb_color)
            img.paste(heatmap_img.resize((w, h), RESAMPLE_FILTER), (0, 0))
            self.draw_pil_contours_for_screen(draw, w, h, grid, nx, ny, vmin, vmax, max(4, 14 + 6*self.signal_correction_level))

        elif (self.gpr_active or self.fibo_active) and hasattr(self, 'scan_grid') and self.scan_grid is not None and not self.compare_active:
            self.draw_pil_gpr(draw, w, h, img)

        elif self.compare_active and self.heatmap_data is not None:
            nx, ny = 140, 140
            grid_geo = self.heatmap_data["grid"] if self.heatmap_data else []
            vmin = self.heatmap_data["min"] if self.heatmap_data else 0.0
            vmax = self.heatmap_data["max"] if self.heatmap_data else 100000.0
            min_xr = self.min_point["x_ratio"] if self.min_point else 0.5
            min_yr = self.min_point["y_ratio"] if self.min_point else 0.5
            invert_for_void = self.has_void_circle()
            span = vmax - vmin if vmax > vmin else 1.0

            img_geo = Image.new("RGBA", (nx, ny))
            self.fibo_active = False
            for j in range(ny):
                yr = j / (ny - 1) if ny > 1 else 0.5
                for i in range(nx):
                    xr = i / (nx - 1) if nx > 1 else 0.5
                    r_c, g_c, b_c = self.resistance_relative_palette_color(grid_geo[j][i], vmin, vmax, invert_for_void, xr, yr)
                    img_geo.putpixel((i, ny - 1 - j), (r_c, g_c, b_c, 255))

            img_fibo = Image.new("RGBA", (nx, ny))
            self.fibo_active = True
            for j in range(ny):
                ry = j / (ny - 1) if ny > 1 else 0.5
                for i in range(nx):
                    rx = i / (nx - 1) if nx > 1 else 0.5
                    val_fib = self.compute_gpr_fibonacci_value(rx, ry, vmin, vmax, min_xr, min_yr)
                    r_c, g_c, b_c = self.resistance_relative_palette_color(val_fib, vmin, vmax, invert_for_void, rx, ry)
                    img_fibo.putpixel((i, ny - 1 - j), (r_c, g_c, b_c, 255))

            img_gpr = Image.new("RGBA", (nx, ny))
            self.fibo_active = False
            R_red = 0.60
            gpr_centers = []
            if self.detected_circles:
                for circ in self.detected_circles[:2]:
                    gpr_centers.append((circ["center_x_ratio"], circ["center_y_ratio"]))
            else:
                gpr_centers.append((min_xr, min_yr))

            for j in range(ny):
                ry = j / (ny - 1) if ny > 1 else 0.5
                for i in range(nx):
                    rx = i / (nx - 1) if nx > 1 else 0.5
                    val_ana = grid_geo[j][i]
                    min_dist_m = float('inf')
                    for cx, cy in gpr_centers:
                        dist_m = math.hypot((rx - cx)*self.width_val, (ry - cy)*self.length_val)
                        if dist_m < min_dist_m:
                            min_dist_m = dist_m
                    if min_dist_m <= R_red:
                        val = self._lerp(val_ana, vmin, (1.0 - min_dist_m / R_red))
                    elif (val_ana - vmin)/span < 0.18:
                        val = vmin + 0.18*span
                    else:
                        val = val_ana
                    r_c, g_c, b_c = self.resistance_relative_palette_color(val, vmin, vmax, invert_for_void, rx, ry)
                    img_gpr.putpixel((i, ny - 1 - j), (r_c, g_c, b_c, 255))

            self.fibo_active = False
            img_geo_resized = img_geo.resize((w, h), RESAMPLE_FILTER)
            img_fibo_resized = img_fibo.resize((w, h), RESAMPLE_FILTER)
            img_gpr_resized = img_gpr.resize((w, h), RESAMPLE_FILTER)

            blend_first_two = Image.blend(img_geo_resized, img_fibo_resized, alpha=0.5)
            final_blend = Image.blend(blend_first_two, img_gpr_resized, alpha=0.333)
            img.paste(final_blend, (0, 0))
            draw = ImageDraw.Draw(img)
            self.draw_pil_contours_for_screen(draw, w, h, grid_geo, nx, ny, vmin, vmax, max(4, 14 + 6*self.signal_correction_level))

            overlapping_zones = []
            if self.detected_circles:
                for circ in self.detected_circles[:2]:
                    overlapping_zones.append((circ["center_x_ratio"], circ["center_y_ratio"]))
            else:
                overlapping_zones.append((min_xr, min_yr))

            for idx, (cx, cy) in enumerate(overlapping_zones):
                min_fib_val = float('inf')
                xf_local, yf_local = cx, cy
                if grid_geo:
                    for j in range(ny):
                        ry = j / (ny - 1) if ny > 1 else 0.5
                        for i in range(nx):
                            rx = i / (nx - 1) if nx > 1 else 0.5
                            if math.hypot(rx - cx, ry - cy) <= 0.20:
                                self.fibo_active = True
                                val_fib = self.compute_gpr_fibonacci_value(rx, ry, vmin, vmax, min_xr, min_yr)
                                self.fibo_active = False
                                if val_fib < min_fib_val:
                                    min_fib_val = val_fib
                                    xf_local, yf_local = rx, ry
                x_avg = (cx + cx + xf_local) / 3.0
                y_avg = (cy + cy + yf_local) / 3.0
                cx_pix = x_avg * w
                cy_pix = h - y_avg * h

                circle_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                ol_draw = ImageDraw.Draw(circle_overlay)
                px_per_m = w / max(self.width_val, 1e-9)
                radius = (0.5 * px_per_m) / 2.0
                ol_draw.ellipse([cx_pix - radius, cy_pix - radius, cx_pix + radius, cy_pix + radius], fill=(255, 255, 255, 40), outline=(255, 255, 255, 255), width=3)
                ol_draw.ellipse([cx_pix - 4, cy_pix - 4, cx_pix + 4, cy_pix + 4], fill=(255, 255, 255, 255))
                img.paste(circle_overlay, (0, 0), circle_overlay)

                self.draw_pil_dashed_line(draw, 0, cy_pix, cx_pix, cy_pix, (0, 0, 0, 255), 1, (10, 8))
                self.draw_pil_dashed_line(draw, cx_pix, cy_pix, cx_pix, h, (0, 0, 0, 255), 1, (10, 8))
            self.fibo_active = False

        self.safe_draw_rectangle(draw, [0, 0, w, h], outline="black", width=4)
        self.draw_pil_dashed_line(draw, 0, 0, w, h, (40, 40, 40, 255), 2, (10, 8))
        self.draw_pil_dashed_line(draw, 0, h, w, 0, (40, 40, 40, 255), 2, (10, 8))
        for cx, cy in [(0, h), (w, h), (0, 0), (w, 0)]:
            draw.ellipse([cx-6, cy-6, cx+6, cy+6], fill="black")

        target_w = w - 100
        target_h = h - 100
        font_sz = 80
        for fs in range(250, 10, -5):
            f_test = self.get_pil_font(fs, bold=True)
            if not f_test:
                continue
            try:
                test_img = Image.new("RGBA", (1, 1))
                test_draw = ImageDraw.Draw(test_img)
                if hasattr(test_draw, 'textbbox'):
                    box = test_draw.textbbox((0, 0), "Cornix\nWinner PRO", font=f_test)
                    tw = box[2] - box[0]
                    th = box[3] - box[1]
                else:
                    tw, th = test_draw.multiline_textsize("Cornix\nWinner PRO", font=f_test)
                if tw <= target_w and th <= target_h:
                    font_sz = fs
                    break
            except Exception:
                tw = 6 * fs * 0.65
                th = fs * 2.3
                if tw <= target_w and th <= target_h:
                    font_sz = fs
                    break

        font_watermark_screen = self.get_pil_font(font_sz, bold=True)
        if font_watermark_screen:
            self.draw_rotated_text(img, "Cornix\nWinner PRO", (w // 2, h // 2 - 35), 0, font_watermark_screen, (0, 0, 0, 18))

        if self.soil_contaminated:
            self.draw_pil_soil_contamination_overlay(draw, w, h)
            self.draw_pil_sad_sticker(draw, w, h)

        elif self.detected_circles and not self.compare_active:
            px_per_m = w / max(self.width_val, 1e-9)
            in_gpr_or_fibo = self.gpr_active or self.fibo_active

            for idx, circ in enumerate(self.detected_circles):
                cx = circ["center_x_ratio"] * w
                cy = h - circ["center_y_ratio"] * h
                radius = max(12.0, (circ["diameter_m"] * px_per_m) / 2.0)
                show_guide_lines = False
                if not in_gpr_or_fibo:
                    show_guide_lines = True
                else:
                    show_guide_lines = getattr(self, 'gpr_fibo_skeleton_visible', False)
                if self.fibo_active:
                    show_guide_lines = False
                if show_guide_lines:
                    self.draw_pil_dashed_line(draw, 0, cy, cx, cy, (0, 0, 0, 255), 1, (8, 6))
                    self.draw_pil_dashed_line(draw, cx, cy, cx, h, (0, 0, 0, 255), 1, (8, 6))
                
                fill_hex = circ.get("fill_color", "#ff0000")
                label = circ.get("label", "")
                if not in_gpr_or_fibo:
                    self.safe_draw_ellipse(draw, [cx-radius, cy-radius, cx+radius, cy+radius], fill=(int(fill_hex[1:3], 16), int(fill_hex[3:5], 16), int(fill_hex[5:7], 16), 255), outline=(58, 58, 58, 255), width=3)
                    text_inside = str(idx + 1) if label not in ["Unknown", "No Target"] else "!"
                    font_sz = int(max(24, min(radius * 1.35, 75)))
                    f_circle = self.get_pil_font(font_sz, bold=True)
                    fill_lower = fill_hex.lower()
                    if fill_lower == "#0000ff":
                        tc = (255, 255, 255, 255)
                    elif fill_lower == "#ffd700":
                        tc = (0, 0, 0, 255)
                    elif fill_lower == "#ff0000":
                        tc = (255, 255, 255, 255)
                    elif fill_lower == "#8b4513":
                        tc = (255, 255, 255, 255)
                    elif fill_lower in ["#8000ff", self.PURPLE.lower()]:
                        tc = (255, 255, 255, 255)
                    elif fill_lower == "#ffa500":
                        tc = (0, 0, 0, 255)
                    elif fill_lower in ["#808080", "#d3d3d3"]:
                        tc = (0, 0, 0, 255)
                    else:
                        tc = (255, 255, 255, 255)
                    self.draw_centered_text(draw, (cx, cy), text_inside, f_circle, tc)
                
                is_water_or_void = label in ["water", "Void", "Small Void", "Medium Void", "Big Void"]
                if self.fibo_active and not self.scanning and self.transition_step >= 2 and is_water_or_void:
                    self.draw_river_pebble(draw, cx, cy, radius * 0.85, idx, (150, 150, 150), (100, 100, 100), 180)
                
                s_eval = self.evaluate_skeleton_or_chamber(circ)
                if s_eval and self.gpr_fibo_skeleton_visible:
                    f_col = (130, 20, 15) if s_eval == "skeleton" else (30, 80, 160)
                    self.draw_irregular_stone(draw, cx, cy, radius * 1.15, idx, f_col, (20, 20, 20), 200)

                vis_mode = self.evaluate_skeleton_or_chamber(circ)
                can_draw_skeleton = False
                can_draw_chamber = False
                
                if not self.fibo_active:
                    show_mode_allowed = False
                    if not in_gpr_or_fibo:
                        show_mode_allowed = True
                    else:
                        show_mode_allowed = getattr(self, 'gpr_fibo_skeleton_visible', False)
                        
                    if show_mode_allowed:
                        if vis_mode == "skeleton":
                            can_draw_skeleton = True
                        elif vis_mode == "chamber":
                            can_draw_chamber = True

                if can_draw_skeleton:
                    px_per_m_x = w / max(self.width_val, 1e-9)
                    px_per_m_y = h / max(self.length_val, 1e-9)
                    sk_w = int(max(40.0, min(w * 0.4, 0.5 * px_per_m_x)))
                    sk_h = int(max(80.0, min(h * 0.8, 1.0 * px_per_m_y)))
                    sk_img = Image.new("RGBA", (sk_w, sk_h), (0, 0, 0, 0))
                    ol_draw = ImageDraw.Draw(sk_img)
                    ol_draw.rectangle([0, 0, sk_w, sk_h], fill=(0, 0, 0, 255))
                    
                    stone_w = max(8, int(min(sk_w, sk_h) * 0.12))
                    R_stone = stone_w * 0.65
                    stone_centers = []
                    
                    for x in range(int(R_stone), int(sk_w - R_stone), int(R_stone * 1.4)):
                        stone_centers.append((x, R_stone))
                    for y in range(int(R_stone), int(sk_h - R_stone), int(R_stone * 1.4)):
                        stone_centers.append((sk_w - R_stone, y))
                    for x in range(int(sk_w - R_stone), int(R_stone), -int(R_stone * 1.4)):
                        stone_centers.append((x, sk_h - R_stone))
                    for y in range(int(sk_h - R_stone), int(R_stone), -int(R_stone * 1.4)):
                        stone_centers.append((R_stone, y))
                        
                    for idx_st, (scx, scy) in enumerate(stone_centers):
                        self.draw_river_pebble(ol_draw, scx, scy, R_stone, idx_st, (240, 240, 240), (15, 15, 15), 255)
                        
                    interior_x0 = R_stone * 1.4
                    interior_y0 = R_stone * 1.4
                    interior_w = sk_w - 2 * interior_x0
                    interior_h = sk_h - 2 * interior_y0
                    cx_int = sk_w / 2.0
                    
                    skull_cx = cx_int
                    skull_cy = interior_y0 + interior_h * 0.12
                    skull_r = max(5.0, interior_w * 0.18)
                    
                    ol_draw.ellipse([skull_cx - skull_r - 1, skull_cy - skull_r - 1, skull_cx + skull_r + 1, skull_cy + skull_r + 1], fill=(0, 0, 0, 255))
                    ol_draw.ellipse([skull_cx - skull_r, skull_cy - skull_r, skull_cx + skull_r, skull_cy + skull_r], fill=(255, 255, 255, 255))
                    
                    jaw_w = skull_r * 0.60
                    jaw_h = skull_r * 0.45
                    jaw_x0 = skull_cx - jaw_w
                    jaw_x1 = skull_cx + jaw_w
                    jaw_y0 = skull_cy + skull_r * 0.3
                    jaw_y1 = skull_cy + skull_r * 1.15
                    
                    ol_draw.polygon([
                        (skull_cx - skull_r * 0.8, skull_cy + skull_r * 0.3),
                        (skull_cx + skull_r * 0.8, skull_cy + skull_r * 0.3),
                        (jaw_x1, jaw_y1),
                        (jaw_x0, jaw_y1)
                      ], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
                      
                    eye_r_w = skull_r * 0.32
                    eye_r_h = skull_r * 0.28
                    ol_draw.ellipse([skull_cx - skull_r * 0.42 - eye_r_w, skull_cy - skull_r * 0.15 - eye_r_h, skull_cx - skull_r * 0.42 + eye_r_w, skull_cy - skull_r * 0.15 + eye_r_h], fill=(0, 0, 0, 255))
                    ol_draw.ellipse([skull_cx + skull_r * 0.42 - eye_r_w, skull_cy - skull_r * 0.15 - eye_r_h, skull_cx + skull_r * 0.42 + eye_r_w, skull_cy - skull_r * 0.15 + eye_r_h], fill=(0, 0, 0, 255))
                    
                    ol_draw.polygon([
                        (skull_cx, skull_cy + skull_r * 0.12),
                        (skull_cx - skull_r * 0.14, skull_cy + skull_r * 0.42),
                        (skull_cx + skull_r * 0.14, skull_cy + skull_r * 0.42)
                    ], fill=(0, 0, 0, 255))
                    
                    teeth_y = jaw_y1 - jaw_h * 0.35
                    for t_i in range(-3, 4):
                        ol_draw.line([skull_cx + t_i * (jaw_w * 0.25), teeth_y - 1, skull_cx + t_i * (jaw_w * 0.25), jaw_y1], fill=(0, 0, 0, 255), width=1)
                    ol_draw.line([skull_cx - jaw_w * 0.65, teeth_y + 1, skull_cx + jaw_w * 0.65, teeth_y + 1], fill=(0, 0, 0, 255), width=1)
                    
                    def draw_bone_line(bx0, by0, bx1, by1, bwidth=3):
                        ol_draw.line([bx0, by0, bx1, by1], fill=(0, 0, 0, 255), width=bwidth + 2)
                        ol_draw.line([bx0, by0, bx1, by1], fill=(255, 255, 255, 255), width=bwidth)
                        
                    def draw_joint_circle(jcx, jcy, jr):
                        ol_draw.ellipse([jcx - jr, jcy - jr, jcx + jr, jcy + jr], fill=(0, 0, 0, 255))
                        ol_draw.ellipse([jcx - jr + 1, jcy - jr + 1, jcx + jr - 1, jcy + jr - 1], fill=(255, 255, 255, 255))

                    spine_start_y = jaw_y1
                    spine_end_y = interior_y0 + interior_h * 0.54
                    num_vertebrae = 12
                    v_step = (spine_end_y - spine_start_y) / num_vertebrae
                    for v_idx in range(num_vertebrae):
                        vy = spine_start_y + v_idx * v_step + v_step * 0.5
                        vw = max(4.0, interior_w * 0.08)
                        vh = v_step * 0.72
                        ol_draw.rectangle([skull_cx - vw/2, vy - vh/2, skull_cx + vw/2, vy + vh/2], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
                        
                    shoulder_dx = interior_w * 0.32
                    collar_y = spine_start_y + v_step * 2.0
                    draw_bone_line(skull_cx - shoulder_dx, collar_y, skull_cx + shoulder_dx, collar_y, bwidth=3)
                    draw_joint_circle(skull_cx - shoulder_dx, collar_y, max(2.5, interior_w * 0.045))
                    draw_joint_circle(skull_cx + shoulder_dx, collar_y, max(2.5, interior_w * 0.045))
                    
                    sternum_h = interior_h * 0.22
                    ol_draw.rectangle([skull_cx - 2, collar_y + 2, skull_cx + 2, collar_y + sternum_h], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
                    
                    num_ribs = 6
                    for r_idx in range(num_ribs):
                        ry = collar_y + sternum_h * 0.15 + r_idx * (sternum_h * 0.14)
                        rib_max_w = shoulder_dx * 0.85
                        left_rib_pts = []
                        right_rib_pts = []
                        steps = 6
                        for pt_idx in range(steps + 1):
                            t_rib = pt_idx / steps
                            theta_r = t_rib * math.pi
                            rx_offset = rib_max_w * math.sin(theta_r)
                            ry_offset = (sternum_h * 0.15) * (1.0 - math.cos(theta_r))
                            left_rib_pts.append((skull_cx - rx_offset, ry + ry_offset))
                            right_rib_pts.append((skull_cx + rx_offset, ry + ry_offset))
                        ol_draw.line(left_rib_pts, fill=(0, 0, 0, 255), width=4)
                        ol_draw.line(left_rib_pts, fill=(255, 255, 255, 255), width=2)
                        ol_draw.line(right_rib_pts, fill=(0, 0, 0, 255), width=4)
                        ol_draw.line(right_rib_pts, fill=(255, 255, 255, 255), width=2)
                        
                    pelvis_y0 = spine_end_y
                    pelvis_y1 = interior_y0 + interior_h * 0.63
                    pelvis_w = interior_w * 0.32
                    ol_draw.polygon([
                        (skull_cx - pelvis_w, pelvis_y0),
                        (skull_cx + pelvis_w, pelvis_y0),
                        (skull_cx + pelvis_w * 0.8, pelvis_y1),
                        (skull_cx - pelvis_w * 0.8, pelvis_y1)
                    ], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
                    
                    ol_draw.ellipse([skull_cx - pelvis_w * 0.5, pelvis_y0 + (pelvis_y1 - pelvis_y0) * 0.25, skull_cx - pelvis_w * 0.15, pelvis_y0 + (pelvis_y1 - pelvis_y0) * 0.75], fill=(0, 0, 0, 255))
                    ol_draw.ellipse([skull_cx + pelvis_w * 0.15, pelvis_y0 + (pelvis_y1 - pelvis_y0) * 0.25, skull_cx + pelvis_w * 0.5, pelvis_y0 + (pelvis_y1 - pelvis_y0) * 0.75], fill=(0, 0, 0, 255))
                    ol_draw.ellipse([skull_cx - pelvis_w * 0.1, pelvis_y0 + 2, skull_cx + pelvis_w * 0.1, pelvis_y0 + (pelvis_y1 - pelvis_y0) * 0.45], fill=(0, 0, 0, 255))
                    
                    elbow_y = interior_y0 + interior_h * 0.40
                    wrist_y = interior_y0 + interior_h * 0.53
                    
                    draw_bone_line(skull_cx - shoulder_dx, collar_y, skull_cx - shoulder_dx * 0.95, elbow_y, bwidth=3)
                    draw_joint_circle(skull_cx - shoulder_dx * 0.95, elbow_y, max(2.0, interior_w * 0.035))
                    draw_bone_line(skull_cx - shoulder_dx * 0.95 - 2, elbow_y, skull_cx - shoulder_dx * 0.9 - 2, wrist_y, bwidth=2)
                    draw_bone_line(skull_cx - shoulder_dx * 0.95 + 2, elbow_y, skull_cx - shoulder_dx * 0.9 + 2, wrist_y, bwidth=2)
                    draw_joint_circle(skull_cx - shoulder_dx * 0.9, wrist_y, max(1.5, interior_w * 0.025))
                    
                    draw_bone_line(skull_cx + shoulder_dx, collar_y, skull_cx + shoulder_dx * 0.95, elbow_y, bwidth=3)
                    draw_joint_circle(skull_cx + shoulder_dx * 0.95, elbow_y, max(2.0, interior_w * 0.035))
                    draw_bone_line(skull_cx + shoulder_dx * 0.95 - 2, elbow_y, skull_cx + shoulder_dx * 0.9 - 2, wrist_y, bwidth=2)
                    draw_bone_line(skull_cx + shoulder_dx * 0.95 + 2, elbow_y, skull_cx + shoulder_dx * 0.9 + 2, wrist_y, bwidth=2)
                    draw_joint_circle(skull_cx + shoulder_dx * 0.9, wrist_y, max(1.5, interior_w * 0.025))
                    
                    finger_len = max(5.0, interior_h * 0.05)
                    for f_idx in range(5):
                        f_offset = (f_idx - 2) * (interior_w * 0.02)
                        draw_bone_line(skull_cx - shoulder_dx * 0.9, wrist_y, skull_cx - shoulder_dx * 0.9 + f_offset, wrist_y + finger_len, bwidth=1)
                        draw_bone_line(skull_cx + shoulder_dx * 0.9, wrist_y, skull_cx + shoulder_dx * 0.9 + f_offset, wrist_y + finger_len, bwidth=1)
                        
                    hip_dx = pelvis_w * 0.55
                    knee_y = interior_y0 + interior_h * 0.77
                    ankle_y = interior_y0 + interior_h * 0.91
                    
                    draw_joint_circle(skull_cx - hip_dx, pelvis_y1 - 2, max(2.5, interior_w * 0.04))
                    draw_bone_line(skull_cx - hip_dx, pelvis_y1, skull_cx - hip_dx * 0.9, knee_y, bwidth=4)
                    draw_joint_circle(skull_cx - hip_dx * 0.9, knee_y, max(2.0, interior_w * 0.035))
                    draw_bone_line(skull_cx - hip_dx * 0.9 - 2, knee_y, skull_cx - hip_dx * 0.85 - 2, ankle_y, bwidth=2)
                    draw_bone_line(skull_cx - hip_dx * 0.9 + 2, knee_y, skull_cx - hip_dx * 0.85 + 2, ankle_y, bwidth=2)
                    draw_joint_circle(skull_cx - hip_dx * 0.85, ankle_y, max(1.5, interior_w * 0.025))
                    
                    draw_joint_circle(skull_cx + hip_dx, pelvis_y1 - 2, max(2.5, interior_w * 0.04))
                    draw_bone_line(skull_cx + hip_dx, pelvis_y1, skull_cx + hip_dx * 0.9, knee_y, bwidth=4)
                    draw_joint_circle(skull_cx + hip_dx * 0.9, knee_y, max(2.0, interior_w * 0.035))
                    draw_bone_line(skull_cx + hip_dx * 0.9 - 2, knee_y, skull_cx + hip_dx * 0.85 - 2, ankle_y, bwidth=2)
                    draw_bone_line(skull_cx + hip_dx * 0.9 + 2, knee_y, skull_cx + hip_dx * 0.85 + 2, ankle_y, bwidth=2)
                    draw_joint_circle(skull_cx + hip_dx * 0.85, ankle_y, max(1.5, interior_w * 0.025))
                    
                    toe_len = max(4.0, interior_h * 0.04)
                    for t_idx in range(5):
                        t_offset = (t_idx - 2) * (interior_w * 0.02)
                        draw_bone_line(skull_cx - hip_dx * 0.85, ankle_y, skull_cx - hip_dx * 0.85 + t_offset - 3, ankle_y + toe_len, bwidth=1)
                        draw_bone_line(skull_cx + hip_dx * 0.85, ankle_y, skull_cx + hip_dx * 0.85 + t_offset + 3, ankle_y + toe_len, bwidth=1)
                    
                    min_pt = self.min_point
                    if min_pt:
                        mx_pix = min_pt["x_ratio"] * w
                        my_pix = h - min_pt["y_ratio"] * h
                        dx_v = mx_pix - cx
                        dy_v = my_pix - cy
                        if math.hypot(dx_v, dy_v) > 1e-3:
                            angle_deg = math.degrees(math.atan2(dy_v, dx_v)) + 90
                        else:
                            angle_deg = 0
                    else:
                        angle_deg = 0
                        
                    sk_img_rotated = sk_img.rotate(angle_deg, expand=True, resample=RESAMPLE_FILTER)
                    rw_r, rh_r = sk_img_rotated.size
                    img.paste(sk_img_rotated, (int(cx - rw_r/2), int(cy - rh_r/2)), sk_img_rotated)
                    draw = ImageDraw.Draw(img)

                elif can_draw_chamber:
                    px_per_m_x = w / max(self.width_val, 1e-9)
                    px_per_m_y = h / max(self.length_val, 1e-9)
                    
                    chamber_w_m = 0.70  
                    chamber_h_m = 1.00  
                    chamber_w = int(chamber_w_m * px_per_m_x)
                    chamber_h = int(chamber_h_m * px_per_m_y)
                    
                    min_pt = self.min_point
                    if min_pt:
                        mx_pix = min_pt["x_ratio"] * w
                        my_pix = h - min_pt["y_ratio"] * h
                        dx_v = mx_pix - cx
                        dy_v = my_pix - cy
                        if math.hypot(dx_v, dy_v) > 1e-3:
                            angle_deg = math.degrees(math.atan2(dy_v, dx_v)) + 90
                        else:
                            angle_deg = 0
                    else:
                        angle_deg = 0
                        
                    pad = int(max(chamber_w, chamber_h) * 0.5) + 10
                    ch_img_w = chamber_w + pad * 2
                    ch_img_h = chamber_h + pad * 2
                    ch_img = Image.new("RGBA", (ch_img_w, ch_img_h), (0, 0, 0, 0))
                    ch_draw = ImageDraw.Draw(ch_img)
                    self.safe_draw_rectangle(ch_draw, [pad + 1, pad + 1, pad + chamber_w - 1, pad + chamber_h - 1], fill=(128, 0, 255, 60))
                    
                    stone_radius = max(8.0, min(chamber_w, chamber_h) * 0.11)
                    num_x_stones = int(chamber_w / (stone_radius * 1.1)) + 1
                    for idx_s in range(num_x_stones):
                        tx_s = idx_s / max(1, num_x_stones - 1)
                        sx_s = pad + tx_s * chamber_w
                        ch_draw.ellipse([sx_s - stone_radius, pad - stone_radius, sx_s + stone_radius, pad + stone_radius], fill=(0, 0, 0, 255))
                        ch_draw.ellipse([sx_s - stone_radius, pad + chamber_h - stone_radius, sx_s + chamber_h + stone_radius, pad + chamber_h + stone_radius], fill=(0, 0, 0, 255))
                        
                    num_y_stones = int(chamber_h / (stone_radius * 1.1)) + 1
                    for jdy_s in range(num_y_stones):
                        ty_s = jdy_s / max(1, num_y_stones - 1)
                        sy_s = pad + ty_s * chamber_h
                        ch_draw.ellipse([pad - stone_radius, sy_s - stone_radius, pad + stone_radius, sy_s + stone_radius], fill=(0, 0, 0, 255))
                        ch_draw.ellipse([pad + chamber_w - stone_radius, sy_s - stone_radius, pad + chamber_w + stone_radius, sy_s + stone_radius], fill=(0, 0, 0, 255))
                    
                    try:
                        rotated_ch = ch_img.rotate(-angle_deg, expand=True, resample=Image.Resampling.BICUBIC)
                    except AttributeError:
                        rotated_ch = ch_img.rotate(-angle_deg, expand=True, resample=Image.BICUBIC)
                        
                    rw_r, rh_r = rotated_ch.size
                    img.paste(rotated_ch, (int(cx - rw_r/2), int(cy - rh_r/2)), rotated_ch)
                    draw = ImageDraw.Draw(img)
                    
                    box_text = "Probably metal inside void or sandy soil"
                    f_box = self.get_pil_font(12, bold=True)
                    try:
                        tw, th = draw.textsize(box_text, font=f_box)
                    except AttributeError:
                        try:
                            bbox = draw.textbbox((0, 0), box_text, font=f_box)
                            tw = bbox[2] - bbox[0]
                            th = bbox[3] - bbox[1]
                        except Exception:
                            tw, th = len(box_text)*7.5, 15
                            
                    padding_x, padding_y = 12, 8
                    box_w = tw + padding_x * 2
                    box_h = th + padding_y * 2

                    space_left = cx
                    space_right = w - cx
                    space_top = cy
                    space_bottom = h - cy
                    
                    dx_sign = 1 if space_right > space_left else -1
                    dy_sign = 1 if space_bottom > space_top else -1
                    
                    mag = math.hypot(dx_sign, dy_sign * 0.7)
                    ux_away = dx_sign / mag if mag > 0 else 1.0
                    pointer_y_away = (dy_sign * 0.7) / mag if mag > 0 else 0.0
                    
                    half_w = chamber_w / 2.0
                    half_h = chamber_h / 2.0
                    
                    theta_rad = math.radians(-angle_deg)
                    cos_t = math.cos(theta_rad)
                    sin_t = math.sin(theta_rad)
                    local_dir_x = ux_away * cos_t - pointer_y_away * sin_t
                    local_dir_y = ux_away * sin_t + pointer_y_away * cos_t
                    
                    t_candidates = []
                    if abs(local_dir_x) > 1e-5:
                        t_candidates.append(half_w / abs(local_dir_x))
                    if abs(local_dir_y) > 1e-5:
                        t_candidates.append(half_h / abs(local_dir_y))
                    t_edge = min(t_candidates) if t_candidates else half_w
                    
                    t_edge_outer = t_edge + stone_radius
                    touch_x = cx + t_edge_outer * ux_away
                    touch_y = cy + t_edge_outer * pointer_y_away
                    
                    arrow_len = 28.0
                    arrow_start_x = touch_x + arrow_len * ux_away
                    arrow_start_y = touch_y + arrow_len * pointer_y_away
                    
                    bx_center_x = arrow_start_x + (box_w / 2.0) * ux_away
                    bx_center_y = arrow_start_y + (box_h / 2.0) * pointer_y_away
                    
                    bx_left = bx_center_x - box_w / 2.0
                    bx_top = bx_center_y - box_h / 2.0
                    
                    bx_left = self.clamp(bx_left, 20.0, w - box_w - 20.0)
                    bx_top = self.clamp(bx_top, 20.0, h - box_h - 20.0)
                    
                    self.draw_pil_arrow(draw, arrow_start_x, arrow_start_y, touch_x, touch_y, color=(255, 165, 0, 255), width=3)
                    self.safe_draw_rounded_rectangle(draw, [bx_left, bx_top, bx_left + box_w, bx_top + box_h], radius=6, fill=(35, 35, 230), outline=(255, 165, 0, 255), width=2)
                    
                    text_x = bx_left + padding_x + tw / 2
                    text_y = bx_top + padding_y + th / 2
                    self.draw_centered_text(draw, (text_x, text_y), box_text, f_box, (255, 255, 255, 255))

        if self.warning_arrows and not self.soil_contaminated and not self.gpr_active and not self.fibo_active and not self.compare_active and self.active_mode != "4-prop":
            for arr in self.warning_arrows:
                arr_color = arr.get("color", (17, 17, 255))
                self.draw_pil_arrow(draw, arr["start_x_ratio"]*w, h - arr["start_y_ratio"]*h, arr["end_x_ratio"]*w, h - arr["end_y_ratio"]*h, arr_color, 3)

        if self.fibo_active and ImageFilter is not None:
            img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
            draw = ImageDraw.Draw(img)
        return img

    def draw_pil_dashed_line(self, draw, x0, y0, x1, y1, fill, width=1, dash=(5, 5)):
        dist = math.hypot(x1 - x0, y1 - y0)
        if dist == 0:
            return
        ux, pointer_y = (x1 - x0) / dist, (y1 - y0) / dist
        step = sum(dash)
        for i in range(0, int(dist), step):
            sx, sy = x0 + i * ux, y0 + i * pointer_y
            ex, ey = sx + dash[0] * ux, sy + dash[0] * pointer_y
            draw.line([sx, sy, ex, ey], fill=fill, width=width)

    def draw_pil_contours_for_screen(self, draw, w, h, grid, nx, ny, vmin, vmax, levels, color=(58, 58, 58, 255)):
        contour_vals = [vmin + (i + 1) * (vmax - vmin) / (levels + 1) for i in range(levels)]
        def interp(p1, p2, v1, v2, level):
            if abs(v2 - v1) < 1e-12:
                return p1
            t = self.clamp((level - v1) / (v2 - v1), 0.0, 1.0)
            return (p1[0] + t*(p2[0]-p1[0]), p1[1] + t*(p2[1]-p1[1]))
        for j in range(ny - 1):
            for i in range(nx - 1):
                p1_val = grid[j][i]
                p2_val = grid[j][i+1]
                p3_val = grid[j+1][i]
                p4_val = grid[j+1][i+1]
                for level in contour_vals:
                    segments = []
                    if (p1_val >= level) != (p2_val >= level):
                        segments.append(interp((i/(nx-1), j/(ny-1)), ((i+1)/(nx-1), j/(ny-1)), p1_val, p2_val, level))
                    if (p2_val >= level) != (p4_val >= level):
                        segments.append(interp(((i+1)/(nx-1), j/(ny-1)), ((i+1)/(nx-1), (j+1)/(ny-1)), p2_val, p4_val, level))
                    if (p4_val >= level) != (p3_val >= level):
                        segments.append(interp(((i+1)/(nx-1), (j+1)/(ny-1)), (i/(nx-1), (j+1)/(ny-1)), p4_val, p3_val, level))
                    if (p3_val >= level) != (p1_val >= level):
                        segments.append(interp((i/(nx-1), (j+1)/(ny-1)), (i/(nx-1), j/(ny-1)), p3_val, p1_val, level))
                    if len(segments) >= 2:
                        draw.line([segments[0][0]*w, h - segments[0][1]*h, segments[1][0]*w, h - segments[1][1]*h], fill=color, width=1)

    def draw_pil_gpr(self, draw, w, h, img):
        sg_ny = len(self.scan_grid)
        sg_nx = len(self.scan_grid[0]) if sg_ny > 0 else 1
        if self.transition_step > 0:
            step = self.transition_step
            render_nx, render_ny, blur_sigma, R_red = (60, 60, 0.5, 0.90) if step == 1 else ((100, 100, 0.8, 0.60) if step == 2 else (140, 140, 1.2, 0.40))
            trans_grid = [[0.0 for _ in range(render_nx)] for _ in range(render_ny)]
            ag_grid = self.heatmap_data["grid"] if self.heatmap_data else None
            ag_ny = len(ag_grid) if ag_grid else 1
            ag_nx = len(ag_grid[0]) if ag_grid and ag_ny > 0 else 1
            flat_ana = [vv for row in ag_grid for vv in row] if ag_grid else []
            vmin, vmax = min(flat_ana) if flat_ana else 0.0, max(flat_ana) if flat_ana else 100000.0
            span = vmax - vmin if vmax > vmin else 1.0
            min_xr = self.min_point["x_ratio"] if self.min_point else 0.5
            min_yr = self.min_point["y_ratio"] if self.min_point else 0.5
            for j in range(render_ny):
                ry = j / (render_ny - 1) if render_ny > 1 else 0.5
                for i in range(render_nx):
                    rx = i / (render_nx - 1) if render_nx > 1 else 0.5
                    val_pix = self.scan_grid[int(self.clamp(ry*(sg_ny-1), 0, sg_ny-1))][int(self.clamp(rx*(sg_nx-1), 0, sg_nx-1))]
                    if val_pix is None:
                        val_pix = vmin + 0.5 * span
                    if self.fibo_active:
                        val_fib = self.compute_gpr_fibonacci_value(rx, ry, vmin, vmax, min_xr, min_yr)
                        val = self._lerp(val_pix, val_fib, step/2.0)
                    else:
                        val_ana = ag_grid[int(self.clamp(ry*(ag_ny-1), 0, ag_ny-1))][int(self.clamp(rx*(ag_nx-1), 0, ag_nx-1))] if ag_grid else val_pix
                        val = self._lerp(val_pix, val_ana, step/3.0)
                        dist_m = math.hypot((rx - min_xr)*self.width_val, (ry - min_yr)*self.length_val)
                        if dist_m <= R_red:
                            val = self._lerp(val, vmin, (1.0 - dist_m / R_red) * (step/3.0))
                        elif (val - vmin)/span < 0.18:
                            val = vmin + self._lerp((val - vmin)/span, 0.18, step/3.0)*span
                    trans_grid[j][i] = val
            trans_grid = self.gaussian_blur_2d(trans_grid, blur_sigma)
            flat_trans = [vv for row in trans_grid for vv in row]
            tmin, tmax = min(flat_trans) if flat_trans else vmin, max(flat_trans) if flat_trans else vmax
            heatmap_img = Image.new("RGB", (render_nx, render_ny))
            invert_for_void = self.has_void_circle()
            for j in range(render_ny):
                ry_local = j / (render_ny - 1) if render_ny > 1 else 0.5
                for i in range(render_nx):
                    rx_local = i / (render_nx - 1) if render_nx > 1 else 0.5
                    rgb_color = self.resistance_relative_palette_color(trans_grid[j][i], tmin, tmax, invert_for_void, rx_local, ry_local)
                    heatmap_img.putpixel((i, render_ny - 1 - j), rgb_color)
            img.paste(heatmap_img.resize((w, h), RESAMPLE_FILTER), (0, 0))
            self.draw_pil_gpr_fast(draw, w, h, trans_grid, render_nx, render_ny, tmin, tmax)
        else:
            scanned_vals = [self.scan_grid[r][c] for r in range(sg_ny) for c in range(sg_nx) if self.scan_grid[r][c] is not None]
            if scanned_vals:
                curr_min, curr_max = min(scanned_vals), max(scanned_vals)
                cell_w, cell_h = w / sg_nx, h / sg_ny
                for r in range(sg_ny):
                    for c in range(sg_nx):
                        val = self.scan_grid[r][c]
                        if val is not None:
                            if abs(val - curr_min) < 0.1:
                                rgb_color = (255, 0, 0)
                            else:
                                rgb_color = self.resistance_relative_palette_color(val, curr_min, curr_max)
                            draw.rectangle([c*cell_w, h - (r+1)*cell_h, (c+1)*cell_w, h - r*cell_h], fill=(rgb_color[0], rgb_color[1], rgb_color[2], 255))
        if self.final_min_points:
            for rx, ry, val, color in self.final_min_points:
                cx, cy = rx * w, h - ry * h
                fc = (255, 0, 0, 255) if color == "red" else (255, 165, 0, 255)
                self.safe_draw_ellipse(draw, [cx-4, cy-4, cx+4, cy+4], fill=fc, outline=(0, 0, 0, 255), width=1)
        if self.scanning:
            cell_w, cell_h = w / self.scan_cols, h / self.scan_rows
            self.safe_draw_rectangle(draw, [self.scan_current_col*cell_w, h - (self.scan_current_row+1)*cell_h, (self.scan_current_col+1)*cell_w, h - self.scan_current_row*cell_h], fill=None, outline=(255, 255, 0, 255), width=2)

    def draw_pil_gpr_fast(self, draw, w, h, trans_grid, rx, ry, tmin, tmax):
        pass

    def draw_pil_soil_contamination_overlay(self, draw, w, h):
        spacing, dot_r, row = 30, 2, 0
        yy = spacing // 2
        while yy <= h - spacing // 2:
            xx = spacing // 2 if row % 2 else 0
            while xx <= w - spacing // 2:
                draw.ellipse([xx - dot_r, yy - dot_r, xx + dot_r, yy + dot_r], fill=(0, 0, 0, 255))
                xx += spacing
            pointer_y = yy + spacing
            yy = pointer_y
            row += 1

    def draw_pil_arrow(self, draw, x0, y0, x1, y1, color=(255, 0, 0), width=4):
        draw.line([x0, y0, x1, y1], fill=color, width=width)
        angle = math.atan2(y1 - y0, x1 - x0)
        arrow_size = 15 * (width / 4.0)
        p1 = (x1 - arrow_size * math.cos(angle - math.pi/6), y1 - arrow_size * math.sin(angle - math.pi/6))
        p2 = (x1 - arrow_size * math.cos(angle + math.pi/6), y1 - arrow_size * math.sin(angle + math.pi/6))
        draw.polygon([(x1, y1), p1, p2], fill=color)

    def draw_pil_edge_labels(self, draw, w, h):
        e = {k: self.ui_entry_values[k] for k in self.edge_keys}
        font = self.get_pil_font(12, bold=True)
        def draw_txt(text, cx, cy):
            if not text: return
            try:
                box = draw.textbbox((0, 0), text, font=font)
                tw, th = box[2] - box[0], box[3] - box[1]
            except Exception:
                tw, th = len(text) * 7, 12
            draw_txt_cx = cx - tw / 2
            draw_txt_cy = cy - th / 2
            draw.text((draw_txt_cx, draw_txt_cy), text, fill=(0, 0, 0, 255), font=font)
        draw_txt(e["p1p2"], w / 2, h - 20)
        draw_txt(e["p2p4"], w - 30, h / 2)
        draw_txt(e["p4p3"], w / 2, 20)
        draw_txt(e["p3p1"], 30, h / 2)
        draw_txt(e["p1p4"], w / 2 - 25, h / 2 - 25)
        draw_txt(e["p2p3"], w / 2 + 25, h / 2 + 25)

    def get_pil_font(self, text_size, bold=False):
        try:
            font_path = resources.resource_find('fonts/DejaVuSans.ttf')
            if font_path:
                return ImageFont.truetype(font_path, text_size)
        except Exception:
            pass
        if ImageFont is None:
            return None
        for font_name in ["arialb.ttf" if bold else "arial.ttf", "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf", "sans-serif"]:
            try:
                return ImageFont.truetype(font_name, text_size)
            except Exception:
                pass
        try:
            return ImageFont.load_default(size=text_size)
        except Exception:
            return ImageFont.load_default()

    def draw_rotated_text(self, img, text, position, angle, font, fill):
        if not text:
            return
        temp_img = Image.new("RGBA", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        try:
            if hasattr(temp_draw, 'textbbox'):
                box = temp_draw.textbbox((0, 0), text, font=font)
                tw = box[2] - box[0]
                th = box[3] - box[1]
            else:
                tw, th = temp_draw.multiline_textsize(text, font=font)
        except Exception:
            lines = text.split('\n')
            tw = max(len(line) for line in lines) * (font.size * 0.6)
            th = len(lines) * font.size * 1.2
        pad = 30
        txt_w = int(tw) + pad * 2
        txt_h = int(th) + pad * 2
        txt_img = Image.new("RGBA", (txt_w, txt_h), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        try:
            txt_draw.multiline_text((txt_w / 2, txt_h / 2), text, fill=fill, font=font, align="center", anchor="mm")
        except Exception:
            lines = text.split('\n')
            y = pad
            for line in lines:
                try:
                    lw, lh = txt_draw.textsize(line, font=font)
                except Exception:
                    lw, lh = len(line) * (font.size * 0.6), font.size
                txt_draw.text(((txt_w - lw) / 2, y), line, fill=fill, font=font)
                y += lh + 4
        try:
            rotated_img = txt_img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        except AttributeError:
            rotated_img = txt_img.rotate(angle, expand=True, resample=Image.BICUBIC)
        rw, rh = rotated_img.size
        text_px, text_py = position
        paste_x = int(text_px - rw / 2)
        paste_y = int(text_py - rh / 2)
        img.paste(rotated_img, (paste_x, paste_y), rotated_img)

    def geo_click(self, *args):
        if self.check_cuts_and_warn():
            return
        self.show_geo_var = True
        self.fibo_active = False
        self.gpr_active = False
        self.compare_active = False
        self.scanning = False
        self.transition_step = 0
        self.gpr_fibo_skeleton_visible = False
        self.calculate_geophysics_heatmap()
        self.invalidate_render_cache()
        self.update_button_states()
        self._update_target_bg(self.t1, None)
        self._update_target_bg(self.t2, None)
        self.push_state()
        self.monitor.redraw()

    def fibo_click(self, *args):
        if self.check_cuts_and_warn():
            return
        self.show_geo_var = False
        self.fibo_active = True
        self.gpr_active = False
        self.compare_active = False
        self.start_gpr_zigzag_scan()
        self.invalidate_render_cache()
        self.update_button_states()
        self._update_target_bg(self.t1, None)
        self._update_target_bg(self.t2, None)
        self.monitor.redraw()

    def gpr_click(self, *args):
        if self.check_cuts_and_warn():
            return
        self.gpr_active = True
        self.show_geo_var = False
        self.fibo_active = False
        self.compare_active = False
        self.start_gpr_zigzag_scan()
        self.invalidate_render_cache()
        self.update_button_states()
        self._update_target_bg(self.t1, None)
        self._update_target_bg(self.t2, None)
        self.monitor.redraw()

    def compare_click(self, *args):
        if self.check_cuts_and_warn():
            return
        self.compare_active = not self.compare_active
        if self.compare_active:
            self.show_geo_var = False
            self.fibo_active = False
            self.gpr_active = False
            self.scanning = False
            self.transition_step = 0
            self.gpr_fibo_skeleton_visible = False
            self.calculate_geophysics_heatmap()
        else:
            self.show_geo_var = True
            self.calculate_geophysics_heatmap()
        self.invalidate_render_cache()
        self.update_button_states()
        self._update_target_bg(self.t1, None)
        self._update_target_bg(self.t2, None)
        self.push_state()
        self.monitor.redraw()

    def update_button_states(self):
        self.btn_geo.is_active = self.show_geo_var
        self.btn_fibo.is_active = self.fibo_active
        self.btn_gpr.is_active = self.gpr_active
        self.btn_compare.is_active = self.compare_active

    def refresh_scan(self, *args):
        if self.check_cuts_and_warn():
            return
        self.loaded_scan_name = ""
        self.width_val = self.ui_width_val
        self.length_val = self.ui_length_val
        self.ref_soil_val = self.ui_ref_soil_val
        self.entry_values = self.ui_entry_values.copy()
        
        self.gpr_active = False
        self.fibo_active = False
        self.compare_active = False
        self.scanning = False
        self.gpr_fibo_skeleton_visible = False
        self.transition_step = 0
        
        self.calculate_geophysics_heatmap()
        self.push_state()
        self.monitor.redraw()

    def minus_click(self, *args):
        self.expansion_level = max(-10, self.expansion_level - 1)
        self.signal_correction_level = max(-10, self.signal_correction_level - 1)
        self.invalidate_render_cache()
        self.push_state()
        self.monitor.redraw()

    def plus_click(self, *args):
        self.expansion_level = min(10, self.expansion_level + 1)
        self.signal_correction_level = min(10, self.signal_correction_level + 1)
        self.invalidate_render_cache()
        self.push_state()
        self.monitor.redraw()

    def update_target_boxes(self):
        self.t1.text = "Target 1:\nX=                         Y=\nDepth (H) = —"
        self.t2.text = "Target 2:\nX=                         Y=\nDepth (H) = —"
        
        boxes = [self.t1, self.t2]
        for idx, target in enumerate(self.detected_circles):
            if idx >= len(boxes):
                break
            box = boxes[idx]
            material = self.translate(target["label"])
            val = target["target_value"]
            x_m = target["center_x_ratio"] * self.width_val
            y_m = target["center_y_ratio"] * self.length_val
            depth = self.calculate_target_depth(target)
            
            box.text = f"Target {idx+1}:  [b][size=11sp]{material}[/size][/b]      Value: {val:.0f}\nX = {x_m:.2f} m        Y = {y_m:.2f} m\nDepth (H) = {depth:.2f} m"

    def calculate_target_depth(self, circ):
        ref = self.ref_soil_val
        val = circ["target_value"]
        contrast = abs(val - ref) / max(1.0, ref)
        return 1.2 + contrast * 3.5

    def reset_all(self, *args):
        self.loaded_scan_name = ""
        self.ui_width_val = 5.0
        self.ui_length_val = 5.0
        self.ui_ref_soil_val = 600.0
        
        self.in_w.value_text = "5.0 M"
        self.in_l.value_text = "5.0 M"
        self.in_ref.value_text = "600"
        
        self.expansion_level = 0
        self.signal_correction_level = 0
        self.expand_pos_count = 0
        self.expand_neg_count = 0
        self.update_plus_minus_labels()
        
        for k in self.edge_keys:
            self.ui_entry_values[k] = ""
            for seg_btn in self.segs:
                if seg_btn.label_text.upper() == k.upper():
                    seg_btn.value_text = ""
                    
        self.entry_values = self.ui_entry_values.copy()
        
        self.heatmap_data = None
        self.detected_circles = []
        self.warning_arrows = []
        self.soil_contaminated = False
        self.center_red_focus_mode = False
        self.gpr_active = False
        self.fibo_active = False
        self.compare_active = False
        self.show_geo_var = True
        self.scanning = False
        self.gpr_fibo_skeleton_visible = False
        self.transition_step = 0
        
        self.update_button_states()
        self._update_target_bg(self.t1, None)
        self._update_target_bg(self.t2, None)
        self.update_target_boxes()
        self.invalidate_render_cache()
        self.push_state()
        self.monitor.redraw()

    def get_storage_root(self, is_internal=True):
        try:
            from kivy.utils import platform
            if platform == 'android':
                from jnius import autoclass
                Environment = autoclass('android.os.Environment')
                return Environment.getExternalStorageDirectory().getAbsolutePath()
            return os.path.expanduser("~")
        except Exception:
            return getattr(self, 'user_data_dir', os.path.expanduser("~"))

    def sanitize_filename(self, filename):
        illegal_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        if not filename.strip():
            filename = f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return filename

    def ask_filename_and_save(self, is_internal, save_type):
        default_name = f"4 prop_"
        title = self.translate("Enter Filename")
        
        def on_name_entered(typed_name):
            sanitized = self.sanitize_filename(typed_name)
            if save_type == "json":
                self.execute_save_memory(is_internal, sanitized)
            elif save_type == "png":
                self.execute_save_jpeg(is_internal, sanitized)
                
        p = VirtualKeyboardPopup(title=title, callback=on_name_entered, default_text=default_name)
        self.register_popup(p)
        p.open()

    def save_memory_click(self, *args):
        if self.get_cut_segments():
            self.show_popup("Error", "Cannot save scan when probe is disconnected.")
            return
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=self.translate("Save Memory to:"), size_hint_y=0.3, font_size='14sp', bold=True)
        content.add_widget(lbl)
        
        btn_internal = PlasticButton(text=self.translate("Internal Storage"), btn_color=[0.1, 0.5, 0.8, 1], size_hint_y=0.35)
        btn_cancel = PlasticButton(text=self.translate("Cancel"), btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.35)
        
        content.add_widget(btn_internal)
        content.add_widget(btn_cancel)
        popup_loc = Popup(title=self.translate("Save Memory"), content=content, size_hint=(0.85, 0.4))
        
        def choose_internal(*args):
            popup_loc.dismiss()
            self.ask_filename_and_save(is_internal=True, save_type="json")
            
        btn_internal.bind(on_release=choose_internal)
        btn_cancel.bind(on_release=popup_loc.dismiss)
        self.register_popup(popup_loc)
        popup_loc.open()

    def execute_save_memory(self, is_internal, filename):
        if not filename.endswith(".json"):
            filename += ".json"
            
        state = {
            "width": str(self.ui_width_val), 
            "height": str(self.ui_length_val),
            "ref_soil": str(self.ui_ref_soil_val),
            "expand_pos": self.expand_pos_count, 
            "expand_neg": self.expand_neg_count, 
            "expansion_level": self.expansion_level,
            "entries": self.ui_entry_values.copy()
        }
        
        try:
            root_dir = self.get_storage_root(is_internal)
            folder = os.path.join(root_dir, "Cornix Winner", "4prop Scan", "File Scan")
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
            self.show_popup("Success", f"Scan saved successfully to:\n{filepath}")
        except Exception as e:
            try:
                fallback_folder = os.path.join(self.user_data_dir, "Cornix Winner", "4prop Scan", "File Scan")
                os.makedirs(fallback_folder, exist_ok=True)
                filepath = os.path.join(fallback_folder, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=4, ensure_ascii=False)
                self.show_popup("Success", f"Saved to:\n{filepath}")
            except Exception as e2:
                self.show_popup("Error", f"Could not save file:\n{e2}")

    def recall_memory_click(self, *args):
        self.recall_memory_with_location(is_internal=True)

    def recall_memory_with_location(self, is_internal):
        files_map = {}
        search_dirs = [
            os.path.join(self.get_storage_root(is_internal), "Cornix Winner", "4prop Scan", "File Scan"),
            os.path.join(self.get_storage_root(is_internal), "Cornix Winner", "File scan"),
            os.path.join(self.get_storage_root(is_internal), "Documents", "Cornix Winner PRO", "File scan"),
            os.path.join(self.user_data_dir, "Cornix Winner", "4prop Scan", "File Scan"),
            os.path.join(self.user_data_dir, "Cornix Winner", "File scan"),
            os.path.join(self.user_data_dir, "Documents", "Cornix Winner PRO", "File scan")
        ]
        
        for target_dir in search_dirs:
            try:
                if os.path.exists(target_dir):
                    for f in os.listdir(target_dir):
                        if f.endswith(".json"):
                            filepath = os.path.join(target_dir, f)
                            try:
                                with open(filepath, 'r', encoding='utf-8') as file_peek:
                                    data_peek = json.load(file_peek)
                                    if data_peek.get("type") == "2prop":
                                        continue
                            except Exception:
                                pass
                            files_map[f] = filepath
            except Exception:
                pass

        fourprop_files_map = {}
        for f, path in files_map.items():
            if not f.startswith("2prop_"):
                fourprop_files_map[f] = path
            else:
                try:
                    with open(path, 'r', encoding='utf-8') as js_f:
                        data = json.load(js_f)
                        if data.get("type") != "2prop":
                            fourprop_files_map[f] = path
                except Exception:
                    pass

        if not fourprop_files_map:
            self.show_popup("Recall", "No saved scans found")
            return

        self.recall_files_list = list(fourprop_files_map.keys())
        self.recall_files_map = fourprop_files_map
        self.current_search_query = ""
        self.delete_mode = False
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        search_row = BoxLayout(spacing=dp(5), size_hint_y=0.15)
        self.btn_search_trigger = PlasticButton(text=self.translate("Search: [Click to type]"), btn_color=[0.2, 0.4, 0.4, 1])
        btn_clear_search = PlasticButton(text="X", btn_color=[0.7, 0.2, 0.2, 1], size_hint_x=0.2)
        search_row.add_widget(self.btn_search_trigger)
        search_row.add_widget(btn_clear_search)
        content.add_widget(search_row)

        from kivy.uix.scrollview import ScrollView
        sv = ScrollView(size_hint_y=0.7)
        self.file_list_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.file_list_grid.bind(minimum_height=self.file_list_grid.setter('height'))
        sv.add_widget(self.file_list_grid)
        content.add_widget(sv)

        bottom_row = BoxLayout(spacing=dp(3), size_hint_y=0.15)
        self.btn_delete_mode = PlasticButton(text="Delete Mode", btn_color=[0.8, 0.2, 0.2, 1])
        btn_cancel_select = PlasticButton(text=self.translate("Cancel"), btn_color=[0.5, 0.5, 0.5, 1])
        
        bottom_row.add_widget(btn_cancel_select)
        bottom_row.add_widget(self.btn_delete_mode)
        content.add_widget(bottom_row)

        self.recall_select_popup = Popup(title=self.translate("Select Scan File"), content=content, size_hint=(0.85, 0.8))
        btn_cancel_select.bind(on_release=self.recall_select_popup.dismiss)

        def populate_file_list(query=""):
            self.file_list_grid.clear_widgets()
            filtered_files = [f for f in self.recall_files_list if not query or query.lower() in f.lower()]
            if not filtered_files:
                self.file_list_grid.add_widget(Label(text=self.translate("No matches found"), size_hint_y=None, height=dp(40)))
                return
            for f in filtered_files:
                display_name = f"🗑 {f}" if self.delete_mode else f
                btn_clr = [0.6, 0.1, 0.1, 1] if self.delete_mode else [0.3, 0.3, 0.3, 1]
                btn = PlasticButton(text=display_name, btn_color=btn_clr, size_hint_y=None, height=dp(40))
                btn.bind(on_release=lambda instance, fn=f: on_file_click(fn))
                self.file_list_grid.add_widget(btn)

        def on_file_click(filename):
            if self.delete_mode:
                file_path = self.recall_files_map.get(filename)
                try:
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                    self.recall_files_list.remove(filename)
                    self.recall_files_map.pop(filename, None)
                except Exception as e:
                    print(e)
                populate_file_list(self.current_search_query)
            else:
                self.show_scan_options_popup(filename)

        def toggle_delete_mode(*args):
            self.delete_mode = not self.delete_mode
            self.btn_delete_mode.text = "Exit Delete" if self.delete_mode else "Delete Mode"
            self.btn_delete_mode.btn_color = [0.1, 0.6, 0.2, 1] if self.delete_mode else [0.8, 0.2, 0.2, 1]
            populate_file_list(self.current_search_query)

        self.btn_delete_mode.bind(on_release=toggle_delete_mode)
        
        def run_search_keyboard(*args):
            p = VirtualKeyboardPopup(title="Type query", callback=lambda q: populate_after_search(q), default_text=self.current_search_query)
            self.register_popup(p)
            p.open()
            
        def populate_after_search(q):
            self.current_search_query = q
            self.btn_search_trigger.text = self.translate("Search: [Click to type]") if not q else q
            populate_file_list(q)

        self.btn_search_trigger.bind(on_release=run_search_keyboard)
        btn_clear_search.bind(on_release=lambda x: populate_after_search(""))
        
        populate_file_list()
        self.register_popup(self.recall_select_popup)
        self.recall_select_popup.open()

    def show_scan_options_popup(self, filename):
        filepath = self.recall_files_map.get(filename)
        if not filepath:
            return
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        info_text = filename
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            w_val = data.get("width", "5.0")
            l_val = data.get("height", "5.0")
            r_val = data.get("ref_soil", "600")
            info_text += f"\n\nWidth: {w_val}M | Length: {l_val}M\nSoil Ref: {r_val}"
        except Exception:
            pass
            
        lbl = Label(text=info_text, halign='center', valign='middle', size_hint_y=0.5, font_size='14sp', bold=True)
        lbl.bind(size=lambda s, v: setattr(lbl, 'text_size', v))
        content.add_widget(lbl)
        
        btn_layout = BoxLayout(spacing=dp(5), size_hint_y=0.5)
        btn_load = PlasticButton(text="Load", btn_color=[0.1, 0.6, 0.2, 1])
        btn_delete = PlasticButton(text="Delete", btn_color=[0.8, 0.2, 0.2, 1])
        btn_share = PlasticButton(text="Share", btn_color=[0.5, 0.0, 0.5, 1])
        btn_cancel = PlasticButton(text="Cancel", btn_color=[0.5, 0.5, 0.5, 1])
        
        btn_layout.add_widget(btn_load)
        btn_layout.add_widget(btn_share)
        btn_layout.add_widget(btn_delete)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)
        
        options_popup = Popup(title=self.translate("Recall Memory"), content=content, size_hint=(0.85, 0.5), auto_dismiss=False)
        
        def on_load(*args):
            options_popup.dismiss()
            if hasattr(self, 'recall_select_popup') and self.recall_select_popup:
                self.recall_select_popup.dismiss()
            self.load_from_json(filepath)
            
        def on_delete(*args):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                options_popup.dismiss()
                if hasattr(self, 'recall_select_popup') and self.recall_select_popup:
                    self.recall_select_popup.dismiss()
                self.show_popup("Success", "File deleted successfully!")
                self.recall_memory_with_location(is_internal=True)
            except Exception as e:
                self.show_popup("Error", str(e))
                
        def on_share(*args):
            self.share_file_native(filepath, "application/json")
            
        def on_cancel(*args):
            options_popup.dismiss()
            
        btn_load.bind(on_release=on_load)
        btn_delete.bind(on_release=on_delete)
        btn_share.bind(on_release=on_share)
        btn_cancel.bind(on_release=on_cancel)
        
        self.register_popup(options_popup)
        options_popup.open()

    def load_from_json(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.ui_width_val = float(data.get("width", 5.0))
            self.ui_length_val = float(data.get("height", 5.0))
            self.ui_ref_soil_val = float(data.get("ref_soil", 600.0))
            self.ui_entry_values = data.get("entries", {k: "" for k in self.edge_keys})
            
            self.width_val = self.ui_width_val
            self.length_val = self.ui_length_val
            self.ref_soil_val = self.ui_ref_soil_val
            
            self.in_w.value_text = f"{self.ui_width_val} M"
            self.in_l.value_text = f"{self.ui_length_val} M"
            self.in_ref.value_text = str(int(self.ui_ref_soil_val))
            for b, key in zip(self.segs, self.edge_keys):
                b.value_text = self.ui_entry_values.get(key, "")
            
            self.entry_values = self.ui_entry_values.copy()
            self.loaded_scan_name = os.path.splitext(os.path.basename(filepath))[0]
            self.push_state()
            self.invalidate_render_cache()
            self.calculate_geophysics_heatmap()
            self.monitor.redraw()
            self.show_popup("Success", "Scan recalled successfully!")
        except Exception as e:
            self.show_popup("Error", f"Failed to load scan:\n{str(e)}")

    def save_jpeg_click(self, *args):
        if self.heatmap_data is None:
            self.show_popup("Error", "Please run scan first.")
            return
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=self.translate("Save Image to:"), size_hint_y=0.3, font_size='14sp', bold=True)
        content.add_widget(lbl)
        
        btn_internal = PlasticButton(text=self.translate("Internal Storage"), btn_color=[0.1, 0.6, 0.2, 1], size_hint_y=0.35)
        btn_cancel = PlasticButton(text=self.translate("Cancel"), btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.35)
        
        content.add_widget(btn_internal)
        content.add_widget(btn_cancel)
        popup_loc = Popup(title=self.translate("Save Image"), content=content, size_hint=(0.85, 0.4))
        
        def choose_internal(*args):
            popup_loc.dismiss()
            self.ask_filename_and_save(is_internal=True, save_type="png")
            
        btn_internal.bind(on_release=choose_internal)
        btn_cancel.bind(on_release=popup_loc.dismiss)
        self.register_popup(popup_loc)
        popup_loc.open()

    def execute_save_jpeg(self, is_internal, filename):
        if not filename.endswith(".png"):
            filename += ".png"
        try:
            folder = self.get_writable_folder(os.path.join("Cornix Winner", "4prop Scan", "picture Scan"))
            filepath = os.path.join(folder, filename)
            self.monitor.export_to_png(filepath)

            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                MediaScannerConnection = autoclass('android.media.MediaScannerConnection')
                MediaScannerConnection.scanFile(PythonActivity.mActivity, [filepath], None, None)
            except Exception:
                pass

            self.show_popup("Success", f"Screenshot saved successfully to:\n{filepath}")
        except Exception as e:
            self.show_popup("Error", f"Could not save file:\n{e}")

    def recall_jpeg_click(self, *args):
        self.recall_jpeg_with_location(is_internal=True)

    def recall_jpeg_with_location(self, is_internal):
        files_map = {}
        search_dirs = [
            os.path.join(self.get_storage_root(is_internal), "Cornix Winner", "4prop Scan", "picture Scan"),
            os.path.join(self.get_storage_root(is_internal), "Pictures", "Cornix Winner PRO", "picture scan"),
            os.path.join(self.user_data_dir, "Cornix Winner", "4prop Scan", "picture Scan"),
            os.path.join(self.user_data_dir, "Pictures", "Cornix Winner PRO", "picture scan")
        ]
        
        for target_dir in search_dirs:
            try:
                if os.path.exists(target_dir):
                    for f in os.listdir(target_dir):
                        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                            if f.startswith("2prop_"):
                                continue
                            files_map[f] = os.path.join(target_dir, f)
            except Exception:
                pass

        if not files_map:
            self.show_popup("Recall Picture", "No saved images found")
            return

        self.recall_pic_files_list = list(files_map.keys())
        self.recall_pic_files_map = files_map
        self.current_pic_search_query = ""
        self.pic_delete_mode = False
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        search_row = BoxLayout(spacing=dp(5), size_hint_y=0.15)
        self.btn_pic_search_trigger = PlasticButton(text=self.translate("Search: [Click to type]"), btn_color=[0.2, 0.4, 0.4, 1])
        btn_clear_pic_search = PlasticButton(text="X", btn_color=[0.7, 0.2, 0.2, 1], size_hint_x=0.2)
        search_row.add_widget(self.btn_pic_search_trigger)
        search_row.add_widget(btn_clear_pic_search)
        content.add_widget(search_row)

        from kivy.uix.scrollview import ScrollView
        sv = ScrollView(size_hint_y=0.7)
        self.pic_file_list_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.pic_file_list_grid.bind(minimum_height=self.pic_file_list_grid.setter('height'))
        sv.add_widget(self.pic_file_list_grid)
        content.add_widget(sv)

        bottom_row = BoxLayout(spacing=dp(3), size_hint_y=0.15)
        self.btn_pic_delet_toggle = PlasticButton(text="Delete Mode", btn_color=[0.8, 0.2, 0.2, 1])
        btn_cancel_select = PlasticButton(text=self.translate("Cancel"), btn_color=[0.5, 0.5, 0.5, 1])
        
        bottom_row.add_widget(btn_cancel_select)
        bottom_row.add_widget(self.btn_pic_delet_toggle)
        content.add_widget(bottom_row)

        self.recall_pic_popup = Popup(title=self.translate("Recall Picture"), content=content, size_hint=(0.85, 0.8))
        btn_cancel_select.bind(on_release=self.recall_pic_popup.dismiss)

        def populate_pic_file_list(query=""):
            self.pic_file_list_grid.clear_widgets()
            filtered_files = [f for f in self.recall_pic_files_list if not query or query.lower() in f.lower()]
            if not filtered_files:
                self.pic_file_list_grid.add_widget(Label(text=self.translate("No matches found"), size_hint_y=None, height=dp(40)))
                return
            for f in filtered_files:
                display_name = f"🗑 {f}" if self.pic_delete_mode else f
                btn_clr = [0.6, 0.1, 0.1, 1] if self.pic_delete_mode else [0.3, 0.3, 0.3, 1]
                btn = PlasticButton(text=display_name, btn_color=btn_clr, size_hint_y=None, height=dp(40))
                btn.bind(on_release=lambda instance, fn=f: on_file_click(fn))
                self.pic_file_list_grid.add_widget(btn)

        def on_file_click(filename):
            if self.pic_delete_mode:
                file_path = self.recall_pic_files_map.get(filename)
                try:
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                    self.recall_pic_files_list.remove(filename)
                    self.recall_pic_files_map.pop(filename, None)
                except Exception as e:
                    print(e)
                populate_pic_file_list(self.current_pic_search_query)
            else:
                self.recall_pic_popup.dismiss()
                self.show_image_viewer(self.recall_pic_files_map[filename])

        def toggle_pic_delete_mode(*args):
            self.pic_delete_mode = not self.pic_delete_mode
            self.btn_pic_delet_toggle.text = "Exit Delete" if self.pic_delete_mode else "Delete Mode"
            self.btn_pic_delet_toggle.btn_color = [0.1, 0.6, 0.2, 1] if self.pic_delete_mode else [0.8, 0.2, 0.2, 1]
            populate_pic_file_list(self.current_pic_search_query)

        self.btn_pic_delet_toggle.bind(on_release=toggle_pic_delete_mode)
        
        def trigger_pic_search_keyboard(*args):
            def on_pic_search_query_submitted(query):
                self.current_pic_search_query = query
                self.btn_pic_search_trigger.text = self.translate("Search: [Click to type]") if not query else query
                populate_pic_file_list(query)
                
            p = VirtualKeyboardPopup(title="Type query", callback=on_pic_search_query_submitted, default_text=self.current_pic_search_query)
            self.register_popup(p)
            p.open()

        self.btn_pic_search_trigger.bind(on_release=trigger_pic_search_keyboard)
        btn_clear_pic_search.bind(on_release=lambda x: (setattr(self, 'current_pic_search_query', ""), populate_pic_file_list("")))
        
        populate_pic_file_list("")
        self.register_popup(self.recall_pic_popup)
        self.recall_pic_popup.open()

    def show_image_viewer(self, filepath):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        img_widget = KivyImage(source=filepath, allow_stretch=True, keep_ratio=True)
        content.add_widget(img_widget)
        
        btn_layout = BoxLayout(spacing=dp(5), size_hint_y=0.15)
        btn_close = PlasticButton(text=self.translate("Close"), btn_color=[0.11, 0.51, 0.84, 1])
        btn_delete = PlasticButton(text=self.translate("Delete"), btn_color=[0.8, 0.2, 0.2, 1])
        btn_share = PlasticButton(text=self.translate("Share"), btn_color=[0.5, 0.0, 0.5, 1])
        
        btn_layout.add_widget(btn_close)
        btn_layout.add_widget(btn_delete)
        btn_layout.add_widget(btn_share)
        content.add_widget(btn_layout)
        
        viewer_popup = Popup(title=os.path.basename(filepath), content=content, size_hint=(0.9, 0.9), auto_dismiss=False)
        
        def on_close(*args):
            viewer_popup.dismiss()
            self.recall_jpeg_click()
            
        def on_delete(*args):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                viewer_popup.dismiss()
                self.show_popup("Success", "File deleted successfully!")
                self.recall_jpeg_click()
            except Exception as e:
                self.show_popup("Error", str(e))
                
        def on_share(*args):
            self.share_file_native(filepath, "image/png")
            
        btn_close.bind(on_release=on_close)
        btn_delete.bind(on_release=on_delete)
        btn_share.bind(on_release=on_share)
        
        self.register_popup(viewer_popup)
        viewer_popup.open()

    def share_file_native(self, filepath, mime_type="*/*"):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = PythonActivity.mActivity

                Intent = autoclass('android.content.Intent')
                String = autoclass('java.lang.String')
                File = autoclass('java.io.File')
                Parcelable = autoclass('android.os.Parcelable')

                file_obj = File(filepath)

                try:
                    StrictMode = autoclass('android.os.StrictMode')
                    VmPolicyBuilder = autoclass('android.os.StrictMode$VmPolicy$Builder')
                    StrictMode.setVmPolicy(VmPolicyBuilder().build())
                except Exception:
                    pass

                file_uri = None
                try:
                    FileProvider = autoclass('androidx.core.content.FileProvider')
                    file_uri = FileProvider.getUriForFile(
                        currentActivity,
                        currentActivity.getPackageName() + ".fileprovider",
                        file_obj
                    )
                except Exception:
                    Uri = autoclass('android.net.Uri')
                    file_uri = Uri.fromFile(file_obj)

                share_intent = Intent(Intent.ACTION_SEND)
                if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
                    share_intent.setType(String("image/*"))
                else:
                    share_intent.setType(String("*/*"))

                share_intent.putExtra(Intent.EXTRA_STREAM, cast(Parcelable, file_uri))
                share_intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

                title_str = "Share File via"
                chooser = Intent.createChooser(share_intent, String(title_str))
                currentActivity.startActivity(chooser)
            except Exception as e:
                self.show_popup("Error Sharing", f"Share failed: {str(e)}")
        else:
            try:
                import subprocess
                if is_windows:
                    os.startfile(os.path.dirname(filepath))
                elif py_platform.system() == 'Darwin':
                    subprocess.Popen(['open', '-R', filepath])
                else:
                    subprocess.Popen(['xdg-open', os.path.dirname(filepath)])
                self.show_popup("Share", "Sharing folder opened.")
            except Exception as e:
                self.show_popup("Share", f"Could not open folder: {str(e)}")

    def push_state(self):
        state = {
            "ui_entry_values": self.ui_entry_values.copy(),
            "ui_width_val": self.ui_width_val,
            "ui_length_val": self.ui_length_val,
            "ui_ref_soil_val": self.ui_ref_soil_val,
            "expand_pos_count": self.expand_pos_count,
            "expand_neg_count": self.expand_neg_count,
            "expansion_level": self.expansion_level,
            "show_geo_var": self.show_geo_var,
            "gpr_active": self.gpr_active,
            "fibo_active": self.fibo_active,
            "compare_active": self.compare_active,
            "loaded_scan_name": self.loaded_scan_name,
            "scan_grid": [row[:] for row in self.scan_grid] if self.scan_grid is not None else None,
            "sampled_points": self.sampled_points.copy() if self.sampled_points else [],
            "final_min_points": self.final_min_points.copy() if self.final_min_points else [],
            "transition_step": self.transition_step,
            "gpr_fibo_skeleton_visible": self.gpr_fibo_skeleton_visible
        }
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(state)
        if len(self.history) > 30:
            self.history.pop(0)
        self.history_index = len(self.history) - 1

    def load_state(self, state):
        self.ui_entry_values = state["ui_entry_values"].copy()
        self.entry_values = self.ui_entry_values.copy()
        self.ui_width_val = state["ui_width_val"]
        self.ui_length_val = state["ui_length_val"]
        self.ui_ref_soil_val = state["ui_ref_soil_val"]
        self.width_val = self.ui_width_val
        self.length_val = self.ui_length_val
        self.ref_soil_val = self.ui_ref_soil_val
        
        self.in_w.value_text = f"{self.ui_width_val} M"
        self.in_l.value_text = f"{self.ui_length_val} M"
        self.in_ref.value_text = f"{int(self.ui_ref_soil_val)}"
        
        for k, b in zip(self.edge_keys, self.segs):
            b.value_text = self.ui_entry_values.get(k, "")
            
        self.expand_pos_count = state["expand_pos_count"]
        self.expand_neg_count = state["expand_neg_count"]
        self.expansion_level = state["expansion_level"]
        self.signal_correction_level = self.expansion_level
        self.update_plus_minus_labels()
        
        self.show_geo_var = state["show_geo_var"]
        self.gpr_active = state["gpr_active"]
        self.fibo_active = state["fibo_active"]
        self.compare_active = state["compare_active"]
        self.loaded_scan_name = state["loaded_scan_name"]
        
        self.scan_grid = [row[:] for row in state["scan_grid"]] if state["scan_grid"] is not None else None
        self.sampled_points = state["sampled_points"].copy() if state["sampled_points"] else []
        self.final_min_points = state["final_min_points"].copy() if state["final_min_points"] else []
        self.transition_step = state["transition_step"]
        self.gpr_fibo_skeleton_visible = state["gpr_fibo_skeleton_visible"]
        
        self.update_button_states()
        self.calculate_geophysics_heatmap()
        self.invalidate_render_cache()

    def show_popup(self, title, text):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=text, halign='center', valign='middle', size_hint_y=0.7)
        lbl.bind(size=lambda s, v: setattr(lbl, 'text_size', v))
        content.add_widget(lbl)
        btn = PlasticButton(text="Close", btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.3)
        popup = Popup(title=title, content=content, size_hint=(0.85, 0.45))
        btn.bind(on_release=popup.dismiss)
        content.add_widget(btn)
        self.register_popup(popup)
        popup.open()

    def undo_click(self, *args):
        if self.history_index > 0:
            self.history_index -= 1
            self.load_state(self.history[self.history_index])
            self.monitor.redraw()
        else:
            self.show_popup("Info", "No more undo steps available.")

    def redo_click(self, *args):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.load_state(self.history[self.history_index])
            self.monitor.redraw()
        else:
            self.show_popup("Info", "No more redo steps available.")

    def show_contamination_help(self, *args):
        msg_en = ("The scanned environment has very severe contamination, this contamination is either related to surface metals or to the soil properties of this spot. To be sure, please first remove the surface metals from the ground with a loop metal detector and scan again, if the problem is not resolved, this environment is dirty.")
        self.show_popup("Contamination Warning", msg_en)

    def show_report_popup(self, *args):
        if self.get_cut_segments():
            self.show_popup("Error", "Cannot generate report when probe is disconnected.")
            return
        if not self.detected_circles:
            self.show_popup("Error", "Please run scan first.")
            return
            
        self.report_target_idx = 0
        self.report_container = FloatLayout()
        with self.report_container.canvas.before:
            Color(0.04, 0.04, 0.04, 1)
            self.report_bg_rect = Rectangle(pos=self.report_container.pos, size=self.report_container.size)
        self.report_container.bind(pos=self.update_report_bg, size=self.update_report_bg)
        
        self.report_nav_box = BoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
        self.btn_close_report = PlasticButton(text="Close", btn_color=[0.8, 0.2, 0.2, 1], size_hint_x=0.5)
        self.btn_next_report = PlasticButton(text="Next Target", btn_color=[0.11, 0.51, 0.84, 1], size_hint_x=0.5)
        
        self.btn_close_report.bind(on_release=lambda x: self.report_popup.dismiss())
        self.btn_next_report.bind(on_release=self.toggle_report_target)
        
        self.report_nav_box.add_widget(self.btn_close_report)
        if len(self.detected_circles) > 1:
            self.report_nav_box.add_widget(self.btn_next_report)
            
        self.report_popup = Popup(
            title=self.translate("Work Report"),
            content=self.report_container,
            size_hint=(0.9, 0.72),
            auto_dismiss=False
        )
        self.build_report_layout()
        self.register_popup(self.report_popup)
        self.report_popup.open()

    def update_report_bg(self, instance, value):
        if hasattr(self, 'report_bg_rect') and self.report_bg_rect:
            self.report_bg_rect.pos = self.report_container.pos
            self.report_bg_rect.size = self.report_container.size

    def toggle_report_target(self, *args):
        self.report_target_idx = 1 - self.report_target_idx
        if self.report_target_idx == 0:
            self.btn_next_report.text = "Next Target"
        else:
            self.btn_next_report.text = "Prev Target"
        self.build_report_layout()

    def build_report_layout(self):
        self.report_container.clear_widgets()
        watermark = Label(
            text="Cornix\nWinner PRO", font_size='48sp', bold=True,
            color=[0.6, 0.05, 0.15, 0.16], halign='center', valign='middle',
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0}
        )
        watermark.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        self.report_container.add_widget(watermark)
        
        content_box = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8), size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        
        from kivy.uix.scrollview import ScrollView
        sv = ScrollView(size_hint=(1, 0.85))
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        circ = self.detected_circles[self.report_target_idx]
        target_num = self.report_target_idx + 1
        material_trans = self.translate(circ["label"])
        
        x_m = circ["center_x_ratio"] * self.width_val
        y_m = circ["center_y_ratio"] * self.length_val
        depth_m = self.calculate_target_depth(circ)
        diameter_cm = circ["diameter_m"] * 100.0
        
        raw_vals = [self.safe_float(v) for v in self.entry_values.values() if v is not None and v != ""]
        if len(raw_vals) > 1:
            v_max = max(raw_vals)
            v_min = min(raw_vals)
            v_avg = sum(raw_vals) / len(raw_vals)
            asymmetry = (v_max - v_min) / max(1.0, v_avg)
            error_cm = int(asymmetry * 35.0 + 3.0)
            error_cm = max(3, min(90, error_cm))
        else:
            error_cm = 5
            
        ref = self.ref_soil_val
        if ref < 200:
            soil_type = "Very Wet / Muddy"
        elif ref < 600:
            soil_type = "Moist / Normal"
        elif ref < 1500:
            soil_type = "Semi-Dry"
        else:
            soil_type = "Very Dry / Sandy"
            
        contrast = abs(circ["target_value"] - ref) / max(1.0, ref) * 100.0
        contrast_str = f"{contrast:.1f}%"
        
        freq_info = self.get_frequency_data(circ["label"])
        pointer_y_freq = freq_info["tx"]
        txt_range = freq_info["range"]
        pointer_y_freq_rx = freq_info["rx"]
        
        rows = [
            ("Target Name:", f"Target {target_num}"),
            ("Material:", material_trans),
            ("X Coordinate:", f"{x_m:.2f} m"),
            ("Y Coordinate:", f"{y_m:.2f} m"),
            ("Target Depth (Deep):", f"{depth_m:.2f} m"),
            ("Contamination Dia:", f"{diameter_cm:.1f} cm"),
            ("Error Tolerance:", f"±{error_cm} m"),
            ("Transmit Freq (TX):", pointer_y_freq),
            ("Receive Freq (RX):", pointer_y_freq_rx),
            ("Frequency Range:", txt_range),
            ("Soil Ref Resistance:", f"{ref:.0f} Ohm"),
            ("Soil Type Estimate:", soil_type),
            ("Signal Contrast:", contrast_str)
        ]
            
        title_lbl = Label(
            text=f"[b]{'Target 1 Report' if target_num == 1 else 'Target 2 Report'}[/b]", 
            markup=True, color=[1, 1, 1, 1], font_size='15sp', size_hint_y=None, height=dp(30), halign='center'
        )
        title_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content_box.add_widget(title_lbl)
        
        for k, v in rows:
            k_lbl = Label(
                text=f"[b]{k}[/b]", markup=True, color=[1, 1, 1, 1], font_size='13sp',
                size_hint_y=None, height=dp(25),  halign='left', valign='middle', padding=(dp(15), 0)
            )
            k_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            
            v_lbl = Label(
                text=f"[b]{v}[/b]", markup=True, color=[0.95, 0.95, 0.1, 1], font_size='11sp',
                size_hint_y=None, height=dp(25), halign='right', valign='middle', padding=(dp(15), 0)
            )
            v_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            
            grid.add_widget(k_lbl)
            grid.add_widget(v_lbl)
            
        sv.add_widget(grid)
        content_box.add_widget(sv)
        
        if self.report_nav_box.parent:
            self.report_nav_box.parent.remove_widget(self.report_nav_box)
            
        content_box.add_widget(self.report_nav_box)
        self.report_container.add_widget(content_box)

    def get_frequency_data(self, label):
        lbl = label.lower() if label else ""
        if "gold" in lbl:
            return {"tx": "5.2 KHz", "rx": "5.2 KHz", "range": "VLF"}
        elif "silver" in lbl:
            return {"tx": "6.8 KHz", "rx": "6.8 KHz", "range": "VLF"}
        elif "copper" in lbl:
            return {"tx": "8.0 KHz", "rx": "8.0 KHz", "range": "VLF"}
        elif "brass" in lbl:
            return {"tx": "9.5 KHz", "rx": "9.5 KHz", "range": "VLF"}
        elif "iron" in lbl:
            return {"tx": "12.0 KHz", "rx": "12.0 KHz", "range": "VLF"}
        elif "water" in lbl:
            return {"tx": "2.4 GHz", "rx": "2.4 GHz", "range": "UHF"}
        elif "void" in lbl:
            return {"tx": "1.6 GHz", "rx": "1.6 GHz", "range": "UHF"}
        return {"tx": "5.0 KHz", "rx": "5.0 KHz", "range": "VLF"}

    def calculate_geophysics_heatmap(self):
        self.invalidate_render_cache()
        self.warning_arrows = []
        self.center_red_focus_mode = False
        vals = self.valid_entries_dict()
        if self.get_cut_segments():
            self.heatmap_data = None
            self.detected_circles = []
            self.update_target_boxes()
            return
        self.soil_contaminated = self.detect_soil_contamination(vals)
        result = self.build_line_sources(vals)
        if not result:
            self.heatmap_data = None
            self.min_point = None
            self.max_point = None
            self.detected_circles = []
            self.update_target_boxes()
            return
        sources, vmin, vmax = result
        nx, ny = 140, 140
        if self.should_use_center_red_focus(vals):
            self.center_red_focus_mode = True
            value_grid = self.build_center_red_focus_grid(nx, ny, vals, vmin, vmax)
            if self.signal_correction_level != 0:
                factor = 0.35 if self.signal_correction_level >= 0 else 0.15
                value_grid = self.gaussian_blur_2d(value_grid, max(0.10, 1.2 + factor * self.signal_correction_level))
        else:
            value_grid = []
            for j in range(ny):
                row = []
                y = j / (ny - 1) if ny > 1 else 0.5
                for i in range(nx):
                    x = i / (nx - 1) if nx > 1 else 0.5
                    row.append(self.compute_cell_value(x, y, sources, vmin, vmax))
                value_grid.append(row)
            factor = 0.35 if self.signal_correction_level >= 0 else 0.15
            value_grid = self.gaussian_blur_2d(value_grid, max(0.10, 0.90 + factor * self.signal_correction_level))
        flat = [vv for row in value_grid for vv in row]
        gmin, vmax = min(flat), max(flat)
        min_i, min_j = 0, 0
        max_i, max_j = 0, 0
        min_val, max_val = value_grid[0][0], value_grid[0][0]
        for j in range(ny):
            for i in range(nx):
                v = value_grid[j][i]
                if v < min_val:
                    min_val, min_i, min_j = v, i, j
                if v > max_val:
                    max_val, max_i, max_j = v, i, j
        min_xr = self.clamp(min_i / (nx - 1) if nx > 1 else 0.5, 0.10, 0.90)
        min_yr = self.clamp(min_j / (ny - 1) if ny > 1 else 0.5, 0.10, 0.90)
        max_xr = self.clamp(max_i / (nx - 1) if nx > 1 else 0.5, 0.10, 0.90)
        max_yr = self.clamp(max_j / (ny - 1) if ny > 1 else 0.5, 0.10, 0.90)
        self.min_point = {"x_ratio": min_xr, "y_ratio": min_yr, "value": min_val}
        self.max_point = {"x_ratio": max_xr, "y_ratio": max_yr, "value": max_val}
        self.heatmap_data = {"grid": value_grid, "nx": nx, "ny": ny, "min": gmin, "max": vmax, "sources": sources}
        self.width_m = self.width_val
        self.height_m = self.length_val
        if self.soil_contaminated:
            self.detected_circles = []
            self.update_target_boxes()
            return
        self.detected_circles = []
        if self.should_allow_circle_rendering_for_mode() and self.should_allow_circle_rendering(vals):
            low_vals_entered = [v for v in vals.values() if v is not None and ((0 <= v <= 500) or (700 <= v <= 1100))]
            void_vals_entered = [v for v in vals.values() if v is not None and (3000 <= v <= 100000)]
            unknown_vals_entered = [v for v in vals.values() if v is not None and ((500 < v < 700) or (1100 < v < 3000))]
            min_d = self.min_diameter
            max_d = self.max_diameter
            if max_d < min_d:
                max_d = min_d
            d = self.clamp(min(self.width_val, self.length_val) * 0.20, min_d, max_d)
            d1 = vals.get("p1p4")
            d2 = vals.get("p2p3")
            sides = [vals.get(k) for k in self.side_keys if self.is_value_in_main_range(vals.get(k))]
            diagonals_are_largest = False
            if (d1 is not None and self.is_value_in_main_range(d1) and d2 is not None and self.is_value_in_main_range(d2) and len(sides) == 4):
                if d1 > max(sides) and d2 > max(sides):
                    diagonals_are_largest = True
            if low_vals_entered:
                candidates_low = self.detect_low_res_zones_multi(value_grid, nx, ny)
                low_spots = [c for c in candidates_low if (0 <= c["target_value"] <= 600) or (650 <= c["target_value"] <= 1300)]
                low_spots = low_spots[:2]
                if not low_spots:
                    entered_low_val = min(low_vals_entered)
                    cx, cy = min_xr, min_yr
                    cx, cy = self.shift_towards_nearest_line(cx, cy, d)
                    label, fill_color, text_color = self.classify_target(entered_low_val, 600.0)
                    self.detected_circles.append({
                        "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": d, "target_value": entered_low_val,
                        "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "fallback"
                    })
                else:
                    for spot in low_spots:
                        cx, cy = spot["center_x_ratio"], spot["center_y_ratio"]
                        cx, cy = self.shift_towards_nearest_line(cx, cy, spot["diameter_m"])
                        spot_d = spot["diameter_m"]
                        label, fill_color, text_color = self.classify_target(spot["target_value"], 600.0)
                        self.detected_circles.append({
                            "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": spot_d, "target_value": spot["target_value"],
                            "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "cluster"
                        })
            if void_vals_entered:
                if diagonals_are_largest:
                    if d1 >= d2:
                        s_p1 = (vals.get("p1p2") or 0.0) + (vals.get("p3p1") or 0.0)
                        s_p4 = (vals.get("p2p4") or 0.0) + (vals.get("p4p3") or 0.0)
                        if s_p4 >= s_p1:
                            if (vals.get("p4p3") or 0.0) >= (vals.get("p2p4") or 0.0):
                                inside_triangle = lambda x, y: (y >= x and y >= 1.0 - x)
                            else:
                                inside_triangle = lambda x, y: (y < x and y >= 1.0 - x)
                        else:
                            if (vals.get("p1p2") or 0.0) >= (vals.get("p3p1") or 0.0):
                                inside_triangle = lambda x, y: (y < x and y < 1.0 - x)
                            else:
                                inside_triangle = lambda x, y: (y >= x and y < 1.0 - x)
                    else:
                        s_p2 = (vals.get("p1p2") or 0.0) + (vals.get("p2p4") or 0.0)
                        s_p3 = (vals.get("p3p1") or 0.0) + (vals.get("p4p3") or 0.0)
                        if s_p3 >= s_p2:
                            if (vals.get("p4p3") or 0.0) >= (vals.get("p3p1") or 0.0):
                                inside_triangle = lambda x, y: (y >= x and y >= 1.0 - x)
                            else:
                                inside_triangle = lambda x, y: (y >= x and y < 1.0 - x)
                        else:
                            if (vals.get("p1p2") or 0.0) >= (vals.get("p2p4") or 0.0):
                                inside_triangle = lambda x, y: (y < x and y < 1.0 - x)
                            else:
                                inside_triangle = lambda x, y: (y < x and y >= 1.0 - x)
                    max_val_tri = float('-inf')
                    best_i, best_j = 0, 0
                    for j in range(ny):
                        y = j / (ny - 1) if ny > 1 else 0.5
                        for i in range(nx):
                            x = i / (nx - 1) if nx > 1 else 0.5
                            if inside_triangle(x, y):
                                grid_val = value_grid[j][i]
                                if grid_val > max_val_tri:
                                    max_val_tri = grid_val
                                    best_i, best_j = i, j
                    cx = best_i / (nx - 1) if nx > 1 else 0.5
                    cy = best_j / (ny - 1) if ny > 1 else 0.5
                    d_size = self.clamp(min(self.width_val, self.length_val) * 0.20, min_d, max_d)
                    radius_ratio = (d_size / 2.0) / max(min(self.width_val, self.length_val), 1e-9)
                    cx, cy = self.repel_circle_from_edges(cx, cy, radius_ratio)
                    label, fill_color, text_color = self.classify_target(max_val_tri, 600.0)
                    self.detected_circles.append({
                        "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": d_size, "target_value": max_val_tri,
                        "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "special_void_triangle"
                    })
                else:
                    candidates_high = self.detect_high_res_zones_multi(value_grid, nx, ny)
                    void_spots = [c for c in candidates_high if 3000 <= c["target_value"] <= 100000]
                    if void_spots:
                        spot = void_spots[0]
                        cx, cy = self.move_void_toward_largest_edge(spot["center_x_ratio"], spot["center_y_ratio"], vals, self.void_pull)
                        cx, cy = self.shift_towards_nearest_line(cx, cy, spot["diameter_m"])
                        self.detected_circles.append({
                            "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": spot["diameter_m"], "target_value": spot["target_value"],
                            "label": spot["label"], "fill_color": spot["fill_color"], "text_color": spot["text_color"], "source_type": "cluster"
                        })
                    else:
                        entered_void_val = max(void_vals_entered)
                        cx, cy = self.move_void_toward_largest_edge(max_xr, max_yr, vals, self.void_pull)
                        cx, cy = self.shift_towards_nearest_line(cx, cy, d)
                        label, fill_color, text_color = self.classify_target(entered_void_val, 600.0)
                        self.detected_circles.append({
                            "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": d, "target_value": entered_void_val,
                            "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "fallback"
                        })
            if unknown_vals_entered and not low_vals_entered and not void_vals_entered:
                entered_unk_val = unknown_vals_entered[0]
                cx, cy = min_xr, min_yr
                cx, cy = self.shift_towards_nearest_line(cx, cy, d)
                label, fill_color, text_color = self.classify_target(entered_unk_val, 600.0)
                self.detected_circles.append({
                    "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": d, "target_value": entered_unk_val,
                    "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "fallback"
                })
        if self.heatmap_data and self.detected_circles:
            for circ in self.detected_circles:
                if circ.get("source_type") == "special_void_triangle":
                    continue
                orig_val = circ["target_value"]
                orig_label = circ["label"]
                closest_val = self.get_closest_matching_input_value(circ["center_x_ratio"], circ["center_y_ratio"], vals, orig_label, orig_val)
                if closest_val is not None:
                    target_val = closest_val
                else:
                    r_ratio = (circ["diameter_m"] / 2.0) / max(self.width_val, 1e-9)
                    if orig_val >= 3000:
                        target_val = self.get_max_value_in_circle(circ["center_x_ratio"], circ["center_y_ratio"], r_ratio)
                    else:
                        target_val = self.get_min_value_in_circle(circ["center_x_ratio"], circ["center_y_ratio"], r_ratio)
                circ["target_value"] = target_val
                label, fill_color, text_color = self.classify_target(target_val, 600.0)
                circ["label"] = label
                circ["fill_color"] = fill_color
                circ["text_color"] = text_color

        if self.active_mode == "4-prop":
            if self.width_val <= 4.0 and self.length_val <= 4.0:
                all_entries = [vals.get(k) for k in self.edge_keys if vals.get(k) is not None]
                if len(all_entries) == 6:
                    for sk in self.side_keys:
                        v_side = vals.get(sk)
                        if v_side is not None and v_side <= 500:
                            other_vals = [vals.get(k) for k in self.edge_keys if k != sk and vals.get(k) is not None]
                            if all((v_other - v_side) > 150 for v_other in other_vals):
                                _, fill_hex, _ = self.classify_target(v_side, 600.0)
                                try:
                                    arrow_color = self.hex_to_rgb(fill_hex) + (255,)
                                except Exception:
                                    arrow_color = (255, 0, 0, 255)
                                self.warning_arrows.append(self.build_warning_arrow_for_edge(sk, arrow_color))

        if self.width_val <= 3.0 and self.length_val <= 3.0:
            if self.detected_circles:
                metals_water = [c for c in self.detected_circles if c.get("target_value", 0) < 3000]
                voids = [c for c in self.detected_circles if c.get("target_value", 0) >= 3000]
                best_metal = None
                best_void = None
                if metals_water:
                    best_metal = min(metals_water, key=lambda x: x.get("target_value", 999999))
                if voids:
                    best_void = max(voids, key=lambda x: x.get("target_value", -999999))
                if best_metal and best_void:
                    ref = getattr(self, 'ref_soil_val', 600.0)
                    contrast_metal = abs(best_metal.get("target_value", 0) - 600.0) / 600.0
                    contrast_void = abs(best_void.get("target_value", 0) - 600.0) / 600.0
                    if contrast_metal >= contrast_void:
                        self.detected_circles = [best_metal]
                    else:
                        self.detected_circles = [best_void]
                elif best_metal:
                    self.detected_circles = [best_metal]
                elif best_void:
                    self.detected_circles = [best_void]
        self.detected_circles = self.filter_circles_for_display(self.detected_circles, vals)
        self.refine_target_positions(0)
        Clock.schedule_once(self.refine_target_positions, 0.0002)

    def update_plus_minus_labels(self):
        pass


if __name__ == '__main__':
    import traceback
    try:
        MainApp().run()
    except Exception as e:
        crash_msg = traceback.format_exc()
        print("CRASH LOG:\n", crash_msg)
        try:
            with open("/sdcard/cornix_crash_log.txt", "w", encoding="utf-8") as f:
                f.write(crash_msg)
        except Exception:
            pass