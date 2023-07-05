find memas -type f -name "*.py" -exec autopep8 --max-line-length 120 -i {} \;
find tests -type f -name "*.py" -exec autopep8 --max-line-length 120 -i {} \;
find integration-tests -type f -name "*.py" -exec autopep8 --max-line-length 120 -i {} \;
