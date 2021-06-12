import sys
import time
from multiprocessing import cpu_count

from PyQt5.Qt import *

from zipper import Zipper

PROGRESSBAR_STYLE = """
QProgressBar {
    text-align: center;
    border: 2px solid #219ff3;
    border-radius: 2px;
    background-color: #d6d6d6;
}
QProgressBar::chunk {
    background-color: #219ff3;
}
"""


class ZipperUi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('zipper 1.0')
        self.resize(700, 300)
        self._init_ui()
        self.zipper = None

    def _init_ui(self):
        # row 1
        label_path = QLabel('Parent Dir:')
        self.ledit_p_path = QLineEdit()
        self.ledit_p_path.setPlaceholderText('please select parent folder')
        self.btn_select = QPushButton('Select')
        self.btn_select.clicked.connect(self.get_parent_path)

        # row 2
        label_progress = QLabel('Progress:')
        self.p_bar = QProgressBar()
        self.p_bar.setStyleSheet(PROGRESSBAR_STYLE)
        self.p_bar.setMinimum(0)
        self.p_bar.setMaximum(100)
        self.p_bar.setValue(0)
        self.btn_run = QPushButton('RUN')
        self.btn_run.clicked.connect(self.run_compress)

        # row 3
        label_crate = QLabel('Level:')
        self.cb_crate = QComboBox()
        for i in range(9):
            self.cb_crate.addItem(str(i + 1))
        label_cpu_core = QLabel('CPUs:')
        self.cb_cpu_core = QComboBox()
        for i in range(cpu_count()):
            self.cb_cpu_core.addItem(str(i + 1))
        self.cb_cpu_core.setCurrentText(str(cpu_count()-1))
        label_password = QLabel('Password:')
        self.ledit_pw = QLineEdit()
        self.ledit_pw.setPlaceholderText('optional')

        # row 4
        self.btn_stop = QPushButton('STOP')
        self.btn_stop.clicked.connect(self.stop_compress)

        # self.status_bar = QStatusBar()
        self.statusBar().showMessage('Welcome!')

        # set layout
        self.global_layout = QGridLayout()
        self.global_layout.addWidget(label_path, 1, 1, 1, 1)
        self.global_layout.addWidget(self.ledit_p_path, 1, 2, 1, 5)
        self.global_layout.addWidget(self.btn_select, 1, 7, 1, 1)
        self.global_layout.addWidget(label_progress, 2, 1, 1, 1)
        self.global_layout.addWidget(self.p_bar, 2, 2, 1, 5)
        self.global_layout.addWidget(self.btn_run, 2, 7, 1, 1)
        self.global_layout.addWidget(label_password, 3, 1, 1, 1)
        self.global_layout.addWidget(self.ledit_pw, 3, 2, 1, 2)
        self.global_layout.addWidget(label_crate, 3, 4, 1, 1)
        self.global_layout.addWidget(self.cb_crate, 3, 5, 1, 1)
        self.global_layout.addWidget(label_cpu_core, 3, 6, 1, 1)
        self.global_layout.addWidget(self.cb_cpu_core, 3, 7, 1, 1)
        self.global_layout.addWidget(self.btn_stop, 4, 7, 1, 1)
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.global_layout)
        self.setCentralWidget(self.main_widget)

    def get_parent_path(self):
        p_path = QFileDialog().getExistingDirectory()
        self.ledit_p_path.setText(str(p_path))

    def run_compress(self):
        self.p_bar.setValue(0)
        p_path = self.ledit_p_path.text()
        crate = int(self.cb_crate.currentText())
        cpu_core = int(self.cb_cpu_core.currentText())
        passwd = None if self.ledit_pw.text() == '' else self.ledit_pw.text()
        self.zipper = Zipper(p_path, crate, cpu_core, passwd)
        self.zipper.progress_value.connect(self.update_pregress_bar)
        self.zipper.log_output.connect(self.update_log_output)
        self.zipper.start()
        self.zipper.close()

    def stop_compress(self):
        if self.zipper is not None:
            self.zipper.kill_all()
        else:
            self.statusBar().showMessage('Zipper not running!')

    def update_pregress_bar(self, i):
        self.p_bar.setValue(i)

    def update_log_output(self, logs: tuple):
        result, msg = logs[0], logs[1].replace('\\', '')
        if result:
            self.statusBar().showMessage(f'{msg}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_wnd = ZipperUi()
    main_wnd.show()
    app.exec()
