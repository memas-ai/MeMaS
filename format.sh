directories="memas tests integration-tests memas_client memas_sdk benchmarking"
for dir in $directories; do
    find $dir -type f -name "*.py" -exec autopep8 --max-line-length 120 -i {} \;
done