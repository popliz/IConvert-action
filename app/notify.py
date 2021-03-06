import requests
from requests.auth import HTTPBasicAuth


def notify_workflow(owner_repo: str, workflow_id: str, github_token: str):
  [owner, repo] = owner_repo.strip().split("/", 1)
  workflow_id = workflow_id.strip()
  print(f"正在启动Workflow...，owner：{owner}，repo：{repo}，workflow_id: {workflow_id}")
  resp = requests.post(
      f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}.yaml/dispatches",
      headers={"accept": "application/vnd.github.v3+json"},
      json={"ref": "main"},
      auth=HTTPBasicAuth(owner, github_token))
  if resp.status_code == 204:
    print(
        f"启动成功, 访问https://github.com/{owner}/{repo}/actions/workflows/{workflow_id}.yaml"
    )
  else:
    print(f"启动失败, 错误状态码: {resp.status_code}, 错误内容: {str(resp.content)}")
