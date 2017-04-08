echo 'BUILDING FOR RELEASE'
python setup.py sdist bdist_wheel clean --all
echo $PWD
curl -F package=@dist/ProsperCommon-*tar.gz $GEMFURY_URL