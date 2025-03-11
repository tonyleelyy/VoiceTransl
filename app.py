import sys, os

os.chdir(sys._MEIPASS)
import shutil
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QFileDialog, QFrame
from qfluentwidgets import PushButton as QPushButton, TextEdit as QTextEdit, LineEdit as QLineEdit, ComboBox as QComboBox, Slider as QSlider, FluentWindow as QMainWindow
from qfluentwidgets import FluentIcon, NavigationItemPosition, SubtitleLabel, TitleLabel, BodyLabel

import re
import json
import subprocess
from yt_dlp import YoutubeDL
from bilibili_dl.bilibili_dl.Video import Video
from bilibili_dl.bilibili_dl.downloader import download
from bilibili_dl.bilibili_dl.utils import send_request
from bilibili_dl.bilibili_dl.constants import URL_VIDEO_INFO

from prompt2srt import make_srt, make_lrc
from srt2prompt import make_prompt
from prompt2srt import make_srt
from GalTransl.__main__ import worker

TRANSLATOR_SUPPORTED = [
    '不进行翻译',
    "gpt-custom",
    "gpt35-1106",
    "gpt4-turbo",
    "moonshot-v1-8k",
    "deepseek-chat",
    "glm-4",
    "glm-4-flash",
    "qwen2-7b-instruct",
    "qwen2-57b-a14b-instruct",
    "qwen2-72b-instruct",
    "abab6.5-chat",
    "abab6.5s-chat",
]

TRANSLATOR_SUPPORTED_LOCAL = [
    '不进行翻译',
    "sakura-009",
    "sakura-010",
    "index",
    "galtransl",
    "qwen-local",
]

class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        # Set the scroll area as the parent of the widget
        self.vBoxLayout = QVBoxLayout(self)

        # Must set a globally unique object name for the sub-interface
        self.setObjectName(text.replace(' ', '-'))

