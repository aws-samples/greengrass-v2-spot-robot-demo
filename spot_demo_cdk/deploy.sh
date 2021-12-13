source .venv/bin/activate
pip install -r requirements.txt
./package_lambdas_py3.sh
cdk bootstrap
cdk synthesize
cdk deploy