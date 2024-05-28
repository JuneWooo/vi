import hashlib


def md5GBK(str1):
    try:
        m = hashlib.md5(str1.encode(encoding='gb2312'))
    except UnicodeEncodeError:
        m = hashlib.md5(str1.encode(encoding='gb18030'))
    return m.hexdigest().upper()
