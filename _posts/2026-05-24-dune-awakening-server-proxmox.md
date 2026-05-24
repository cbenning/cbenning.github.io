---
layout: post
title: "Self-Hosting a Dune: Awakening Server on Proxmox / KVM"
date: 2026-05-24
tags: [dune-awakening, proxmox, kvm, self-hosting, kubernetes, gaming]
description: "Step-by-step guide to running a Dune: Awakening dedicated server in a native Linux VM on Proxmox, bypassing the official Windows + Hyper-V requirement."
status: publish
type: post
published: true
comments: true
---

<style>
.styled-table {
  border-collapse: collapse;
  margin: 1em 0;
  width: 100%;
}
.styled-table th,
.styled-table td {
  border: 1px solid #ccc;
  padding: 8px 12px;
  text-align: left;
  vertical-align: top;
}
.styled-table th {
  background-color: #f4f4f4;
  font-weight: 600;
}
.styled-table tr:nth-child(even) td {
  background-color: #fafafa;
}
</style>

## For the Live (Non-Beta) Version of the Game

This guide targets the **Live server** (Steam AppID `4754530`) — the version that connects to
Funcom's production FLS infrastructure and is visible to standard game clients in the server
browser.

If you and all of your players are on the PTC beta client instead, you would use AppID `3104830`
and connect to a separate FLS test environment. The two are **not cross-compatible** — a server
built on one cannot be seen or joined by clients on the other.

---

## Background

The official Funcom setup requires Windows + Hyper-V, but the "Windows-only" requirement is
purely a packaging wrapper. Funcom ships an Alpine Linux VHDX containing k3s + their Kubernetes
operators. Everything inside is Linux-native — this guide boots that VHDX directly under KVM
on Proxmox, with no nested virtualisation needed.

### Sources and Credits

The bulk of the reverse-engineering work was done by the community before this guide existed:

