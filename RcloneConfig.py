import pyrebase
import sys


class Firebase:

  def __init__(self, api_key, db_url, project_id, email, password):
    firebase = pyrebase.initialize_app({
        "apiKey": api_key,
        "databaseURL": db_url,
        "authDomain": f"{project_id}.firebaseapp.com",
        "storageBucket": f"{project_id}.appspot.com",
    })
    auth = firebase.auth()
    user = auth.sign_in_with_email_and_password(email, password)
    self.id_token = user["idToken"]
    self.db = firebase.database()

  def get(self, path):
    return self.db.child("IGameSyncAction").child(path).get(self.id_token).val()

  def set(self, path, data):
    return self.db.child("IGameSyncAction").child(path).set(data, self.id_token)

  def update(self, path, data):
    return self.db.child("IGameSyncAction").child(path).update(
        data, self.id_token)

  def remove(self, path):
    return self.db.child("IGameSyncAction").child(path).remove(self.id_token)


if __name__ == "__main__":
  firebase = Firebase(
      sys.argv[2],
      "https://lizkes-default-rtdb.asia-southeast1.firebasedatabase.app/",
      "lizkes",
      "lizkes@lizkes.com",
      sys.argv[3],
  )

  if sys.argv[1] == "download":
    data = firebase.get("RcloneConfig")
    with open("/root/.rclone.conf", "w") as file:
      file.write(str(data))
    print("从云端下载rclone.conf...")
  elif sys.argv[1] == "upload":
    with open("/root/.rclone.conf", "r") as file:
      data = file.read()
    firebase.set("RcloneConfig", data)
    print("上传rclone.conf到云端...")
  else:
    print("参数错误")
