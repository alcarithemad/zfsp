#!/bin/bash

static_path="$(realpath "$(dirname $0)")"/static

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

create_checksum_datasets() {
    zfs create -o checksum=sha256 $1/sha256
    cp "$static_path"/words /$1/sha256/sha256

    zfs create -o checksum=fletcher2 $1/fletcher2
    cp "$static_path"/words /$1/fletcher2/fletcher2
    zfs create -o checksum=fletcher4 $1/fletcher4
    cp "$static_path"/words /$1/fletcher4/fletcher4
}

create_compression_datasets() {
    zfs create -o compression=gzip-1 $1/gzip-1
    cp "$static_path"/words /$1/gzip-1/gzip-1
    zfs create -o compression=gzip-2 $1/gzip-2
    cp "$static_path"/words /$1/gzip-2/gzip-2
    zfs create -o compression=gzip-3 $1/gzip-3
    cp "$static_path"/words /$1/gzip-3/gzip-3
    zfs create -o compression=gzip-4 $1/gzip-4
    cp "$static_path"/words /$1/gzip-4/gzip-4
    zfs create -o compression=gzip-5 $1/gzip-5
    cp "$static_path"/words /$1/gzip-5/gzip-5
    zfs create -o compression=gzip-6 $1/gzip-6
    cp "$static_path"/words /$1/gzip-6/gzip-6
    zfs create -o compression=gzip-7 $1/gzip-7
    cp "$static_path"/words /$1/gzip-7/gzip-7
    zfs create -o compression=gzip-8 $1/gzip-8
    cp "$static_path"/words /$1/gzip-8/gzip-8
    zfs create -o compression=gzip-9 $1/gzip-9
    cp "$static_path"/words /$1/gzip-9/gzip-9

    # zfs create -o compression=zle $1/zle
    # cp "$static_path"/zeroes /$1/zle/zle

    zfs create -o compression=lzjb $1/lzjb
    cp "$static_path"/words /$1/lzjb/lzjb
}

create_fletcher2_fixtures() {
    cp "$static_path"/words /$1/fletcher2/words
    # cp "$static_path"/zeroes /$1/fletcher2/zeroes
    pushd /$1/fletcher2
    echo -en '\x01' > 01
    echo -en '\0\0\0\0\0\0\0\x01' > 0000_0000_0000_0001
    echo -en '\0\0\0\0\0\0\0\0\x01' > 0000_0000_0000_0000_01
    popd
}

create_pool_snapshots() {
    zfs snapshot $1@snap1
    zfs snapshot $1@snap2
    zfs snapshot $1@snap3
    zfs send $1@snap3 > $(pwd)/$1-send
}

create_pool_ashift_12() {
    create_backing_file ashift_12
    zpool create -o ashift=12 -d ashift_12 $(pwd)/ashift_12
    create_pool_contents ashift_12
    zpool export ashift_12
}

create_pool_simple() {
    create_backing_file simple
    zpool create -d simple $(pwd)/simple
    create_pool_contents simple
    zpool export simple
}

create_pool_nested_datasets() {
    create_backing_file nested_datasets
    zpool create -d nested_datasets $(pwd)/nested_datasets
    create_pool_contents nested_datasets
    create_checksum_datasets nested_datasets
    create_compression_datasets nested_datasets
    create_pool_snapshots nested_datasets
    zpool export nested_datasets
}

create_pool_two_vdevs() {
    create_backing_file two_vdevs_1
    create_backing_file two_vdevs_2
    zpool create -d two_vdevs $(pwd)/two_vdevs_1 $(pwd)/two_vdevs_2
    create_pool_contents two_vdevs
    zpool export two_vdevs
}

create_pool_three_vdevs() {
    create_backing_file three_vdevs_1
    create_backing_file three_vdevs_2
    create_backing_file three_vdevs_3
    zpool create -d three_vdevs $(pwd)/three_vdevs_1 $(pwd)/three_vdevs_2 $(pwd)/three_vdevs_3
    create_pool_contents three_vdevs
    zpool export three_vdevs
}

create_pool_five_vdevs() {
    create_backing_file five_vdevs_1
    create_backing_file five_vdevs_2
    create_backing_file five_vdevs_3
    create_backing_file five_vdevs_4
    create_backing_file five_vdevs_5
    zpool create -d five_vdevs $(pwd)/five_vdevs_1 $(pwd)/five_vdevs_2 $(pwd)/five_vdevs_3 $(pwd)/five_vdevs_4 $(pwd)/five_vdevs_5
    create_pool_contents five_vdevs
    zpool export five_vdevs
}

create_pool_fletcher2() {
    create_backing_file fletcher2
    zpool create -d fletcher2 $(pwd)/fletcher2
    zfs list
    zfs create -o checksum=fletcher2 fletcher2/fletcher2
    zfs mount fletcher2/fletcher2
    create_fletcher2_fixtures fletcher2
    zpool export fletcher2
}

create_pool_lz4() {
    create_backing_file lz4
    zpool create -d -o feature@lz4_compress=enabled lz4 $(pwd)/lz4
    zfs create -o compression=lz4 lz4/lz4
    zfs mount lz4/lz4
    cp "$static_path"/words /lz4/lz4/lz4
    zpool export lz4
}

create_pool_raidz1() {
    create_backing_file zraid1-1
    create_backing_file zraid1-2
    create_backing_file zraid1-3
    zpool create -d zraid1 raidz1 $(pwd)/zraid1-1 $(pwd)/zraid1-2 $(pwd)/zraid1-3
    create_pool_contents zraid1
    zpool export zraid1
}

create_pool_mirror() {
    create_backing_file zmirror1
    create_backing_file zmirror2
    zpool create -d zmirror mirror $(pwd)/zmirror1 $(pwd)/zmirror2
    create_pool_contents zmirror
    zpool export zmirror
}

create_pool_feature_x() {
    feature="$1"
    shift
    create_backing_file feature_$feature
    zpool create -d -o feature@$feature=enabled $* feature_$feature $(pwd)/feature_$feature
    create_pool_contents feature_$feature
    zpool export feature_$feature
}

create_pool_feature_large_blocks() {
    create_backing_file feature_large_blocks
    zpool create -d -o feature@large_blocks=enabled -O recordsize=256k feature_large_blocks $(pwd)/feature_large_blocks
    create_pool_contents feature_large_blocks
    cat "$static_path"/words \
        "$static_path"/words \
        "$static_path"/words \
        "$static_path"/words \
        "$static_path"/words > /feature_large_blocks/words5
    zpool export feature_large_blocks
}

create_pool_zvol() {
    create_backing_file zvol_pool
    zpool create -d zvol_pool $(pwd)/zvol_pool
    zfs create -V 128K zvol_pool/z1m
    sleep 0.1
    dd if=/dev/urandom of=/dev/zvol/zvol_pool/z1m bs=513 count=27
    zfs create -s -V 128K zvol_pool/sparse_z1m
    sleep 0.1
    dd if=/dev/urandom of=/dev/zvol/zvol_pool/sparse_z1m bs=513 count=29
    zpool export zvol_pool
}

create_pool_simple
create_pool_nested_datasets
create_pool_ashift_12
create_pool_two_vdevs
create_pool_fletcher2
create_pool_lz4
create_pool_three_vdevs
create_pool_five_vdevs
create_pool_raidz1
create_pool_mirror
create_pool_feature_x extensible_dataset -o feature@bookmarks=enabled
create_pool_feature_x hole_birth
create_pool_feature_x embedded_data
create_pool_feature_large_blocks
create_pool_zvol
