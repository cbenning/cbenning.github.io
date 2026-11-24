+++
title = "Webcam head tracking for Nuclear Option on Bazzite"
date = 2026-11-23
description = "Building opentrack in a distrobox so a plain webcam can stand in for a TrackIR in a Proton game, without touching the read-only host or cluttering the home folder."
[taxonomies]
tags = ["Linux", "gaming", "opentrack", "distrobox", "proton", "bazzite"]
[extra]
categories = ["gaming", "notes"]
+++

[Nuclear Option](https://store.steampowered.com/app/2168680/Nuclear_Option/) lets you look around the cockpit by turning your head, if you have a TrackIR. I don't, but [opentrack](https://github.com/opentrack/opentrack) can fake one using an ordinary webcam and a neural-net face tracker. That sounded like a quick evening project.

It wasn't, mostly because of where I was running it. My desktop is [Bazzite](https://bazzite.gg/), an immutable Fedora with a read-only `/usr`, so there's no just installing a package. I also gave myself one rule: nothing gets scattered around my home folder. What follows is the setup that worked, and the seven things that broke on the way there.

# The end result

opentrack 2026.1.0 runs in an Arch Linux distrobox with its own separate home folder. An Anker PowerConf C200 webcam feeds its NeuralNet tracker, and its Wine output pretends to be a TrackIR inside the game's Proton 10.0 prefix. The game lives in a second Steam library on another drive, which turned out to matter.

Using it is three steps:

1. Press **Start** in opentrack. It says "waiting for game...".
2. Launch Nuclear Option from Steam.
3. Turn on TrackIR in the game's options.

# How a Linux container fools a Windows game

opentrack runs in the container, but the game runs on the host's Steam. To fake a TrackIR, opentrack starts a small Windows helper inside the *game's* Proton prefix. The helper writes a registry key pointing at opentrack's fake `NPClient64.dll`, which the game loads, thinking a TrackIR is plugged in. Then it copies head pose data from Linux shared memory into Windows shared memory.

That only works if the container and the host agree on three things:

- **`/tmp`**, where the wineserver socket lives, so the helper and the game share one wineserver.
- **`/dev/shm`**, where the pose data goes.
- **File paths**, because the DLL path in the registry has to exist for the game on the host.

Distrobox shares the first two out of the box. The third is where it got interesting.

# Reading the source before it bit me

Before testing anything, I read opentrack's `proto-wine` code to see what the helper actually writes. It puts its *own install folder* into the game's registry. Installed from a normal package, that's `/usr/libexec/opentrack`, which only exists inside the container. The game would go looking for the DLL and find nothing.

The way out: a distrobox home folder is a real folder on the host, at the same path on both sides. So I built opentrack from source and installed it into the container's home, at `$HOME/.local/opt/opentrack`. Now the path in the registry is valid for the game too.

opentrack also finds Proton by looking in `~/.steam` and `~/.local/share/Steam`, which the container's home doesn't have. Two symlinks to the real Steam folders sorted that out.

# Everything else that broke

| What I saw | What was going on | Fix |
| --- | --- | --- |
| No opentrack on Flathub, Homebrew, Fedora, Debian or Ubuntu | Only the AUR has a current build with `-DSDK_WINE=ON`, which TrackIR needs | An Arch distrobox with its own home |
| `error: target not found: xplane-sdk-devel` | It's an AUR package, and `makepkg -s` only installs from the official repos | Build it from the AUR first |
| No NeuralNet tracker in the Input list | `onnxruntime` is an *optional* dependency, and without it the tracker is skipped silently | Install `onnxruntime-cpu` and rebuild |
| "Couldn't find a Wineprefix for AppId 2168680" | The AppID lookup only checks the default Steam library and ignores `libraryfolders.vdf` | Use "UMU enabled Launchers (select prefix)" and give it the prefix path |
| "Failed to start Wine! Make sure the binary is set correctly." | Proton's `bin/wine` is a 32-bit ELF, and the container had no 32-bit libraries | Enable `[multilib]`, install `lib32-glibc lib32-gcc-libs` |
| "Couldn't open the camera." | With no camera chosen, opentrack grabbed the first one: OBS Virtual Camera, blank unless OBS is running | Pick the real webcam |

The Wine one was a good puzzle. The binary was right there, but running it by hand said `No such file or directory`. That message means the *loader* is missing, and `file` showed it wanted `/lib/ld-linux.so.2`.

# Building it

Create the container with its own home:

```bash
distrobox create --name opentrack \
  --image docker.io/library/archlinux:latest \
  --home ~/.local/share/distrobox-homes/opentrack
distrobox enter opentrack
```

Then, inside it:

```bash
# 32-bit repo for Proton's wine
printf '\n[multilib]\nInclude = /etc/pacman.d/mirrorlist\n' | sudo tee -a /etc/pacman.conf
sudo pacman -Syu --needed base-devel git cmake ninja qt6-base qt6-5compat \
  qt6-tools qt6-declarative opencv onnxruntime-cpu wine procps-ng \
  lib32-glibc lib32-gcc-libs v4l-utils

# AUR build dependency
git clone https://aur.archlinux.org/xplane-sdk-devel.git
(cd xplane-sdk-devel && makepkg -si)

# fetch the source via the AUR recipe, build into the container home
git clone https://aur.archlinux.org/opentrack.git
cd opentrack && makepkg -od
cd src/opentrack-*/ && mkdir build && cd build
mkdir -p xplane_sdk/CHeaders
for d in Wrappers Widgets XPLM; do ln -sf /usr/include/xplane_sdk/$d xplane_sdk/CHeaders/; done
ONNXRuntime_ROOT=/usr cmake .. -GNinja -DCMAKE_BUILD_TYPE=Release \
  -DSDK_XPLANE=xplane_sdk -DSDK_WINE=ON \
  -DONNXRuntime_DIR=/usr/lib/cmake/onnxruntime \
  -DCMAKE_INSTALL_PREFIX="$HOME/.local/opt/opentrack"
ninja && ninja install

# let opentrack find Steam and Proton (host home is /var/home/<you> on Bazzite)
mkdir -p ~/.local/share
ln -sfn /var/home/$USER/.local/share/Steam ~/.local/share/Steam
ln -sfn /var/home/$USER/.steam ~/.steam
```

To start it from the host, save this as `~/.local/bin/opentrack`:

```sh
#!/bin/sh
# opentrack lives in the 'opentrack' distrobox, installed under its home
exec /usr/bin/distrobox-enter -n opentrack -- \
  "$HOME/.local/share/distrobox-homes/opentrack/.local/opt/opentrack/bin/opentrack" "$@"
```

A `.desktop` file with the same `Exec` line puts it in the app menu. I made a second one with `--platform xcb` added, for XWayland.

# The settings I landed on

| Setting | Value | Why |
| --- | --- | --- |
| Input | NeuralNet Tracker | Face tracking with a plain webcam. No IR LEDs or hat. |
| Camera | Real webcam, MJPEG | Otherwise it picks OBS Virtual Camera. |
| Output | Wine | On Linux, TrackIR and FreeTrack output live here. |
| Wine variant | Proton, "UMU enabled Launchers (select prefix)" | The AppID lookup misses second Steam libraries. |
| Prefix | `<library>/steamapps/compatdata/2168680/pfx` | The game's own Proton prefix. |
| Proton version | Proton 10.0 | Must match the game's, so both share one wineserver. |
| Protocol | Both (TrackIR + FreeTrack) | Covers games that use either. |
| Axis inversion | Yaw, roll and X | Tuned by hand until movement matched the game. |

# Taking it all back out

The home-folder rule paid off here. Everything opentrack made lives in `~/.local/share/distrobox-homes/opentrack`, and the only files outside it are the wrapper and two menu entries. Removing it all is one `distrobox rm opentrack`, one folder and three files.
