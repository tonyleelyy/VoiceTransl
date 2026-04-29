import os
import shutil
import threading
import queue
import asyncio
import yaml

from GalTransl.ConfigHelper import CProjectConfig
from GalTransl.Runner import run_galtransl
from prompt2srt import make_srt, make_lrc, merge_lrc_files
from srt2prompt import merge_srt_files


class ConcurrentTranslationPool:
    """并发翻译线程池：每文件一个线程，工作空间隔离"""

    def __init__(self, project_dir, base_config_path, max_concurrent, stop_event):
        self._project_dir = project_dir
        self._base_config_path = base_config_path
        self._max_concurrent = max_concurrent
        self._stop_event = stop_event
        self._queue = queue.Queue()
        self._workspace_counter = 0
        self._counter_lock = threading.Lock()
        self._active_threads: list[threading.Thread] = []
        self._error_count = 0
        self._error_lock = threading.Lock()

    @property
    def error_count(self):
        with self._error_lock:
            return self._error_count

    def start(self, engine, status_callback):
        """启动 N 个工作线程"""
        self._engine = engine
        self._status_callback = status_callback
        for _ in range(self._max_concurrent):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            self._active_threads.append(t)
            t.start()

    def submit(self, tf):
        """提交翻译任务"""
        self._queue.put(tf)

    def done(self):
        """所有任务已提交，发送哨兵信号"""
        for _ in range(self._max_concurrent):
            self._queue.put(None)

    def wait_all(self, timeout=600):
        """等待所有工作线程结束"""
        for t in self._active_threads:
            t.join(timeout=timeout)

    def stop(self):
        """停止所有工作线程：设置停止事件 + 清空待处理队列"""
        self._stop_event.set()
        # 清空队列中未处理的任务，让线程尽快退出
        while True:
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break

    def _worker_loop(self):
        """工作线程主循环：从队列取任务 -> 翻译 -> 输出"""
        while not self._stop_event.is_set():
            try:
                tf = self._queue.get(timeout=1)
            except queue.Empty:
                continue

            if tf is None:  # 哨兵信号
                self._queue.task_done()
                break

            # 取出任务后再次检查停止信号，避免取消后仍启动新翻译
            if self._stop_event.is_set():
                self._queue.task_done()
                continue

            try:
                self._translate_one(tf)
            finally:
                self._queue.task_done()

    def _translate_one(self, tf):
        """翻译单个文件：创建工作空间 -> 复制输入 -> 运行 GalTransl -> 生成输出"""
        base = os.path.basename(tf.base_path)
        self._status_callback(f"[INFO] 开始翻译：{base}")

        if self._stop_event.is_set():
            return

        workspace = self._create_workspace()
        json_name = os.path.basename(tf.json_src)

        # 将听写产出的 JSON 复制到工作空间的 gt_input
        shutil.copy(tf.json_src, os.path.join(workspace, 'gt_input', json_name))

        # 准备独立配置文件
        self._prepare_config(workspace)

        try:
            cfg = CProjectConfig(workspace, 'config.yaml')
            asyncio.run(run_galtransl(cfg, self._engine))
        except Exception as e:
            self._status_callback(f"[ERROR] 翻译 {base} 失败: {e}")
            with self._error_lock:
                self._error_count += 1
            return

        # 生成翻译后字幕
        self._status_callback(f"[INFO] 正在生成字幕文件：{base}...")
        self._generate_output(tf, workspace)

        self._status_callback(f"[INFO] 文件 {base} 翻译完成！")

    def _create_workspace(self):
        """分配独立工作空间目录 project/cache/translate_<N>/"""
        with self._counter_lock:
            idx = self._workspace_counter
            self._workspace_counter += 1
        workspace = os.path.join(self._project_dir, 'cache', f'translate_{idx}')
        for sub in ('gt_input', 'gt_output', 'transl_cache'):
            os.makedirs(os.path.join(workspace, sub), exist_ok=True)
        return workspace

    def _prepare_config(self, workspace):
        """从主配置复制并调整路径，返回工作空间内 config.yaml 路径"""
        with open(self._base_config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 将 (project_dir) 替换为主项目目录的绝对路径，保持字典引用正确
        abs_project_dir = os.path.abspath(self._project_dir).replace('\\', '/')
        content = content.replace('(project_dir)', abs_project_dir + '/')

        config_path = os.path.join(workspace, 'config.yaml')
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return config_path

    def _generate_output(self, tf, workspace):
        """从工作空间的 gt_output 生成字幕文件到实际输出目录"""
        json_name = os.path.basename(tf.json_src)
        gt_output_json = os.path.join(workspace, 'gt_output', json_name)
        base_name = os.path.basename(tf.base_path)

        if tf.output_format in ('中文SRT', '双语SRT'):
            zh_srt_output = os.path.join(tf.output_dir, base_name + '.zh.srt')
            make_srt(gt_output_json, zh_srt_output)

        if tf.output_format in ('中文LRC', '双语LRC'):
            lrc_output = os.path.join(tf.output_dir, base_name + '.lrc')
            make_lrc(gt_output_json, lrc_output)

        # 双语合并
        if tf.output_format == '双语SRT':
            left = os.path.join(tf.output_dir, base_name + '.srt')
            right = os.path.join(tf.output_dir, base_name + '.zh.srt')
            if os.path.exists(left) and os.path.exists(right):
                merge_srt_files([left, right],
                                os.path.join(tf.output_dir, base_name + '.combine.srt'))

        if tf.output_format == '双语LRC':
            left = os.path.join(tf.output_dir, base_name + '.orig.lrc')
            right = os.path.join(tf.output_dir, base_name + '.zh.lrc')
            if os.path.exists(left) and os.path.exists(right):
                merge_lrc_files([left, right],
                                os.path.join(tf.output_dir, base_name + '.combine.lrc'))
