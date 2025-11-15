import re
from urllib.parse import urlparse
import argparse

errors = []

def validate_package_name(package_name):
    global errors
    if not package_name.strip():
        errors.append("Имя пакета не может быть пустым.")
    elif not re.match(r'^[a-zA-Z\d][\w.:-]*$', package_name):
        errors.append("Некорректное имя пакета")

def validate_filename(filename):
    global errors
    if not filename.strip():
        errors.append("Имя файла не может быть пустым.")

    max_length = 255
    if len(filename) > max_length:
        errors.append("Имя файла слишком длинное.")

    if not (((filename.find('\\') == filename.find(':')+1) or (filename.find('/') == filename.find(':')+1)) and filename.count(':') == 1):
        errors.append("Недопустимо как имя файла.")

    invalid_chars = ['*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in filename:
            errors.append(f"Имя файла содержит запрещённый символ {char}.")

    reserved_names = {'CON', 'PRN', 'AUX', 'NUL',
                      'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                      'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}

    if '/' in filename and '\\' in filename:
        errors.append("Неправильное имя файла")
    if '/' in filename:
        name = filename.split('/')
    else:
        name = filename.split('\\')

    name[0] = name[0][:-1]
    name[-1] = name[-1][:name[-1].find('.')]

    for i in name:
        if i.upper() in reserved_names:
            errors.append("Недопустимо как имя файла.")

def validate_url(url):
    global errors
    if not url.strip():
        errors.append("Адрес URL не может быть пустым.")
    else:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            errors.append("Неправильно задан URL.")

        unsafe_chars = r'[]\{\}|,%~\#<>'
        control_chars = ''.join(chr(i) for i in range(32)) + chr(127)
        if any(char in url for char in unsafe_chars + control_chars):
            errors.append("URL содержит недопустимые символы.")

def check_repository(repository):
    global errors
    repo = repository.strip()
    is_url = bool(urlparse(repo).scheme and urlparse(repo).netloc)
    if is_url:
        validate_url(repo)
    else:
        validate_filename(repo)

def validate_args(args):
    global errors
    validate_package_name(args.package_name)
    check_repository(args.repository)
    if not args.mode.strip():
        errors.append("Режим не может быть пустым")
    if errors:
        for error in errors:
            print(error)
        exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("--package-name", required=True)
parser.add_argument("--repository", required=True)
parser.add_argument("--mode", required=True)
parser.add_argument("--filter", nargs='?', const="", default="")

args = parser.parse_args()
validate_args(args)

print("Имя пакета:", args.package_name)
print("Репозиторий:", args.repository)
print("Режим:", args.mode)
print("Подстрока для фильтрации:", args.filter)