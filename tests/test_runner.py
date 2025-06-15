import subprocess

tests = [
    {
        "name": "Abendmodus",
        "args": ["--input", "tests/testdaten_abend.json", "--dry-run", "--modus", "abend"]
    },
    {
        "name": "Morgenmodus",
        "args": ["--input", "tests/testdaten_morgen.json", "--dry-run", "--modus", "morgen"]
    },
    {
        "name": "Tageswarnung",
        "args": ["--input", "tests/testdaten_tag_warnung.json", "--dry-run", "--modus", "tag"]
    },
    {
        "name": "Fehlerhafte Daten",
        "args": ["--input", "tests/testdaten_fehlerhaft.json", "--dry-run", "--modus", "abend"]
    },
    {
        "name": "InReach Kurzmodus",
        "args": ["--input", "tests/testdaten_abend.json", "--dry-run", "--modus", "abend", "--inreach"]
    }
]

for test in tests:
    print(f"\n=== Test: {test['name']} ===")
    try:
        cmd = ["python", "main.py"] + test["args"]
        print("Running:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print("Fehlgeschlagen:")
        print(e.stderr.strip())