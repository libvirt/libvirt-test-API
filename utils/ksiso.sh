#!/bin/bash

# - simple support to add kernel args

cwd=`pwd`
boot_iso="boot.iso"
custom_iso="custom.iso"
boot_iso_dir="/mnt/boot_iso_dir"
custom_iso_dir="/mnt/new"
kscfg=$1


echo "- clean out any stale custom iso"
echo "- create work directories"
mkdir -p $boot_iso_dir
mkdir -p $custom_iso_dir

echo "- mount $boot_iso"
mount -t iso9660 -o loop $boot_iso $boot_iso_dir

echo "- copy original iso files to custom work directory"
cp -rf ${boot_iso_dir}/* $custom_iso_dir
chmod -R 777 ${custom_iso_dir}/* 
umount $boot_iso_dir    

echo "- copy kickstart to custom work directory"
cp $kscfg $custom_iso_dir

echo "- edit isolinux.cfg and add kickstart entry"
WORKING_ISO="${custom_iso_dir}/isolinux/isolinux.cfg"

echo "label custom_ks
  kernel vmlinuz $kernel_args
  append initrd=initrd.img ks=cdrom:/$kscfg ramdisk_size=20000" >> $WORKING_ISO

# change default boot target and timeout
DEFAULT_LINE=`cat $WORKING_ISO | grep default | head -1`
TIMEOUT_LINE=`cat $WORKING_ISO | grep timeout | head -1`

cat $WORKING_ISO | sed "s/${DEFAULT_LINE}/default custom_ks/" | sed "s/${TIMEOUT_LINE}/timeout 5/" > isocfgtmp

mv -f isocfgtmp $WORKING_ISO

# cd to custom_iso_dir, otherwise mkisofs seems to bomb...
cd $custom_iso_dir
mkisofs -R -b isolinux/isolinux.bin -no-emul-boot -boot-load-size 4 -boot-info-table -o $cwd/$custom_iso .

EXITVAL=$?
if [ $EXITVAL -ne '0' ] ; then
    echo -e "\n mkisofs exited with $EXITVAL!"
fi

# clean up
rm -rf $boot_iso_dir
rm -rf $custom_iso_dir

exit
