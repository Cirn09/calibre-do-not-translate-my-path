import os
import ast

import click


def patch(input: str, output: str | None):
    if output is None:
        output = input

    with open(input, "r", encoding="utf8") as f:
        _ast = ast.parse(f.read())

    iter = ast.walk(_ast)

    # 替换检查更新链接
    for node in iter:
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "URL"
        ):
            node.value.value = "https://calibre.cirn09.xyz/version"  # type:ignore
            break
    else:
        raise ValueError("URL not found")

    # 替换下载链接
    new_func_str = "def get_download_url(): return localize_website_link('https://calibre.cirn09.xyz/download')"
    new_func_body: list[ast.stmt] = ast.parse(new_func_str).body[0].body  # type:ignore
    for node in iter:
        if isinstance(node, ast.FunctionDef) and node.name == "get_download_url":
            node.body = new_func_body
            break
    else:
        raise ValueError("function get_download_url not found")

    with open(output, "w", encoding="utf8") as f:
        f.write(ast.unparse(_ast))


@click.command()
@click.argument("input", required=True, type=click.Path(exists=True))
@click.argument("output", required=False, type=click.Path(exists=False))
def cli(input, output):
    patch(input, output)


if __name__ == "__main__":
    cli()
