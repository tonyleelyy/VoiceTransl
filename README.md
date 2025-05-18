
<h1><p align='center' >VoiceTransl</p></h1>
<div align=center><img src="https://img.shields.io/github/v/release/shinnpuru/VoiceTransl"/>   <img src="https://img.shields.io/github/license/shinnpuru/VoiceTransl"/>   <img src="https://img.shields.io/github/stars/shinnpuru/VoiceTransl"/></div>

VoiceTransl是一站式离线AI视频字幕生成和翻译软件，从视频下载，音频提取，听写打轴，字幕翻译，视频合成，字幕总结各个环节为翻译者提供便利。本项目基于[Galtransl](https://github.com/xd2333/GalTransl)，采用GPLv3许可。使用说明请见 [视频教程](https://www.bilibili.com/video/BV1koZ6YuE1x)。

<div align=center><img src="title.jpg" alt="title" style="width:512px;"/></div>

## 特色

* 支持多种翻译模型，包括在线模型（任意OpenAI兼容接口）和本地模型（Sakura、Galtransl及Ollama、Llamacpp）。
* 支持AMD/NVIDIA/Intel GPU加速，翻译引擎支持调整显存占用。
* 支持多种输入格式，包括音频、视频、SRT字幕。
* 支持多种输出格式，包括SRT字幕、LRC字幕。
* 支持多种语言，包括日语，英语，韩语，俄语，法语。
* 支持字典功能，可以自定义翻译字典，替换输入输出。
* 支持从YouTube/Bilibili及媒体链接直接下载视频。
* 支持文件和链接批量处理，自动识别文件类型。
* 支持音频切分，字幕合并和视频合成。
* 支持字幕总结，可以自定义Prompt。

## 下载

下载最新版本的[VoiceTransl](https://github.com/shinnpuru/VoiceTransl/releases/)，解压后运行`VoiceTransl.exe`。

## 听写

* 本项目使用[whisper.cpp](https://github.com/ggerganov/whisper.cpp)模型，引擎已经为Vulkan编译配置好，兼容N卡/A卡/I卡。模型需要自行下载，请选择合适的whisper.cpp模型下载然后放到`whisper`文件夹。

| 名称 | 磁盘    | 显存     | 链接 |
| ------ | ------- | ------- | ----- |
| ggml-small.bin  | 466 MiB | ~852 MB | [下载](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin?download=true) |
| ggml-medium.bin | 1.5 GiB | ~2.1 GB | [下载](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin?download=true) |
| ggml-large-v2.bin  | 2.9 GiB | ~3.9 GB | [下载](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v2.bin?download=true) |

* NVIDIA显卡可以使用[faster-whisper](https://github.com/Purfview/whisper-standalone-win)模型，支持更高的速度和VAD功能。请根据[配置要求](whisper-faster/README.md)下载文件。模型需要自行下载，请选择合适的模型下载然后放到`whisper-faster`文件夹。

| 名称  | 磁盘    | 显存     | 链接 |
| ------ | ------- | ------- | ----- |
| faster-whisper-small  | 463 MiB | ~1 GB | [下载](https://huggingface.co/Systran/faster-whisper-small) |
| faster-whisper-medium | 1.42 GiB | ~2 GB | [下载](https://huggingface.co/Systran/faster-whisper-medium) |
| faster-whisper-large-v3  | 2.87 GiB | ~3 GB | [下载](https://huggingface.co/Systran/faster-whisper-large-v3) |

`faster-whisper`模型请参考下面的文件夹结构，必须要以`faster-whisper-`开头。

```plaintext
faster-whisper-xxx/
    config.json
    model.bin
    preprocessor_config.json
    tokenizer.json
    vocabulary.json
```


## 在线翻译

本项目支持以下在线模型API接口，需要填写模型名称和Token。

  * [DeepSeek系列](https://platform.deepseek.com/)
  * [Moonshot系列](https://platform.moonshot.cn/)
  * [GLM系列](https://open.bigmodel.cn)
  * [Minimax系列](https://platform.minimaxi.com/)
  * [Doubao系列](https://doubao.ai)
  * [Qwen系列](https://help.aliyun.com/zh/model-studio/developer-reference/use-qwen-by-calling-api)
  * [Gemini系列](https://www.gemini.ai)
  * [Ollama引擎](https://ollama.com/blog/openai-compatibility)

其他模型请使用`gpt-custom`兼容接口并配置自定义OpenAI地址（例如`https://api.openai.com`，默认会自动添加`/v1/chat/completions`）。

## 离线翻译

* 本地翻译模型基于[llama.cpp](https://github.com/ggerganov/llama.cpp)引擎，已经为Vulkan编译配置好，兼容N卡/A卡/I卡。

* NVIDIA显卡可以使用为[CUDA编译的版本](https://github.com/ggerganov/llama.cpp/releases/latest)，支持更高的速度和显存占用，请解压到`llama`文件夹覆盖原有文件。

```
cudart-llama-bin-win-cu12.4-x64.zip
llama-bxxxx-bin-win-cuda-cu12.4-x64.zip
```

* 模型需要自行下载，请选择合适的llama.cpp模型下载然后放到`llama`文件夹。选择模型的时候请使用对应代码，并选择模型。非日语模型，如Qwen和Gemma，请选择`llamacpp`。

| 名称 | 语言 | 代码 | 磁盘    | 显存     | 链接 |
| ------ | ------ | ------ |  ------- | ------- | ----- |
| [Sakura-7B-v1.0-Q4](https://github.com/SakuraLLM/SakuraLLM) | 日语 | sakura-010 |  ~5 GiB | ~8 GB | [下载](https://huggingface.co/SakuraLLM/Sakura-7B-Qwen2.5-v1.0-GGUF) |
| [Sakura-GalTransl-7B-v3](https://github.com/xd2333/GalTransl) | 日语 | galtransl | ~5 GiB | ~8 GB | [下载](https://huggingface.co/SakuraLLM/Sakura-GalTransl-7B-v3) |
| [Sakura-14B-v1.0-Q4](https://github.com/SakuraLLM/SakuraLLM) | 日语 |  sakura-010 | ~9 GiB | ~16 GB | [下载](https://huggingface.co/SakuraLLM/Sakura-14B-Qwen2.5-v1.0-GGUF) |

## 模式

本软件支持四种模式，分别是下载模式，翻译模式，听写模式和完整模式。

1. 下载模式：支持从YouTube/Bilibili直接下载视频。请填写视频链接，语音识别选择不进行听写，字幕翻译选择不进行翻译，然后点击运行按钮。
2. 翻译模式：支持字幕翻译，支持多种翻译模型。请填写字幕文件，语音识别选择不进行听写，字幕翻译选择模型，然后点击运行按钮。
3. 听写模式：支持音频听写，支持多种听写模型。请填写音视频文件或视频链接，语音识别选择模型，字幕翻译选择不进行翻译，然后点击运行按钮。
4. 完整模式：支持从下载到翻译的完整流程。请填写音视频文件或视频链接，语音识别选择模型，字幕翻译选择模型，然后点击运行按钮。

## 常见问题

1. 翻译时提示网络连接错误

* 在线模型请检查网络连接是否正常，或者尝试更换代理。
* 离线模型出现连接错误，先检查是否超显存，把离线参数从0开始逐步增加10；然后确认关闭所有的代理软件，在系统设置-网络和Internet-代理里面应该是空的。

2. 多次使用之后闪退

缓存文件中可能存在问题，可以尝试清理下载缓存，或者重新解压程序到一个新的目录。

3. 命令行输出乱码

请检查系统编码是否为UTF-8，Windows控制面板-区域-更改日期、时间或数字格式-管理-更改系统区域设置-使用UTF-8提供全球语言支持。

4. 不是Windows系统可以用吗

Linux可以使用服务器部署进行运行，详细请参考[server分支](https://github.com/shinnpuru/GalTransl-for-ASMR/tree/server)。MacOS暂时不支持，用户可以使用[镜像部署](https://www.compshare.cn/images-detail?ImageID=compshareImage-16qc028dgfoh&ImageType=Community)。

5. 没有显卡/手机可以用吗

可以使用在线镜像进行运行，不需要显卡，手机也可以用，详细请参考[镜像部署](https://www.compshare.cn/images-detail?ImageID=compshareImage-16qc028dgfoh&ImageType=Community)。

## 开发

1. 安装依赖
```
pip install -r requirements.txt
```

2. 构建程序
```
pyinstaller app.spec
```

## 声明

本软件仅供学习交流使用，不得用于商业用途。本软件不对任何使用者的行为负责，不保证翻译结果的准确性。使用本软件即代表您同意自行承担使用本软件的风险，包括但不限于版权风险、法律风险等。请遵守当地法律法规，不要使用本软件进行任何违法行为。

## 如果对你有帮助的话请给一个Star!

![Star History Chart](https://api.star-history.com/svg?repos=shinnpuru/VoiceTransl&type=Date)