- **[adainrivers/dune-dedicated-server-manager — Issue #1: "Dune Awakening Self-Hosted Server on Linux — Generic Guide"](https://github.com/adainrivers/dune-dedicated-server-manager/issues/1)**
  — the foundational community write-up that documented running the VHDX under native KVM on
  the PTC build. This guide is a direct descendant of that work.
- **[n0logic/dune-linux-tools](https://github.com/n0logic/dune-linux-tools)** — community guide
  and tooling for bare-metal Linux + k3s deployments (Debian 12). Useful cross-reference for
  the Live AppID and tuning beyond the default scaling.
- **[snapetech/DuneAwakeningSelfHost](https://github.com/snapetech/DuneAwakeningSelfHost)** —
  Docker Compose + Web UI admin panel tooling with thorough troubleshooting docs, including
  TLS, FLS environment, and LAN reflection notes.
- **[awakening.wiki — Self-Hosted Server Guide](https://awakening.wiki/Self-Hosted_Server_Guide)**
  — community wiki page with architecture concepts (battlegroups, sietches, partitions, DBs)
  and Funcom-supported (Windows + Hyper-V) workflow.
- **Funcom's own `initial-setup.ps1` and `bootstrap/setup` scripts** — shipped in the Windows
  depot and readable as plain PowerShell / shell. These document the intended setup flow and
  revealed several details (default `dune`/`dune` credentials, pre-installed bootstrap, automatic
  disk resize) that the older PTC-era community guides predate.
- **[Funcom — Self-Hosted Servers product page](https://duneawakening.com/self-hosted-servers/)**
  and **[launch announcement](https://duneawakening.com/news/self-hosted-servers-now-live/)** —
  the official (Windows + Hyper-V) workflow, port requirements, and feature scope.
- **[Funcom Help Center — How to Self-Host a World?](https://funcom.helpshift.com/hc/en/4-dune-awakening/faq/85-how-to-self-host-a-world-1778514422/)**
  — official FAQ covering account setup, JWT generation, and the supported workflow.

This guide adds:
- Live (non-PTC) AppIDs and FLS environment
- Live-specific bootstrap flow (password is `dune`/`dune` on first boot)
- Updated port forwarding ranges confirmed from a running server
- Server password configuration via `UserEngine.ini` instead of `bg-util`
- Post-reboot recovery and troubleshooting notes

---

## Prerequisites

### Host requirements
- **AVX2 CPU** — Intel Haswell / AMD Excavator (2013) or newer. Hard requirement; the game binary will SIGILL without it. Verify with: `grep avx2 /proc/cpuinfo`
- **40+ GB RAM** allocatable to the VM (24 GB minimum but very tight; 40 GB recommended)
- **~120 GB free SSD storage** (~80 GB VM + ~5 GB Steam depot + headroom)
- **OVMF/UEFI** firmware support (standard in Proxmox)

### Accounts needed
- Dune: Awakening ownership on Steam
- Funcom account with a **self-hosting JWT** generated at `account.duneawakening.com`
- Steam credentials to download the Windows depot (the VHDX lives there; the Linux depot is anonymous)

### Network
- A real public IPv4 — **not CGNAT**. Verify your WAN IP is not in `100.64.0.0/10` or the server won't be reachable externally.

---

## Step 1 — Download the Windows Steam Depot

You only need the **Windows depot** on your workstation — it contains the VHDX.
The Linux game depot (~5 GB) is downloaded later from *inside* the VM itself in Step 6, where
the setup scripts expect it. Don't bother downloading it here.

Install `steamcmd` on any Linux machine (the Proxmox host itself works), then run:

```bash
steamcmd +@sSteamCmdForcePlatformType windows \
         +force_install_dir ~/dune-windows \
         +login YOUR_STEAM_USERNAME \
         +app_update 4754530 validate +quit
```

From this depot you only need one thing:
- `Virtual Hard Disks/dune-server.vhdx` — the Alpine Linux VM image

The `bootstrap/setup` script is pre-installed inside the VHDX — you do not need to copy it from the depot.

**Steam AppIDs:** Live Server = `4754530` · PTC Server = `3104830`. These are not cross-compatible and connect to different FLS environments. This guide uses the **Live** AppID (`4754530`) throughout.

---

## Step 2 — Convert and Resize the VHDX

```bash
qemu-img convert -f vhdx -O qcow2 dune-server.vhdx dune-server.qcow2
qemu-img resize dune-server.qcow2 80G
```

The VHDX virtual size is only 1 GB — the bootstrap expands the LVM root volume to fill the disk on first boot.

---

## Step 3 — Pre-configure the VM Disk

Mount the image via NBD to configure networking before first boot. **Run as root.**

```bash
modprobe nbd max_part=8
qemu-nbd --connect /dev/nbd0 dune-server.qcow2
vgchange -ay vg0
mount /dev/mapper/vg0-lv_root /mnt
```

Set a static IP in `/mnt/etc/network/interfaces` (or leave DHCP if your LAN supports it):
```
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
    address <VM_LAN_IP>        # adjust to your LAN
    netmask 255.255.255.0
    gateway <GATEWAY_IP>
```

**Important:** Set this before first boot. If the VM boots via DHCP first and gets a different IP, k3s will bind to that IP internally. Changing the IP afterwards requires a k3s restart and may cause pod networking issues until the cluster fully stabilises.

Set `/mnt/etc/resolv.conf`:
```
nameserver <GATEWAY_IP>
nameserver 1.1.1.1
```

**Required for KVM** — Alpine uses `mdev` not `udev`, so virtio drivers won't auto-load.
Add these to `/mnt/etc/modules`:
```
af_packet
ipv6
virtio_pci
virtio_net
virtio_scsi
virtio_blk
```

**Optional but recommended** — add serial console output to `/mnt/boot/grub/grub.cfg` for debugging.
On the `linux` line: add `console=tty0 console=ttyS0,115200n8` and remove `quiet`.

Unmount when done:
```bash
umount /mnt
vgchange -an vg0
qemu-nbd --disconnect /dev/nbd0
```

---

## Step 4 — Create the VM in Proxmox

Copy the qcow2 to your Proxmox image store:
```bash
cp dune-server.qcow2 /var/lib/vz/images/<VMID>/vm-<VMID>-disk-0.qcow2
```

Create the VM (adjust VMID, storage, and bridge as needed):
```bash
qm create 200 \
  --name dune-awakening \
  --memory 40960 \
  --cores 6 \
  --cpu host \
  --machine q35 \
  --bios ovmf \
  --efidisk0 local-lvm:1 \
  --scsihw virtio-scsi-pci \
  --scsi0 local:200/vm-200-disk-0.qcow2 \
  --net0 virtio,bridge=vmbr0 \
  --serial0 socket \
  --boot order=scsi0
```

**Critical VM settings:**

| Setting | Value | Why |
|---|---|---|
| CPU type | `host` | Required for AVX2 passthrough |
| Machine | `q35` | Required for OVMF |
| BIOS | OVMF/UEFI | The VHDX is EFI-bootable; legacy BIOS will hang at SeaBIOS |
| Disk bus | virtio-scsi | Required — add virtio modules to `/etc/modules` (done in Step 3) |
| NIC | virtio | On your LAN bridge |
{: .styled-table}

Start the VM — it should boot to an Alpine login on the serial console. Hostname is `duneawakening`.

---

## Step 5 — SSH In and Secure Access

The Live VHDX has default credentials:
- **User:** `dune`
- **Password:** `dune`

SSH in with password authentication:
```bash
ssh dune@<VM_LAN_IP>
# Enter password: dune
```

**Immediately install your own SSH key and disable password auth:**
```bash
# From your workstation
ssh-copy-id -i ~/.ssh/your_key.pub dune@<VM_LAN_IP>

# Verify your key works
ssh -i ~/.ssh/your_key dune@<VM_LAN_IP>

# Then disable password authentication
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo rc-service sshd restart
```

**Change the default dune user password** (even with key auth disabled, good practice):
```bash
passwd
```

---

## Step 6 — Bootstrap the Server

**Set your public IP** — this is what clients will connect to:
```bash
printf '\n\n\n<YOUR_PUBLIC_IP>\n' > /home/dune/.dune/settings.conf
```

**Run the setup script** (it is pre-installed in the VHDX):
```bash
/home/dune/.dune/bin/setup
```

The setup script will:
1. Check and grow the disk automatically if needed
2. Download the Linux game depot (~5 GB) via steamcmd anonymously
3. Start k3s and scale up the Funcom operators
4. Run the interactive world setup — you will be prompted for:
   - World name (e.g. `Squanchicus`)
   - Region
   - Your Funcom self-hosting JWT from `account.duneawakening.com`

**Verify pods are up after setup completes:**
```bash
sudo kubectl get pods -A
~/.dune/bin/battlegroup status
```

You should see all operators Running and the battlegroup status showing `Stopped` with Database `Ready`.
Gateway and Director will show `Suspended` — this is normal before starting.

**Expected:** Two db-dbdepl-util jobs will appear — one `Completed` and one `Error`. The error is harmless: it's a retry that tried to create the `dune` DB role after the first job already succeeded. The error will read `psycopg2.errors.DuplicateObject: role "dune" already exists`.

---

## Step 7 — Verify and Start

Check that the battlegroup is configured correctly and ready to start:

```bash
cat /home/dune/.dune/settings.conf      # line 4 should be your public IP
~/.dune/bin/battlegroup status          # should show Stopped, Database Ready
sudo kubectl get pods -A                # all pods should be Running or Completed
```

If `settings.conf` line 4 is wrong, fix it and restart k3s:
```bash
printf '\n\n\n<YOUR_PUBLIC_IP>\n' > /home/dune/.dune/settings.conf
sudo rc-service k3s restart
```

Start the battlegroup:
```bash
~/.dune/bin/battlegroup start
```

Watch pods come up:
```bash
sudo kubectl get pods -n <your-world-namespace> -w
```

Your world namespace looks like `funcom-seabass-sh-<hash>-<suffix>` and can be found with:
```bash
sudo kubectl get namespaces | grep funcom-seabass
```

After a minute or two, verify everything is healthy:
```bash
~/.dune/bin/battlegroup status
```

A healthy battlegroup looks like:

```
Status     Database   Gateway    Director   Uptime
---------- ---------- ---------- ---------- --------
Healthy    Ready      Healthy    Healthy    Xm
```

With game servers:

```
Map             Phase     Ready  Players
Overmap         Running   true   0
Survival_1      Running   true   0
```

If pods crash-loop briefly during startup (gateway, text router), that is normal — they start before the database is ready and self-recover within a few minutes.

```bash
~/.dune/bin/battlegroup start
```

Watch pods come up:
```bash
sudo kubectl get pods -n <your-world-namespace> -w
```

Your world namespace is visible in `kubectl get pods -A` — it will look like:
`funcom-seabass-sh-<hash>-<suffix>`

After a minute or two, verify everything is healthy:
```bash
~/.dune/bin/battlegroup status
```

A healthy battlegroup looks like:
```
Status     Database   Gateway    Director   Uptime
---------- ---------- ---------- ---------- --------
Healthy    Ready      Healthy    Healthy    Xm
```

With game servers:
```
Map             Phase     Ready  Players
Overmap         Running   true   0
Survival_1      Running   true   0
```

---

## Step 8 — Set a Server Password (Optional)

To restrict your server to friends only, edit `UserEngine.ini`:

```bash
nano ~/.dune/download/scripts/setup/config/UserEngine.ini
```

Find the commented-out line:
```
;Bgd.ServerLoginPassword="Sandworm"
```

Uncomment it and set your password:
```
Bgd.ServerLoginPassword="yourpassword"
```

Save the file, then apply and restart:
```bash
~/.dune/bin/battlegroup apply-default-usersettings
~/.dune/bin/battlegroup restart
```

The config is deployed to the file broker pod which serves it to all game servers at runtime —
it applies globally to all partitions without needing to set it per-map.

Players will be prompted for the password when joining your server from the browser.

**Note:** The `bg-util` TUI does have a per-partition password field but it does not reliably propagate to the live server. Use `UserEngine.ini` instead.

---

## Step 9 — Port Forwards

### Router → VM (`<VM_LAN_IP>`)

Replace `<VM_LAN_IP>` with your VM's actual LAN IP throughout.

The game servers use sequential UDP ports starting from `7777` — one port per active map
partition. The default world has up to 27 partitions (most spin up on demand as players
enter them). Forward a generous range to avoid having to update your router rules as new
partitions come online.

**Confirmed from live server logs:**
Each partition uses **two** ports — a game port and an IGW (inter-server gateway) port:
- Overmap → game `7777`, IGW `7888`
- Survival_1 → game `7778`, IGW `7889`
- Additional partitions → `7779`/`7890`, `7780`/`7891`... and so on

The IGW ports are always offset by 111 from the game ports (`7888 = 7777 + 111`).

| External Port(s) | Internal Port(s) | Protocol | Purpose |
|---|---|---|---|
| 7777–7830 | 7777–7830 | UDP | Game server partitions (one per active map) |
| 7888–7941 | 7888–7941 | UDP | IGW ports (inter-server gateway, one per partition) |
| 31982 | 31982 | TCP | RabbitMQ game queue (TLS-AMQPS, safe to expose) |
{: .styled-table}

**Why 54 ports per band?** 27 default partitions + headroom for future expansion and Sietches (player housing servers). The IGW range mirrors the game range exactly, just offset by 111. Better to forward too many than too few.

The RabbitMQ game port (`31982`) uses TLS with cert-manager-issued certs and a randomly generated 64-byte credential, so WAN exposure is acceptable.

### Verify actual ports in use at any time

```bash
# See what UDP ports are currently bound by game server processes
sudo netstat -lnup | grep DuneSandbox

# Or check the gateway logs for "came up" lines showing port assignments
sudo kubectl logs -n <your-world-namespace> -l role=igw-server-gateway | grep "came up"
```

### Do NOT expose these externally

| Port | Service |
|---|---|
| BGD NodePort | Battlegroup Director admin UI (plain HTTP, no auth) |
| MQ admin NodePort | RabbitMQ admin management UI |
| MQ game mgmt NodePort | RabbitMQ game management UI |
| 32445 | RabbitMQ admin AMQP (internal) |
| 15432 | PostgreSQL database |
{: .styled-table}

**Note:** The admin UI and RabbitMQ management NodePorts (`31805`, `30438`, `30338`) are assigned dynamically by k3s and may differ on your setup. Always verify with: `sudo kubectl get svc -n <your-world-namespace>`

---

## Admin Web Interfaces (LAN Only)

| URL | Purpose |
|---|---|
| `http://<VM_LAN_IP>:<bgd-port>` | Battlegroup Director — server health, travel queues, map status |
| `http://<VM_LAN_IP>:<mq-admin-port>` | RabbitMQ admin queues management |
| `http://<VM_LAN_IP>:<mq-game-port>` | RabbitMQ game queues management |
{: .styled-table}

These ports were assigned dynamically by k3s. If yours differ, check with: `sudo kubectl get svc -n <your-world-namespace>`

---

## Day-to-Day Operations

```bash
~/.dune/bin/battlegroup status                    # health, map list, player counts
~/.dune/bin/battlegroup start                     # start the battlegroup
~/.dune/bin/battlegroup stop                      # stop the battlegroup
~/.dune/bin/battlegroup restart                   # restart
~/.dune/bin/battlegroup update                    # pull latest patch from Steam + roll pods
~/.dune/bin/battlegroup update-from-downloads     # apply build already on disk (no Steam fetch)
~/.dune/bin/battlegroup apply-default-usersettings
~/.dune/bin/battlegroup backup [name]             # DB backup
~/.dune/bin/battlegroup import [name]             # DB restore (overwrites data!)
~/.dune/bin/battlegroup logs-export               # capture all pod logs
~/.dune/bin/battlegroup operator-logs-export
```

**Before applying any game update, take a backup:**
```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
~/.dune/bin/battlegroup backup "pre-update-$TS"
~/.dune/bin/battlegroup update
```

**Find your world namespace:**
```bash
sudo kubectl get namespaces | grep funcom-seabass
```

---

## Troubleshooting: Image Tag Mismatch

If after a reboot some pods are stuck in `ImagePullBackOff`, you have likely hit the image tag
mismatch issue. The world template references images tagged `0-0-shipping` but locally loaded
images are tagged `<buildnumber>-0-shipping`. Retag them locally:

```bash
sudo ctr -n k8s.io images list --quiet | grep seabass-
# Note the build number shown (e.g. 1960494)

BUILD=<buildnumber>
for img in $(sudo ctr -n k8s.io images list --quiet | grep seabass- | grep ${BUILD}-0-shipping); do
    new="${img/${BUILD}-0-shipping/0-0-shipping}"
    sudo ctr -n k8s.io images tag --force "$img" "$new"
done
```

Delete the stuck pods so they recreate against the retagged images:

```bash
sudo kubectl get pods -A | grep ImagePullBackOff
sudo kubectl delete pod -n <namespace> <pod-name>
```

This issue typically only appears after a reboot or game update — not on initial setup.

---

## Gotcha Cheatsheet

**1. Game binary crashes immediately** — AVX2 not exposed. Set CPU type to `host` in Proxmox.

**2. VM hangs at boot** — BIOS set to SeaBIOS. Must use OVMF/UEFI.

**3. VM boots but has no network** — virtio modules missing from `/etc/modules`.

**4. Clients hang connecting forever** — Check `settings.conf` line 4 is your public IP, then restart k3s.

**5. `ImagePullBackOff` after restart** — Image tag mismatch. Retag `<build>-0-shipping` → `0-0-shipping`.

**6. SSH locked out of fresh VM** — Default password is `dune`. Use console access in Proxmox to recover.

**7. Can't reach server from internet** — Check WAN IP is not CGNAT (`100.64.0.0/10`).

**8. Admin UI not reachable** — Battlegroup not started, or check actual NodePort with `kubectl get svc -A`.

**9. `db-dbdepl-util` pod in Error** — Harmless duplicate role error. The Completed sibling did the work.

**10. High memory usage at idle** — Hagga Basin eats 12+ GB idle. Allocate 40 GB to the VM.

**11. Gateway/text router crash-loop after reboot** — Normal. DB not ready yet, pods self-recover within ~5 minutes.

**12. Pod networking broken after IP change** — Restart k3s: `sudo rc-service k3s restart`.

---

## Architecture Reference

The VHDX contains:
- **Alpine Linux 3.23 + OpenRC**
- **k3s** (single-node Kubernetes)
- **cert-manager** for internal TLS
- **4 Funcom custom k8s operators** (battlegroup, database, server, utilities)
- **PostgreSQL** — world state database
- **RabbitMQ** — inter-pod messaging (game + admin instances)
- **Unreal Engine 5 game servers** — one pod per map partition, spun up on demand
- **Gateway, Director, Text Router** — auxiliary services

The operators are pre-baked into the VHDX at scale=0. `setup.sh` scales them up and patches
the BattleGroup CR — it does not install the operators. Running setup against a from-scratch
k3s install will fail; the VHDX is required.