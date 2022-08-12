import time
import subprocess
import logging
import sys
from pathlib import Path

import app.var as GLOBAL
from app.libs.encode import get_file_encoding, file_to_utf8
from app.libs.info import VideoInfo, AC, VC
from app.libs.path import rm, change_parent_dir


def ffmpeg_subprocess(command):
  logging.debug(f"执行命令: {' '.join(command)}")
  now_time = time.time()
  with subprocess.Popen(
      command,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      bufsize=1,
      text=True,
      encoding="utf-8",
      errors="utf-8",
  ) as proc:
    log_count = 40
    log_interval = 58
    if proc.stdout is None:
      raise subprocess.SubprocessError("子进程没有标准输出")
    while True:
      text = proc.stdout.readline().rstrip("\n")
      if text == "":
        if proc.poll() is None:
          logging.debug("子进程未退出，等待1秒")
          time.sleep(1)
          continue
        else:
          logging.debug("子进程已退出，转换完毕")
          break
      elif text.startswith("frame="):
        if log_count == log_interval:
          log_count = 0
          logging.info(text)
          if time.time() - now_time > 20000:
            raise subprocess.TimeoutExpired(command, 20000, "超时20000s")
        else:
          log_count += 1
      else:
        logging.debug(text)
    if proc.returncode != 0:
      raise subprocess.SubprocessError("ffmpeg转换失败，检查日志查看详细信息")


def ffmpeg_convert(video_path: Path):
  video_format = GLOBAL.CONFIG.format

  video_info = VideoInfo(video_path)
  if video_format == "webm":
    match_vc_index = video_info.match_vc(VC.VP9)
    match_ac_index = video_info.match_ac(AC.OPUS)
  else:
    match_vc_index = video_info.match_vc(VC.H264)
    match_ac_index = video_info.match_vc(AC.AAC)

  # 计算输出文件路径
  output_path = change_parent_dir(
      video_path, Path(GLOBAL.CONFIG.input_dir),
      Path(GLOBAL.CONFIG.output_dir)).with_suffix(f".{video_format}")
  output_path.parent.mkdir(parents=True, exist_ok=True)

  # 检查字幕文件是否存在
  sub_path = None
  for sub_suffix in ["ass", "ssa", "srt", "ASS", "SSA", "SRT"]:
    sp = video_path.with_suffix(f".{sub_suffix}")
    if sp.exists():
      sub_path = sp
      break
  # 确保字幕文件的编码为UTF-8
  if sub_path is not None:
    sub_file_encoding = get_file_encoding(sub_path)
    if sub_file_encoding != "UTF-8":
      logging.debug(f"字幕文件编码为{sub_file_encoding}, 转换为UTF-8")
      file_to_utf8(sub_file_encoding, sub_path, sub_path)

  # 判断是否可以跳过
  if (video_path.suffix[1:] == video_format and match_vc_index is not None and
      match_ac_index is not None and sub_path is None):
    logging.info("输入文件与转码格式完全相同，且没有字幕文件，跳过")
    return

  # build ffmpeg run command
  # sn mean not subtitle stream
  command = [
      "ffmpeg",
      "-hide_banner",
      "-y",
      "-loglevel",
      "info",
      "-i",
      video_path.as_posix(),
  ]
  command.extend(["-threads", str(GLOBAL.CONFIG.thread)])

  if match_vc_index is None or sub_path is not None:
    if video_format == "webm":
      command.extend([
          "-c:v",
          "libvpx-vp9",
          "-pix_fmt",
          "yuv420p",
          "-quality",
          "good",
          "-profile:v",
          "0",
          "-cpu-used",
          "2",
          "-lag-in-frames",
          "25",
          "-crf",
          "23",
          "-b:v",
          "0",
          "-g",
          "240",
          "-arnr-maxframes",
          "7",
          "-arnr-strength",
          "5",
          "-enable-tpl",
          "1",
          # github action只有两个核心，无需开启row-mt
          # "-row-mt",
          # "1",
      ])
    else:
      command.extend([
          "-movflags",
          "+faststart",
          "-c:v",
          "libx264",
          "-preset",
          "medium",
          "-pix_fmt",
          "yuv420p",
          "-crf",
          "20",
      ])
  else:
    command.extend([f"-c:v:{match_vc_index}", "copy"])

  # 去除自带字幕
  command.extend(["-sn"])

  # 添加字幕
  if sub_path is not None:
    if sub_path.suffix.lower() == ".srt":
      sub_command = "subtitles"
    elif sub_path.suffix.lower() == ".ass":
      sub_command = "ass"
    else:
      logging.error("字幕格式不正确！")
      sys.exit(1)

    command.extend([
        "-vf",
        f"{sub_command}={sub_path.as_posix()}",
    ])

  if match_ac_index is None:
    if video_format == "webm":
      command.extend([
          "-c:a",
          "libopus",
          "-ac",
          "2",
          "-b:a",
          "192K",
      ])
    else:
      command.extend([
          "-c:a",
          "libfdk_aac",
          "-ac",
          "2",
          "-vbr",
          "5",
      ])
  else:
    command.extend([f"-c:a:{match_ac_index}", "copy"])

  if video_format == "webm":
    command.extend(["-f", "webm"])
  else:
    command.extend(["-f", "mp4"])

  command.append(output_path.as_posix())

  # 开始转码
  ffmpeg_subprocess(command)

  # keep origin file
  if GLOBAL.CONFIG.keep_origin is False:
    rm(video_path)
    logging.info(f"删除原始文件{str(video_path)}")
    if sub_path is not None:
      rm(sub_path)
      logging.info(f"删除字幕文件{str(sub_path)}")

  return output_path
  # move target file
  # dist_path = input_path.parent.joinpath(
  #     temp_path.name.rstrip("vctemp").rstrip("."))
  # move(temp_path, dist_path)
  # logging.debug(f"Moved temp file to {str(dist_path)}")

  # get video duration
  # try:
  #     video_duration = int(info["format"]["duration"][:-7])
  # except KeyError:
  #     logging.debug(f"can't get duration from {input_path.as_posix()}, skip...")
  #     return


