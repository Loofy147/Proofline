.PHONY: test compile preflight

test:
	python3 -m unittest discover -s tests -v

compile:
	python3 -m compileall -q vap_lab tests

preflight:
	python3 -m vap_lab.cli preflight --task examples/task.demo.json
