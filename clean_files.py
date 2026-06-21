import argparse
import os
import hashlib
import shutil
import time
import configparser


def load_config():
    config_path = os.path.expanduser("~/.clean_files")
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        print("nieee")
        return {
            "suggested_mode": "644",
            "bad_chars": ':;"*?$#`|\\',
            "substitute_char": "_",
            "temp_extensions": ["tmp", "bak", "~"],
        }
    config.read(config_path)
    return {
        "suggested_mode": config.get(
            "settings", "suggested_mode", fallback="644"),
        "bad_chars": config.get("settings", "bad_chars", fallback=':*?"<>|\\'),
        "substitute_char": config.get(
            "settings", "substitute_char", fallback="_"),
        "temp_extensions": [
            ext.strip() for ext in config.get(
                "settings", "temp_extensions", fallback="tmp, bak, ~"
                ).split(",")],
    }


def extract_data(line, name):
    line = line.replace(name + " = ", "")
    value = line.strip().replace(" ", "")
    return value


def get_all_files(directory_list):
    file_list = []
    for directory in directory_list:
        for path, _, files in os.walk(directory):
            for file in files:
                file_list.append((path, file))
    return file_list


def delete_file(path, filename):
    os.remove(os.path.join(path, filename))


def replace_chars(path, filename, bad_chars, replace_with):
    new_name = filename
    for char in bad_chars:
        if filename.find(char) != -1:
            new_name = new_name.replace(char, replace_with)
    if new_name != filename:
        os.rename(os.path.join(path, filename),
                  os.path.join(path, new_name))


