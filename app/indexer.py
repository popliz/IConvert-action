from pathlib import Path

import app.var as GLOBAL
from app.libs.task import Task
from app.libs.tasks import Tasks


class Indexer:
  SUPPORT_VIDEO_SUFFIXES = [
      "mp4",
      "wmv",
      "avi",
      "webm",
      "mkv",
      "rmvb",
      "mpeg",
      "flv",
      "mpg",
      "m4v",
      "3gp",
      "mov",
      "qt",
      "mp2",
      "mpe",
      "mpv",
  ]

  def __init__(self,
               tasks=Tasks(),
               path=Path(GLOBAL.CONFIG.input_dir),
               need_num=-1):
    self.tasks = tasks
    self.path = path
    self.added_num = 0
    self.need_num = need_num

  def filter_file(self, file_path: Path):
    file_format = file_path.suffix[1:]
    if file_format.lower() in self.SUPPORT_VIDEO_SUFFIXES:
      new_task = Task(path=file_path)
      if self.tasks.append_task(new_task):
        self.added_num += 1

  def traverse(self, dir_path: Path):
    for child in dir_path.iterdir():
      if self.added_num == self.need_num:
        return

      if child.is_file():
        self.filter_file(child)
      elif child.is_dir():
        self.traverse(child)

  def execute(self):
    if self.path.is_file():
      self.filter_file(self.path)
    elif self.path.is_dir():
      self.traverse(self.path)
