# ────────────────────────────────────────────────
# opt4048_gui.py
# ────────────────────────────────────────────────
import sys
import serial
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QSizePolicy, QTabWidget, QInputDialog
)
from PySide6.QtCore import QThread, Signal, Qt, QTimer
import pyqtgraph as pg
import serial.tools.list_ports

# ────────────────────────────────────────────────

MAX_POINTS = 100

def get_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "USB Serial" in port.description or "CH340" in port.description:
            print(f"Arduino gefunden auf {port.device}")
            return port.device
    return None




app = QApplication(sys.argv)

SERIAL_PORT = get_arduino_port()
if SERIAL_PORT is None:
    SERIAL_PORT, ok = QInputDialog.getText(
        None,
        "COM-Port eingeben", ### muss ich noch ändern damit ohne eingabe auch geht. also automatisch erkennnen 
        "Kein Arduino erkannt. Gib den COM-Port ein (z.B. COM14):"
    )
    if not ok or not SERIAL_PORT.strip():
        sys.exit(1)

BAUD_RATE = 115200 # 9600  - 115200

class SerialThread(QThread):
    data_received = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._running = True
        self.ser = None
    
    def run(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"Verbunden mit {SERIAL_PORT}")
        except serial.SerialException as e:
            print("Serial Error:", e)
            return
        
        while self._running:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    self.data_received.emit(line)
            except Exception:
                pass  
        
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def stop(self):
        self._running = False
    
    def send_mode(self, mode):
        if self.ser and self.ser.is_open:
            self.ser.write(mode.encode())
            self.ser.flush()

