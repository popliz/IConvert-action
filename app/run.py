import sys
import logging
import logging.handlers
from pathlib import Path
from time import sleep

import app.var as GLOBAL
from app.indexer import Indexer
from app.libs.tasks import Tasks
from app.notify import notify_workflow


def search(file_path):
  with open(file_path, mode="r", encoding="utf-8") as f:
    content = f.read()
  start_upload_number = content.count("starting upload")
  upload_success_number = content.count("upload succeeded")
  logging.debug(f"start_upload_number: {start_upload_number}")
  logging.debug(f"upload_success_number: {upload_success_number}")
  return start_upload_number != 0 and start_upload_number == upload_success_number


if __name__ == "__main__":
  # 初始化日志
  stream_handler = logging.StreamHandler(sys.stdout)
  stream_handler.setLevel(
      logging._nameToLevel.get(GLOBAL.CONFIG.log_level, logging.INFO))
  logging.basicConfig(
      level=logging.DEBUG,
      format="%(asctime)s [%(levelname)s] %(message)s",
      datefmt="%y/%m/%d %H:%M:%S",
      handlers=[stream_handler],
  )

  # 开始任务
  if GLOBAL.CONFIG.role == "indexer":
    tasks = Tasks()
    tasks_obj = GLOBAL.DB.get_data("tasks")
    if tasks_obj is None:
      indexer = Indexer(tasks=tasks)
      indexer.execute()
      if indexer.added_num > 0:
        GLOBAL.DB.set_data("tasks", tasks.serialize())
      else:
        logging.info("没有新增的任务，直接退出")
        sys.exit(0)
    else:
      tasks.deserialize(tasks_obj)
      indexer = Indexer(tasks=tasks)
      indexer.execute()
      if indexer.added_num > 0:
        GLOBAL.DB.update_tasks(tasks.serialize())
      else:
        logging.info("没有新增的任务，直接退出")
        sys.exit(0)
  elif GLOBAL.CONFIG.role == "converter":
    Path(GLOBAL.CONFIG.input_dir).mkdir(parents=True, exist_ok=True)
    Path(GLOBAL.CONFIG.output_dir).mkdir(parents=True, exist_ok=True)

    task = GLOBAL.DB.get_task()
    tasks = Tasks()
    tasks.append_task(task, keep_index=True)
    tasks.execute()

    # 检查是否开始下一班车
    for i in range(3):
      if i != 0:
        sleep(60)
      running_task_number = GLOBAL.DB.get_running_task_number()
      if running_task_number > 0:
        logging.info(f"还有{running_task_number}个任务正在运行，直接退出...")
        sys.exit(0)
      else:
        logging.info(f"尚无运行中的任务，60秒后再次检测，还需要检测{2-i}次")

    waiting_task_number = GLOBAL.DB.get_waiting_task_number()
    if waiting_task_number > 0:
      logging.info(f"还有{waiting_task_number}个任务等待完成，通知下一班车...")
      notify_workflow(GLOBAL.CONFIG.owner_repo, GLOBAL.CONFIG.workflow_id,
                      GLOBAL.CONFIG.github_token)
    else:
      logging.info("所有任务都已经完成！直接退出")
