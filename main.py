from functools import partial
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
import time
import json
import os.path
from threading import Thread
import requests

Builder.load_file('main.kv')


class Programm(TabbedPanel):
    pass


class CustomBtn(Button):

    def on_press(self):
        self.time = time.time()
        return super().on_press()

    def on_release(self):
        if (time.time() - self.time > 3):
            self.action()
        return super().on_release()

    def pressed(self, action):
        self.action = action


class ItemScroll(BoxLayout):

    def setText(self, name, ip):
        self.ids.nameDevice.text = name
        self.ids.ipDevice.text = ip
        self.ip = ip

    def setStatusDevice(self, status):
        self.status = status

    def getIP(self):
        return self.ip

    def getStatus(self):
        return self.status


class MyApp(App):

    def run(self, settings):
        self.settings = settings
        return super().run()

    def on_start(self):
        self.count = 0
        self.devices = []
        for item in self.settings['devices']:
            widget = ItemScroll()
            widget.setText(item[0], item[1])
            widget.ids.rmvbtn.pressed(partial(self.remove_btn, widget))
            widget.ids.btn.bind(on_press=partial(self.getRequest, widget))
            self.root.ids.box.add_widget(widget)
            self.devices.append([item[0], item[1], widget, 0])
        Thread(target=self.getHandler, args=()).start()
        return super().on_start()

    def getRequest(self, widget, *args):
        if widget.getStatus() == 1:
            res = requests.get('http://' + widget.getIP() + '/update?state=0', timeout=0.5)
        else:
            res = requests.get('http://' + widget.getIP() + '/update?state=1', timeout=0.5)

    def on_stop(self):
        self.flag = False
        return super().on_stop()

    def build(self):
        return Programm()

    def getHandler(self):
        self.flag = True
        while (self.flag):
            time.sleep(1)
            for item in self.devices:
                try:
                    res = requests.get('http://' + item[1] + '/state',
                                       timeout=0.1)
                    if res.text == '0':
                        item[2].ids.btn.background_color = (1, 0, 0, 1)
                        item[2].ids.btn.text = 'Off'
                        item[3] = 0
                        item[2].setStatusDevice(item[3])
                    else:
                        item[2].ids.btn.background_color = (0, 1, 0, 1)
                        item[2].ids.btn.text = 'On'
                        item[3] = 1
                        item[2].setStatusDevice(item[3])
                except:
                    item[2].ids.btn.background_color = (0.5, 0.5, 0.5, 1)
                    item[2].ids.btn.text = ''

    def add_new_widget(self):
        if self.checkTextToIP(self.root.ids.inputIPDevice.text
                              ) and self.root.ids.inputNameDevice.text != '':
            vp_height = self.root.ids.scroll.viewport_size[1]
            sv_height = self.root.ids.scroll.height

            name = self.root.ids.inputNameDevice.text
            ip = self.root.ids.inputIPDevice.text
            widget = ItemScroll()
            widget.setText(name, ip)
            widget.ids.rmvbtn.pressed(partial(self.remove_btn, widget))
            self.settings['devices'].append([name, ip])
            self.devices.append([name, ip, widget, 0])
            SaveFile('settings.json', self.settings)
            self.root.ids.box.add_widget(widget)
            self.root.ids.inputIPDevice.text = ''
            self.root.ids.errNotif.text = ''
            self.root.ids.inputNameDevice.text = ''
            self.count += 1

            if vp_height > sv_height:
                scroll = self.root.ids.scroll.scroll_y
                bottom = scroll * (vp_height - sv_height)
                Clock.schedule_once(
                    partial(self.adjust_scroll, bottom + widget.height), -1)

        else:
            self.root.ids.errNotif.text = 'Неверные данные'

    def remove_btn(self, boxLayout, *args):
        for item in self.settings['devices']:
            if item[0] == boxLayout.ids.nameDevice.text and item[
                    1] == boxLayout.ids.ipDevice.text:
                self.settings['devices'].remove(item)
                break
        for item in self.devices:
            if item[0] == boxLayout.ids.nameDevice.text and item[
                    1] == boxLayout.ids.ipDevice.text:
                self.devices.remove(item)
                break
        SaveFile('settings.json', self.settings)
        self.root.ids.box.remove_widget(boxLayout)

    def adjust_scroll(self, bottom, dt):
        vp_height = self.root.ids.scroll.viewport_size[1]
        sv_height = self.root.ids.scroll.height
        self.root.ids.scroll.scroll_y = bottom / (vp_height - sv_height)

    def checkTextToIP(self, text: str):
        ip = text.split('.')
        if len(ip) != 4:
            return False
        for item in ip:
            if not item.isdigit():
                return False
            if not int(item) in range(0, 256):
                return False
        return True


def LoadFile(file):
    if not os.path.exists(file):
        return {}
    data = ""
    with open(file, "r", encoding='utf-8') as file:
        data = json.load(file)
    return data


def SaveFile(file, data):
    with open(file, "w", encoding='utf-8') as writeFile:
        json.dump(data,
                  writeFile,
                  sort_keys=False,
                  indent=4,
                  ensure_ascii=False,
                  separators=(',', ': '))


def LoadSettings():
    settings = LoadFile('settings.json')
    keys = settings.keys()
    if not 'devices' in keys:
        settings['devices'] = []

    SaveFile('settings.json', settings)
    return settings


if __name__ == '__main__':
    settings = LoadSettings()
    MyApp().run(settings)