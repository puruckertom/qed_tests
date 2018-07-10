#!/bin/sh

for package in $(cat ./requirements_travis.txt)
do
    if [[ "$package" == #* ]] || [[ "$package" == *gdal* ]] || [[ "$package" == *fiona* ]] || [[ "$package" == *coverage* ]] || [[ "$package" == *conda* ]]
    then
        echo "Not installing $package"
    else
        pip install $package
    fi
done