import logging
from enum import Enum
from pathlib import Path
import subprocess

import app.var as GLOBAL
from app.libs.convert import ffmpeg_convert


class TaskStatus(str, Enum):
  Waiting = "waiting"
  Running = "running"
  Done = "done"
  Error = "error"
  Timeout = "timeout"


class TaskReturnCode(str, Enum):
  Done = "done"
  Error = "error"
  Skip = "skip"
  Stop = "stop"
  Timeout = "timeout"


class Task():

  def __init__(
      self,
      index=0,
      status=TaskStatus.Waiting,
      path=Path(),
  ):
    self.index = index
    self.status = status
    self.path = path
    self.outputPath = Path()

  def __str__(self):
    return f"{{index: {self.index}, status: {self.status}, path: {self.path}}}"

  def __repr__(self):
    return self.__str__()

  def update_status(self, status: TaskStatus):
    self.status = status

  def serialize(self):
    obj = {
        "index": self.index,
        "status": self.status,
        "path": str(self.path.relative_to(Path(GLOBAL.CONFIG.input_dir))),
    }
    return obj

  def deserialize(self, task_obj):
    self.index = task_obj["index"]
    self.status = task_obj["status"]
    self.path = Path(GLOBAL.CONFIG.input_dir).joinpath(task_obj["path"])

  def execute(self):
    if self.status == TaskStatus.Done:
      logging.warn("该任务已经完成，跳过")
      return TaskReturnCode.Skip
    elif self.status == TaskStatus.Running:
      logging.warn("该任务已经开始运行，跳过")
      return TaskReturnCode.Skip
    elif self.status == TaskStatus.Error:
      logging.warn("该任务已经发生错误，跳过")
      return TaskReturnCode.Skip
    elif self.status == TaskStatus.Timeout:
      logging.warn("该任务已经超时，跳过")
      return TaskReturnCode.Skip
    else:
      self.update_status(TaskStatus.Running)
      GLOBAL.DB.update_task_status(self)

      if not self.path.exists():
        logging.error("任务路径不存在: {self.path}")
        self.update_status(TaskStatus.Error)
        GLOBAL.DB.update_task_status(self)
        return TaskReturnCode.Error

      try:
        self.outputPath = ffmpeg_convert(self.path)
      except KeyboardInterrupt:
        return TaskReturnCode.Stop
      except subprocess.TimeoutExpired:
        return TaskReturnCode.Timeout
      except Exception as e:
        logging.error(f"转码任务发生未预期的错误: {e}")
        return TaskReturnCode.Error

      return TaskReturnCode.Done


# class TranscodingTask(Task):

#   def __init__(
#       self,
#       path=None,
#       ttype=None,
#       index=0,
#       status=TaskStatus.Waiting,
#   ):
#     super().__init__(path, index, status)
#     self.ttype = ttype

#   def __str__(self):
#     return (
#         f"{{index: {self.index}, activate_time: {strf_datetime(self.activate_time)},"
#         f"status: {self.status}, uuid: {self.uuid}, path: {self.path}, type: {self.ttype}}}"
#     )

#   def from_obj(self, index, obj):
#     super().from_obj(index, obj)
#     self.ttype = obj["ttype"]

#   def to_obj(self):
#     index, obj = super().to_obj()
#     obj["otype"] = "transcoding"
#     obj["ttype"] = self.ttype
#     return index, obj

#   def execute(self):
#     try:
#       super().execute()
#     except ValueError:
#       return TaskReturnCode.Error

#     input_path = self.path
#     if not input_path.exists():
#       logging.error("can not find input_path: {self}")
#       self.update_status(TaskStatus.Done)
#       return TaskReturnCode.Error

#     try:
#       temp_path = get_temp_path(input_path, config["format"])
#     except FileNotFoundError:
#       logging.error("can not find temp_path: {self}")
#       self.update_status(TaskStatus.Error)
#       return TaskReturnCode.Error

#     try:
#       if self.ttype == "normal":
#         result = ffmpeg_convert(input_path, temp_path)
#         if result is False:
#           self.update_status(TaskStatus.Done)
#           return TaskReturnCode.DoNothing
#         self.path, self.origin_paths = result
#       elif (self.ttype == "dvd" or self.ttype == "dvd-folder" or
#             self.ttype == "iso"):
#         self.path, self.origin_paths = handbrake_convert(input_path, temp_path)
#       else:
#         logging.error(f"unknown task_type: {self.ttype}")
#         self.update_status(TaskStatus.Error)
#         return TaskReturnCode.Error
#     except KeyboardInterrupt:
#       logging.info("\nUser stop tasks")
#       rm(temp_path)
#       self.update_status(TaskStatus.Waiting)
#       _exit(1)
#     except Exception as e:
#       logging.error(f"unexpected error: {e}")
#       rm(temp_path)
#       self.update_status(TaskStatus.Error)
#       return TaskReturnCode.Error

#     self.status = TaskStatus.Done
#     self.update_task()
#     return TaskReturnCode.Complete

# class BurnsubTask(Task):

#   def __init__(
#       self,
#       path=None,
#       sub_path=None,
#       index=0,
#       status=TaskStatus.Waiting,
#   ):
#     super().__init__(path, index, status)
#     self.sub_path = sub_path

#   def __str__(self):
#     return (
#         f"{{index: {self.index}, activate_time: {strf_datetime(self.activate_time)},"
#         f"status: {self.status}, uuid: {self.uuid}, path: {self.path}, sub_path: {self.sub_path}}}"
#     )

#   def from_obj(self, index, obj):
#     super().from_obj(index, obj)
#     self.sub_path = Path(obj["sub_path"])

#   def to_obj(self):
#     index, obj = super().to_obj()
#     obj["otype"] = "burnsub"
#     obj["sub_path"] = str(self.sub_path)
#     return index, obj

#   def execute(self):
#     try:
#       super().execute()
#     except ValueError:
#       return TaskReturnCode.Error

#     input_path = self.path
#     sub_path = self.sub_path

#     if not input_path.exists():
#       logging.error("can not find input_path: {self}")
#       self.update_status(TaskStatus.Done)
#       return TaskReturnCode.Error
#     if not sub_path.exists():
#       logging.error("can not find sub_path: {self}")
#       self.update_status(TaskStatus.Done)
#       return TaskReturnCode.Error

#     try:
#       temp_path = get_temp_path(input_path, config["format"])
#     except FileNotFoundError:
#       logging.error("can not find temp_path: {self}")
#       self.update_status(TaskStatus.Error)
#       return TaskReturnCode.Error

#     try:
#       self.path, self.origin_paths = burn_sub(input_path, sub_path, temp_path)
#     except KeyboardInterrupt:
#       logging.info("\nUser stop tasks")
#       rm(temp_path)
#       self.update_status(TaskStatus.Waiting)
#       _exit(1)
#     except Exception as e:
#       logging.error(f"unexpected error: {e}")
#       rm(temp_path)
#       self.status = TaskStatus.Error
#       return TaskReturnCode.Error

#     self.status = TaskStatus.Done
#     self.update_task()
#     return TaskReturnCode.Complete