# def handbrake_convert(input_path, temp_path):
#   input_path_str = input_path.as_posix()

#   # build handbrake run command
#   command = [
#       "handbrake",
#       "--format",
#       f"av_{config['format']}",
#       "-r",
#       "60",
#       "--pfr",
#       "--optimize",
#   ]

#   if config["vc"] == "h264":
#     command.extend([
#         "--encoder",
#         "x264",
#         "--encoder-profile",
#         "high",
#         "--encoder-level",
#         "4.1",
#     ])
#   elif config["vc"] == "h265":
#     command.extend([
#         "--encoder",
#         "x265",
#         "--encoder-profile",
#         "main",
#     ])
#   elif config["vc"] == "vp9":
#     command.extend(["--encoder", "VP9"])

#   command.extend([
#       "--quality",
#       config["crf"],
#       "--encoder-preset",
#       config["preset"],
#       # "--align-av",
#       "--auto-anamorphic",
#       "--keep-display-aspect",
#       # "--maxHeight",
#       # "1080",
#       # "--maxWidth",
#       # "1920",
#       "--main-feature",
#       "--first-audio",
#   ])

#   if config["ac"] == "aac":
#     command.extend(["--aencoder", "copy:aac", "--audio-fallback", "ca_haac"])
#   elif config["ac"] == "opus":
#     command.extend(["--aencoder", "opus"])
#   command.extend(["--aq", "8"])

#   if config["remove_subtitle"] != "true":
#     command.extend([
#         "--all-subtitles",
#         #  "--subtitle-lang-list", "eng,chi"
#     ])

#   command.extend([
#       "-i",
#       input_path_str,
#       "-o",
#       temp_path.as_posix(),
#   ])
#   logging.debug(f"execute command: {' '.join(command)}")

