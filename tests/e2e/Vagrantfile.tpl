# -*- mode: ruby -*-
# vi: set ft=ruby :


BOX = "##BOXNAME##"

Vagrant.configure("2") do |config|
  config.vm.box = BOX
  config.vm.synced_folder ".", "/vagrant", type: "rsync"
end
