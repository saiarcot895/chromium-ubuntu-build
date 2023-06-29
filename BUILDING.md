# From zero to deb packages

Instructions how to build Chromium from this repository.

## Requirements

* This guide was tested on Ubuntu 20.04.
* x86_64. No cross-building for ARM.
* 10GB free space.

## Plan

1. Setup Docker build environment.
2. Download Chromium source code.
3. Patch it.
4. Install build dependencies.
5. Build the packages and workaround problems.

## Setup Docker build environment

```
sudo apt install docker.io
sudo usermod -G docker -a $(whoami)  # we don't want to run `sudo docker` every time
sudo reboot # or logout and kill the remaining GNOME processes running from your user from the kernel terminal
cd /directory/where/everything/will/happen
docker run -it --rm -v `pwd`:/io ubuntu:20.04
apt update
```

All the following commands will assume that you are inside the docker container.
If you exit, you'll lose all the installed packages and will have to reinstall them.
So don't exit.

## Download

```
apt install git
cd /io
git clone https://github.com/saiarcot895/chromium-ubuntu-build.git
cd chromium-ubuntu-build
git branch -a
```

You'll see the available branches - Chromium build numbers. The bigger, the newer.
Choose the one that has the least error reports in the [Issues](https://github.com/saiarcot895/issues).

```
git checkout branch-4147
cp debian/changelog.focal debian/changelog
cp debian/control.standard.focal debian/control
head debian/changelog
```

You'll see something like this:

```
chromium-browser (84.0.4147.56-0ubuntu1~ppa1~20.04.1) focal; urgency=low

  * New upstream version 84.0.4147.56
  * Updated patches.

 -- Saikrishna Arcot <saiarcot895@gmail.com>  Fri, 19 Jun 2020 11:35:26 -0400
```

Record the Chromium version number: `84.0.4147.56`. It must match the changelong, there are existing reports in the issues where people mismatch and run into trouble.

```
apt install make wget xz-utils
ORIG_VERSION=84.0.4147.56 debian/rules get-packaged-orig-source
tar -xf chromium-84.0.4147.56.tar.xz
```

You should have `chromium-84.0.4147.56` directory now.

## Patch

```
cd chromium-84.0.4147.56
ln -s ../debian debian
apt install quilt
QUILT_PATCHES=debian/patches quilt push -a
```

There should not be any errors. It is important, otherwise you'll not be able to build.

## Install build dependencies

```
apt install devscripts equivs --no-install-recommends
mk-build-deps --install debian/control
```

You can optionally bake in your Google API keys. [Follow the guide](https://gist.github.com/cvan/44a6d60457b20133191bd7b104f9dcc4)
and make these exports:

```
export GOOGLEAPI_APIKEY_UBUNTU="$GOOGLE_API_KEY"
export GOOGLEAPI_CLIENTID_UBUNTU="$GOOGLE_DEFAULT_CLIENT_ID"
export GOOGLEAPI_CLIENTSECRET_UBUNTU="$GOOGLE_DEFAULT_CLIENT_SECRET"
```

## Building

We have to patch `/usr/share/xcb/dri3.xml`. Either the XML spec or `xcbgen` is broken, so it generates invalid C++ bindings.
This problem is mentioned in [Odroid forums](https://forum.odroid.com/viewtopic.php?f=177&t=39260).
`PixmapFromBuffers` is not found in Chromium source code, so we are free to patch it as we wish. For example,

```
sed -i '0,/<list type="fd" name="buffers">/s//<list type="fd" name="buf">/' /usr/share/xcb/dri3.xml
```

Finally, build:

```
debuild -b -uc -us -nc
```

The options mean:

* `-b` for the binary build.
* `-uc` for not signing the .changes file.
* `-us` for not signing the source package.
* `-nc` for not cleaning the build directory so that if it fails, you don't have to build from scratch.

You should see `.deb` packages in the parent directory, which is the same as `/directory/where/everything/will/happen/chromium-ubuntu-build`.
