# Testing checklist

## First run

Run against one Kali VM only:

```bash
ludus range deploy -t user-defined-roles --limit '*-kali' --only-roles jahncer.kali_ctf
```

## Validate core tools

```bash
which nmap
which nxc || which netexec
which evil-winrm
which ffuf
which feroxbuster
which nuclei
which pdtm
which msfconsole
which searchsploit
which proxychains4
which chisel
which ligolo-agent
which ligolo-proxy
which kerbrute
tmux -V
```

The role performs these checks itself and fails the Ludus deployment when a
required command is missing.

## Validate XRDP from macOS

```bash
systemctl is-enabled xrdp xrdp-sesman
systemctl is-active xrdp xrdp-sesman
ss -lnt | grep ':3389'
```

From Microsoft Windows App / Microsoft Remote Desktop on macOS, connect to the
Kali VM IP on port 3389 using the Kali VM account credentials. The session
must open directly into XFCE. XRDP and its session manager must remain enabled
after a reboot.

## Validate NVIDIA RTX 3090 passthrough

When `kali_install_nvidia_gpu: true`, the role runs these checks itself after
installing the driver and rebooting the VM:

```bash
lspci -nn -d 10de:
nvidia-smi
clinfo -l
hashcat -I
systemctl is-enabled nvidia-persistenced
systemctl is-active nvidia-persistenced
```

The RTX 3090 should appear in all three compute queries. The active graphical
session should remain XRDP/Xorg on the VirtIO display adapter.

## Validate BloodHound CE

```bash
which bloodhound-cli
bh-start
bh-pass
bh-ui
cd /opt/bloodhound && docker compose ps
```

## Validate aliases

Open a new shell or run:

```bash
source ~/.zshrc
myip
ports
ctf
```

## Re-run idempotency check

Run the same Ludus role deployment a second time. Required checks must pass and
there should be no unexpected changes. Template database updates are skipped
unless `kali_update_tools: true` is explicitly set.

## Repository checks

```bash
python3 -m unittest discover -s tests -v
yamllint .
ansible-lint site.yml
ansible-playbook --syntax-check site.yml
bash -n scripts/install-ludus-role.sh
```
