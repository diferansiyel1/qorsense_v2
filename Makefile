.PHONY: install run test clean

install:
	pip install -r requirements.txt

run:
	./run_demo.sh

test:
	./run_tests.sh

clean:
	rm -f *.pdf *.png backend.log
	rm -rf __pycache__
	rm -rf backend/__pycache__
	rm -rf tests/__pycache__
