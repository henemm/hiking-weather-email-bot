
import subprocess

def run_test(input_file, modus, inreach=False):
    cmd = ["python", "main.py", "--input", input_file, "--dry-run", "--modus", modus]
    if inreach:
        cmd.append("--inreach")
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    print("\n=== Test: Abendmodus ===")
    run_test("tests/testdaten_abend.json", "abend")

    print("\n=== Test: Morgenmodus ===")
    run_test("tests/testdaten_morgen.json", "morgen")

    print("\n=== Test: Tageswarnung ===")
    run_test("tests/testdaten_tag_warnung.json", "tag")

    print("\n=== Test: Fehlerhafte Daten ===")
    run_test("tests/testdaten_fehlerhaft.json", "abend")

    print("\n=== Test: InReach Kurzmodus ===")
    run_test("tests/testdaten_abend.json", "abend", inreach=True)
