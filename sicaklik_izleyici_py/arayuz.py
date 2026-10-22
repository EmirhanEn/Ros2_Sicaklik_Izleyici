
import sys
import csv
import time
from collections import deque
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.srv import SetParameters

from std_msgs.msg import Float32

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QDoubleSpinBox, QFileDialog,
    QFrame, QMessageBox
)

import pyqtgraph as pg


class SicaklikArayuzu(Node):

    def __init__(self):
        super().__init__('sicaklik_arayuzu')

        self.subscription = self.create_subscription(
            Float32,
            '/sicaklik',
            self.sicaklik_geldi,
            10
        )

        self.declare_parameter('esik_degeri', 30.0)
        self.esik = 30.0

        self.veriler = deque(maxlen=60)
        self.tum_veriler = []
        self.son_veri_zamani = None
        self.yeni_veri = None

        self.param_client = self.create_client(
            SetParameters,
            '/sicaklik_izleyici/set_parameters'
        )
        self.param_future = None

    def sicaklik_geldi(self, mesaj):
        deger = float(mesaj.data)
        self.yeni_veri = deger
        self.son_veri_zamani = time.monotonic()

        self.veriler.append(deger)
        self.tum_veriler.append((
            datetime.now().isoformat(timespec='seconds'),
            deger
        ))

    def esik_guncelle(self, yeni_esik):
        if not self.param_client.service_is_ready():
            return False

        parametre = Parameter(
            'esik_degeri',
            Parameter.Type.DOUBLE,
            float(yeni_esik)
        )

        istek = SetParameters.Request()
        istek.parameters = [parametre.to_parameter_msg()]

        self.param_future = self.param_client.call_async(istek)
        return True