class MainWindow(QMainWindow):
    status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None

        self.setWindowTitle("VoiceTransl")
        self.status.connect(lambda x: self.setWindowTitle(f"VoiceTransl - {x}"))
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.resize(800, 600)
        self.initUI()
        
    def initUI(self):
        self.initInputOutputTab()
        self.initSettingsTab()
        self.initAdvancedSettingTab()
        self.initDictTab()
        self.initToolTab()
        self.initAboutTab()

        # load config
        if os.path.exists('config.txt'):
            with open('config.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                whisper_file = lines[0].strip()
                translator = lines[1].strip()
                language = lines[2].strip()
                gpt_token = lines[3].strip()
                gpt_address = lines[4].strip()
                gpt_model = lines[5].strip()
                sakura_file = lines[6].strip()
                sakura_mode = int(lines[7].strip())
                proxy_address = lines[8].strip()
                translator_local = lines[9].strip()

                if self.whisper_file: self.whisper_file.setCurrentText(whisper_file)
                self.translator_group.setCurrentText(translator)
                self.translator_group_local.setCurrentText(translator_local)
                self.input_lang.setCurrentText(language)
                self.gpt_token.setText(gpt_token)
                self.gpt_address.setText(gpt_address)
                self.gpt_model.setText(gpt_model)
                if self.sakura_file: self.sakura_file.setCurrentText(sakura_file)
                self.sakura_mode.setValue(sakura_mode)
                self.proxy_address.setText(proxy_address)

        if os.path.exists('whisper/param.txt'):
            with open('whisper/param.txt', 'r', encoding='utf-8') as f:
                self.param_whisper.setPlainText(f.read())

        if os.path.exists('llama/param.txt'):
            with open('llama/param.txt', 'r', encoding='utf-8') as f:
                self.param_llama.setPlainText(f.read())

    def initAboutTab(self):
        self.about_tab = Widget("About", self)
        self.about_layout = self.about_tab.vBoxLayout

        # introduce
        self.about_layout.addWidget(TitleLabel("📖 关于"))
        self.introduce_text = QTextEdit()
        self.introduce_text.setReadOnly(True)
        self.introduce_text.setPlainText("VoiceTransl（原Galtransl for ASMR）是一个离线AI视频字幕生成和翻译软件，您可以使用本程序从外语音视频文件/字幕文件生成中文字幕文件。项目地址及使用说明: https://github.com/shinnpuru/VoiceTransl。")
        self.about_layout.addWidget(self.introduce_text)

        # mode
        self.about_layout.addWidget(TitleLabel("🔧 模式说明"))
        self.mode_text = QTextEdit()
        self.mode_text.setReadOnly(True)
        self.mode_text.setPlainText("""（1）仅下载模式：选择不进行听写和不进行翻译；
（2）仅听写模式：选择不进行翻译，并且选择听写模型；
（3）仅翻译模式：上传SRT文件，并且选择翻译模型；  
（4）完整模式：选择所有功能。   """)
        self.about_layout.addWidget(self.mode_text)

        # disclaimer
        self.about_layout.addWidget(TitleLabel("⚠️ 免责声明"))
        self.disclaimer_text = QTextEdit()
        self.disclaimer_text.setReadOnly(True)
        self.disclaimer_text.setPlainText("本程序仅供学习交流使用，不得用于商业用途。请遵守当地法律法规，不得传播色情、暴力、恐怖等违法违规内容。本软件不对任何使用者的行为负责，不保证翻译结果的准确性。使用本软件即代表您同意自行承担使用本软件的风险，包括但不限于版权风险、法律风险等。")
        self.about_layout.addWidget(self.disclaimer_text)

        self.addSubInterface(self.about_tab, FluentIcon.INFO, "关于", NavigationItemPosition.TOP)
        
    def initInputOutputTab(self):
        self.input_output_tab = Widget("Home", self)
        self.input_output_layout = self.input_output_tab.vBoxLayout
        
        # Input Section
        self.input_output_layout.addWidget(BodyLabel("📂 请拖拽音视频文件/SRT文件到这里（可多选）。"))
        self.input_files_list = QTextEdit()
        self.input_files_list.setAcceptDrops(True)
        self.input_files_list.dropEvent = lambda e: self.input_files_list.setPlainText('\n'.join([i[8:] for i in e.mimeData().text().split('\n')]))
        self.input_files_list.setPlaceholderText("当前未选择本地文件...")
        self.input_output_layout.addWidget(self.input_files_list)

        # YouTube URL Section
        self.input_output_layout.addWidget(BodyLabel("🔗 或者输入B站视频BV号或者YouTube视频链接。"))
        self.yt_url = QTextEdit()
        self.yt_url.setAcceptDrops(False)
        self.yt_url.setPlaceholderText("例如：https://www.youtube.com/watch?v=...\n例如：BV1Lxt5e8EJF")
        self.input_output_layout.addWidget(self.yt_url)

        # Proxy Section
        self.input_output_layout.addWidget(BodyLabel("🌐 设置代理地址以便下载视频和翻译。"))
        self.proxy_address = QLineEdit()
        self.proxy_address.setPlaceholderText("例如：http://127.0.0.1:7890，留空为不使用")
        self.input_output_layout.addWidget(self.proxy_address)

        self.run_button = QPushButton("🚀 运行")
        self.run_button.clicked.connect(self.run_worker)
        self.input_output_layout.addWidget(self.run_button)

        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setPlaceholderText("当前无输出信息...")
        self.status.connect(self.output_text_edit.append)
        self.input_output_layout.addWidget(self.output_text_edit)

        self.open_output_button = QPushButton("📁 打开下载文件夹")
        self.open_output_button.clicked.connect(lambda: os.startfile(os.path.join(os.getcwd(),'project/cache')))
        self.input_output_layout.addWidget(self.open_output_button)
        
        self.clean_button = QPushButton("🧹 清空缓存")
        self.clean_button.clicked.connect(self.cleaner)
        self.input_output_layout.addWidget(self.clean_button)
        
        self.addSubInterface(self.input_output_tab, FluentIcon.HOME, "主页", NavigationItemPosition.TOP)

    def initDictTab(self):
        self.dict_tab = Widget("Dict", self)
        self.dict_layout = self.dict_tab.vBoxLayout

        self.dict_layout.addWidget(BodyLabel("📚 配置翻译前的字典。"))
        self.before_dict = QTextEdit()
        self.before_dict.setPlaceholderText("日文\t日文\n日文\t日文")
        self.dict_layout.addWidget(self.before_dict)
        
        self.dict_layout.addWidget(BodyLabel("📚 配置翻译中的字典。"))
        self.gpt_dict = QTextEdit()
        self.gpt_dict.setPlaceholderText("日文\t中文\n日文\t中文")
        self.dict_layout.addWidget(self.gpt_dict)
        
        self.dict_layout.addWidget(BodyLabel("📚 配置翻译后的字典。"))
        self.after_dict = QTextEdit()
        self.after_dict.setPlaceholderText("中文\t中文\n中文\t中文")
        self.dict_layout.addWidget(self.after_dict)

        self.addSubInterface(self.dict_tab, FluentIcon.DICTIONARY, "字典", NavigationItemPosition.TOP)
        
    def initSettingsTab(self):
        self.settings_tab = Widget("Settings", self)
        self.settings_layout = self.settings_tab.vBoxLayout
        
        # Whisper Section
        self.settings_layout.addWidget(BodyLabel("🗣️ 选择用于语音识别的模型文件。"))
        self.whisper_file = QComboBox()
        whisper_lst = [i for i in os.listdir('whisper') if i.startswith('ggml') and i.endswith('bin')] + [i for i in os.listdir('whisper-faster') if i.startswith('faster-whisper')] + ['不进行听写']
        self.whisper_file.addItems(whisper_lst)
        self.settings_layout.addWidget(self.whisper_file)

        self.settings_layout.addWidget(BodyLabel("选择输入的语言。"))
        self.input_lang = QComboBox()
        self.input_lang.addItems(['auto','cn','ja','en','ko','ru','fr'])
        self.settings_layout.addWidget(self.input_lang)

        # Translator Section
        self.settings_layout.addWidget(BodyLabel("🌍 选择用于在线翻译的模型类别。"))
        self.translator_group = QComboBox()
        self.translator_group.addItems(TRANSLATOR_SUPPORTED)
        self.settings_layout.addWidget(self.translator_group)
        
        self.settings_layout.addWidget(BodyLabel("在线模型令牌（如果选择在线模型）"))
        self.gpt_token = QLineEdit()
        self.gpt_token.setPlaceholderText("留空为使用上次配置的Token。")
        self.settings_layout.addWidget(self.gpt_token)

        self.settings_layout.addWidget(BodyLabel("自定义OpenAI地址 (请选择gpt-custom，支持本地或在线OpenAI接口)"))
        self.gpt_address = QLineEdit()
        self.gpt_address.setPlaceholderText("例如：http://127.0.0.1:11434")
        self.settings_layout.addWidget(self.gpt_address)

        self.settings_layout.addWidget(BodyLabel("自定义OpenAI模型 (请选择gpt-custom，支持本地或在线OpenAI接口)"))
        self.gpt_model = QLineEdit()
        self.gpt_model.setPlaceholderText("例如：qwen2.5")
        self.settings_layout.addWidget(self.gpt_model)

        self.settings_layout.addWidget(BodyLabel("💻 选择用于离线翻译的模型类别。"))
        self.translator_group_local = QComboBox()
        self.translator_group_local.addItems(TRANSLATOR_SUPPORTED_LOCAL)
        self.settings_layout.addWidget(self.translator_group_local)
        
        self.settings_layout.addWidget(BodyLabel("离线模型文件（如果选择离线模型）"))
        self.sakura_file = QComboBox()
        sakura_lst = [i for i in os.listdir('llama') if i.endswith('gguf')]
        self.sakura_file.addItems(sakura_lst)
        self.settings_layout.addWidget(self.sakura_file)
        
        self.settings_layout.addWidget(BodyLabel("离线模型参数（越大表示使用GPU越多）: "))
        self.sakura_value = QLineEdit()
        self.sakura_value.setPlaceholderText("100")
        self.sakura_value.setReadOnly(True)
        self.settings_layout.addWidget(self.sakura_value)
        self.sakura_mode = QSlider(Qt.Horizontal)
        self.sakura_mode.setRange(0, 100)
        self.sakura_mode.setValue(100)
        self.sakura_mode.valueChanged.connect(lambda: self.sakura_value.setText(str(self.sakura_mode.value())))
        self.settings_layout.addWidget(self.sakura_mode)

        self.addSubInterface(self.settings_tab, FluentIcon.SETTING, "基础设置", NavigationItemPosition.TOP)

    def initAdvancedSettingTab(self):
        self.advanced_settings_tab = Widget("AdvancedSettings", self)
        self.advanced_settings_layout = self.advanced_settings_tab.vBoxLayout
        
        self.advanced_settings_layout.addWidget(BodyLabel("🔧 输入额外的Whisper命令行参数。"))
        self.param_whisper = QTextEdit()
        self.param_whisper.setPlaceholderText("每个参数单独一行，请参考Whisper.cpp和Faster-Whisper文档，不清楚请保持默认。")
        self.advanced_settings_layout.addWidget(self.param_whisper)

        self.advanced_settings_layout.addWidget(BodyLabel("🔧 输入额外的Llama.cpp命令行参数。"))
        self.param_llama = QTextEdit()
        self.param_llama.setPlaceholderText("每个参数单独一行，请参考Llama.cpp文档，不清楚请保持默认。")
        self.advanced_settings_layout.addWidget(self.param_llama)

        self.addSubInterface(self.advanced_settings_tab, FluentIcon.ASTERISK, "高级设置", NavigationItemPosition.TOP)

    def initToolTab(self):
        self.tool_tab = Widget("Tool", self)
        self.tool_layout = self.tool_tab.vBoxLayout

        # Split Section
        self.tool_layout.addWidget(BodyLabel("🔪 分割合并工具"))
        self.split_value = QLineEdit()
        self.split_value.setPlaceholderText("600")
        self.split_value.setReadOnly(True)
        self.tool_layout.addWidget(self.split_value)
        self.split_mode = QSlider(Qt.Horizontal)
        self.split_mode.setRange(0, 3600)
        self.split_mode.setValue(600)
        self.split_mode.valueChanged.connect(lambda: self.split_value.setText(str(self.split_mode.value())))
        self.tool_layout.addWidget(self.split_mode)

        self.split_files_list = QTextEdit()
        self.split_files_list.setAcceptDrops(True)
        self.split_files_list.dropEvent = lambda e: self.split_files_list.setPlainText('\n'.join([i[8:] for i in e.mimeData().text().split('\n')]))
        self.split_files_list.setPlaceholderText("拖拽文件到方框内，点击运行即可，每个文件生成一个文件夹，滑动条数字代表切割每段音频的长度（秒）。")
        self.tool_layout.addWidget(self.split_files_list)
        self.run_split_button = QPushButton("🚀 分割")
        self.run_split_button.clicked.connect(self.run_split)
        self.tool_layout.addWidget(self.run_split_button)

        self.merge_files_list = QTextEdit()
        self.merge_files_list.setAcceptDrops(True)
        self.merge_files_list.dropEvent = lambda e: self.merge_files_list.setPlainText('\n'.join([i[8:] for i in e.mimeData().text().split('\n')]))
        self.merge_files_list.setPlaceholderText("拖拽多个字幕文件到方框内，点击运行即可，每次合并成一个文件。时间戳按照上面滑动条分割的时间累加。")
        self.tool_layout.addWidget(self.merge_files_list)
        self.run_merge_button = QPushButton("🚀 合并")
        self.run_merge_button.clicked.connect(self.run_merge)
        self.tool_layout.addWidget(self.run_merge_button)

        # Merge Section
        self.tool_layout.addWidget(BodyLabel("💾 字幕合成工具"))
        self.synth_files_list = QTextEdit()
        self.synth_files_list.setAcceptDrops(True)
        self.synth_files_list.dropEvent = lambda e: self.synth_files_list.setPlainText('\n'.join([i[8:] for i in e.mimeData().text().split('\n')]))
        self.synth_files_list.setPlaceholderText("拖拽字幕文件和视频文件到下方框内，点击运行即可。字幕和视频文件需要一一对应，例如output.mp4和output.mp4.srt。")
        self.tool_layout.addWidget(self.synth_files_list)
        self.run_synth_button = QPushButton("🚀 合成")
        self.run_synth_button.clicked.connect(self.run_synth)
        self.tool_layout.addWidget(self.run_synth_button)
        
        self.addSubInterface(self.tool_tab, FluentIcon.BRUSH, "工具", NavigationItemPosition.TOP)
        
    def select_input(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "选择音视频文件/SRT文件", "", "All Files (*);;Video Files (*.mp4 *.webm, *.flv);;SRT Files (*.srt);;Audio Files (*.wav, *.mp3, *.flac)", options=options)
        if files:
            self.input_files_list.setPlainText('\n'.join(files))

    def run_worker(self):
        self.thread = QThread()
        self.worker = MainWorker(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def run_split(self):
        self.thread = QThread()
        self.worker = MainWorker(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.split)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def run_merge(self):
        self.thread = QThread()
        self.worker = MainWorker(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.merge)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def run_synth(self):
        self.thread = QThread()
        self.worker = MainWorker(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.synth)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()
    
    def cleaner(self):
        self.status.emit("[INFO] 正在清理中间文件...")
        if os.path.exists('project/gt_input'):
            shutil.rmtree('project/gt_input')
        if os.path.exists('project/gt_output'):
            shutil.rmtree('project/gt_output')
        if os.path.exists('project/transl_cache'):
            shutil.rmtree('project/transl_cache')
        self.status.emit("[INFO] 正在清理输出...")
        if os.path.exists('project/cache'):
            shutil.rmtree('project/cache')
        os.makedirs('project/cache', exist_ok=True)


class MainWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, master):
        super().__init__()
        self.master = master
        self.status = master.status

    def split(self):
        self.status.emit("[INFO] 正在读取配置...")
        input_files = self.master.split_files_list.toPlainText()
        split_mode = self.master.split_mode.value()
        if input_files:
            input_files = input_files.strip().split('\n')
            for idx, input_file in enumerate(input_files):
                if not os.path.exists(input_file):
                    self.status.emit(f"[ERROR] {input_file}文件不存在，请重新选择文件！")
                    self.finished.emit()

                self.status.emit(f"[INFO] 当前处理文件：{input_file} 第{idx+1}个，共{len(input_files)}个")
                os.makedirs(os.path.join(*(input_file.split('.')[:-1])), exist_ok=True)

                self.status.emit(f"[INFO] 正在进行音频提取...每{split_mode}秒分割一次")
                self.pid = subprocess.Popen(['ffmpeg', '-y', '-i', input_file,  '-f', 'segment', '-segment_time', str(split_mode), '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', os.path.join(*(input_file.split('.')[:-1]+['%04d.wav']))])
                self.pid.wait()
                self.pid.kill()
                self.pid.terminate()
                self.status.emit("[INFO] 音频分割完成！")
        self.finished.emit()

    def merge(self):
        self.status.emit("[INFO] 正在读取配置...")
        input_files = self.master.merge_files_list.toPlainText()
        split_mode = self.master.split_mode.value()
        if input_files:
            input_files = sorted(input_files.strip().split('\n'))
            merged_prompt = []
            for idx, input_file in enumerate(input_files):
                if not os.path.exists(input_file):
                    self.status.emit(f"[ERROR] {input_file}文件不存在，请重新选择文件！")
                    self.finished.emit()

                self.status.emit(f"[INFO] 当前处理文件：{input_file} 第{idx+1}个，共{len(input_files)}个")
                prompt = make_prompt(input_file)

                for i in prompt:
                    i['start'] += idx * split_mode
                    i['end'] += idx * split_mode
                    merged_prompt.append(i)

            with open(input_files[0].replace('.srt','_merged.json'), 'w', encoding='utf-8') as f:
                json.dump(merged_prompt, f, ensure_ascii=False, indent=4)
            make_srt(input_files[0].replace('.srt','_merged.json'), input_files[0].replace('.srt','_merged.srt'))
            self.status.emit("[INFO] 所有文件处理完成！")
        self.finished.emit()

    def synth(self):
        self.status.emit("[INFO] 正在读取配置...")
        input_files = self.master.synth_files_list.toPlainText()
        if input_files:
            input_files = input_files.strip().split('\n')
            srt_files = sorted([i for i in input_files if i.endswith('.srt')])
            video_files = sorted([i for i in input_files if not i.endswith('.srt')])
            if len(srt_files) != len(video_files):
                self.status.emit("[ERROR] 字幕文件和视频文件数量不匹配，请重新选择文件！")
                self.finished.emit()
            
            for idx, (input_file, input_srt) in enumerate(zip(video_files, srt_files)):
                if not os.path.exists(input_file):
                    self.status.emit(f"[ERROR] {input_file}文件不存在，请重新选择文件！")
                    self.finished.emit()

                if not os.path.exists(input_srt):
                    self.status.emit(f"[ERROR] {input_srt}文件不存在，请重新选择文件！")
                    self.finished.emit()

                input_srt = shutil.copy(input_srt, 'project/cache/')

                self.status.emit(f"[INFO] 当前处理文件：{input_file} 第{idx+1}个，共{len(video_files)}个")
                self.pid = subprocess.Popen(['ffmpeg', '-y', '-i', input_file,  '-vf', f'subtitles={input_srt}', '-c:v', 'libx264', '-c:a', 'copy', input_file+'_synth.mp4'])
                self.pid.wait()
                self.pid.kill()
                self.pid.terminate()
                self.status.emit("[INFO] 视频合成完成！")
            
        self.finished.emit()

    def run(self):
        self.status.emit("[INFO] 正在读取配置...")
        input_files = self.master.input_files_list.toPlainText()
        yt_url = self.master.yt_url.toPlainText()
        whisper_file = self.master.whisper_file.currentText()
        translator = self.master.translator_group.currentText()
        translator_local = self.master.translator_group_local.currentText()
        language = self.master.input_lang.currentText()
        gpt_token = self.master.gpt_token.text()
        gpt_address = self.master.gpt_address.text()
        gpt_model = self.master.gpt_model.text()
        sakura_file = self.master.sakura_file.currentText()
        sakura_mode = self.master.sakura_mode.value()
        proxy_address = self.master.proxy_address.text()
        before_dict = self.master.before_dict.toPlainText()
        gpt_dict = self.master.gpt_dict.toPlainText()
        after_dict = self.master.after_dict.toPlainText()
        param_whisper = self.master.param_whisper.toPlainText()
        param_llama = self.master.param_llama.toPlainText()

        # save config
        with open('config.txt', 'w', encoding='utf-8') as f:
            f.write(f"{whisper_file}\n{translator}\n{language}\n{gpt_token}\n{gpt_address}\n{gpt_model}\n{sakura_file}\n{sakura_mode}\n{proxy_address}\n{translator_local}\n")

        with open('whisper/param.txt', 'w', encoding='utf-8') as f:
            f.write(param_whisper)

        with open('llama/param.txt', 'w', encoding='utf-8') as f:
            f.write(param_llama)

        translator = translator if translator != '不进行翻译' else translator_local

        self.status.emit("[INFO] 正在初始化项目文件夹...")

        os.makedirs('project/cache', exist_ok=True)
        if before_dict:
            with open('project/项目字典_译前.txt', 'w', encoding='utf-8') as f:
                f.write(before_dict.replace(' ','\t'))
        else:
            if os.path.exists('project/项目字典_译前.txt'):
                os.remove('project/项目字典_译前.txt')
        if gpt_dict:
            with open('project/项目GPT字典.txt', 'w', encoding='utf-8') as f:
                f.write(gpt_dict.replace(' ','\t'))
        else:
            if os.path.exists('project/项目GPT字典.txt'):
                os.remove('project/项目GPT字典.txt')
        if after_dict:
            with open('project/项目字典_译后.txt', 'w', encoding='utf-8') as f:
                f.write(after_dict.replace(' ','\t'))
        else:
            if os.path.exists('project/项目字典_译后.txt'):
                os.remove('project/项目字典_译后.txt')

        self.status.emit(f"[INFO] 当前输入文件：{input_files}, 当前视频链接：{yt_url}")

        if input_files:
            input_files = input_files.split('\n')
        else:
            input_files = []

        if yt_url:
            input_files.extend(yt_url.split('\n'))

        os.makedirs('project/cache', exist_ok=True)

        self.status.emit("[INFO] 正在进行翻译配置...")
        with open('project/config.yaml', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for idx, line in enumerate(lines):
            if 'language' in line:
                lines[idx] = f'  language: "{language}2zh-cn"\n'
            if 'gpt' in translator:
                if not gpt_address:
                    gpt_address = 'https://api.openai.com'
                if not gpt_model:
                    gpt_model = ''
                if not gpt_token:
                    gpt_token = 'sk-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
                if 'GPT35:' in line:
                    lines[idx+4] = f"      - token: {gpt_token}\n"
                    lines[idx+6] = f"    defaultEndpoint: {gpt_address}\n"
                    lines[idx+7] = f'    rewriteModelName: "{gpt_model}"\n'
                if 'GPT4: # GPT4 API' in line:
                    lines[idx+2] = f"      - token: {gpt_token}\n"
                    lines[idx+4] = f"    defaultEndpoint: {gpt_address}\n"
            if 'moonshot' in translator:
                if 'GPT35:' in line:
                    lines[idx+4] = f"      - token: {gpt_token}\n"
                    lines[idx+6] = f"    defaultEndpoint: https://api.moonshot.cn\n"
                    lines[idx+7] = f'    rewriteModelName: "{translator}"\n'
            if 'deepseek' in translator:
                if 'GPT35:' in line:
                    lines[idx+4] = f"      - token: {gpt_token}\n"
                    lines[idx+6] = f"    defaultEndpoint: https://api.deepseek.com\n"
                    lines[idx+7] = f'    rewriteModelName: "{translator}"\n'
            if 'qwen2' in translator:
                if 'GPT35:' in line:
                    lines[idx+4] = f"      - token: {gpt_token}\n"
                    lines[idx+6] = f"    defaultEndpoint: https://dashscope.aliyuncs.com/compatible-mode\n"
                    lines[idx+7] = f'    rewriteModelName: "{translator}"\n'
            if 'glm' in translator:
                if 'GPT35:' in line:
                    lines[idx+4] = f"      - token: {gpt_token}\n"
                    lines[idx+6] = f"    defaultEndpoint: https://open.bigmodel.cn/api/paas\n"
                    lines[idx+7] = f'    rewriteModelName: "{translator}"\n'
            if 'abab' in translator:
                if 'GPT35:' in line:
                    lines[idx+4] = f"      - token: {gpt_token}\n"
                    lines[idx+6] = f"    defaultEndpoint: https://api.minimax.chat\n"
                    lines[idx+7] = f'    rewriteModelName: "{translator}"\n'
            if proxy_address:
                if 'proxy' in line:
                    lines[idx+1] = f"  enableProxy: true\n"
                    lines[idx+3] = f"    - address: {proxy_address}\n"
            else:
                if 'proxy' in line:
                    lines[idx+1] = f"  enableProxy: false\n"

        if 'moonshot' in translator or 'qwen2' in translator or 'glm' in translator or 'abab' in translator or 'gpt-custom' in translator or 'deepseek' in translator:
            translator = 'gpt35-1106'
        
        if 'index' in translator:
            translator = 'sakura-009'

        if 'galtransl' in translator:
            translator = 'sakura-010'

        with open('project/config.yaml', 'w', encoding='utf-8') as f:
            f.writelines(lines)

        for idx, input_file in enumerate(input_files):
            if not os.path.exists(input_file):
                if 'youtu.be' in input_file or 'youtube.com' in input_file:
                    if os.path.exists('project/YoutubeDL.webm'):
                        os.remove('project/YoutubeDL.webm')
                    with YoutubeDL({'proxy': proxy_address,'outtmpl': 'project/YoutubeDL.webm'}) as ydl:
                        self.status.emit("[INFO] 正在下载视频...")
                        results = ydl.download([input_file])
                        self.status.emit("[INFO] 视频下载完成！")
                    input_file = 'project/YoutubeDL.webm'

                elif 'BV' in yt_url:
                    self.status.emit("[INFO] 正在下载视频...")
                    res = send_request(URL_VIDEO_INFO, params={'bvid': input_file})
                    download([Video(
                        bvid=res['bvid'],
                        cid=res['cid'] if res['videos'] == 1 else res['pages'][0]['cid'],
                        title=res['title'] if res['videos'] == 1 else res['pages'][0]['part'],
                        up_name=res['owner']['name'],
                        cover_url=res['pic'] if res['videos'] == 1 else res['pages'][0]['pic'],
                    )], False)
                    self.status.emit("[INFO] 视频下载完成！")
                    title = res['title'] if res['videos'] == 1 else res['pages'][0]['part']
                    title = re.sub(r'[.:?/\\]', ' ', title).strip()
                    title = re.sub(r'\s+', ' ', title)
                    input_file = f'{title}.mp4'

                else:
                    self.status.emit(f"[ERROR] {input_file}文件不存在，请重新选择文件！")
                    continue

                if os.path.exists(os.path.join('project/cache', os.path.basename(input_file))):
                    os.remove(os.path.join('project/cache', os.path.basename(input_file)))
                input_file = shutil.move(input_file, 'project/cache/')

            self.status.emit(f"[INFO] 当前处理文件：{input_file} 第{idx+1}个，共{len(input_files)}个")

            os.makedirs('project/gt_input', exist_ok=True)
            if input_file.endswith('.srt'):
                self.status.emit("[INFO] 正在进行字幕转换...")
                output_file_path = os.path.join('project/gt_input', os.path.basename(input_file).replace('.srt','.json'))
                make_prompt(input_file, output_file_path)
                self.status.emit("[INFO] 字幕转换完成！")
            else:
                if whisper_file == '不进行听写':
                    self.status.emit("[INFO] 不进行听写，跳过听写步骤...")
                    continue

                if input_file.endswith('.wav'):
                    input_file = input_file[:-4]
                else:
                    self.status.emit("[INFO] 正在进行音频提取...")
                    self.pid = subprocess.Popen(['ffmpeg', '-y', '-i', input_file, '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', input_file+'.wav'])
                    self.pid.wait()
                    self.pid.kill()
                    self.pid.terminate()

                if not os.path.exists(input_file+'.wav'):
                    self.status.emit("[ERROR] 音频提取失败，请检查文件格式！")
                    break

                self.status.emit("[INFO] 正在进行语音识别...")

                if whisper_file.startswith('ggml'):
                    self.pid = subprocess.Popen(['whisper/whisper-cli', '-m', 'whisper/'+whisper_file, '-osrt', '-l', language, input_file+'.wav', '-of', input_file]+param_whisper.split())
                elif whisper_file.startswith('faster-whisper'):
                    self.pid = subprocess.Popen(['Whisper-Faster/whisper-faster.exe', '--beep_off', '--verbose', 'True', '--model', whisper_file[15:], '--model_dir', 'Whisper-Faster', '--task', 'transcribe', '--language', language, '--output_format', 'srt', '--output_dir', os.path.dirname(input_file), input_file+'.wav']+param_whisper.split())
                else:
                    self.status.emit("[INFO] 不进行听写，跳过听写步骤...")
                    continue
                self.pid.wait()
                self.pid.kill()
                self.pid.terminate()

                output_file_path = os.path.join('project/gt_input', os.path.basename(input_file)+'.json')
                make_prompt(input_file+'.srt', output_file_path)
                self.status.emit("[INFO] 语音识别完成！")

            if translator == '不进行翻译':
                self.status.emit("[INFO] 翻译器未选择，跳过翻译步骤...")
                continue

            if 'sakura' in translator or 'qwen' in translator:
                self.status.emit("[INFO] 正在启动Sakura翻译器...")
                if not sakura_file:
                    self.status.emit("[INFO] 未选择模型文件，跳过翻译步骤...")
                    continue

                self.pid = subprocess.Popen(['llama/llama-server', '-m', 'llama/'+sakura_file, '-ngl' , str(sakura_mode), '--port', '8989']+param_llama.split())

            self.status.emit("[INFO] 正在进行翻译...")
            worker('project', 'config.yaml', translator, show_banner=False)

            self.status.emit("[INFO] 正在生成字幕文件...")
            make_srt(output_file_path.replace('gt_input','gt_output'), input_file+'.zh.srt')
            make_lrc(output_file_path.replace('gt_input','gt_output'), input_file+'.lrc')
            self.status.emit("[INFO] 字幕文件生成完成！")

            if 'sakura' in translator:
                self.pid.kill()
                self.pid.terminate()

        self.status.emit("[INFO] 所有文件处理完成！")
        self.finished.emit()

if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
