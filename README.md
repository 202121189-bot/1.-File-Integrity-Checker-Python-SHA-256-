\# 🔐 File Integrity Checker



SHA-256 based tool to detect file changes. Built for Cybersecurity \& DFIR.



\## Features

\- SHA-256 hash for every file

\- Baseline snapshot (JSON)

\- Detect: Modified / Added / Deleted files

\- No external dependencies



\## Usage

python fic.py scan <dir>      # create baseline

python fic.py check <dir>     # verify integrity

python fic.py info <dir>      # show file hashes



\## License

MIT

