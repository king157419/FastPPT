"""视频处理模块：关键帧提取 + Qwen-VL 理解 + Paraformer 字幕

流程：
  视频文件
    ├── 音频轨 → Paraformer → 字幕文本 → 分块入 RAG
    └── 视频帧 → OpenCV 每10s一帧
              → Qwen-VL-Max 理解帧内容
              → 帧截图保存（可作为PPT配图）
              → 帧描述入 RAG
"""
import os
import base64
import tempfile
from dataclasses import dataclass, field


@dataclass
class VideoFrame:
    id: str                    # e.g. "frame_001"
    timestamp: float           # 秒
    image_base64: str          # JPEG base64（空字符串表示未保存）
    description: str = ""      # Qwen-VL 理解的内容
    save_path: str = ""        # 磁盘保存路径


@dataclass
class VideoParseResult:
    frames: list[VideoFrame] = field(default_factory=list)
    subtitle_text: str = ""    # 完整字幕文本
    duration: float = 0.0      # 视频时长(秒)
    error: str = ""            # 非空表示部分失败


FRAME_INTERVAL = 10  # 每隔多少秒取一帧
MAX_FRAMES = 30      # 最多取帧数（防止超长视频）
MAX_VIDEO_SECONDS = 600  # 限制视频最长10分钟


def parse_video(video_path: str, output_dir: str = "uploads") -> VideoParseResult:
    """
    解析视频文件，返回 VideoParseResult。
    output_dir: 帧截图保存目录
    """
    result = VideoParseResult()
    try:
        import cv2
    except ImportError:
        result.error = "opencv-python 未安装"
        return result

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        result.error = f"无法打开视频文件: {video_path}"
        return result

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    result.duration = total_frames / fps

    if result.duration > MAX_VIDEO_SECONDS:
        result.error = f"视频超过{MAX_VIDEO_SECONDS//60}分钟，已截断处理前{MAX_VIDEO_SECONDS//60}分钟"

    # ---- 提取关键帧 ----
    frame_count = 0
    target_seconds = 0.0
    while target_seconds <= min(result.duration, MAX_VIDEO_SECONDS) and frame_count < MAX_FRAMES:
        cap.set(cv2.CAP_PROP_POS_MSEC, target_seconds * 1000)
        ret, frame = cap.read()
        if not ret:
            break

        # 编码为 JPEG base64
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        img_b64 = base64.b64encode(buf.tobytes()).decode()

        frame_id = f"frame_{frame_count:03d}"
        save_path = os.path.join(output_dir, f"{os.path.basename(video_path)}_{frame_id}.jpg")
        with open(save_path, "wb") as f:
            f.write(buf.tobytes())

        vf = VideoFrame(
            id=frame_id,
            timestamp=target_seconds,
            image_base64=img_b64,
            save_path=save_path,
        )
        result.frames.append(vf)
        frame_count += 1
        target_seconds += FRAME_INTERVAL

    cap.release()

    # ---- Qwen-VL 理解每帧 ----
    if os.environ.get("DASHSCOPE_API_KEY"):
        _describe_frames(result.frames)

    # ---- Paraformer 字幕提取 ----
    subtitle = _extract_subtitle(video_path)
    result.subtitle_text = subtitle

    return result


def _describe_frames(frames: list[VideoFrame]):
    """批量调用 Qwen-VL-Max 理解帧内容"""
    from core.llm import describe_image
    for frame in frames:
        try:
            frame.description = describe_image(
                frame.image_base64,
                prompt="请简洁描述这一帧的教学内容（知识点、公式、图表、代码等），50字以内。",
            )
        except Exception as e:
            frame.description = f"[帧{frame.id} 理解失败: {e}]"


def _extract_subtitle(video_path: str) -> str:
    """用 Paraformer 提取视频字幕，返回纯文本"""
    try:
        import dashscope
        from dashscope.audio.asr import Transcription
        dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        if not dashscope.api_key:
            return ""

        # 先提取音频轨
        audio_path = _extract_audio(video_path)
        if not audio_path:
            return ""

        response = Transcription.async_call(
            model="paraformer-v2",
            file_urls=[f"file://{os.path.abspath(audio_path)}"],
            language_hints=["zh", "en"],
        )
        # 等待完成（同步等待，最多60s）
        response = Transcription.wait(response)
        if response.status_code == 200:
            results = response.output.get("results", [])
            texts = []
            for r in results:
                for sentence in r.get("transcription", {}).get("sentences", []):
                    texts.append(sentence.get("text", ""))
            return " ".join(texts)
    except Exception as e:
        print(f"[Video] Paraformer subtitle failed: {e}")
    return ""


def _extract_audio(video_path: str) -> str:
    """从视频提取音频，返回临时 wav 文件路径"""
    try:
        import subprocess
        audio_path = video_path + "_audio.wav"
        ret = subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-vn", "-ar", "16000", "-ac", "1", audio_path],
            capture_output=True, timeout=120,
        )
        if ret.returncode == 0 and os.path.exists(audio_path):
            return audio_path
    except Exception as e:
        print(f"[Video] ffmpeg audio extract failed: {e}")
    return ""


def build_rag_chunks(result: VideoParseResult) -> list[str]:
    """
    将解析结果转为 RAG 文本块列表，供 rag.add_document() 使用。
    """
    chunks = []
    # 字幕分块（每300字）
    if result.subtitle_text:
        text = result.subtitle_text
        size = 300
        for i in range(0, len(text), size - 50):
            chunks.append(text[i:i + size])

    # 每帧描述
    for frame in result.frames:
        if frame.description:
            chunks.append(f"[视频帧 {frame.id} @ {frame.timestamp:.0f}s] {frame.description}")

    return chunks
