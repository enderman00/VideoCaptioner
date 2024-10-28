# -*- coding: utf-8 -*-

import os
from pathlib import Path
import sys
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QApplication, 
                             QFileDialog, QProgressBar, QStatusBar)
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent
from qfluentwidgets import (ComboBox, SwitchButton, SimpleCardWidget, CaptionLabel, 
                            CardWidget, PrimaryPushButton, LineEdit, BodyLabel,
                            InfoBar, InfoBarPosition, ProgressBar, PushButton)

from app.core.thread.create_task_thread import CreateTaskThread
from app.core.thread.video_synthesis_thread import VideoSynthesisThread
from ..core.entities import Task
from ..common.config import cfg, SubtitleLayoutEnum
from ..components.SimpleSettingCard import ComboBoxSimpleSettingCard, SwitchButtonSimpleSettingCard


current_dir = Path(__file__).parent.parent
SUBTITLE_STYLE_DIR = current_dir / "resource" / "subtitle_style"


class VideoSynthesisInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAcceptDrops(True)  # 启用拖放功能
        self.setup_ui()
        self.set_value()
        self.setup_signals()
        self.task = None

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        # 配置卡片
        self.config_card = CardWidget(self)
        # self.config_card.setFixedWidth(600)
        self.config_layout = QVBoxLayout(self.config_card)
        self.config_layout.setContentsMargins(20, 10, 20, 10)

        # 字幕文件选择
        self.subtitle_layout = QHBoxLayout()
        self.subtitle_layout.setSpacing(10)
        self.subtitle_label = BodyLabel("字幕文件:", self)
        self.subtitle_input = LineEdit(self)
        self.subtitle_input.setPlaceholderText("选择或者拖拽字幕文件")
        self.subtitle_input.setAcceptDrops(True)  # 启用拖放
        self.subtitle_button = PushButton("浏览", self)
        self.subtitle_layout.addWidget(self.subtitle_label)
        self.subtitle_layout.addWidget(self.subtitle_input)
        self.subtitle_layout.addWidget(self.subtitle_button)
        self.config_layout.addLayout(self.subtitle_layout)

        # 视频文件选择
        self.video_layout = QHBoxLayout()
        self.video_layout.setSpacing(10)
        self.video_label = BodyLabel("视频文件:", self)
        self.video_input = LineEdit(self)
        self.video_input.setPlaceholderText("选择或者拖拽视频文件")
        self.video_input.setAcceptDrops(True)  # 启用拖放
        self.video_button = PushButton("浏览", self)
        self.video_layout.addWidget(self.video_label)
        self.video_layout.addWidget(self.video_input)
        self.video_layout.addWidget(self.video_button)
        self.config_layout.addLayout(self.video_layout)

        self.main_layout.addWidget(self.config_card)

        # 合成按钮和打开文件夹按钮
        self.button_layout = QHBoxLayout()
        self.synthesize_button = PushButton("开始合成", self)
        self.open_folder_button = PushButton("打开视频文件夹", self)
        self.button_layout.addWidget(self.synthesize_button)
        self.button_layout.addWidget(self.open_folder_button)
        self.main_layout.addLayout(self.button_layout)

        self.main_layout.addStretch(1)

        # 底部进度条和状态信息
        self.bottom_layout = QHBoxLayout()
        self.progress_bar = ProgressBar(self)
        self.status_label = BodyLabel("就绪", self)
        self.status_label.setMinimumWidth(100)  # 设置最小宽度
        self.status_label.setAlignment(Qt.AlignCenter)  # 设置文本居中对齐
        self.bottom_layout.addWidget(self.progress_bar, 1)  # 进度条使用剩余空间
        self.bottom_layout.addWidget(self.status_label)  # 状态标签使用固定宽度
        self.main_layout.addLayout(self.bottom_layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return
        
        file_path = urls[0].toLocalFile()
        if not os.path.exists(file_path):
            return

        # 判断文件类型并放入对应输入框
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in ['.srt', '.ass']:
            self.subtitle_input.setText(file_path)
        # TODO 添加更多视频格式
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.3gp', '.ts', '.m3u8', '.ts']:
            self.video_input.setText(file_path)
        
        InfoBar.success(
            "成功",
            "文件已成功放入输入框",
            duration=2000,
            position=InfoBarPosition.TOP,
            parent=self
        )

    def setup_signals(self):
        # 文件选择相关信号
        self.subtitle_button.clicked.connect(self.choose_subtitle_file)
        self.video_button.clicked.connect(self.choose_video_file)
        
        # 合成和文件夹相关信号
        self.synthesize_button.clicked.connect(self.process)
        self.open_folder_button.clicked.connect(self.open_video_folder)

    def set_value(self):
        self.subtitle_input.setText("E:/GithubProject/VideoCaptioner/app/core/subtitles0.srt")
        self.video_input.setText("C:/Users/weifeng/Videos/佛山周末穷游好去处!.mp4")

    def choose_subtitle_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择字幕文件", "", "字幕文件 (*.srt)")
        if file_path:
            self.subtitle_input.setText(file_path)

    def choose_video_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "", "视频文件 (*.mp4 *.avi *.mov)")
        if file_path:
            self.video_input.setText(file_path)

    def create_task(self):
        subtitle_file = self.subtitle_input.text()
        video_file = self.video_input.text()
        if not subtitle_file or not video_file:
            InfoBar.error(
                "错误",
                "请选择字幕文件和视频文件",
                duration=2000,
                position=InfoBarPosition.TOP,
                parent=self
            )
            return None
        
        self.task = CreateTaskThread.create_video_synthesis_task(subtitle_file, video_file)
        return self.task

    def set_task(self, task: Task):
        self.task = task
        self.update_info()

    def update_info(self):
        if self.task:
            self.video_input.setText(self.task.file_path)
            self.subtitle_input.setText(self.task.result_subtitle_save_path)

    def process(self):
        self.synthesize_button.setEnabled(False)
        if not self.task:
            self.task = None
            self.create_task()
        if self.task.file_path != self.video_input.text() or self.task.result_subtitle_save_path != self.subtitle_input.text():
            self.task = None
            self.create_task()
        
        if self.task:
            self.video_synthesis_thread = VideoSynthesisThread(self.task)
            self.video_synthesis_thread.finished.connect(self.on_video_synthesis_finished)
            self.video_synthesis_thread.progress.connect(self.on_video_synthesis_progress)
            self.video_synthesis_thread.error.connect(self.on_video_synthesis_error)
            self.video_synthesis_thread.start()
        else:
            InfoBar.error(
                "错误",
                "无法创建任务",
                duration=2000,
                position=InfoBarPosition.TOP,
                parent=self
            )

    def on_video_synthesis_finished(self, task):
        self.synthesize_button.setEnabled(True)
        InfoBar.success(
            "成功",
            "视频合成已完成",
            duration=2000,
            position=InfoBarPosition.TOP,
            parent=self
        )
    
    def on_video_synthesis_progress(self, progress, message):
        print(f"{progress} {message}")
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)

    def on_video_synthesis_error(self, error):
        self.synthesize_button.setEnabled(True)
        InfoBar.error(
            "错误",
            str(error),
            duration=2000,
            position=InfoBarPosition.TOP,
            parent=self
        )

    def open_video_folder(self):
        if self.task and self.task.work_dir:
            file_path = Path(self.task.video_save_path)
            if os.path.exists(file_path):
                os.system(f'explorer /select,"{file_path}"')
            else:
                os.startfile(self.task.work_dir)
        else:
            InfoBar.warning(
                "警告",
                "没有可用的视频文件夹",
                duration=2000,
                position=InfoBarPosition.TOP,
                parent=self
            )

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = VideoSynthesisInterface()
    window.resize(600, 400)  # 设置窗口大小
    window.show()
    sys.exit(app.exec_())