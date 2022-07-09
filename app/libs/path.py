import shutil
import logging
from pathlib import Path
from time import sleep


def change_parent_dir(input_path: Path, before_parent: Path,
                      after_parent: Path):
  return after_parent.joinpath(input_path.relative_to(before_parent))


def add_suffix(input_path, suffix):
  return Path(f"{input_path.as_posix()}.{suffix}")


def remove_suffix(input_path, suffix):
  return input_path.with_suffix(input_path.suffix.rstrip(suffix))


def rm(paths):

  def try_to_rm(path):
    try_count = 10
    while try_count > 0:
      try:
        if path.exists():
          if path.is_dir():
            shutil.rmtree(path)
            logging.debug(f"{path} is folder, removed")
          elif path.is_file():
            path.unlink()
            logging.debug(f"{path} is file, removed")
          else:
            logging.warn(f"{path} is neither file nor folder, can't delete.")
        else:
          logging.info(f"{path} is not exist, can't delete.")
        break
      except PermissionError as e:
        try_count -= 1
        logging.error("\n", e, "\nRetry after one second")
        sleep(1)

  if type(paths) == list:
    for path in paths:
      try_to_rm(path)
  else:
    try_to_rm(paths)