class SicaklikPenceresi(QWidget):

    def __init__(self, node):
        super().__init__()

        self.node = node
        self.esik = 30.0
        self.son_gosterilen = None

        self.setWindowTitle('ROS 2 | Sicaklik Izleme Merkezi')
        self.resize(1050, 750)
        self.setMinimumSize(800, 600)

        self.arayuz_olustur()

        self.ros_timer = QTimer(self)
        self.ros_timer.timeout.connect(self.ros_isle)
        self.ros_timer.start(50)

        self.grafik_timer = QTimer(self)
        self.grafik_timer.timeout.connect(self.ekrani_guncelle)
        self.grafik_timer.start(200)

    def kart(self, baslik):
        cerceve = QFrame()
        cerceve.setObjectName('kart')

        duzen = QVBoxLayout(cerceve)
        duzen.setSpacing(8)

        etiket = QLabel(baslik)
        etiket.setObjectName('kartBaslik')
        duzen.addWidget(etiket)

        return cerceve, duzen

    def arayuz_olustur(self):

        self.setStyleSheet("""
            QWidget {
                background-color: #0B1220;
                color: #E5E7EB;
                font-family: Ubuntu, Arial;
                font-size: 14px;
            }

            QFrame#kart {
                background-color: #172235;
                border: 1px solid #293548;
                border-radius: 14px;
            }

            QLabel#baslik {
                font-size: 26px;
                font-weight: bold;
            }

            QLabel#kartBaslik {
                color: #94A3B8;
                font-size: 13px;
            }

            QLabel#sicaklik {
                font-size: 55px;
                font-weight: bold;
                color: #22D3EE;
            }

            QLabel#istatistik {
                font-size: 24px;
                font-weight: bold;
            }

            QPushButton {
                background-color: #0891B2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #06B6D4;
            }

            QDoubleSpinBox {
                background-color: #253247;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 8px;
                color: white;
            }
        """)

        ana = QVBoxLayout(self)
        ana.setContentsMargins(25, 25, 25, 25)
        ana.setSpacing(18)

        baslik = QLabel('SICAKLIK IZLEME MERKEZI')
        baslik.setObjectName('baslik')
        ana.addWidget(baslik)

        alt_baslik = QLabel(
            'ROS 2 Humble | Gercek Zamanli Sensor Simulasyonu'
        )
        alt_baslik.setStyleSheet('color: #94A3B8;')
        ana.addWidget(alt_baslik)

        ust = QHBoxLayout()
        ust.setSpacing(15)

        sicaklik_karti, sicaklik_duzen = self.kart(
            'ANLIK SICAKLIK'
        )

        self.sicaklik_label = QLabel('--.- °C')
        self.sicaklik_label.setObjectName('sicaklik')
        sicaklik_duzen.addWidget(self.sicaklik_label)

        self.durum_label = QLabel('Sensor bekleniyor...')
        sicaklik_duzen.addWidget(self.durum_label)

        ust.addWidget(sicaklik_karti, 2)

        esik_karti, esik_duzen = self.kart('UYARI ESIGI')

        self.esik_spin = QDoubleSpinBox()
        self.esik_spin.setRange(0.0, 100.0)
        self.esik_spin.setDecimals(1)
        self.esik_spin.setSuffix(' °C')
        self.esik_spin.setValue(30.0)
        esik_duzen.addWidget(self.esik_spin)

        self.esik_buton = QPushButton('Esigi Guncelle')
        self.esik_buton.clicked.connect(self.esik_degistir)
        esik_duzen.addWidget(self.esik_buton)

        self.esik_bilgi = QLabel('Varsayilan: 30 °C')
        esik_duzen.addWidget(self.esik_bilgi)

        ust.addWidget(esik_karti, 1)

        ana.addLayout(ust)

        grafik_karti, grafik_duzen = self.kart(
            'CANLI SICAKLIK GRAFIGI | SON 60 OLCUM'
        )

        self.grafik = pg.PlotWidget()
        self.grafik.setBackground('#172235')
        self.grafik.showGrid(x=True, y=True, alpha=0.2)
        self.grafik.setLabel('left', 'Sicaklik', units='°C')
        self.grafik.setLabel('bottom', 'Olcum numarasi')
        self.grafik.setYRange(15, 45)

        self.cizgi = self.grafik.plot(
            pen=pg.mkPen('#22D3EE', width=3)
        )

        self.esik_cizgisi = pg.InfiniteLine(
            pos=self.esik,
            angle=0,
            pen=pg.mkPen(
                '#F59E0B',
                width=2,
                style=Qt.DashLine
            )
        )
        self.grafik.addItem(self.esik_cizgisi)

        grafik_duzen.addWidget(self.grafik)
        ana.addWidget(grafik_karti, 3)

        istatistikler = QHBoxLayout()
        istatistikler.setSpacing(15)

        self.min_label = self.istatistik_karti(
            istatistikler, 'MINIMUM'
        )
        self.max_label = self.istatistik_karti(
            istatistikler, 'MAKSIMUM'
        )
        self.ort_label = self.istatistik_karti(
            istatistikler, 'ORTALAMA'
        )

        ana.addLayout(istatistikler)

        alt = QHBoxLayout()

        self.baglanti_label = QLabel(
            '● ROS 2 sensor baglantisi bekleniyor'
        )
        self.baglanti_label.setStyleSheet(
            'color: #F59E0B;'
        )
        alt.addWidget(self.baglanti_label)

        alt.addStretch()

        self.kaydet_buton = QPushButton('CSV Olarak Kaydet')
        self.kaydet_buton.clicked.connect(self.csv_kaydet)
        alt.addWidget(self.kaydet_buton)

        ana.addLayout(alt)

    def istatistik_karti(self, ana_duzen, baslik):
        kart, duzen = self.kart(baslik)

        deger = QLabel('--.- °C')
        deger.setObjectName('istatistik')
        duzen.addWidget(deger)

        ana_duzen.addWidget(kart)
        return deger

    def ros_isle(self):
        rclpy.spin_once(self.node, timeout_sec=0.0)

        future = self.node.param_future

        if future is not None and future.done():
            self.node.param_future = None
            self.esik_buton.setEnabled(True)

            try:
                cevap = future.result()
                basarili = (
                    bool(cevap.results)
                    and all(r.successful for r in cevap.results)
                )

                if basarili:
                    self.esik = self.node.esik
                    self.esik_cizgisi.setValue(self.esik)
                    self.esik_bilgi.setText(
                        f'Aktif esik: {self.esik:.1f} °C'
                    )
                else:
                    self.esik_bilgi.setText(
                        'Esik guncellenemedi'
                    )
            except Exception as hata:
                self.esik_bilgi.setText(
                    f'Parametre hatasi: {hata}'
                )

    def ekrani_guncelle(self):
        node = self.node

        if node.son_veri_zamani is None:
            return

        gecen = time.monotonic() - node.son_veri_zamani

        if gecen > 3.0:
            self.baglanti_label.setText(
                '● Sensor verisi alinmiyor'
            )
            self.baglanti_label.setStyleSheet(
                'color: #EF4444;'
            )
            self.durum_label.setText('Baglanti bekleniyor')
            return

        self.baglanti_label.setText(
            '● ROS 2 sensor baglantisi aktif'
        )
        self.baglanti_label.setStyleSheet(
            'color: #22C55E;'
        )

        if node.yeni_veri is None:
            return

        sicaklik = node.yeni_veri

        if sicaklik == self.son_gosterilen:
            return

        self.son_gosterilen = sicaklik

        self.sicaklik_label.setText(
            f'{sicaklik:.2f} °C'
        )

        if sicaklik > self.esik:
            self.sicaklik_label.setStyleSheet(
                'color: #EF4444;'
            )
            self.durum_label.setText(
                'UYARI! Yuksek sicaklik'
            )
            self.durum_label.setStyleSheet(
                'color: #F87171;'
            )
        else:
            self.sicaklik_label.setStyleSheet(
                'color: #22D3EE;'
            )
            self.durum_label.setText(
                'Sicaklik normal seviyede'
            )
            self.durum_label.setStyleSheet(
                'color: #22C55E;'
            )

        veriler = list(node.veriler)

        self.cizgi.setData(
            list(range(len(veriler))),
            veriler
        )

        self.min_label.setText(
            f'{min(veriler):.2f} °C'
        )
        self.max_label.setText(
            f'{max(veriler):.2f} °C'
        )
        self.ort_label.setText(
            f'{sum(veriler) / len(veriler):.2f} °C'
        )

    def esik_degistir(self):
        yeni_esik = self.esik_spin.value()

        if self.node.param_future is not None:
            return

        self.node.esik = yeni_esik

        if self.node.esik_guncelle(yeni_esik):
            self.esik_buton.setEnabled(False)
            self.esik_bilgi.setText('Esik guncelleniyor...')
        else:
            self.esik_bilgi.setText(
                'Izleyici servisi bulunamadi'
            )

    def csv_kaydet(self):
        if not self.node.tum_veriler:
            QMessageBox.information(
                self,
                'Bilgi',
                'Henuz kaydedilecek veri yok.'
            )
            return

        dosya, _ = QFileDialog.getSaveFileName(
            self,
            'Sicaklik Verilerini Kaydet',
            'sicaklik_kayitlari.csv',
            'CSV Dosyalari (*.csv)'
        )

        if not dosya:
            return

        try:
            with open(
                dosya, 'w', newline='', encoding='utf-8'
            ) as f:
                yazici = csv.writer(f)
                yazici.writerow(['Tarih', 'Sicaklik_C'])
                yazici.writerows(self.node.tum_veriler)

            QMessageBox.information(
                self, 'Basarili', 'CSV dosyasi kaydedildi.'
            )
        except OSError as hata:
            QMessageBox.critical(
                self, 'Kayit Hatasi', str(hata)
            )


def main(args=None):
    rclpy.init(args=args)

    node = SicaklikArayuzu()
    app = QApplication(sys.argv)

    pencere = SicaklikPenceresi(node)
    pencere.show()

    try:
        app.exec_()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
