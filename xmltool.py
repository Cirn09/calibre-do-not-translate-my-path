import hashlib

import click
from lxml import etree


def _find(xml: str, filename: str):
    with open(xml, "rb") as f:
        root: etree._Element = etree.XML(f.read())  # type:ignore

    r: list[etree._Element] = root.xpath(f'//td[contains(.,"|{filename}")]/..')
    if len(r) != 1:
        raise ValueError(
            f'xpath "//td[contains(.,"|{filename}")]/.." result more than 1'
        )
    target: etree._Element = list(r[0])[0]  # type:ignore
    path = target.attrib["href"]
    print(path)
    return path


def _patch(xml: str, filename: str, newfile: str):
    with open(newfile, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()

    print(f"new hash: {md5}")

    with open(xml, "rb") as f:
        root: etree._Element = etree.XML(f.read())  # type:ignore

    r: list[etree._Element] = root.xpath(f'//td[contains(.,"|{filename}")]/..')
    if len(r) != 1:
        raise ValueError(
            f'xpath "//td[contains(.,"|{filename}")]/.." result more than 1'
        )
    target: etree._Element = list(r[0])[0]  # type:ignore
    old_md5 = target.attrib["md5"]

    with open(xml, "r", encoding="utf8") as f:
        data = f.read()

    data = data.replace(old_md5, md5)

    with open(xml, "w", encoding="utf8") as f:
        f.write(data)


@click.group()
def cli():
    ...


@cli.command()
@click.argument("xml", required=True, type=click.Path(exists=True))
@click.argument("filename", required=True, type=click.Path(exists=False))
def find(xml: str, filename: str):
    _find(xml, filename)


@cli.command()
@click.argument("xml", required=True, type=click.Path(exists=True))
@click.argument("filename", required=True, type=click.Path(exists=False))
@click.argument("newfile", required=True, type=click.Path(exists=True))
def patch(xml: str, filename: str, newfile: str):
    _patch(xml, filename, newfile)


if __name__ == "__main__":
    cli()
