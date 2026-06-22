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
git clone https://github.com/jahncer/KaliSetup.git
cd KaliSetup
ansible-galaxy collection install -r requirements.yml
ludus ansible role add ./roles/jahncer.kali_ctf
ludus ansible roles list
```

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

## ProjectDiscovery / Nuclei

This role installs PDTM and uses it to install/update ProjectDiscovery tools such as Nuclei, httpx, subfinder, dnsx, naabu, katana, interactsh-client, mapcidr, tlsx, and uncover.

To update later:

```bash
pdtm -bp /usr/local/bin -ua
nuclei -update-templates
```

## Idempotency notes

Most tasks use Ansible modules with `state: present`, meaning packages/files/repos that already exist should be left alone. For one-time installers like BloodHound CE, the role uses guard files so repeated Ansible runs do not reinstall BloodHound or regenerate credentials.

## Important safety notes

- This role is intended for authorized labs, CTFs, your Ludus ranges, and environments where you have permission to test.
- Do not store real client secrets, tokens, or lab passwords in this repo.
- Use `role_vars` or local ignored files for private config.
