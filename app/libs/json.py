import json


# save tasks obj to file
def save_json(task_file, tasks_obj):
  with open(task_file, "w") as f:
    json.dump(tasks_obj.__dict__, f, indent=2, sort_keys=True)


def file_parse_json(file):
  try:
    with open(file, "r") as f:
      return json.load(f)
  except Exception:
    raise


def str_parse_json(str):
  try:
    return json.loads(str)
  except Exception:
    raise
