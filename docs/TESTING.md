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
tmux -V
```

## Validate BloodHound CE

```bash
which bloodhound-cli
bh-start
bh-pass
bh-ui
cd /opt/bloodhound-ce && docker compose ps
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

Run the same Ludus role deployment a second time. Most tasks should be `ok`; package installs should not reinstall packages that already exist.
