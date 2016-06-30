import os
import re
import json
import tarfile
import click
import requests
import shlex

from io import BytesIO
from pathlib2 import Path

PARTICLES_PATH = [Path(p).expanduser() for p in [
    "~/.lepton/particles",
    "/usr/lib/lepton/particles"
]]

@click.group(context_settings={
    "help_option_names": ["-h", "--help"],
})
def cli():
    """
    The universal runtime version manager.
    """
    pass


class Particle:
    """
    A Particle is a runtime package (i. e. Electron, nw.js or something) that
    is managed by Lepton.
    """

    def __init__(self, meta, path=None):
        self.meta = meta
        self.path = path
        self.main = path / meta["main"]

    @classmethod
    def get_local(cls, name, version):
        for path in PARTICLES_PATH:
            p_path = path / name / version
            if p_path.exists():
                meta = json.load((p_path / "particle.json").open())
                return cls(meta, p_path)

    @classmethod
    def fetch(cls, name, version):
        p = cls.get_local(name, version)
        if p:
            print("already installed")
            return p

        r = requests.get("http://localhost:5555/particles/%s-%s-%s-%s.tar.lzma"
                         % (name, version, "linux", "x64"), stream=True)
        r.raise_for_status()
        with tarfile.open(fileobj=BytesIO(r.raw.read())) as tar:
            try:
                metafile = tar.extractfile(tar.getmember("particle.json"))
                meta = json.loads(metafile.read().decode())
            except KeyError:
                raise Exception("Invalid particle: no particle.json file")
            except ValueError:
                raise Exception("Invalid particle: "
                                "particle.json is not valid JSON")

            path = PARTICLES_PATH[0] / name / version
            tar.extractall(str(path))  # dirs are created automatically
            return cls(meta, path)


@cli.command("install")
def cmd_install():
    """
    Installs a package.
    """
    Particle.fetch("electron", "1.2.5")


@cli.command("run")
@click.argument("path", default=".")
def cmd_run(path):
    """
    Runs an appliction.
    """
    os.chdir(path)
    package = Path("./package.json")
    if not package.is_file():
        raise Exception("Invalid package: no package.json file")

    package = json.load(package.open())

    if "engines" not in package or package["engines"] == {}:
        raise Exception("Invalid package: no engines specified")

    variables = {}
    for name, version in package["engines"].items():
        p = Particle.get_local(name, version)
        if not p:
            # if auto_fetch:
            print("Downloading %s..." % name)
            p = Particle.fetch(name, version)
        variables["$" + name.upper().replace("-", "_")] = str(p.main)

    pattern = re.compile('|'.join(map(re.escape, variables.keys())))

    if "lepton" not in package:
        raise Exception("Invalid package: no lepton key in particle.json")
    elif "run" not in package["lepton"]:
        raise Exception("Invalid package: no lepton.run key in particle.json")

    args = package["lepton"]["run"]
    args = pattern.sub(lambda x: variables[x.group()], args)
    args = shlex.split(args)
    print("Resulting command line: %r" % args)
    print("Current dir: %s" % os.getcwd())
    os.execvp(args[0], args)
