#!/bin/bash

branch=$(git symbolic-ref HEAD --short)
v=$(cat ../app/main.py | grep "version" | grep -Po "version=.\K([0-9]+\.[0-9]+(\.[0-9]+)?)")

if [[ $branch == "master" || $branch =~ release\/v[0-9]+\.[0-9]+\.[0-9]+ ]]
then
    export version=${v}
else
    export version=v${v}-$(git log --format="%H" -n 1 | cut -c1-15)
fi

echo $version