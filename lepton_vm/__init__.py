import os
import sys
import re
import json
import tarfile
import click
import requests
import shlex
import semver

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

    REPO = "https://iamale.github.io/lepton-particles/"

    def __init__(self, meta, path=None):
        self.meta = meta
        self.path = path
        self.main = path / meta["main"]

    @classmethod
    def get_local(cls, name, range_):
        versions = {}

        for path in PARTICLES_PATH:
            p_path = path / name
            if p_path.exists():
                for v_path in p_path.iterdir():
                    versions[v_path.name] = v_path

        max_version = semver.max_satisfying(versions.keys(), range_, False)
        if max_version:
            meta = json.load((versions[max_version] / "particle.json").open())
            return cls(meta, versions[max_version])

    @classmethod
    def fetch(cls, name, version):
        r = requests.get("%s/%s-%s-%s-%s.tar.lzma"
                         % (cls.REPO, name, version, "linux", "x64"),
                         stream=True)
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
@click.argument("name")
@click.argument("version")
def cmd_install(name, version):
    """
    Installs a package.
    """
    Particle.fetch(name, version)


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

    r = requests.get("%s/index.json" % Particle.REPO)
    r.raise_for_status()
    remote_particles = r.json()["particles"]

    variables = {}
    for name, range_ in package["engines"].items():
        p = Particle.get_local(name, range_)
        if not p:
            # if auto_fetch:
            if name in remote_particles:
                v = semver.max_satisfying(remote_particles[name], range_, False)
                if v:
                    print("Downloading %s %s..." % (name, v))
                    p = Particle.fetch(name, v)
                else:
                    print("Cannot satisfy %s (%s), aborting." % (name, range_))
                    sys.exit(1)
            else:
                print("No particle named %s exists, aborting." % name)
                sys.exit(1)
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
