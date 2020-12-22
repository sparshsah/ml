.PHONY: diff commit clean

diff:
	clear && git status && git diff

commit:
	# e.g. `make commit f="source.py" m="commit message"`
	# TODO(sparshsah): why can't i just do `f=${f:="."}` or
	#     `[[ -z "$f" ]] && f="."` for this line?
	echo "files = $f" && echo "commit message = $m"
	git add $f && git commit -m "$m" && git push && git status

clean:
	# delete compiled bytecode
	find . -name "*.pyc" -exec rm {} +
	find . -name "*.pyo" -exec rm {} +
	find . -name "*.pyd" -exec rm {} +
	find . -name "__pycache__" -exec rm -r {} +
	find . -name ".ipynb_checkpoints" -exec rm -r {} +
