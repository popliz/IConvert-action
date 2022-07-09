import chardet
import logging


def get_file_encoding(input_file):
  with open(input_file, "rb") as f:
    rawdata = f.read()
    result = chardet.detect(rawdata)
    return result["encoding"].upper()


def file_to_utf8(input_file_encoding, input_file, output_file):
  if input_file_encoding.lower() == "gb2312":
    input_file_encoding = "gb18030"
  try:
    with open(input_file, "r", encoding=input_file_encoding.lower()) as f1:
      content = f1.read()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f2:
      f2.write(content)
  except UnicodeDecodeError as e:
    logging.error(f"{str(input_file)}解码错误: {e}")
