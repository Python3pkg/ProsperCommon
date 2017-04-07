python setup.py sdist bdist_wheel clean --all
curl -F package=@dist/ProsperCommon-*tar.gz $GEMFURY_URL