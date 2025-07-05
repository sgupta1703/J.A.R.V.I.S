import sys
import threading
import time
import datetime
import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QMessageBox
)

import jarvis_chat 


class JarvisApp(QWidget):

    text_signal = pyqtSignal(str)

    def __init__(self):

        super().__init__()

        self.setWindowTitle("JARVIS")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet("background:#111; color:cyan;")

        layout = QVBoxLayout(self)

        self.full_title_text = "J.A.R.V.I.S"
        self.title_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont("Orbitron", 26, QFont.Weight.Bold))
        self.title_label.setStyleSheet("margin-bottom:10px; background:transparent;")
        layout.addWidget(self.title_label)

        self.title_anim_timer = QTimer()
        self.title_anim_timer.timeout.connect(self.update_title_animation)
        self.title_anim_index = 0
        self.title_fade_values = [0.0] * len(self.full_title_text)
        self.title_anim_timer.start(200)

        self.text = QTextEdit(readOnly=True)
        self.text.setFont(QFont("Consolas", 12))
        self.text.setStyleSheet("background:#222; border:none; color:#eee; padding:5px;")
        layout.addWidget(self.text, stretch=3)

        self.text_signal.connect(lambda msg: self.text.append(msg))

        pg.setConfigOptions(useOpenGL=True, antialias=True)
        self.plot = pg.PlotWidget(background="#111")
        self.plot.hideAxis("bottom")
        self.plot.hideAxis("left")
        layout.addWidget(self.plot, stretch=2)

        self.n = 40
        self.xs = np.arange(self.n)
        self.taper = np.hanning(self.n)
        self.curr = np.zeros(self.n)
        self.target = np.zeros(self.n)
        self.speaking = False
        self.last_silence = None
        self.opacity = 1.0

        self.bars_top = []
        self.bars_bot = []
        for x in self.xs:
            r1 = pg.QtWidgets.QGraphicsRectItem(x - 0.4, 0, 0.8, 0)
            r2 = pg.QtWidgets.QGraphicsRectItem(x - 0.4, 0, 0.8, 0)
            r1.setPen(pg.mkPen(None))
            r2.setPen(pg.mkPen(None))
            self.plot.addItem(r1)
            self.plot.addItem(r2)
            self.bars_top.append(r1)
            self.bars_bot.append(r2)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_bars)
        self.timer.start(16)

        threading.Thread(
            target=jarvis_chat.run_jarvis,
            kwargs={
                "display_callback": self.show_text,
                "visualizer_callback": self.speaking_callback,
            },
            daemon=True,
        ).start()

        QTimer.singleShot(2000, self.show_greeting)

    def update_title_animation(self):

        text = self.full_title_text
        length = len(text)

        left = self.title_anim_index
        right = length - 1 - self.title_anim_index

        if left <= right:
            if left < length:
                self.title_fade_values[left] = min(1.0, self.title_fade_values[left] + 0.2)
            if right >= 0 and right != left:
                self.title_fade_values[right] = min(1.0, self.title_fade_values[right] + 0.2)

        visible_text = ""
        for i, ch in enumerate(text):
            opacity = self.title_fade_values[i]
            if opacity <= 0.0:
                visible_text += "<span style='color:transparent;'>%s</span>" % ch
            else:
                min_alpha = 50  
                adjusted_opacity = opacity ** 0.5
                alpha = int(min_alpha + adjusted_opacity * (255 - min_alpha))
                visible_text += f"<span style='color:rgba(0,130,255,{alpha});'>{ch}</span>"

        self.title_label.setText(f"<span style='letter-spacing:2px;'>{visible_text}</span>")

        if self.title_anim_index >= (length // 2):
            if all(v >= 1.0 for v in self.title_fade_values):
                self.title_anim_timer.stop()

        self.title_anim_index += 1

    def show_text(self, msg: str):


        html = f"<b style='color:#0ff;'>JARVIS:</b> {msg}"
        self.text_signal.emit(html)

    def show_greeting(self):

        now = datetime.datetime.now()
        hour = now.hour
        if 5 <= hour < 12:
            greet = "Good morning"
        elif 12 <= hour < 17:
            greet = "Good afternoon"
        elif 17 <= hour < 21:
            greet = "Good evening"
        else:
            greet = "Hello"

        message = f"{greet}, sir!"

        threading.Thread(
            target=jarvis_chat.speak,
            args=(message,),
            kwargs={"visualizer_callback": self.speaking_callback},
            daemon=True
        ).start()

    def speaking_callback(self, speaking: bool):

        now = time.time()
        if speaking:
            self.opacity = 1.0
            self.last_silence = None
        else:
            if self.last_silence is None:
                self.last_silence = now
        self.speaking = speaking

    def update_bars(self):
        t = time.time()

        if self.speaking:
            wave = (np.sin(self.xs * 0.3 + t * 10) + 1) * 0.5
            rand = (np.random.rand(self.n) - 0.5) * self.taper
            self.target = (0.6 * wave + 0.4 * rand) * self.taper
            lerp = 0.03
        else:
            self.target[:] = 0.0
            lerp = 0.01

        self.curr += (self.target - self.curr) * lerp

        if not self.speaking and self.last_silence is not None:
            elapsed = t - self.last_silence
            self.opacity = max(0.0, 1.0 - elapsed / 0.75)
            if self.opacity <= 0.0 or np.max(self.curr) < 0.005:
                self.curr[:] = 0.0
                self.target[:] = 0.0

        for i in range(self.n):
            h = self.curr[i]
            color = self.get_color_from_height(h)
            color.setAlphaF(self.opacity)
            brush = QBrush(color)

            self.bars_top[i].setBrush(brush)
            self.bars_top[i].setRect(i - 0.4, 0, 0.8, h)
            self.bars_bot[i].setBrush(brush)
            self.bars_bot[i].setRect(i - 0.4, -h, 0.8, h)

    def get_color_from_height(self, h: float) -> QColor:
        base = min(1.0, max(0.0, h))
        if base < 0.5:
            t = base / 0.5
            r = 0
            g = int(255 * t)
            b = 255
        else:
            t = (base - 0.5) / 0.5
            r = int(255 * t)
            g = 255
            b = 255
        return QColor(r, g, b)

    def closeEvent(self, event):
        try:
            pg.exit()
        except Exception:
            pass
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    win = JarvisApp()
    win.show()

    try:
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Application crashed: {e}")
        raise


if __name__ == "__main__":
    main()
