import sys
import logging
import pyrebase
from datetime import timedelta

import app.var as GLOBAL
from app.libs.time import get_now_datetime, sleep
from app.libs.task import Task


class Firebase:

  def __init__(self, api_key, db_url, project_id, email, password):
    self.email = email
    self.password = password

    firebase = pyrebase.initialize_app({
        "apiKey": api_key,
        "databaseURL": db_url,
        "authDomain": f"{project_id}.firebaseapp.com",
        "storageBucket": f"{project_id}.appspot.com",
    })
    self.auth = firebase.auth()
    self.db = firebase.database()
    self.data = None
    user = self.auth.sign_in_with_email_and_password(email, password)
    self.id_token = user["idToken"]
    self.refresh_token = user["refreshToken"]
    self.refresh_time = get_now_datetime()

  def refresh(self):
    now_datetime = get_now_datetime()
    if now_datetime > self.refresh_time + timedelta(minutes=40):
      if now_datetime < self.refresh_time + timedelta(minutes=60):
        user = self.auth.refresh(self.refresh_token)
      else:
        user = self.auth.sign_in_with_email_and_password(
            self.email, self.password)
      self.id_token = user["idToken"]
      self.refresh_token = user["refreshToken"]
      self.refresh_time = now_datetime

  def get_data(self, path):
    self.refresh()
    return self.db.child("IConvertAction").child(path).get(self.id_token).val()

  def set_data(self, path, data):
    self.refresh()
    return self.db.child("IConvertAction").child(path).set(data, self.id_token)

  def update_data(self, path, data):
    self.refresh()
    return self.db.child("IConvertAction").child(path).update(
        data, self.id_token)

  def remove_data(self, path):
    self.refresh()
    return self.db.child("IConvertAction").child(path).remove(self.id_token)

  def get_task(self) -> Task:
    while True:
      tasks_length = self.get_data("tasks/length")
      task_index = self.get_data("tasks/next_index")
      if task_index + 1 > tasks_length:
        logging.info("找不到可用任务，直接退出")
        sys.exit(0)

      self.update_data(
          "", {
              "tasks/next_index": task_index + 1,
              f"running_task/{task_index}": GLOBAL.APPID,
          })
      sleep(3, 5)
      if self.get_data(f"running_task/{task_index}") == GLOBAL.APPID:
        # 如果获取到任务
        task_obj = self.get_data(f"tasks/data/{task_index}")
        task = Task()
        task.deserialize(task_obj)
        return task
      else:
        sleep(1, 10)

  def update_task(self, task: Task):
    task_obj = task.serialize()
    return self.update_data(
        f"tasks/data/{task.index}",
        task_obj,
    )

  def update_task_status(self, task: Task):
    task_obj = task.serialize()
    return self.update_data(
        f"tasks/data/{task.index}",
        {
            "status": task_obj["status"],
        },
    )

  def update_tasks(self, tasks_obj):
    self.update_data("tasks", {
        "length": tasks_obj["length"],
        "data": tasks_obj["data"]
    })

  def remove_running_task(self, task: Task):
    self.remove_data(f"running_task/{task.index}")

  def get_waiting_task_number(self):
    tasks_length = self.get_data("tasks/length")
    task_index = self.get_data("tasks/next_index")
    return tasks_length - task_index

  def get_running_task_number(self):
    running_task = self.get_data("running_task")
    if running_task is None:
      return 0
    else:
      running_task = list(filter(None, running_task))
      return len(running_task)


#   def remove_unuseful(self, data):
#     now_datetime = get_now_datetime()
#     sleep_time_delta = timedelta(seconds=int(CONFIG."sleep_time"))
#     for index, task in enumerate(data["tasks"]):
#       if (task["status"] == TaskStatus.Error or
#           task["status"] == TaskStatus.Running) and strp_datetime(
#               task["activate_time"]) + sleep_time_delta < now_datetime:
#         self.remove_data(f"tasks/{index}")
