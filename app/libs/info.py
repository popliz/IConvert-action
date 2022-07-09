import subprocess
from enum import Enum
from pathlib import Path

from app.libs.json import str_parse_json


class VC(str, Enum):
  VP9 = "vp9"
  H264 = "h264"


class AC(str, Enum):
  OPUS = "opus"
  AAC = "aac"


class VideoInfo:

  def __init__(
      self,
      path: Path,
  ):
    result = subprocess.run(
        [
            "ffprobe",
            "-hide_banner",
            "-loglevel",
            "quiet",
            "-show_format",
            "-show_streams",
            "-print_format",
            "json",
            path.as_posix(),
        ],
        capture_output=True,
        check=True,
    )
    info_obj = str_parse_json(result.stdout.decode("utf-8"))

    self.streams = info_obj["streams"]
    self.format = info_obj["format"]
    self.video_streams = dict()
    self.audio_streams = dict()
    for index, stream in enumerate(self.streams):
      if stream.get("codec_type") == "video":
        self.video_streams[index] = {
            # vp9 h264 hevc
            "codec": stream.get("codec_name"),
            # yuv420p yuv422p yuv444p yuvj420p yuvj422p yuvj444p yuv420p10le yuv422p10le yuv444p10le
            "pix_fmt": stream.get("pix_fmt"),
            # 8 10 12
            "bits": stream.get("bits_per_raw_sample")
        }
      if stream.get("codec_type") == "audio":
        self.audio_streams[index] = {
            # aac opus
            "codec": stream.get("codec_name"),
        }

  def match_vc(self, vc):
    for index, video_stream in self.video_streams.items():
      if video_stream.get("codec") == vc:
        return index
    return None

  def match_ac(self, ac):
    for index, audio_stream in self.audio_streams.items():
      if audio_stream.get("codec") == ac:
        return index
    return None
