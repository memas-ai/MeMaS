find memas -type f -name "*.py" -exec autopep8 -i {} \;
find tests -type f -name "*.py" -exec autopep8 -i {} \;
find integration-tests -type f -name "*.py" -exec autopep8 -i {} \;