def file_hash(path, filename, chunk_size=8192):
    hash_md5 = hashlib.md5()
    with open(os.path.join(path, filename), "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def find_empty_files(file_list):
    empty_files = []
    for path, filename in file_list:
        if os.path.getsize(os.path.join(path, filename)) == 0:
            empty_files.append((path, filename))
    return empty_files


def find_duplicates(file_list):
    files_by_hash = {}
    for path, filename in file_list:
        hash = file_hash(path, filename)
        time = os.path.getmtime(os.path.join(path, filename))
        files_by_hash.setdefault(hash, []).append((path, filename, time))
    for hash, files in files_by_hash.items():
        if len(files) > 1:
            files.sort(key=lambda p: p[2], reverse=False)
    return files_by_hash


def find_problematic_names(file_list, bad_chars):
    bad_name_files = []
    for path, filename in file_list:
        for char in bad_chars:
            if filename.find(char) != -1:
                bad_name_files.append((path, filename))
                break
    return bad_name_files


def find_temp(file_list, temp_extensions):
    temp_files = []
    for path, filename in file_list:
        for ext in temp_extensions:
            if filename.endswith(ext):
                temp_files.append((path, filename))
    return temp_files


def find_bad_perms(file_list, suggested_mode):
    files = []
    for path, filename in file_list:
        status = os.stat(os.path.join(path, filename))
        mode = oct(status.st_mode)[-3:]
        if mode != suggested_mode:
            files.append((path, filename))
    return files


def find_duplicate_names(file_list):
    files_by_name = {}
    for path, filename in file_list:
        time = os.path.getmtime(os.path.join(path, filename))
        files_by_name.setdefault(filename, []).append((path, time))
    for filename, paths in files_by_name.items():
        if len(paths) > 1:
            paths.sort(key=lambda p: p[1], reverse=True)
            files_by_name[filename] = paths
    return files_by_name


def find_files_to_move(main_dir, directory_list):
    files_to_move = {}
    exisitng_hashes = []
    main_files = get_all_files([main_dir])
    for path, filename in main_files:
        hash = file_hash(path, filename)
        if hash not in exisitng_hashes:
            exisitng_hashes.append(hash)

    files = get_all_files(directory_list)
    for path, filename in files:
        hash = file_hash(path, filename)
        if hash not in exisitng_hashes:
            time = time = os.path.getmtime(os.path.join(path, filename))
            files_to_move.setdefault(hash, []).append((path, filename, time))

    return files_to_move


def delete_empty_files(directory_list, interactive):
    file_list = get_all_files(directory_list)
    empty_files = find_empty_files(file_list)
    if interactive:
        for path, filename in empty_files:
            print(f'File {path}/{filename} is empty.')
            answer = input('Do you want to delete this file? (Y/n): ')
            if answer in ['y', 'Y', 'yes', 'Yes', '']:
                delete_file(path, filename)
    else:
        for path, filename in empty_files:
            delete_file(path, filename)


def delete_duplicates(directory_list, interactive):
    file_list = get_all_files(directory_list)
    duplicates = find_duplicates(file_list)
    if interactive:
        for _, files in duplicates.items():
            if len(files) < 2:
                continue
            print('Found duplicate files (same content):')
            for i, (path, filename, mtime) in enumerate(files):
                print(f'[{i}] {path}/{filename} ', end='')
                print(f'modified: {time.ctime(mtime)}')
            input_text = 'Keep (o)ldest, (n)ewest, or (m)anually '
            input_text += 'choose which to delete? (o/n/m): '
            answer = input(input_text).strip().lower()
            if answer in ['o', 'oldest']:
                to_delete = files[1:]
            elif answer in ['n', 'newest']:
                to_delete = files[:-1]
            elif answer in ['m', 'manual']:
                input_text = 'Enter indexes to delete (comma-separated): '
                idxs = input(input_text).split(",")
                to_delete = [
                    files[int(i)] for i in idxs if i.strip().isdigit()]
            else:
                continue
            for path, filename, _ in to_delete:
                delete_file(path, filename)
    else:
        for _, files in duplicates.items():
            if len(files) > 1:
                for path, filename, _ in files[1:]:
                    delete_file(path, filename)


def fix_bad_names(directory_list, bad_chars, substitute_char, interactive):
    file_list = get_all_files(directory_list)
    bad_names = find_problematic_names(file_list, bad_chars)
    if interactive:
        for path, filename in bad_names:
            print(f'File {path}/{filename} contains bad chars.')
            input_text = 'Do you want to replace these chars with '
            input_text += f'\'{substitute_char}\'? (Y/n): '
            answer = input(input_text)
            if answer in ['y', 'Y', 'yes', 'Yes', '']:
                replace_chars(path, filename, bad_chars, substitute_char)
    else:
        for path, filename in bad_names:
            replace_chars(path, filename, bad_chars, substitute_char)


def delete_temp_files(directory_list, temp_extensions, interactive):
    file_list = get_all_files(directory_list)
    temp_files = find_temp(file_list, temp_extensions)
    if interactive:
        for path, filename in temp_files:
            print(f'File {path}/{filename} is temporary.')
            answer = input('Do you want to delete this file? (Y/n): ')
            if answer in ['y', 'Y', 'yes', 'Yes', '']:
                delete_file(path, filename)
    else:
        for path, filename in temp_files:
            delete_file(path, filename)


def fix_file_perms(directory_list, suggested_mode, interactive):
    file_list = get_all_files(directory_list)
    perms = find_bad_perms(file_list, suggested_mode)
    if interactive:
        for path, filename in perms:
            file_path = os.path.join(path, filename)
            curr_perms = oct(os.stat(file_path).st_mode)[-3:]
            print(f'File {path}/{filename} has unusual permissions:', end='')
            print(f' {curr_perms}')
            input_text = 'Do you want to change permissions of this file'
            input_text += f' to \'{suggested_mode}\'? (Y/n): '
            answer = input(input_text)
            if answer in ['y', 'Y', 'yes', 'Yes', '']:
                os.chmod(os.path.join(path, filename), int(suggested_mode, 8))
    else:
        for path, filename in perms:
            os.chmod(os.path.join(path, filename), int(suggested_mode, 8))


def delete_duplicate_names(directory_list, interactive):
    file_list = get_all_files(directory_list)
    name_dupes = find_duplicate_names(file_list)
    if interactive:
        for filename, entries in name_dupes.items():
            if len(entries) < 2:
                continue
            print(f'Found files with the same name: {filename}')
            for i, (path, mtime) in enumerate(entries):
                print(f'[{i}] {path}/{filename} ', end='')
                print(f'modified: {time.ctime(mtime)}')
            input_text = 'Keep (o)ldest, (n)ewest, or (m)anually '
            input_text += 'choose which to delete? (o/n/m): '
            answer = input(input_text).strip().lower()
            if answer in ['o', 'oldest']:
                to_delete = entries[:-1]
            elif answer in ['n', 'newest']:
                to_delete = entries[1:]
            elif answer in ['m', 'manual']:
                input_text = 'Enter indexes to delete (comma-separated): '
                idxs = input(input_text).split(",")
                to_delete = [
                    entries[int(i)] for i in idxs if i.strip().isdigit()]
            else:
                continue
            for path, _ in to_delete:
                delete_file(path, filename)
    else:
        for filename, entries in name_dupes.items():
            if len(entries) > 1:
                for path, _ in entries[1:]:
                    delete_file(path, filename)


def collect_files(directory_list, interactive):
    main_dir = directory_list[0]
    source_dirs = directory_list[1:]
    files_to_move = find_files_to_move(main_dir, source_dirs)
    for _, files in files_to_move.items():
        files.sort(key=lambda p: p[2])
        path, filename, _ = files[0]
        src_path = os.path.join(path, filename)
        source_root = next(
            (src for src in source_dirs if src_path.startswith(src)),
            path
        )
        rel_path = os.path.relpath(src_path, start=source_root)
        dst_path = os.path.join(main_dir, rel_path)
        dst_dir = os.path.dirname(dst_path)
        if interactive:
            print(f'Found file: {src_path}')
            print(f'Target location: {dst_path}')
            if os.path.exists(dst_path):
                print('File already exists in target directory.')
                print('Options: [o]verwrite, [s]kip, [r]ename new copy')
                choice = input('Your choice (o/s/r): ').strip().lower()
                if choice in ('s', 'skip'):
                    continue
                elif choice in ('r', 'rename'):
                    base, ext = os.path.splitext(dst_path)
                    dst_path = base + '_copy' + ext
                    dst_dir = os.path.dirname(dst_path)
                strategy = 'move'
            else:
                input_text = 'Do you want to [m]ove, [c]opy, or'
                input_text += '[s]kip this file? (m/c/s): '
                choice = input(input_text).strip().lower()
                if choice in ('s', 'skip'):
                    continue
                elif choice == 'c':
                    strategy = 'copy'
                elif choice == 'm':
                    strategy = 'move'
                else:
                    continue
            os.makedirs(dst_dir, exist_ok=True)
            if strategy == 'move':
                shutil.move(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
        else:
            os.makedirs(dst_dir, exist_ok=True)
            shutil.move(src_path, dst_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'directory_list', nargs='*',
        help=('List of directories to process. '
              'The first directory is treated as the main one.')
    )
    parser.add_argument('--empty', action='store_true',
                        help='Find and optionally delete empty files.')
    parser.add_argument('--duplicates', action='store_true',
                        help='Find and remove duplicate files (by content).')
    parser.add_argument(
        '--bad-names', action='store_true',
        help=('Detect files with invalid or problematic characters '
              'in their names.')
    )
    parser.add_argument('--temp', action='store_true',
                        help='Detect and remove temporary or backup files.')
    parser.add_argument(
        '--bad-perms', action='store_true',
        help=('Detect and fix files with incorrect permissions.')
    )
    parser.add_argument(
        '--duplicate-names', action='store_true',
        help=('Find and remove files that share the same name, '
              'regardless of their content.')
    )
    parser.add_argument(
        '--move-files', action='store_true',
        help=('Move unique files from other directories into '
              'the first (main) directory.')
    )
    parser.add_argument(
        '--all', action='store_true',
        help=('Perform all cleaning and maintenance actions in one run.')
    )
    parser.add_argument(
        '--interactive', action='store_true',
        help=('Enable interactive mode — ask before performing actions '
              '(delete, move, etc.).')
    )

    args = parser.parse_args()
    directory_list = args.directory_list
    interactive = args.interactive
    config = load_config()
    suggested_mode = config["suggested_mode"]
    bad_chars = config["bad_chars"]
    substitute_char = config["substitute_char"]
    temp_extensions = config["temp_extensions"]

    if args.empty or args.all:
        delete_empty_files(directory_list, interactive)

    if args.temp or args.all:
        delete_temp_files(directory_list, temp_extensions, interactive)

    if args.bad_names or args.all:
        fix_bad_names(directory_list, bad_chars, substitute_char, interactive)

    if args.bad_perms or args.all:
        fix_file_perms(directory_list, suggested_mode, interactive)

    if args.duplicates or args.all:
        delete_duplicates(directory_list, interactive)

    if args.duplicate_names or args.all:
        delete_duplicate_names(directory_list, interactive)

    if args.move_files or args.all:
        collect_files(directory_list, interactive)


if __name__ == '__main__':
    main()
