import argparse
import glob
from pathlib import Path
import requests
import shutil
import sys

GITHUB_MD_API_URL = "https://api.github.com/markdown"


def md2html(input_filepath: str, output_dirpath: str, verbose: bool = False, force: bool = False) -> None:
    # 出力htmlのパスを設定
    output_filename = str(Path(Path(input_filepath).stem).with_suffix(".html"))
    output_filepath = str(Path(output_dirpath) / output_filename)

    # 既にファイルが存在してforceがFalseなら聞く
    if not force and Path(output_filepath).exists():
        executable_filename = Path(__file__).name
        should_overwrite = input(f"{executable_filename}: overwrite '{output_filepath}'? ")
        if len(should_overwrite) == 0 or should_overwrite[0].lower() != "y": return

    # apiをたたく
    with open(input_filepath, "r", encoding="utf-8") as f:
        payload = {"text": f.read(), "mode": "markdown"}
        output_content = requests.post(GITHUB_MD_API_URL, json=payload).text

    # テンプレートファイルに書き込む
    template_filepath = str(Path(__file__).parent / "templates" / "template.html")
    with open(template_filepath, "r", encoding="utf-8") as f:
        template_content = f.read()
    template_content = template_content.replace("__title__", str(Path(input_filepath).name))
    template_content = template_content.replace("__content__", output_content)
    with open(output_filepath, "w") as f:
        f.write(template_content)
    if verbose: print(f"saved html '{output_filepath}'")


def main() -> None:
    # エラーメッセージが出力できるargparserクラス
    class ParserHelpOnError(argparse.ArgumentParser):
        def error(self, message):
            self.print_help()
            sys.stderr.write('\nerror: %s\n' % message)
            sys.exit(2)

    # 引数の解析
    arg_parser = ParserHelpOnError()
    arg_parser.add_argument('input')
    arg_parser.add_argument('-o', '--output')
    arg_parser.add_argument('-v', '--verbose', action='store_true')
    arg_parser.add_argument('-f', '--force', action='store_true')
    args = arg_parser.parse_args()
    if not Path(args.input).exists(): arg_parser.error("invalid input")
    if args.output is not None and not Path(args.output).is_dir(): arg_parser.error("invalid output")

    # 出力ディレクトリの準備とか
    output_dirpath = (str(Path(args.input).parent) if args.output is None else args.output)
    glob_filepath = (str(Path(args.input) / "*.md") if Path(args.input).is_dir() else args.input)
    md_filepaths = [filepath for filepath in glob.glob(glob_filepath)]
    Path(output_dirpath).mkdir(parents=True, exist_ok=True)

    # 各ファイルに対して変換
    [md2html(filepath, output_dirpath, args.verbose, args.force) for filepath in md_filepaths]

    # cssを出力
    css_output_filepath = str(Path(output_dirpath) / "style.css")
    if not args.force and Path(css_output_filepath).exists():
        executable_filename = Path(__file__).name
        should_overwrite = input(f"{executable_filename}: overwrite '{css_output_filepath}'? ")
        if len(should_overwrite) == 0 or should_overwrite[0].lower() != "y": return
    shutil.copy(str(Path(__file__).parent / "templates" / "github-markdown.css"), css_output_filepath)
    if args.verbose: print(f"saved css '{css_output_filepath}'")


if __name__ == "__main__":
    main()
