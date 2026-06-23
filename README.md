# KaliSetup

A Ludus-ready Ansible role for building a Kali attacker VM that is ready for CTFs, OSCP-style practice, GOAD, Active Directory labs, web testing, and general research.

This repo is designed to replace a manually customized Kali VM with a repeatable baseline:

- base packages and quality-of-life tooling
- AD/Windows tooling
- web/recon tooling
- CTF/pwn/reversing/forensics helpers
- latest ProjectDiscovery tools via PDTM, including Nuclei
- BloodHound CE using the Docker/BloodHound CLI workflow
- IppSec-style tmux config and tmux logging
- helper aliases for common workflows
- GitHub release downloads for PEASS, Chisel, Ligolo-ng, pspy, Kerbrute, and more

## Why this shape?

Ludus applies Ansible roles to VMs after deployment. Put this role on your Ludus server, reference it from each Kali attacker VM, and rerun only the role whenever you want to refresh or rebuild the box.

## Repo layout

```text
KaliSetup/
├── README.md
├── requirements.yml
├── site.yml
├── ludus-example-kali.yml
├── scripts/
│   └── install-ludus-role.sh
└── roles/
    └── jahncer.kali_ctf/
        ├── defaults/main.yml
        ├── files/gh_release_download.py
        ├── meta/main.yml
        ├── tasks/
        │   ├── main.yml
        │   ├── packages.yml
        │   ├── directories.yml
        │   ├── pipx.yml
        │   ├── github-releases.yml
        │   ├── projectdiscovery.yml
        │   ├── bloodhound-docker.yml
        │   ├── tmux.yml
        │   ├── browser.yml
        │   └── shell.yml
        └── templates/policies.json.j2
```

## Quick start with Ludus

On the Ludus server, as the Ludus user that owns the range:

```bash
git clone https://github.com/jahncer/kali-setup.git
cd kali-setup
./scripts/install-ludus-role.sh
```

The installer intentionally does not modify Ludus's globally managed Ansible
collections. In particular, Ludus pins `community.general` for compatibility
with its Proxmox deployment modules.

Add the role to your Kali VM in the Ludus range YAML:

```yaml
roles:
  - jahncer.kali_ctf
role_vars:
  kali_user: kali
  kali_home: /home/kali
  kali_tools_dir: /opt/tools
```

Then deploy only the user-defined role against Kali:

```bash
ludus range deploy -t user-defined-roles --limit '*-kali' --only-roles jahncer.kali_ctf
```

## Local test without Ludus

Inside a Kali VM:

```bash
sudo apt update
sudo apt install -y ansible git
ansible-galaxy collection install -r requirements.yml
ansible-playbook -K site.yml
```

## BloodHound CE

This role uses BloodHound CE through Docker and `bloodhound-cli` by default.

After deployment:

```bash
bh-start
bh-pass
bh-ui
```

The admin password is captured at install time and stored locally on the Kali VM:

```text
/home/kali/.config/bloodhound/initial-admin-password.txt
```

The file is created with mode `0600`. Do not commit it to Git.

If the password is lost or the database is reset:

```bash
bh-reset
```

## RDP-first access from macOS

XRDP, XorgXRDP, and XFCE are part of the required baseline. The role enables
`xrdp` and `xrdp-sesman` at boot, configures XFCE as the remote session, and
fails provisioning if port 3389 is not listening.

Connect Microsoft Windows App / Microsoft Remote Desktop to the Kali VM IP on
port `3389` using the account credentials supplied by the Kali Ludus template.
The role does not replace the account password.

## NVIDIA RTX 3090 passthrough

For an existing Proxmox VM with the RTX 3090 already attached through
`hostpci`, enable the compute profile in the Ludus role variables:

```yaml
role_vars:
  kali_install_nvidia_gpu: true
  kali_nvidia_expected_gpu: RTX 3090
```

The role installs Kali's NVIDIA driver, kernel headers, OpenCL runtime,
Hashcat, and persistence daemon; blacklists Nouveau; reboots when required;
then fails unless `nvidia-smi`, `clinfo`, and Hashcat all detect the card.
XRDP continues to use the VirtIO display, so the 3090 remains available for
compute workloads without needing a physical monitor.

Ludus range configuration does not currently express Proxmox `hostpci`
devices. Apply this role to the existing GPU-enabled VM rather than destroying
and recreating it, or reattach the PCI device in Proxmox after a rebuild.

## Tool profiles and updates

The default profile includes CTF, AD, web, pwn, pivoting, forensics, wordlists,
BloodHound, and remote-desktop essentials. It also installs Kali's official
`kali-linux-default` metapackage first, then layers the curated CTF additions
on top. For a leaner custom image, disable only the broad Kali default baseline
while keeping the curated role packages enabled:

```yaml
role_vars:
  kali_install_default_metapackage: false
```

Cloud and wireless packages are available but disabled by default:

```yaml
role_vars:
  kali_install_cloud_tools: true
  kali_install_wireless_tools: true
```

External baseline assets are pinned and checksum-verified. To deliberately
refresh tool databases and ProjectDiscovery binaries on an existing VM:

```yaml
role_vars:
  kali_update_tools: true
```

## ProjectDiscovery / Nuclei

The essential ProjectDiscovery tools (Nuclei, httpx-toolkit, subfinder, dnsx,
and naabu) come from Kali's rolling repositories so provisioning does not
depend on GitHub API discovery. PDTM is also installed and is used to attempt
installation of the additional ProjectDiscovery utilities.

To update later:

```bash
pdtm -bp /usr/local/bin -ua
nuclei -update-templates
```

## Idempotency notes

Most tasks use Ansible modules with `state: present`, meaning packages/files/repos that already exist should be left alone. For one-time installers like BloodHound CE, the role uses guard files so repeated Ansible runs do not reinstall BloodHound or regenerate credentials.

## CI

The repository includes the validated workflow at
`docs/github-actions-ci.yml.example`. Copy it to `.github/workflows/ci.yml`
using GitHub credentials with `workflow` scope to enable automatic YAML,
Ansible lint, syntax, shell, and downloader safety checks.

## Important safety notes

- This role is intended for authorized labs, CTFs, your Ludus ranges, and environments where you have permission to test.
- Do not store real client secrets, tokens, or lab passwords in this repo.
- Use `role_vars` or local ignored files for private config.