#   with subprocess.Popen(
#       command,
#       stdout=subprocess.PIPE,
#       stderr=subprocess.STDOUT,
#       bufsize=1,
#       text=True,
#       encoding="utf-8",
#       errors="ignore",
#   ) as proc:
#     log_count = 50
#     log_interval = 58
#     while True:
#       text = proc.stdout.readline().rstrip("\n")
#       if text == "":
#         if proc.poll() is None:
#           logging.debug("subprocess not exit, sleep 0.5s")
#           sleep(0.5)
#           continue
#         else:
#           logging.debug("subprocess exit, done")
#           break
#       elif text.startswith("frame="):
#         if log_count == log_interval:
#           log_count = 0
#           logging.info(text)
#         else:
#           log_count += 1
#       else:
#         logging.debug(text)
#     if proc.returncode != 0:
#       raise subprocess.SubprocessError(
#           "handbrake error, check debug level log for more information.")

#   # rename and keep origin file
#   origin_input_path = Path(f"{input_path_str}.origin")
#   input_path.rename(origin_input_path)
#   logging.debug(f"Renamed origin file to {str(origin_input_path)}")

#   # move target file
#   dist_path = input_path.parent.joinpath(
#       temp_path.name.rstrip("vctemp").rstrip("."))
#   move(temp_path, dist_path)
#   logging.debug(f"Moved temp file to {str(dist_path)}")

#   return Path(dist_path), [origin_input_path]

# # def uncompress(in_path_str, out_path_str):
# #     command = ["7z", "e", "-y", "-o" + out_path_str, "-aoa", in_path_str]
# #     print(f"Start uncompress: {in_path_str}")
# #     res = subprocess.run(command, stdout=subprocess.PIPE)
# #     if res.returncode != 0:
# #         raise subprocess.SubprocessError(
# #             "uncompress error, set debug mode and check log file for more information.")
# #     else:
# #         print("Complete uncompress.")

# def burn_sub(input_path, sub_path, temp_path):
#   info = Info(input_path)
#   info.match_video_codec(config["vc"])
#   video_bit = info.get_bit()
#   audio_index = info.match_audio_codec(config["ac"])
#   input_path_str = input_path.as_posix()
#   sub_path_str = sub_path.as_posix()
#   sub_path_format = sub_path.suffix[1:]
#   sub_file_encoding = file_encoding(sub_path)

#   if sub_path_format == "srt":
#     ffmpeg_sub_command = "subtitles"
#   elif sub_path_format == "ass" or sub_path_format == "ssa":
#     ffmpeg_sub_command = "ass"
#   else:
#     logging.error(f"Unrecognized subtitle format: {sub_path_format}")
#     return

#   if sub_file_encoding == "UTF-8":
#     temp_sub_path = sub_path
#     logging.debug("sub file encoding is UTF-8, no need to convert")
#   else:
#     temp_sub_path = change_parent_dir(sub_path, config["input_dir"],
#                                       config["temp_sub_dir"])
#     logging.debug(
#         f"sub file encoding is {sub_file_encoding}, convert to UTF-8...")
#     to_utf8(sub_file_encoding, sub_path, temp_sub_path)

#   command = [
#       "ffmpeg",
#       "-hide_banner",
#       "-y",
#       "-loglevel",
#       "info",
#       "-i",
#       input_path_str,
#       "-vf",
#       f"{ffmpeg_sub_command}={quote(temp_sub_path.as_posix())}",
#       "-movflags",
#       "+faststart",
#       "-max_muxing_queue_size",
#       "1024",
#   ]

#   if config["format"] == "mkv":
#     command.extend(["-f", "matroska"])
#   elif config["format"] == "mp4":
#     command.extend(["-f", "mp4"])
#   elif config["format"] == "webm":
#     command.extend(["-f", "webm"])

#   if config["threads"] != "0":
#     command.extend(["-threads", config["threads"]])

