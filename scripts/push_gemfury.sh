echo 'BUILDING FOR RELEASE'
python setup.py sdist bdist_wheel clean --all
echo 'UPLOADING TO GEMFURY'
for file in $PWD/dist/*
do
	if [[ $file =~ tar.gz ]]
		then 
			echo $file
			curl -F package=@$file $GEMFURY_URL
		fi
done