class ValueCard(QFrame):
    def __init__(self, title, color):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setAlignment(Qt.AlignCenter)
        
        self.value_label = QLabel("0")
        self.value_label.setObjectName("cardValue")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(f"color: {color};")
        
        layout = QVBoxLayout(self)
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()  
    
    def set_value(self, value):
        self.value_label.setText(str(value))

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OPT 4048 Monitor")
        self.resize(1200, 700)
        
        self.tab_widget = QTabWidget()
        
        # RGB Tab
        tab_rgb = QWidget()
        layout_rgb = QVBoxLayout(tab_rgb)
        
        self.r_card = ValueCard("RED", "#ff4c4c")
        self.g_card = ValueCard("GREEN", "#4cff4c")
        self.b_card = ValueCard("BLUE", "#4c7bff")
        
        cards_layout = QHBoxLayout()
        cards_layout.addWidget(self.r_card)
        cards_layout.addWidget(self.g_card)
        cards_layout.addWidget(self.b_card)
        cards_layout.setSpacing(30)
        layout_rgb.addLayout(cards_layout)
        layout_rgb.addSpacing(20)
        
        self.color_frame = QFrame()
        self.color_frame.setFixedHeight(100)
        self.color_frame.setStyleSheet("background-color: black; border-radius: 12px;")
        layout_rgb.addWidget(self.color_frame)
        layout_rgb.addSpacing(20)
        
        self.plot = pg.PlotWidget(background="#121212")
        self.plot.setYRange(0, 255)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.addLegend()
        self.plot.setLabel('left', 'Wert (0-255)')
        self.plot.setLabel('bottom', 'Messungen')
        
        self.r_curve = self.plot.plot(pen=pg.mkPen("#ff4c4c", width=3), name="Rot")
        self.g_curve = self.plot.plot(pen=pg.mkPen("#4cff4c", width=3), name="Grün")
        self.b_curve = self.plot.plot(pen=pg.mkPen("#4c7bff", width=3), name="Blau")
        
        layout_rgb.addWidget(self.plot, stretch=1)
        self.tab_widget.addTab(tab_rgb, "RGB")
        
        # Lux Tab
        tab_lux = QWidget()
        layout_lux = QVBoxLayout(tab_lux)
        
        self.lux_card = ValueCard("LUX", "#ffffff")
        
        lux_cards_layout = QHBoxLayout()
        lux_cards_layout.addStretch()
        lux_cards_layout.addWidget(self.lux_card)
        lux_cards_layout.addStretch()
        layout_lux.addLayout(lux_cards_layout)
        layout_lux.addSpacing(20)
        
        self.lux_plot = pg.PlotWidget(background="#121212")
        self.lux_plot.setYRange(0, 10000)
        self.lux_plot.showGrid(x=True, y=True, alpha=0.3)
        self.lux_plot.addLegend()
        self.lux_plot.setLabel('left', 'Lux')
        self.lux_plot.setLabel('bottom', 'Messungen')
        
        self.lux_curve = self.lux_plot.plot(pen=pg.mkPen("#ffffff", width=3), name="Lux")
        
        layout_lux.addWidget(self.lux_plot, stretch=1)
        self.tab_widget.addTab(tab_lux, "Lux")
        
        # CIE Tab
        tab_cie = QWidget()
        layout_cie = QVBoxLayout(tab_cie)
        
        self.x_card = ValueCard("x", "#ffaa00")
        self.y_card = ValueCard("y", "#00aaff")
        self.cct_card = ValueCard("CCT (K)", "#ffdd00")
        
        cie_cards_layout = QHBoxLayout()
        cie_cards_layout.addWidget(self.x_card)
        cie_cards_layout.addWidget(self.y_card)
        cie_cards_layout.addWidget(self.cct_card)
        cie_cards_layout.setSpacing(30)
        layout_cie.addLayout(cie_cards_layout)
        layout_cie.addSpacing(20)
        
        self.cie_plot = pg.PlotWidget(background="#121212")
        self.cie_plot.setXRange(0, 0.8)
        self.cie_plot.setYRange(0, 0.9)
        self.cie_plot.setAspectLocked(True)
        self.cie_plot.showGrid(x=True, y=True, alpha=0.3)
        self.cie_plot.setLabel('left', 'y')
        self.cie_plot.setLabel('bottom', 'x')
        self.cie_plot.setTitle("CIE 1931 Chromaticity Diagram")
        
        locus_x = [0.1741,0.1738,0.1733,0.1726,0.1714,0.1689,0.1644,0.1566,0.1440,0.1241,
                   0.0913,0.0455,0.0082,0.0139,0.0743,0.1547,0.2296,0.3016,0.3731,0.4441,
                   0.5125,0.5752,0.6270,0.6658,0.6915,0.7079,0.7190,0.7260,0.7303,0.7333,
                   0.7354,0.7369,0.7380,0.7389,0.7395,0.7400,0.7404,0.7407,0.7409,0.7411,0.7413]
        locus_y = [0.0050,0.0049,0.0048,0.0048,0.0051,0.0069,0.0109,0.0177,0.0297,0.0578,
                   0.1327,0.2950,0.5384,0.7502,0.8338,0.8059,0.7543,0.6923,0.6245,0.5547,
                   0.4866,0.4242,0.3725,0.3340,0.3083,0.2921,0.2810,0.2740,0.2697,0.2667,
                   0.2646,0.2631,0.2620,0.2611,0.2605,0.2600,0.2596,0.2593,0.2591,0.2589,0.2587]
        self.cie_plot.plot(locus_x, locus_y, pen=pg.mkPen('cyan', width=2))
        self.cie_plot.plot([locus_x[0], locus_x[-1]], [locus_y[0], locus_y[-1]], pen=pg.mkPen('magenta', width=2))
        
        planck_x = [0.5609411935680847, 0.5495540027434842, 0.5381364624580842, 0.5269025875, 0.5159816991685563, 0.5054484320060105, 0.495341935070272, 0.485678330150463, 0.4764588864, 0.46767543104233045, 0.4593139523446629, 0.45135700637755105, 0.4437853243675427, 0.4365788814814815, 0.42971760048336743, 0.42318180676269535, 0.416952513676712, 0.411011592102585, 0.4053418612244898, 0.39992712611454045, 0.3947521798116597, 0.3898027821839918, 0.38506562410020395, 0.38052828281249995, 0.37613233973680005, 0.37200359988122234, 0.3680634334461117, 0.3643020920830203, 0.36071017914951986, 0.35727869166598175, 0.35399904378605895, 0.35086307678674766, 0.34786305932902106, 0.3449916808, 0.3422420398413883, 0.33960762963700497, 0.3370823211308664, 0.33466034504394654, 0.33233627332832455, 0.33010500052387026, 0.3279617253513902, 0.3259019327770716, 0.32392137670842686, 0.3220160634259259, 0.3201822358126891, 0.3184163584136148, 0.31671510333257347, 0.31507533695983886, 0.3134941075102412, 0.3119686333444639, 0.31049629204057677, 0.30907461017962545, 0.3077012538073538, 0.3063740195335277, 0.30509082623054334, 0.30384970729381, 0.3026488034276137, 0.30148635592166306, 0.3003607003851852, 0.2992702609072022, 0.2982135446134233, 0.2971891365919857, 0.296195695162046, 0.2952319474609375, 0.29429668532725173, 0.29338876145877163, 0.29250708582566587, 0.29165062232075367, 0.2908183856299613, 0.29000943830731885, 0.28922288803999374, 0.288457885089923, 0.2877136198995984, 0.2869893208504801, 0.28628425216336617, 0.2855977119308375, 0.2849290302726277, 0.28427756760544387, 0.2836427130193906, 0.2830238827537254, 0.28242051876520946, 0.2818320873828082, 0.2812580780429538, 0.2806980021, 0.2801513917068895, 0.2796177987614115, 0.27909679391375886, 0.27858796563140076, 0.2780909193175683, 0.27760527647991295, 0.277130673946139, 0.2766667631236346, 0.2762132093003323, 0.2757696909842224]
        planck_y = [0.4043036207558297, 0.40811649925948823, 0.41111360112489215, 0.41326488475771883, 0.4146068353946314, 0.41520938803625207, 0.41521613774003885, 0.414694671379217, 0.41371563614631013, 0.4123496958785189, 0.41066024937841794, 0.40870320019401596, 0.40652725547321833, 0.4041744895645527, 0.40168101688773217, 0.3990776851656569, 0.3963907405041974, 0.3936424400405525, 0.39085160216636283, 0.38803409251885246, 0.38520324840843256, 0.3823702465921863, 0.3795444202225341, 0.3767335309611144, 0.3739571304994823, 0.37127050391370453, 0.36862921576443286, 0.3660362522712848, 0.3634939308089278, 0.3610039886634774, 0.3585676625031755, 0.3561857590886318, 0.3538587178541486, 0.3515866660417546, 0.3493694670805447, 0.34720676288850993, 0.3450980107417081, 0.34304251531316854, 0.3410394564362569, 0.3390879130976743, 0.33718688411618225, 0.33533530591595095, 0.3335320677590653, 0.33177602476068535, 0.3300660089728513, 0.3284008387889532, 0.326779326890385, 0.32520028692964054, 0.32366253911989207, 0.3221649148796364, 0.3207062606620791, 0.31928544108226753, 0.3179013414403554, 0.31655286972657704, 0.3152389581822732, 0.31395856448152937, 0.3127106725894159, 0.3114942933453607, 0.310308464813683, 0.30915225243765354, 0.3080247490285112, 0.30692507461658847, 0.30585237618795846, 0.30480582732678796, 0.3037846277807573, 0.3027880029644684, 0.30181520341363943, 0.3008655042010465, 0.29993820432357443, 0.29903262606835157, 0.29814811436475674, 0.2972840361280339, 0.29643977959936385, 0.29561475368645895, 0.29480838730808057, 0.2940201287452987, 0.2932494450018114, 0.292495821175219, 0.29175875984077215, 0.29103778044879913, 0.29033241873674676, 0.2896422261565358, 0.28896676931773335, 0.2883056294468803, 0.2876584018631648, 0.2870246954705161, 0.2864041322660894, 0.28579634686503197, 0.2852009860413459, 0.2846177082846112, 0.2840461833722798, 0.2834860919572213, 0.2829371251701619, 0.28239898423664667]
        self.cie_plot.plot(planck_x, planck_y, pen=pg.mkPen('yellow', width=3))
        
        cct_labels = ["2000K", "3000K", "4000K", "5000K", "6000K", "7000K", "8000K", "9000K", "10000K", "11000K"]
        label_indices = [3, 13, 23, 33, 43, 53, 63, 73, 83, 93]
        
        for j, idx in enumerate(label_indices):
            text = pg.TextItem(text=cct_labels[j], color='white', anchor=(0.5, 1.2))
            text.setPos(planck_x[idx], planck_y[idx])
            self.cie_plot.addItem(text)
        
        self.cie_point = pg.ScatterPlotItem(size=14, brush=pg.mkBrush('red'), pen=pg.mkPen('white', width=2))
        self.cie_plot.addItem(self.cie_point)
        
        layout_cie.addWidget(self.cie_plot, stretch=1)
        self.tab_widget.addTab(tab_cie, "CIE 1931")
        
        # CCT-Skala Tab
        tab_cct = QWidget()
        layout_cct = QVBoxLayout(tab_cct)
        
        title_label = QLabel("Farbtemperatur-Skala (CCT in Kelvin)")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; color: #ffffff; margin: 20px;")
        layout_cct.addWidget(title_label)
        
        self.scale_container = QWidget()
        self.scale_container.setContentsMargins(50, 20, 50, 40)
        scale_container_layout = QVBoxLayout(self.scale_container)
        scale_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.gradient_frame = QFrame()
        self.gradient_frame.setMinimumHeight(50)
        self.gradient_frame.setMinimumWidth(800)
        self.gradient_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gradient_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:0.1 #ff4500, stop:0.2 #ff8c00, stop:0.3 #ffd700,
                    stop:0.4 #fffff0, stop:0.5 #ffffff, stop:0.6 #f0f8ff,
                    stop:0.7 #add8e6, stop:0.8 #87cefa, stop:0.9 #4682b4, stop:1.0 #4169e1);
                border-radius: 25px;
                border: 3px solid #666666;
            }
        """)
        scale_container_layout.addWidget(self.gradient_frame, alignment=Qt.AlignCenter)
        
        layout_cct.addWidget(self.scale_container, alignment=Qt.AlignCenter)
        
        self.indicator = QLabel("|", self.scale_container)
        self.indicator.setStyleSheet("color: gold; font-size: 50px; background: transparent; font-weight: bold;")
        self.indicator.raise_()
        self.indicator.hide()
        
        self.current_cct_card = ValueCard("Aktuelle CCT", "#ffdd00")
        self.current_cct_card.value_label.setStyleSheet("font-size: 60px; color: #ffdd00;")
        layout_cct.addWidget(self.current_cct_card)
        layout_cct.addStretch()
        
        self.tab_widget.addTab(tab_cct, "CCT Skala")
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)
        
        self.r_vals = []
        self.g_vals = []
        self.b_vals = []
        self.lux_vals = []
        
        self.thread = SerialThread()
        self.thread.data_received.connect(self.update_ui)
        self.serial_worker = self.thread
        self.thread.start()
        
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        QTimer.singleShot(1000, lambda: self.on_tab_changed(self.tab_widget.currentIndex()))
        
        self.setStyleSheet(self.dark_style())
        
        self.current_cct = None
        self.min_cct = 1000
        self.max_cct = 11000
    
    def on_tab_changed(self, index):
        worker = self.serial_worker
        if index == 0:
            worker.send_mode("MODE:RGB\n")
        elif index == 1:
            worker.send_mode("MODE:LUX\n")
        else:
            worker.send_mode("MODE:CIE\n")
    
    def update_ui(self, line):
        try:
            line = line.strip()
            if line.startswith("RGB:"):
                parts = line[4:].split(",")
                if len(parts) == 3:
                    r, g, b = map(int, parts)
                    self.r_card.set_value(r)
                    self.g_card.set_value(g)
                    self.b_card.set_value(b)
                    self.color_frame.setStyleSheet(f"background-color: rgb({r},{g},{b}); border-radius: 12px;")
                    self.r_vals.append(r)
                    self.g_vals.append(g)
                    self.b_vals.append(b)
                    if len(self.r_vals) > MAX_POINTS:
                        self.r_vals.pop(0)
                        self.g_vals.pop(0)
                        self.b_vals.pop(0)
                    x = np.arange(len(self.r_vals))
                    self.r_curve.setData(x, self.r_vals)
                    self.g_curve.setData(x, self.g_vals)
                    self.b_curve.setData(x, self.b_vals)
            elif line.startswith("LUX:"):
                lux = float(line[4:])
                self.lux_card.set_value(f"{lux:.2f}")
                self.lux_vals.append(lux)
                if len(self.lux_vals) > MAX_POINTS:
                    self.lux_vals.pop(0)
                x = np.arange(len(self.lux_vals))
                self.lux_curve.setData(x, self.lux_vals)
            elif line.startswith("CIE:"):
                parts = line[4:].split(",")
                if len(parts) == 3:
                    x_val, y_val, cct = map(float, parts)
                    self.x_card.set_value(f"{x_val:.4f}")
                    self.y_card.set_value(f"{y_val:.4f}")
                    self.cct_card.set_value(f"{cct:.0f} K")
                    self.cie_point.setData([x_val], [y_val])
                    self.current_cct_card.set_value(f"{int(cct)} K")
                    self.current_cct = cct
                    self.update_indicator_position()
        except Exception as e:
            print("Parse error:", e)
    
    def update_indicator_position(self):
        if self.current_cct is None or not self.gradient_frame.isVisible():
            self.indicator.hide()
            return
        
        cct = max(self.min_cct, min(self.max_cct, self.current_cct))
        ratio = (cct - self.min_cct) / (self.max_cct - self.min_cct)
        
        gradient_width = self.gradient_frame.width()
        if gradient_width <= 0:
            return
        
        pos_x = int(ratio * gradient_width)
        arrow_width = self.indicator.sizeHint().width()
        final_x = pos_x - arrow_width // 2
        
        y_pos = self.gradient_frame.height() + 10
        
        self.indicator.move(final_x, y_pos)
        self.indicator.show()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_indicator_position()
        self.gradient_frame.updateGeometry()
        
    def closeEvent(self, event):
        self.serial_worker.stop()
        self.serial_worker.wait()
        event.accept()
    
    def dark_style(self):
        return """
        QWidget { background-color: #121212; color: #e0e0e0; font-family: "Segoe UI", Arial, sans-serif; }
        QFrame#card { background-color: #1e1e1e; border-radius: 16px; padding: 20px; margin: 10px; }
        QLabel#cardTitle { font-size: 16px; color: #aaaaaa; background-color: transparent; }
        QLabel#cardValue { font-size: 48px; font-weight: bold; background-color: transparent; }
        """

if __name__ == "__main__":
    window = MainWindow()
    window.show()
    sys.exit(app.exec())