#   # pix_fmt: yuv420p yuv422p yuv444p yuvj420p yuvj422p yuvj444p yuv420p10le yuv422p10le
#   yuv444p10le
#   # for x265 doc, see https://x265.readthedocs.io/en/default/cli.html#profile-level-tier
#   if config["vc"] == "h264":
#     command.extend(
#         ["-c:v", "libx264", "-level:v", "4.1", "-preset", config["preset"]])
#     if video_bit == "8":
#       command.extend(["-profile:v", "high", "-pix_fmt", "yuv420p"])
#     elif video_bit == "10":
#       command.extend(["-profile:v", "high10", "-pix_fmt", "yuv420p10le"])
#   elif config["vc"] == "h265":
#     command.extend([
#         "-c:v",
#         "libx265",
#         "-preset",
#         config["preset"],
#     ])
#     if video_bit == "8":
#       command.extend(["-profile:v", "main", "-pix_fmt", "yuv420p"])
#     elif video_bit == "10":
#       command.extend(["-profile:v", "main10", "-pix_fmt", "yuv420p10le"])
#   elif config["vc"] == "vp9":
#     command.extend([
#         "-c:v",
#         "libvpx-vp9",
#         # https://trac.ffmpeg.org/wiki/Encode/VP9#constantq
#         "-b:v",
#         "0",
#         # https://trac.ffmpeg.org/wiki/Encode/VP9#rowmt
#         "-row-mt",
#         "1",
#     ])
#     if video_bit == "8":
#       command.extend(["-pix_fmt", "yuv420p"])
#     elif video_bit == "10":
#       command.extend(["-pix_fmt", "yuv420p10le"])

#   command.extend(["-crf", config["crf"]])

#   if audio_index is None or config["force_convert"] == "true":
#     if config["ac"] == "aac":
#       # -vbr min:1 max:5
#       command.extend(["-c:a", "libfdk_aac", "-vbr", "5"])
#     elif config["ac"] == "opus":
#       command.extend(["-c:a", "libopus", "-vbr", "on", "-b:a", "96K"])
#   else:
#     command.extend([f"-c:a:{audio_index}", "copy"])

#   command.append(temp_path.as_posix())
#   logging.debug(f"execute command: {' '.join(command)}")

#   # start convert
#   with subprocess.Popen(
#       command,
#       stdout=subprocess.PIPE,
#       stderr=subprocess.STDOUT,
#       bufsize=1,
#       text=True,
#       encoding="utf-8",
#       errors="ignore",
#   ) as proc:
#     log_count = 50
#     log_interval = 58
#     while True:
#       text = proc.stdout.readline().rstrip("\n")
#       if text == "":
#         if proc.poll() is None:
#           logging.debug("subprocess not exit, sleep 0.5s")
#           sleep(0.5)
#           continue
#         else:
#           logging.debug("subprocess exit, done")
#           break
#       elif text.startswith("frame="):
#         if log_count == log_interval:
#           log_count = 0
#           logging.info(text)
#         else:
#           log_count += 1
#       else:
#         logging.debug(text)
#     if proc.returncode != 0:
#       raise subprocess.SubprocessError(
#           "ffmpeg error, check debug level log for more information.")

#   # rename and keep origin file
#   origin_input_path = Path(f"{input_path_str}.origin")
#   origin_sub_path = Path(f"{sub_path_str}.origin")
#   input_path.rename(origin_input_path)
#   logging.debug(f"Renamed origin file to {str(origin_input_path)}")
#   sub_path.rename(origin_sub_path)
#   logging.debug(f"Renamed origin file to {str(origin_sub_path)}")

#   # move target file
#   dist_path = input_path.parent.joinpath(
#       temp_path.name.rstrip("vctemp").rstrip("."))
#   move(temp_path, dist_path)
#   logging.debug(f"Moved temp file to {dist_path.as_posix()}")

#   return dist_path, [origin_input_path, origin_sub_path]
