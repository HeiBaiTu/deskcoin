import sys
import requests
from PyQt5 import QtWidgets, QtCore, QtGui
import configparser


class DraggableWidget(QtWidgets.QWidget):
    def __init__(self, coin_list):
        super().__init__()
        self.oldPos = None
        self.coin_labels = None
        self.coin_list = coin_list
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Crypto Price Ticker')
        self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.2)
        self.resize(300, 300) 

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(5, 5, 5, 5)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(240, 240, 240, 255);
                color: black;
                font-size: 10pt;
                border-radius: 10px;
            }
            QLabel {
                color: black;
            }
        """)

        content_layout = QtWidgets.QVBoxLayout()
        scroll_widget = QtWidgets.QWidget()
        scroll_widget.setLayout(content_layout)
        scroll_area.setWidget(scroll_widget)

        self.coin_labels = [] 
        for coin in self.coin_list:
            coin_layout = QtWidgets.QHBoxLayout()
            coin_layout.setSpacing(1)
            name_label = QtWidgets.QLabel(coin['name'])
            price_label = QtWidgets.QLabel(coin['price'])
            change_label = QtWidgets.QLabel(coin['change'])
            coin_layout.addWidget(name_label)
            coin_layout.addWidget(price_label)
            coin_layout.addWidget(change_label)
            content_layout.addLayout(coin_layout)
            self.coin_labels.append((name_label, price_label, change_label))

        self.oldPos = self.pos()

    def quit(self):
        QtWidgets.QApplication.quit()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            delta = QtCore.QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def updateCoinList(self, config):

        new_coin_list = query_coin_price_list(config)
        self.coin_list.clear()
        try:
            for coin_info in new_coin_list:
                self.coin_list.append(coin_info) 
            for i, coin_info in enumerate(self.coin_list):
                if i < len(self.coin_labels):
                    name_label, price_label, change_label = self.coin_labels[i]
                    name_label.setText(coin_info['name'])
                    price_label.setText(coin_info['price'])
                    change_label.setText(coin_info['change'])
                else:
                    coin_layout = QtWidgets.QHBoxLayout()
                    coin_layout.setSpacing(1)


                    name_label = QtWidgets.QLabel(coin_info['name'])


                    price_label = QtWidgets.QLabel(coin_info['price'])


                    change_label = QtWidgets.QLabel(coin_info['change'])


                    coin_layout.addWidget(name_label)
                    coin_layout.addWidget(price_label)
                    coin_layout.addWidget(change_label)


                    scroll_widget = self.findChild(QtWidgets.QScrollArea).widget()
                    content_layout = scroll_widget.layout()
                    content_layout.addLayout(coin_layout)

                    self.coin_labels.append((name_label, price_label, change_label))
        except Exception as e:
            print("Failed to update coin list:", e)


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.setToolTip('Crypto Price Ticker')
        self.window = parent
        menu = QtWidgets.QMenu(parent)
        show_hide_action = menu.addAction("Show/Hide")
        show_hide_action.triggered.connect(self.toggleWindow)
        exit_action = menu.addAction("Quit")
        exit_action.triggered.connect(self.window.quit)
        self.setContextMenu(menu)
        self.activated.connect(self.onTrayIconActivated)
        self.window.show()
        self.show()

    def toggleWindow(self):
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window.show()

    def onTrayIconActivated(self, reason):
        if reason == self.Trigger:
            self.toggleWindow()


def query_coin_price_list(config):
    coin_price_list = []
    try:

        api_key = config['settings']['api_key']
        url = config['settings']['url']
        symbols = config['coins']['symbols']
        proxy = config['proxy']['proxy_http']
        parameters = {
            'symbol': symbols, 
            'CMC_PRO_API_KEY': api_key
        }
        if proxy:
            proxys = {
                'http': proxy,
                'https': proxy
            }
            response = requests.get(url, params=parameters, proxies=proxys)
        else:
            response = requests.get(url, params=parameters)
        data = response.json()
        for coin, coin_data in data['data'].items():
            coin_price_list.append({
                'name': coin,
                'price': str(round(coin_data['quote']['USD']['price'], 3)),
                'change': "%.2f%%" % coin_data['quote']['USD']['percent_change_24h']
            })
        print(coin_price_list)
    except Exception as e:
        print("Failed to query coin price list:", e)

    return coin_price_list


def main():
    app = QtWidgets.QApplication(sys.argv)
    config = configparser.ConfigParser()
    config.read('config.ini')
    coin_list = query_coin_price_list(config)

    hidden_main_window = QtWidgets.QWidget()
    hidden_main_window.setWindowFlags(QtCore.Qt.Tool) 
    hidden_main_window.hide()


    window = DraggableWidget(coin_list)
    window.setWindowFlags(window.windowFlags() | QtCore.Qt.Tool)

    tray_icon_path = "./timg3.jpg"
    tray_icon = QtGui.QIcon(tray_icon_path) if tray_icon_path else app.style().standardIcon(
        QtWidgets.QStyle.SP_ComputerIcon)
    SystemTrayIcon(tray_icon, window)

    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: window.updateCoinList(config))
    timer.start(int(config['flush']['flush_interval']) * 1000) 

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
