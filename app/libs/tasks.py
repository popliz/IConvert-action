import subprocess
import logging
import sys
import time
from pathlib import Path

import app.var as GLOBAL
from app.libs.task import Task, TaskReturnCode, TaskStatus
from app.libs.path import change_parent_dir


class Tasks:

  def __init__(self, next_index=0, data=list()):
    self.next_index: int = next_index
    self.length: int = 0
    self.data: list[Task] = data
    self.success_number: int = 0

  def __str__(self):
    return (
        f"{{next_index: {self.next_index}, length: {self.length}, data: {self.data}}}"
    )

  def deserialize(self, tasks_obj):
    self.next_index = tasks_obj["next_index"]
    self.length = tasks_obj["length"]
    for task_obj in tasks_obj["data"]:
      task = Task()
      task.deserialize(task_obj)
      self.data.append(task)

  def serialize(self):
    data = list()
    for task in self.data:
      task_obj = task.serialize()
      data.append(task_obj)
    return {
        "next_index": self.next_index,
        "length": self.length,
        "data": data,
    }

  def append_task(self, task: Task, keep_index=False):
    for t in self.data:
      # 检查是否已有相同路径的task存在
      if str(t.path) == str(task.path):
        return False

    file_size = task.path.stat().st_size
    if file_size >= GLOBAL.CONFIG.max_size * 1024 * 1024:
      logging.debug(f"文件大小超过{GLOBAL.CONFIG.max_size}MB，不添加任务: {str(task.path)}")
      return False
    elif file_size <= GLOBAL.CONFIG.min_size * 1024 * 1024:
      logging.debug(f"文件大小低于{GLOBAL.CONFIG.min_size}MB，不添加任务: {str(task.path)}")
      return False
    else:
      if not keep_index:
        task.index = self.length
      self.length += 1
      self.data.append(task)
      return True

  def execute(self):
    for index, task in enumerate(self.data):
      logging.info(
          f"[{index + 1}/{len(self.data)}]开始任务，序号：{task.index}, 路径：{str(task.path)}"
      )

      result = task.execute()

      if result == TaskReturnCode.Done:
        logging.info(f"[{index + 1}/{len(self.data)}]任务完成，开始上传...")
        # 检查上传是否成功
        start_time = time.time()
        upload_success = False
        while time.time() - start_time < 3600:
          if task.outputPath is None:
            logging.error(f"[{index + 1}/{len(self.data)}]任务转码失败")
            sys.exit(1)
          remote_output_file = change_parent_dir(
              task.outputPath, Path(GLOBAL.CONFIG.output_dir),
              Path(GLOBAL.CONFIG.remote_output_dir))
          # 运行rclone
          proc = subprocess.run([
              "rclone", "ls", remote_output_file, "--timeout", "20s",
              "--contimeout", "10s", "--low-level-retries", "10"
          ],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                encoding="utf-8")
          if proc.stdout.count("ERROR") > 0:
            logging.debug(f"[{index + 1}/{len(self.data)}]任务尚未上传完成，等待30s...")
            time.sleep(30)
            continue
          else:
            upload_success = True
            logging.info(f"[{index + 1}/{len(self.data)}]任务上传完成")
            task.update_status(TaskStatus.Done)
            GLOBAL.DB.update_task_status(task)
            break
        if upload_success is False:
          logging.error(f"[{index + 1}/{len(self.data)}]任务上传失败")
          task.update_status(TaskStatus.Error)
          GLOBAL.DB.update_task_status(task)
        else:
          self.success_number += 1
      elif result == TaskReturnCode.Error:
        logging.info(f"[{index + 1}/{len(self.data)}]任务失败")
        task.update_status(TaskStatus.Error)
        GLOBAL.DB.update_task_status(task)
      elif result == TaskReturnCode.Stop:
        logging.info(f"[{index + 1}/{len(self.data)}]用户取消了转码")
        task.update_status(TaskStatus.Waiting)
        GLOBAL.DB.update_task_status(task)
      elif result == TaskReturnCode.Timeout:
        logging.info(f"[{index + 1}/{len(self.data)}]任务超时")
        task.update_status(TaskStatus.Timeout)
        GLOBAL.DB.update_task_status(task)

      # 善后处理
      GLOBAL.DB.remove_running_task(task)
