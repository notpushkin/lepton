# Lepton Version Manager

Requires Python 3.4+. [pipsi][] is recommended:

```bash
pipsi install --python python3 git+https://github.com/iamale/lepton.git#egg=lepton-vm
# or:
pip3 install git+https://github.com/iamale/lepton.git#egg=lepton-vm
```

[pipsi]: https://github.com/mitsuhiko/pipsi

## Applications

A Lepton application is a folder with a `package.json` in root. This is
a generic [package.json](https://docs.npmjs.com/files/package.json), but
in the `engines` object, at least one particle (runtime) must be specified.
Also, a `lepton` object should be there, containing a `run` command. Particle
binaries are passed as `$VARIABLE`-like strings (uppercase and `s/-/_/g`).

```json
{
  "name": "atom",
  "productName": "Atom",
  "version": "1.10.0",
  "description": "A hackable text editor for the 21st Century.",
  "engines": {
    "electron": "1.2.5"
  },
  "lepton": {
    "run": "$ELECTRON ."
  }
}
```

For now, Lepton only supports strict versioning (e. g. `0.15.2` and not
`>=0.15.2`).

## Particles

A particle is a folder with runtime and a `particle.json` file, which is just
like a package.json (we use a different name so that it won't be confused with
generic packages). It must specify a path to the binary in the `main` field
(this is what will be passed to the `lepton.run` in the packages).

```json
{
  "name": "electron",
  "productName": "Electron",
  "version": "1.2.5",
  "main": "./bin/",
  "os": ["linux"],
  "cpu": ["x64"]
}
```
