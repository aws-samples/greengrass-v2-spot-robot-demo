rm -rf _lambda_py3_output/
mkdir _lambda_py3_output
cp -R lambda_py3_* _lambda_py3_output
cd _lambda_py3_output
for d in */; do
    python3 -m pip install -r "$d"requirements.txt -t "$d"
done