"""语音识别接口：Paraformer ASR"""
import os
import uuid
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
import aiofiles

router = APIRouter()


@router.post("/asr")
async def asr(file: UploadFile = File(...)):
    """
    接收录音文件（WAV/MP3/WebM），调用 Paraformer 返回识别文字。
    前端可用 MediaRecorder API 录制后上传。
    """
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise HTTPException(503, "未配置 DASHSCOPE_API_KEY，语音识别不可用")

    ext = os.path.splitext(file.filename or "")[1].lower() or ".wav"
    tmp_path = os.path.join("uploads", f"asr_{uuid.uuid4().hex[:8]}{ext}")

    async with aiofiles.open(tmp_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    try:
        text = _transcribe(tmp_path, api_key)
    except Exception as e:
        raise HTTPException(500, f"语音识别失败：{e}")
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    return {"text": text}


def _transcribe(audio_path: str, api_key: str) -> str:
    """调用 DashScope Paraformer 识别音频，返回文字"""
    import dashscope
    from dashscope.audio.asr import Recognition

    dashscope.api_key = api_key

    # Paraformer 实时识别（短音频 <60s 直接同步）
    recognition = Recognition(
        model="paraformer-realtime-v2",
        format=audio_path.rsplit(".", 1)[-1].lower(),
        sample_rate=16000,
        language_hints=["zh", "en"],
        callback=None,
    )
    result = recognition.call(audio_path)
    if result.status_code == 200:
        sentences = result.get_sentence()
        return " ".join(s["text"] for s in sentences if s.get("text"))
    # fallback: 异步转写（适合长音频）
    return _transcribe_async(audio_path, api_key)


def _transcribe_async(audio_path: str, api_key: str) -> str:
    """Paraformer 异步转写（长音频备用路径）"""
    import dashscope
    from dashscope.audio.asr import Transcription

    dashscope.api_key = api_key
    abs_path = os.path.abspath(audio_path)
    response = Transcription.async_call(
        model="paraformer-v2",
        file_urls=[f"file://{abs_path}"],
        language_hints=["zh", "en"],
    )
    response = Transcription.wait(response)
    if response.status_code == 200:
        texts = []
        for r in response.output.get("results", []):
            for s in r.get("transcription", {}).get("sentences", []):
                texts.append(s.get("text", ""))
        return " ".join(texts)
    raise RuntimeError(f"Transcription failed: {response.message}")
