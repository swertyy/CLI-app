import argparse
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from urllib.parse import urlparse
import sys
import re

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
        return
        
    max_length = 255
    if len(filename) > max_length:
        errors.append("Имя файла слишком длинное.")
    
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in filename:
            errors.append(f"Имя файла содержит запрещённый символ {char}.")

    reserved_names = {'CON', 'PRN', 'AUX', 'NUL',
                     'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                     'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
    name = filename.split('.')[0].upper()
    if name in reserved_names:
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
    if not repo:
        errors.append("Репозиторий не может быть пустым.")
        return
        
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

def get_dependencies(package_name, repository_url):
    parts = package_name.split(':')
    if len(parts) != 3:
        print("Неправильный формат имени пакета")
        sys.exit(1)
        
    group_id, artifact_id, version = parts
    group_path = group_id.replace('.', '/')
    pom_url = f"{repository_url}/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    
    try:
        response = urlopen(pom_url)
        pom_content = response.read().decode('utf-8')
        root = ET.fromstring(pom_content)
        
        ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
        
        dependencies = []
        
        deps_section = root.find('.//maven:dependencies', ns)
        if deps_section is not None:
            for dep in deps_section.findall('maven:dependency', ns):
                groupId_elem = dep.find('maven:groupId', ns)
                artifactId_elem = dep.find('maven:artifactId', ns)
                version_elem = dep.find('maven:version', ns)
                
                if groupId_elem is not None and artifactId_elem is not None:
                    groupId = groupId_elem.text
                    artifactId = artifactId_elem.text
                    version = version_elem.text if version_elem is not None else "unknown"
                    
                    full_name = f"{groupId}:{artifactId}:{version}"
                    dependencies.append(full_name)        
        return dependencies
    except Exception:
        return []

parser = argparse.ArgumentParser()
parser.add_argument("--package-name", required=True)
parser.add_argument("--repository", required=True)
parser.add_argument("--mode", required=True)
parser.add_argument("--filter", nargs='?', const="", default="")

args = parser.parse_args()
validate_args(args)
    
if args.mode != "online":
    print("Режим должен быть online для URL")
    sys.exit(1)
    
dependencies = get_dependencies(args.package_name, args.repository)
    
if not args.filter:
    for dep in dependencies:
        print(dep)
else:
    filter_str = args.filter.lower()
    for dep in dependencies:
        if filter_str in dep.lower():
            print(dep)