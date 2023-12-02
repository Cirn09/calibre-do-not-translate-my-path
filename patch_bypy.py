import stat
import shutil

import click

import launcher_helper as helper


def patch(
    bypy: str,
    new_pyc_file: str,
    launcher: str,
    embed_path: str,
    output: str | None = None,
    _os: str = "win",
):
    if output is None:
        output = bypy
    else:
        shutil.copyfile(bypy, output)
    with open(new_pyc_file, "rb") as f:
        data = f.read()[0x10:]

    offset, cap = helper.find(launcher, embed_path, _os)
    if cap < len(data):
        raise ValueError(f"new pyc size({len(data)}) large than capacity({cap})")

    print(f"[+] pyc size {cap:#x} -> {len(data):#x} (shrink: {cap-len(data):#x})")

    with open(output, "r+b") as f:
        f.seek(offset)
        f.write(data)


@click.command()
@click.option("--bypy", required=True, type=click.Path(exists=True))
@click.option("--new-pyc-file", required=True, type=click.Path(exists=True))
@click.option("--launcher", required=True, type=click.Path(exists=True))
@click.option("--embed_path", required=True, type=click.Path(exists=False))
@click.option("--output", required=False, type=click.Path(exists=False), default=None)
@click.option(
    "--os",
    type=click.Choice(["win", "linux", "mac"]),
    default="win",
    required=False,
)
def cli(
    bypy: str,
    new_pyc_file: str,
    launcher: str,
    embed_path: str,
    output: str | None = None,
    os: str = "win",
):
    patch(bypy, new_pyc_file, launcher, embed_path, output, os)


if __name__ == "__main__":
    cli()
