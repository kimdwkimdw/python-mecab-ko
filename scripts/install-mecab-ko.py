import os
import site
import subprocess
from pathlib import Path
import sys
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

MECAB_KO_URL = 'https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-0.996-ko-0.9.2.tar.gz'
MECAB_KO_DIC_URL = 'https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz'


def is_writable(directory: str) -> bool:
    path = Path(directory)
    while not path.is_dir():
        parent = path.parent
        if path == parent:
            break
        path = parent

    return os.access(path, os.W_OK)


def guess_prefix() -> str:
    candidates = [
        sys.prefix,
        site.getuserbase(),
    ]

    for candidate in candidates:
        if is_writable(candidate):
            return candidate

    raise RuntimeError("All prefixes are not writable")

@contextmanager
def change_directory(directory):
    original = os.path.abspath(os.getcwd())

    os.chdir(directory)
    yield

    os.chdir(original)


def path_of(filename):
    for path, _, filenames in os.walk(os.getcwd()):
        if filename in filenames:
            return path

    raise ValueError('File {} not found'.format(filename))


def fancy_print(*args, color=None, bold=False, **kwargs):
    if bold:
        print('\033[1m', end='')

    if color:
        print('\033[{}m'.format(color), end='')

    print(*args, **kwargs)

    print('\033[0m', end='')  # reset


def install(url, *args, environment=None):
    def download(url):
        components = urlparse(url)
        filename = os.path.basename(components.path)

        subprocess.run([
            'wget',
            '--progress=dot:binary',
            '--output-document={}'.format(filename),
            url,
        ], check=True)
        subprocess.run(['tar', '-xzf', filename], check=True)

    def configure(*args):
        with change_directory(path_of('configure')):
            try:
                subprocess.run(['./autogen.sh'])
            except:
                pass

            subprocess.run(['./configure', *args], check=True)

    def make():
        with change_directory(path_of('Makefile')):
            subprocess.run(['make'], check=True, env=environment)
            subprocess.run(['make', 'install'], check=True, env=environment)

    with TemporaryDirectory() as directory:
        with change_directory(directory):
            download(url)
            configure(*args)
            make()


if __name__ == '__main__':
    prefix = guess_prefix()
    os.makedirs(prefix, exist_ok=True)

    fancy_print('Installing mecab-ko...', color=32, bold=True)
    install(MECAB_KO_URL, '--prefix={}'.format(prefix),
                          '--enable-utf8-only')

    fancy_print('Installing mecab-ko-dic...', color=32, bold=True)
    mecab_config_path = os.path.join(prefix, 'bin', 'mecab-config')
    install(MECAB_KO_DIC_URL, '--prefix={}'.format(prefix),
                              '--with-charset=utf8',
                              '--with-mecab-config={}'.format(mecab_config_path),
                              environment={
                                  'LD_LIBRARY_PATH': os.path.join(prefix, 'lib'),
                              })
