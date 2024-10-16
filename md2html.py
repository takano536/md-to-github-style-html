import argparse
import sys
from pathlib import Path

import requests

GITHUB_MD_API_URL = 'https://api.github.com/markdown'
CSS_URL = 'https://raw.githubusercontent.com/sindresorhus/github-markdown-css/refs/heads/main/github-markdown.css'
CSS_LICENSE_URL = 'https://raw.githubusercontent.com/sindresorhus/github-markdown-css/refs/heads/main/license'

TEMPLATE_DIRPATH = str(Path(__file__).parent / 'templates')
TEMPLATE_FILEPATH = str(Path(TEMPLATE_DIRPATH) / 'template.html')
MINIMUM_CSS_FILEPATH = str(Path(TEMPLATE_DIRPATH) / 'minimum.css')


def md2html(input_filepath: str, output_dirpath: str, force: bool = False) -> tuple[str, str]:

    # 出力htmlのパスを設定
    output_filepath = str(Path(output_dirpath) / str(Path(input_filepath).with_suffix('.html')))

    # 既にファイルが存在してforceがFalseなら聞く
    if not force and Path(output_filepath).exists():
        executable_filename = Path(__file__).name
        should_overwrite = input(f'{executable_filename}: overwrite "{output_filepath}" ? [y/n] ')
        if len(should_overwrite) == 0 or should_overwrite[0].lower() != 'y':
            return ('', output_filepath)

    # apiをたたく
    with open(input_filepath, 'r', encoding='utf-8') as f:
        payload = {'text': f.read(), 'mode': 'markdown'}
    try:
        response = requests.post(GITHUB_MD_API_URL, json=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f'error: {e}')
        return ('', output_filepath)
    output_content = response.text
    output_content = output_content.replace('user-content-', '')

    # テンプレートファイルに書き込む
    with open(TEMPLATE_FILEPATH, 'r', encoding='utf-8') as f:
        template_content = f.read()
    template_content = template_content.replace('__title__', str(Path(input_filepath).stem))
    template_content = template_content.replace('__content__', output_content)

    return (template_content, output_filepath)


def main() -> None:

    # エラーメッセージが出力できるargparserクラス
    class ParserHelpOnError(argparse.ArgumentParser):
        def error(self, message):
            self.print_help()
            sys.stderr.write('\nerror: %s\n' % message)
            sys.exit(2)

    # 引数の解析
    arg_parser = ParserHelpOnError()
    arg_parser.add_argument('input', help='input markdown file not directory. output will be saved in the same directory.')
    arg_parser.add_argument('-f', '--force', action='store_true', help='overwrite without asking')
    arg_parser.add_argument('-e', '--embed', action='store_true', help='embed css in html')
    arg_parser.add_argument('-v', '--verbose', action='store_true')
    args = arg_parser.parse_args()
    if not Path(args.input).exists():
        arg_parser.error('input file not found')
    if Path(args.input).is_dir():
        arg_parser.error('input must be a file not directory')

    # 出力ディレクトリの設定
    output_dirpath = str(Path(args.input).parent)

    # cssをリポジトリから取得
    try:
        response = requests.get(CSS_URL)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f'error: {e}')
        return
    github_css = response.text
    try:
        response = requests.get(CSS_LICENSE_URL)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f'error: {e}')
        return
    github_css = '/*\n' + response.text + '\n*/\n\n' + github_css  # ライセンス文を追加

    # cssを埋め込まない用の最小cssを取得
    with open(MINIMUM_CSS_FILEPATH, 'r', encoding='utf-8') as f:
        minimum_css = f.read()
    embed_css = '\n'.join([github_css, minimum_css])

    # 各ファイルに対して変換
    html, output_filepath = md2html(args.input, output_dirpath, args.force)

    # 出力を保存
    html = html.replace('/* __css__ */', embed_css if args.embed else minimum_css)
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    if args.verbose:
        print(f'saved html "{output_filepath}"')

    # cssを出力するか確認
    if args.embed:
        return

    # cssの出力先を設定
    css_output_filepath = str(Path(output_dirpath) / 'style.css')
    if not args.force and Path(css_output_filepath).exists():
        executable_filename = Path(__file__).name
        should_overwrite = input(f'{executable_filename}: overwrite "{css_output_filepath}" ? [y/n] ')
        if len(should_overwrite) == 0 or should_overwrite[0].lower() != 'y':
            return

    # cssを保存
    with open(css_output_filepath, 'w', encoding='utf-8') as f:
        f.write(github_css)
    if args.verbose:
        print(f'saved css "{css_output_filepath}"')


if __name__ == '__main__':
    main()
