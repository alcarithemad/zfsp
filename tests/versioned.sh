#!/bin/bash
create_backing_file () {
    rm $1
    truncate -s 64M $1
    echo $1 created
}

create_pool_contents() {
    zfs create -p $1/n1/n2/n3
    zfs mount $1/n1/n2/n3
    pushd /$1
    chmod 765 n1
    chown 321:654 n1/n2
    echo x > n1/n2/n3/x
    echo y > n1/n2/n3/y
    echo a > a
    echo b > b
    dd if=/dev/zero of=zeros bs=4097 count=1
    mkdir -p d1/d2/d3
    mkdir -p fat/greater_than_50_character_name_to_force_use_of_a_fatzap
    mkdir -p fat/second_long_nameAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    mkdir -p fat/third_long_nameAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    mkdir -p fat/fourth_long_nameAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    pushd d1/d2/d3
    echo c > c
    chown 123:456 c
    chmod 765 c
    echo d > d
    chmod 1765 d
    popd
    popd
}

create_pool_version() {
    create_backing_file zversion_$1
    zpool create -o version=$1 -d zversion_$1 $(pwd)/zversion_$1
    create_pool_contents zversion_$1
    zpool export zversion_$1
}

for version in {1..28}; do
    create_pool_version $version
done
