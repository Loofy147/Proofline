"""Public fixture only; not a secret or production submission."""
import sys

for line in sys.stdin:
    values = []
    for token in line.split():
        try:
            values.append(int(token))
        except ValueError:
            continue
    print(sum(values))
