#/bin/bash
set -u

a=$(realpath $1)
b=$(realpath $2)

pushd $a > /dev/null
a_rpms=$(find . -name *.rpm | sort)
popd > /dev/null

pushd $b > /dev/null
b_rpms=$(find . -name *.rpm | sort)
popd > /dev/null

if [[ $a_rpms != $b_rpms ]]; then
    echo "$a_rpms != $b_rpms"
    exit 1
fi

tmp_a="$a-tmp"
tmp_b="$b-tmp"
for rpm in $a_rpms
do
    folder_name="$(dirname $rpm)/$(basename $rpm .rpm)"
    for src in $a $b
    do
        dst="${src}-tmp/$folder_name"
        mkdir -p $dst
        pushd $dst > /dev/null
        rpm2cpio $src/$rpm | cpio -idm > /dev/null 2>&1
        popd > /dev/null
    done
    diff -qr $tmp_a/$folder_name $tmp_b/$folder_name
done

